from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


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
        ("submitted", "Submitted"),
        ("manager_approved", "Manager Approved"),
        ("confirmed", "Confirmed"),
        ("done", "Done"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ], default="draft")
    notes = fields.Text()

    # --- approval metadata (audit trail) ---
    submitted_by_id = fields.Many2one("res.users", string="Submitted By", readonly=True)
    submitted_date = fields.Datetime(string="Submitted Date", readonly=True)
    manager_approved_by_id = fields.Many2one(
        "res.users", string="Level 1 Approved By", readonly=True)
    manager_approved_date = fields.Datetime(string="Level 1 Approved Date", readonly=True)
    final_approved_by_id = fields.Many2one(
        "res.users", string="Final Approved By", readonly=True)
    final_approved_date = fields.Datetime(string="Final Approved Date", readonly=True)
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)

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

    # --- approval workflow buttons ---
    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Only draft enrollment can be submitted.")
            rec.write({
                "state": "submitted",
                "submitted_by_id": self.env.user.id,
                "submitted_date": fields.Datetime.now(),
            })

    def action_manager_approve(self):
        if not self.env.user.has_group(
                "academy_management.academy_group_approval_l1"):
            raise UserError("You are not allowed to perform level 1 approval.")
        for rec in self:
            if rec.state != "submitted":
                raise UserError(
                    "Only submitted enrollment can be approved by level 1.")
            rec.write({
                "state": "manager_approved",
                "manager_approved_by_id": self.env.user.id,
                "manager_approved_date": fields.Datetime.now(),
            })

    def action_final_approve(self):
        if not self.env.user.has_group(
                "academy_management.academy_group_approval_l2"):
            raise UserError("You are not allowed to perform final approval.")
        for rec in self:
            if rec.state != "manager_approved":
                raise UserError(
                    "Only manager-approved enrollment can be finally approved.")
            rec.write({
                "state": "confirmed",
                "final_approved_by_id": self.env.user.id,
                "final_approved_date": fields.Datetime.now(),
            })

    def action_done(self):
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(
                    "Only confirmed enrollment can be marked as done.")
            rec.state = "done"

    def _reject_with_reason(self, reason):
        if not (
            self.env.user.has_group("academy_management.academy_group_approval_l1")
            or self.env.user.has_group("academy_management.academy_group_approval_l2")
        ):
            raise UserError("You are not allowed to reject this enrollment.")

        for rec in self:
            if rec.state not in ("submitted", "manager_approved"):
                raise UserError(
                    "Only submitted or manager-approved enrollment can be rejected.")
            rec.write({
                "state": "rejected",
                "rejection_reason": reason,
            })

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ("rejected", "cancelled"):
                raise UserError(
                    "Only rejected or cancelled enrollment can be reset to draft.")
            rec.state = "draft"
