from odoo import models, fields
from odoo.exceptions import UserError
import requests


class ImportExternalCoursesWizard(models.TransientModel):
    _name = "academy.import.courses.wizard"
    _description = "Import External Courses Wizard"

    api_url = fields.Char(
        string="API URL",
        default="http://localhost:9090/api/courses",
        required=True)
    last_response = fields.Text(string="Result", readonly=True)

    @property
    def _default_api_url(self):
        return self.env["ir.config_parameter"].sudo().get_param(
            "academy_management.external_courses_api_url",
            "http://localhost:9090/api/courses"
        )

    def _get_oauth2_token(self):
        token_url = self.env["ir.config_parameter"].sudo().get_param(
            "academy_management.external_courses_oauth2_token_url"
        )
        client_id = self.env["ir.config_parameter"].sudo().get_param(
            "academy_management.external_courses_oauth2_client_id"
        )
        client_secret = self.env["ir.config_parameter"].sudo().get_param(
            "academy_management.external_courses_oauth2_client_secret"
        )
        if not token_url or not client_id or not client_secret:
            return False
        try:
            token_response = requests.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=10,
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise UserError("OAuth2 token response does not contain 'access_token'.")
            return access_token
        except requests.exceptions.RequestException as error:
            raise UserError("Failed to get OAuth2 token: %s" % error)
        except ValueError:
            raise UserError("Invalid OAuth2 token response.")

    def action_import(self):
        api_url = self.api_url or self._default_api_url
        headers = {}
        token = self._get_oauth2_token()
        if token:
            headers["Authorization"] = "Bearer %s" % token
        try:
            response = requests.get(api_url, timeout=10, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            raise UserError("Failed to call API: %s" % error)

        try:
            data = response.json()
        except ValueError:
            raise UserError("Invalid JSON response.")

        courses = data.get("courses")
        if not isinstance(courses, list):
            raise UserError("Unexpected payload: 'courses' missing or invalid.")

        Course = self.env["academy.course"]
        created = 0
        updated = 0
        for item in courses:
            code = (item.get("code") or "").strip()
            name = (item.get("name") or "").strip()
            if not code or not name:
                continue
            vals = {"name": name, "code": code}
            level = item.get("level")
            if level in ("beginner", "intermediate", "advanced"):
                vals["level"] = level
            if item.get("duration_hours") is not None:
                vals["duration_hours"] = item["duration_hours"]
            if item.get("price") is not None:
                vals["price"] = item["price"]
            existing = Course.search([("code", "=", code)], limit=1)
            if existing:
                existing.write(vals)
                updated += 1
            else:
                Course.create(vals)
                created += 1

        self.last_response = "Imported: %s, Updated: %s" % (created, updated)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
