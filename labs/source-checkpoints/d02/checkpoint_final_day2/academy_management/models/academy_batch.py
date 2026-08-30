from odoo import models, fields, api


class AcademyBatch(models.Model):
    _name = "academy.batch"
    _description = "Academy Batch"
    _order = "start_date desc"

    name = fields.Char(required=True)
    course_id = fields.Many2one(
        "academy.course", required=True, ondelete="restrict")
    start_date = fields.Date()
    end_date = fields.Date()
    capacity = fields.Integer(default=20)
    state = fields.Selection([
        ("draft", "Draft"), ("confirmed", "Confirmed"),
        ("done", "Done"), ("cancelled", "Cancelled")], default="draft")
    enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
    enrollment_count = fields.Integer(
        compute="_compute_enrollment_count", store=True)
    available_seats = fields.Integer(
        compute="_compute_available_seats", store=True)
    active = fields.Boolean(default=True)

    @api.depends("enrollment_ids")
    def _compute_enrollment_count(self):
        for batch in self:
            batch.enrollment_count = len(batch.enrollment_ids)

    @api.depends("capacity", "enrollment_ids")
    def _compute_available_seats(self):
        for batch in self:
            batch.available_seats = batch.capacity - len(batch.enrollment_ids)

    @api.onchange("course_id")
    def _onchange_course_id(self):
        if self.course_id:
            self.name = self.course_id.name
