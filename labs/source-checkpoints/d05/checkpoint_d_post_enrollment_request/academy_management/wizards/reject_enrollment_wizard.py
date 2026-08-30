from odoo import models, fields


class RejectEnrollmentWizard(models.TransientModel):
    _name = "academy.enrollment.reject.wizard"
    _description = "Reject Enrollment Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)

    def action_reject(self):
        ids = self.env.context.get("active_ids", [])
        enrollments = self.env["academy.enrollment"].browse(ids)
        enrollments._reject_with_reason(self.rejection_reason)
        return {"type": "ir.actions.act_window_close"}
