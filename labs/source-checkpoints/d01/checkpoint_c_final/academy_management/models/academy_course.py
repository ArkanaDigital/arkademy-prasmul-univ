from odoo import models, fields


class AcademyCourse(models.Model):
    _name = "academy.course"
    _description = "Academy Course"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(copy=False)
    description = fields.Html()
    duration_hours = fields.Float()
    price = fields.Monetary()
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    level = fields.Selection(
        [
            ("beginner", "Beginner"),
            ("advanced", "Advanced"),
        ],
        default="beginner",
    )
    active = fields.Boolean(default=True)
