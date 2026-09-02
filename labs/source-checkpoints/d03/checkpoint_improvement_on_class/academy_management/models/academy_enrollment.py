from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError


class AcademyEnrollment(models.Model):
    _name        = "academy.enrollment"
    _inherit     = ["mail.thread"]
    _description = "Academy Enrollment"

    name = fields.Char(required=True, default="New")
    batch_id = fields.Many2one(
        "academy.batch", required=True, ondelete="cascade"
    )
    batch_code = fields.Char(related="batch_id.code", store=True, readonly=True)
    batch_capacity = fields.Integer(related="batch_id.capacity", store=True, readonly=True)
    batch_start_date = fields.Date(related="batch_id.start_date", store=True, readonly=True)
    batch_end_date = fields.Date(related="batch_id.end_date", store=True, readonly=True)
    responsible_email = fields.Char(related="batch_id.responsible_id.email", store=True, readonly=True)
    student_id = fields.Many2one(
        "academy.student", required=True, ondelete="restrict"
    )
    enrollment_date = fields.Date(default=fields.Date.context_today)
    state = fields.Selection([
        ("draft",            "Draft"),
        ("submitted",        "Submitted"),
        ("manager_approved", "Manager Approved"),
        ("confirmed",        "Confirmed"),
        ("done",             "Done"),
        ("rejected",         "Rejected"),
        ("cancelled",        "Cancelled"),
    ], default="draft", tracking=True)
    notes = fields.Text()
    # jejak audit
    submitted_by_id = fields.Many2one("res.users", readonly=True, string="Submitted By")
    submitted_date = fields.Datetime(readonly=True)
    manager_approved_by_id = fields.Many2one("res.users", readonly=True,
                                             string="Level 1 Approved By")
    manager_approved_date = fields.Datetime(readonly=True)
    final_approved_by_id = fields.Many2one("res.users", readonly=True,
                                           string="Final Approved By")
    final_approved_date = fields.Datetime(readonly=True)
    rejection_reason = fields.Text(readonly=True, tracking=True)

    _sql_constraints = [
        ("unique_student_batch",
         "unique(batch_id, student_id)",
         "Student tidak boleh terdaftar dua kali di batch yang sama."),
    ]

    # @api.onchange("batch_id")
    # def _onchange_batch_id(self):
    #     if self.batch_id and self.batch_id.available_seats <= 0:
    #         return {
    #             "warning": {
    #                 "title": "Batch Penuh",
    #                 "message": "Batch ini sudah tidak punya kursi tersisa.",
    #             }
    #         }

    # @api.constrains("batch_id", "student_id")
    # def _check_batch_capacity(self):
    #     for record in self:
    #         if record.batch_id and record.student_id:
    #             if record.batch_id.available_seats <= 0:
    #                 raise ValidationError(
    #                     "Batch ini sudah tidak punya kursi tersisa."
    #                 )

    @api.constrains("batch_id", "state")
    def _check_batch_capacity_on_confirm(self):
        for record in self:
            if record.state == "confirmed" and record.batch_id:
                confirmed_enrollments = self.search_count([
                    ("batch_id", "=", record.batch_id.id),
                    ("state", "=", "confirmed")
                ])
                if record.batch_id.capacity < confirmed_enrollments:
                    raise ValidationError(
                        "Batch ini sudah tidak punya kursi tersisa."
                    )

    # Kumpulan method untuk action state management
    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Hanya enrollment draft yang bisa di-submit.")
            rec.write({
                "state": "submitted",
                "submitted_by_id": self.env.user.id,
                "submitted_date": fields.Datetime.now(),
            })

    def action_manager_approve(self):
        # if not self.env.user.has_group(
        #         "academy_management.academy_group_approval_l1"):
        #     raise UserError("Anda tidak berhak melakukan approval level 1.")
        for rec in self:
            if rec.state != "submitted":
                raise UserError(
                    "Hanya enrollment submitted yang bisa di-approve level 1.")
            rec.write({
                "state": "manager_approved",
                "manager_approved_by_id": self.env.user.id,
                "manager_approved_date": fields.Datetime.now(),
            })

    def action_final_approve(self):
        # if not self.env.user.has_group(
        #         "academy_management.academy_group_approval_l2"):
        #     raise UserError("Anda tidak berhak melakukan final approval.")
        for rec in self:
            if rec.state != "manager_approved":
                raise UserError(
                    "Hanya enrollment manager-approved yang bisa "
                    "di-final approve.")
            rec.write({
                "state": "confirmed",
                "final_approved_by_id": self.env.user.id,
                "final_approved_date": fields.Datetime.now(),
            })

    def action_done(self):
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(
                    "Hanya enrollment confirmed yang bisa diselesaikan.")
            rec.state = "done"

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ("rejected", "cancelled"):
                raise UserError(
                    "Hanya enrollment rejected atau cancelled yang bisa "
                    "dikembalikan ke draft.")
            rec.state = "draft"
