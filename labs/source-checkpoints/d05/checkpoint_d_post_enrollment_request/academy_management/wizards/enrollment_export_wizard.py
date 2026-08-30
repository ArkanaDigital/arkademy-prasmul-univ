from odoo import models, fields
import io
import base64
import xlsxwriter


class EnrollmentExportWizard(models.TransientModel):
    _name = "academy.enrollment.export.wizard"
    _description = "Enrollment Export Wizard"

    date_from = fields.Date()
    date_to = fields.Date()
    batch_id = fields.Many2one("academy.batch")
    file_data = fields.Binary(string="File", readonly=True)
    file_name = fields.Char()

    def action_export(self):
        domain = []
        if self.date_from:
            domain.append(("enrollment_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("enrollment_date", "<=", self.date_to))
        if self.batch_id:
            domain.append(("batch_id", "=", self.batch_id.id))
        records = self.env["academy.enrollment"].search(domain)

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        sheet = workbook.add_worksheet("Enrollments")
        headers = ["Enrollment Name", "Student", "Course",
                   "Batch", "Enrollment Date", "State"]
        for col, header in enumerate(headers):
            sheet.write(0, col, header)
        row = 1
        for enr in records:
            sheet.write(row, 0, enr.name or "")
            sheet.write(row, 1, enr.student_id.name or "")
            sheet.write(row, 2, enr.batch_id.course_id.name or "")
            sheet.write(row, 3, enr.batch_id.name or "")
            sheet.write(row, 4, str(enr.enrollment_date or ""))
            sheet.write(row, 5, enr.state or "")
            row += 1
        workbook.close()
        buffer.seek(0)
        self.file_data = base64.b64encode(buffer.read())
        self.file_name = "enrollments.xlsx"
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
