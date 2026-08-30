from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    responsible_id = fields.Many2one(
        "res.users", string="Responsible",
        default=lambda self: self.env.user)
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

    @api.constrains("capacity")
    def _check_capacity(self):
        for batch in self:
            if batch.capacity <= 0:
                raise ValidationError("Capacity must be greater than 0.")

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for batch in self:
            if (batch.start_date and batch.end_date
                    and batch.start_date > batch.end_date):
                raise ValidationError(
                    "Start date must be before or equal to end date.")

    @api.constrains("capacity")
    def _check_capacity_not_below_confirmed(self):
        for batch in self:
            confirmed = self.env["academy.enrollment"].search_count([
                ("batch_id", "=", batch.id),
                ("state", "=", "confirmed"),
            ])
            if confirmed > batch.capacity:
                raise ValidationError(
                    "Capacity cannot be lower than confirmed enrollments.")
