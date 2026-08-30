from odoo import models, fields


class AcademyEnrollment(models.Model):
    _name = "academy.enrollment"
    _description = "Academy Enrollment"

    name = fields.Char(required=True, default="New")
    batch_id = fields.Many2one(
        "academy.batch", required=True, ondelete="cascade")
    student_id = fields.Many2one(
        "academy.student", required=True, ondelete="restrict")
    enrollment_date = fields.Date()
    state = fields.Selection([
        ("draft", "Draft"), ("confirmed", "Confirmed"),
        ("done", "Done"), ("cancelled", "Cancelled")], default="draft")
    notes = fields.Text()
