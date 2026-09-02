from odoo import fields, models


class AcademyCourseTag(models.Model):
    _name        = "academy.course.tag"
    _description = "Academy Course Tag"
    _order       = "name"

    name  = fields.Char(required=True)
    color = fields.Integer()
