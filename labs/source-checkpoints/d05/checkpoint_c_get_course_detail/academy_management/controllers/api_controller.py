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
