from odoo import fields, models, api


class AcademyCourse(models.Model):
    _name = "academy.course"
    _description = "Academy Course"
    _order = "name"
    _rec_names_search = ['name', 'code']

    name = fields.Char(required=True, string="Nama Course")
    code = fields.Char(copy=False, help="Kode unik untuk course ini, misal: PYTHON-101")
    description = fields.Html()
    note = fields.Text()
    duration_hours = fields.Float()
    price = fields.Monetary()
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    level = fields.Selection([
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ], default="beginner")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "Kode course harus unik!"),
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            if record.code:
                record.display_name = f"[{record.code}] {record.name}"
            else:
                record.display_name = record.name
