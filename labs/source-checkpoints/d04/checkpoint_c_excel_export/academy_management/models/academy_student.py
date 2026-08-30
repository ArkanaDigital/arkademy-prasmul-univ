from odoo import models, fields


class AcademyStudent(models.Model):
    _name = "academy.student"
    _description = "Academy Student"

    name = fields.Char(required=True)
    email = fields.Char()
    phone = fields.Char()
    birthdate = fields.Date()
    gender = fields.Selection([
        ("male", "Male"), ("female", "Female"), ("other", "Other")])
    active = fields.Boolean(default=True)
