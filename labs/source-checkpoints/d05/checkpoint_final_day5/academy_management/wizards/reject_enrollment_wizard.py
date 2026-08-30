from odoo import models, fields
from odoo.exceptions import UserError


class RejectEnrollmentWizard(models.TransientModel):
    _name = "academy.enrollment.reject.wizard"
    _description = "Reject Enrollment Wizard"

    rejection_reason = fields.Text(string="Rejection Reason", required=True)

    def action_reject(self):
        ids = self.env.context.get("active_ids", [])
        enrollments = self.env["academy.enrollment"].browse(ids)
        for enr in enrollments:
            if enr.state not in ("submitted", "manager_approved"):
                raise UserError(
                    "Only submitted or manager-approved enrollment "
                    "can be rejected.")
            enr.write({
                "state": "rejected",
                "rejection_reason": self.rejection_reason,
            })
        return {"type": "ir.actions.act_window_close"}
