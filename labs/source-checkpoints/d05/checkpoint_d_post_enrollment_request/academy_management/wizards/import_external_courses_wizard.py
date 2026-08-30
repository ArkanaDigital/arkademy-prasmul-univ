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

    def action_import(self):
        try:
            response = requests.get(self.api_url, timeout=10)
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
