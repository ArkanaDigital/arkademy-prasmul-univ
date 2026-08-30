from odoo import http
from odoo.http import request
import json


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def _ok(data, status=200):
    return request.make_response(
        json.dumps({"success": True, "data": data, "error": None}),
        headers=[("Content-Type", "application/json")],
        status=status,
    )


def _err(code, message, status=400):
    return request.make_response(
        json.dumps({
            "success": False,
            "data": None,
            "error": {"code": code, "message": message},
        }),
        headers=[("Content-Type", "application/json")],
        status=status,
    )


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class AcademyApiController(http.Controller):

    # -- serializer ----------------------------------------------------------

    def _course_to_dict(self, course):
        return {
            "code": course.code or "",
            "name": course.name,
            "level": course.level or "",
            "duration_hours": course.duration_hours,
        }

    # -- endpoints -----------------------------------------------------------

    @http.route(
        "/academy/api/v1/ping",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def ping(self, **kw):
        return _ok({"status": "ok", "version": "1.0"})

    @http.route(
        "/academy/api/v1/courses",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def get_courses(self, **kw):
        courses = request.env["academy.course"].sudo().search([])
        return _ok([self._course_to_dict(c) for c in courses])

    @http.route(
        "/academy/api/v1/courses/<string:code>",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def get_course(self, code, **kw):
        course = request.env["academy.course"].sudo().search(
            [("code", "=", code)], limit=1
        )
        if not course:
            return _err(
                "COURSE_NOT_FOUND",
                "Course with code '%s' not found." % code,
                status=404,
            )
        return _ok(self._course_to_dict(course))

    @http.route(
        "/academy/api/v1/enrollment-requests",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def create_enrollment_request(self, **kw):
        # 1. Parse JSON body
        try:
            payload = json.loads(request.httprequest.data or b"{}")
        except (json.JSONDecodeError, ValueError):
            return _err("INVALID_JSON", "Request body must be valid JSON.", status=400)

        # 2. Validate required fields
        required = ["student_name", "student_email", "batch_code"]
        missing = [f for f in required if not (payload.get(f) or "").strip()]
        if missing:
            return _err(
                "MISSING_FIELDS",
                "Required fields missing: %s." % ", ".join(missing),
                status=400,
            )

        student_name  = payload["student_name"].strip()
        student_email = payload["student_email"].strip()
        batch_code    = payload["batch_code"].strip()
        notes         = (payload.get("notes") or "").strip()

        env = request.env

        # 3. Lookup batch by code — NEVER auto-create
        batch = env["academy.batch"].sudo().search(
            [("code", "=", batch_code)], limit=1
        )
        if not batch:
            return _err(
                "BATCH_NOT_FOUND",
                "Batch with code '%s' not found." % batch_code,
                status=404,
            )

        # 4. Find or create student by email
        student = env["academy.student"].sudo().search(
            [("email", "=", student_email)], limit=1
        )
        if not student:
            student = env["academy.student"].sudo().create({
                "name": student_name,
                "email": student_email,
            })

        # 5. Check for existing enrollment (same student + same batch)
        existing = env["academy.enrollment"].sudo().search([
            ("batch_id", "=", batch.id),
            ("student_id", "=", student.id),
        ], limit=1)

        if existing:
            # 200 OK — not a new resource
            return _ok(
                {
                    "enrollment_id": existing.id,
                    "enrollment_name": existing.name,
                    "state": existing.state,
                    "note": "Enrollment already exists.",
                },
                status=200,
            )

        # 6. Create new enrollment
        # IMPORTANT: state is left as default ("draft").
        # Do NOT set state="confirmed".
        # Do NOT write approval metadata (submitted_by_id, etc.).
        # The approval workflow runs through the normal Odoo UI.
        enrollment = env["academy.enrollment"].sudo().create({
            "batch_id": batch.id,
            "student_id": student.id,
            "notes": notes,
        })

        # 201 Created — new resource
        return _ok(
            {
                "enrollment_id": enrollment.id,
                "enrollment_name": enrollment.name,
                "state": enrollment.state,
                "batch_code": batch_code,
                "student_email": student_email,
            },
            status=201,
        )
