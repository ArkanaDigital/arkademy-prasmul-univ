from odoo import http
from odoo.http import request
import json


class AcademyApiController(http.Controller):

    @http.route(
        "/academy/api/v1/ping",
        type="http",
        auth="public",
        methods=["GET"],
    )
    def ping(self, **kw):
        payload = {
            "success": True,
            "data": {"status": "ok", "version": "1.0"},
            "error": None,
        }
        return request.make_response(
            json.dumps(payload),
            headers=[("Content-Type", "application/json")],
            status=200,
        )
