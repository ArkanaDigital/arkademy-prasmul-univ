from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AcademyStudent(models.Model):
    _name = "academy.student"
    _description = "Academy Student"
    _order = "name"

    name = fields.Char(required=True)
    email = fields.Char()
    phone = fields.Char()
    birthdate = fields.Date()
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
    )
    active = fields.Boolean(default=True)
    nim = fields.Char(string="NIM", copy=False, default='New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('nim', _("New")) == _("New"):
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.now()
                )
                vals['nim'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(
                    'academy.student', sequence_date=seq_date) or _("New")

        return super().create(vals_list)

    def unlink(self):
        if self.active:
            raise UserError(_("You cannot delete an active student. Please deactivate the student first."))
        return super().unlink()
