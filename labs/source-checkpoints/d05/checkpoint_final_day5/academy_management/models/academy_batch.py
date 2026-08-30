from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, MissingError, ValidationError


class AcademyBatch(models.Model):
    _name = "academy.batch"
    _description = "Academy Batch"
    _order = "start_date desc"

    name = fields.Char(required=True)
    code = fields.Char(
        string="Batch Code",
        copy=False,
        help="Unique external reference used by the REST API "
             "(e.g. PY-101-JAN). Required for API-targeted batches.",
    )
    course_id = fields.Many2one(
        "academy.course",
        required=True,
        ondelete="restrict"
    )
    start_date = fields.Date()
    end_date = fields.Date()
    capacity = fields.Integer()
    state = fields.Selection([
        ("draft", "Draft"), ("confirmed", "Confirmed"),
        ("done", "Done"), ("cancelled", "Cancelled")], default="draft")
    enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
    enrollment_count = fields.Integer(
        compute="_compute_enrollment_count", store=True)
    available_seats = fields.Integer(
        compute="_compute_available_seats", store=True)
    responsible_id = fields.Many2one(
        "res.users", string="Responsible",
        default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique",
         "unique(code)",
         "Batch code must be unique. API-targeted batches require a unique code."),
    ]

    @api.depends("enrollment_ids")
    def _compute_enrollment_count(self):
        for batch in self:
            batch.enrollment_count = len(batch.enrollment_ids)

    @api.depends("capacity", "enrollment_ids")
    def _compute_available_seats(self):
        for batch in self:
            batch.available_seats = batch.capacity - len(batch.enrollment_ids)

    @api.constrains("capacity")
    def _check_capacity(self):
        for batch in self:
            if batch.capacity <= 0 :
                raise UserError("Capacity must be greater than 0.")

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        """
        1. Validasi pengisian start date_dan end_date
        2. Validasi start_date tidak boleh lebih besar dari end_date
        """
        for batch in self:
            # bisa comment
            # if batch.name == "Tes":
            #     raise UserError("Tidak boleh input value 'Tes' pada kolom Nama!")
            if (batch.start_date and batch.end_date
                    and batch.start_date > batch.end_date):
                raise ValidationError(
                    "Start date must be before or equal to end date.")

    @api.constrains("capacity")
    def _check_capacity_not_below_confirmed(self):
        for batch in self:
            confirmed = self.env["academy.enrollment"].search_count([
                ("batch_id", "=", batch.id),
                ("state", "=", "confirmed"),
            ])
            if confirmed > batch.capacity:
                raise ValidationError(
                    "Capacity cannot be lower than confirmed enrollments.")

    @api.constrains("enrollment_ids")
    def _check_enrollment_name(self):
        for batch in self:
            for enrolment_id in batch.enrollment_ids:
                if enrolment_id.student_id.gender == "female":
                    raise UserError(
                        "There si Enrollment Student with female gender.")

    def get_enrollment_by_batch(self, batch_id=None):
        domain = []
        if batch_id is not None:
            domain.append(("id", "=", batch_id))

        res = [
            {
                "id": batch.get('id'),
                "name": batch.get('name'),
                "course_id": batch.get('course_id')[0] if batch.get('course_id') else None,
                "course_name": batch.get('course_id')[1] if batch.get('course_id') else None,
                "start_date": batch.get('start_date'),
                "end_date": batch.get('end_date'),
                "capacity": batch.get('capacity'),
                "state": batch.get('state'),
                "enrollment_count": batch.get('enrollment_count'),
                "available_seats": batch.get('available_seats'),
            }
            for batch in self.search_read(domain, [])
        ]
        return res

    # def get_batch_enrollment_by_gender(self, batch_id=None):
    #     sql = """
    #     SELECT
    #         ae.id AS batch_id,
    #         ast.gender
    #     FROM
    #         academy_enrollment ae
    #     LEFT JOIN
    #         academy_student ast ON ae.student_id = ast.id
    #     WHERE
    #         ae.batch_id = %s
    #     """
    #     env.cr.execute(sql, (batch_id,))
    #     rows = env.cr.fetchall()

    #     domain = []
    #     if batch_id is not None:
    #         domain.append(("batch_id", "=", batch_id))
    #     male = female = 0
    #     student_ids = self.env["academy.enrollment"].search_read(domain, ["student_id"])
    #     for student in student_ids:
    #         student_record = self.env["academy.student"].browse(student.get("student_id")[0])
    #         if student_record.gender == "male":
    #             male += 1
    #         else:
    #             female += 1
    #     res = [
    #         "male": male,
    #         "female": female
    #     ]
