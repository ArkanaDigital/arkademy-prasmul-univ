from odoo import models, fields
from odoo.exceptions import ValidationError, UserError


class AcademyCourse(models.Model):
    _name = "academy.course"
    _description = "Academy Course"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(copy=False)
    description = fields.Html()
    duration_hours = fields.Float()
    price = fields.Monetary()
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    batch_ids = fields.One2many(
        "academy.batch", "course_id", string="Batches"
    )
    level = fields.Selection(
        [
            ("beginner", "Beginner"),
            # ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="beginner",
    )
    active = fields.Boolean(default=True)

    def get_active_course(self, level=None):
        """Return active courses as a list of dictionaries."""
        domain = [("active", "=", True)]
        if level is not None:
            domain.append(("level", "=", level))
        return [
            {
                "code": course.code,
                "name": course.name,
                "level": course.level,
                "duration_hours": course.duration_hours,
                "price": course.price,
            }
            for course in self.search(domain)
        ]

    def get_beginner_courses(self):
        """Return active beginner courses as a list of dictionaries."""
        return self.get_active_course(level="beginner")

    def get_detailed_course_by_code(self, code):
        """Return detailed course information by course code."""
        course = self.env["academy.course"].sudo().search(
            [("code", "=", code)], limit=1
        )
        if not course:
            return None
        return course
