from datetime import timedelta

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AcademyBatch(models.Model):
    _name = "academy.batch"
    _description = "Academy Batch"
    _order = "start_date desc"

    def default_course_id(self):
        # Return the first course as default, or None if no courses exist
        first_course = self.env['academy.course'].search([], limit=1)
        return first_course.id if first_course else None

    def default_code_generator(self):
        # Generate a default code based on the course code and current date
        if self.course_id:
            course_code = self.course_id.code or "COURSE"
            date_str = fields.Date.today().strftime("%Y%m%d")
            return f"{course_code}-{date_str}"
        return "BATCH-DEFAULT"

    name = fields.Char(required=True)
    course_id = fields.Many2one(
        comodel_name="academy.course",
        # domain="['&', ('code', '!=', False), ('duration_hours', '>', 0)]",
        # domain="['|', ('level', '=', 'beginner'), ('level', '=', 'advanced')]",
        domain="[('level', 'in', ['beginner', 'intermediate'])]",
        required=True,
        ondelete="restrict",
        default=lambda self: self.default_course_id(),
    )
    code = fields.Char(
        string="Batch Code", copy=False,
        help="Referensi unik yang dipakai REST API (contoh: PY-101-JAN).",
        default=lambda self: self.default_code_generator()
    )
    start_date = fields.Date()
    end_date = fields.Date()
    capacity = fields.Integer(default=20)
    state = fields.Selection([
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ], default="draft")
    enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
    responsible_id = fields.Many2one(
        comodel_name="res.users", string="Responsible",
        default=lambda self: self.env.user,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Batch code harus unik."),
        ("capacity_positive", "CHECK (capacity > 0)", "Capacity harus lebih dari 0."),
    ]

    enrollment_count = fields.Integer(
        compute="_compute_enrollment_count", store=True)
    available_seats = fields.Integer(
        compute="_compute_available_seats", store=True)

    @api.depends("enrollment_ids")
    def _compute_enrollment_count(self):
        # untuk setiap batch, hitung jumlah enrollment yang terkait dan simpan di field enrollment_count
        for batch in self:
            batch.enrollment_count = len(batch.enrollment_ids)

    @api.depends("capacity", "enrollment_ids")
    def _compute_available_seats(self):
        for batch in self:
            batch.available_seats = batch.capacity - len(batch.enrollment_ids)

    # @api.constrains("capacity", "enrollment_ids")
    # def _check_capacity_not_less_than_enrollments(self):
    #     for batch in self:
    #         enrolled = len(batch.enrollment_ids)
    #         if batch.capacity is not None and batch.capacity < enrolled:
    #             raise ValidationError(
    #                 f"Capacity ({batch.capacity}) cannot be less than "
    #                 f"number of enrollments ({enrolled})."
    #             )

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for batch in self:
            if (batch.start_date and batch.end_date
                    and batch.start_date > batch.end_date):
                raise ValidationError(
                    "Start date harus sebelum atau sama dengan end date."
                )

    @api.constrains("capacity", "enrollment_ids")
    def _check_capacity_not_below_confirmed(self):
        for batch in self:
            confirmed = self.env["academy.enrollment"].search_count([
                ("batch_id", "=", batch.id),
                ("state", "=", "confirmed"),
            ])
            if confirmed > batch.capacity:
                raise ValidationError(
                    "Capacity tidak boleh lebih kecil dari jumlah "
                    "enrollment yang sudah confirmed."
                )

    @api.onchange("start_date")
    def _onchange_start_end_dates(self):
        for batch in self:
            if batch.start_date:
                batch.end_date = batch.start_date + timedelta(days=3)
            else:
                batch.end_date = None
