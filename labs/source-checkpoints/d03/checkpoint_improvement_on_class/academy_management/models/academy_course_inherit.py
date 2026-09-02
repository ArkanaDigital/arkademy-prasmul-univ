from odoo import fields, models


class AcademyCourse(models.Model):
    _inherit = "academy.course"

    is_published   = fields.Boolean(default=False)
    internal_notes = fields.Text()
    tag_ids        = fields.Many2many("academy.course.tag", string="Tags")
