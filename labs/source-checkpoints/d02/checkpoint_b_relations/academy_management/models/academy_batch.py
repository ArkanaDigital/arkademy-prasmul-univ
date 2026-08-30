from odoo import models, fields


class AcademyBatch(models.Model):
    _name = "academy.batch"
    _description = "Academy Batch"
    _order = "start_date desc"

    name = fields.Char(required=True)
    course_id = fields.Many2one(
        "academy.course", required=True, ondelete="restrict")
    start_date = fields.Date()
    end_date = fields.Date()
    capacity = fields.Integer()
    state = fields.Selection([
        ("draft", "Draft"), ("confirmed", "Confirmed"),
        ("done", "Done"), ("cancelled", "Cancelled")], default="draft")
    enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
    active = fields.Boolean(default=True)
