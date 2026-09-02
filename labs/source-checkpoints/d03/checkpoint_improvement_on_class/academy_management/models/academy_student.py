from odoo import fields, models


class AcademyStudent(models.Model):
    _name        = "academy.student"
    _description = "Academy Student"
    _order       = "name"

    name      = fields.Char(required=True)
    email     = fields.Char()
    phone     = fields.Char()
    birthdate = fields.Date()
    gender    = fields.Selection([
        ("male",   "Male"),
        ("female", "Female"),
        ("other",  "Other"),
    ])
    active    = fields.Boolean(default=True)
