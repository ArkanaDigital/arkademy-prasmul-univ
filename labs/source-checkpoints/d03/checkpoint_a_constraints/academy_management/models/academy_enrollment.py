from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AcademyEnrollment(models.Model):
    _name = "academy.enrollment"
    _description = "Academy Enrollment"

    name = fields.Char(required=True, default="New")
    batch_id = fields.Many2one(
        "academy.batch", required=True, ondelete="cascade")
    student_id = fields.Many2one(
        "academy.student", required=True, ondelete="restrict")
    enrollment_date = fields.Date(default=fields.Date.context_today)
    state = fields.Selection([
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ], default="draft")
    notes = fields.Text()

    _sql_constraints = [
        ("unique_student_batch",
         "unique(batch_id, student_id)",
         "A student cannot be enrolled twice in the same batch."),
    ]

    @api.constrains("state", "batch_id")
    def _check_capacity(self):
        for enr in self:
            if enr.state == "confirmed" and enr.batch_id.capacity:
                confirmed = self.search_count([
                    ("batch_id", "=", enr.batch_id.id),
                    ("state", "=", "confirmed"),
                ])
                if confirmed > enr.batch_id.capacity:
                    raise ValidationError("Batch capacity exceeded.")
