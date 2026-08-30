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
        """
        Cari data enrollment berdasarkan input filter
        * start_date
        * end_date
        * batch_id
        """

        # Menyusun domain
        domain = []
        if self.date_from:
            domain.append(("enrollment_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("enrollment_date", "<=", self.date_to))
        if self.batch_id:
            domain.append(("batch_id", "=", self.batch_id.id))
        # eksekusi search dengan domain yang sudah disusun
        records = self.env["academy.enrollment"].search(domain)

        buffer = io.BytesIO()
        # 1. Inisialisasi Workbook dan Worksheet
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        sheet = workbook.add_worksheet("Enrollments")

        # 2. Definisi Format / Styling (Agar Excel Terlihat Profesional)
        header_format = workbook.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "vcenter",
            "align": "center",
            "fg_color": "#2F5597",  # Warna biru formal
            "font_color": "white",
            "border": 1
        })

        data_format = workbook.add_format({
            "valign": "vcenter",
            "border": 1
        })

        # 3. Menulis Header
        headers = [
            "Enrollment Name", 
            "Student", 
            "Course",
            "Batch", 
            "Enrollment Date", 
            "State"
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # 4. Menulis Data Records
        for row, enr in enumerate(records, start=1):
            sheet.write(row, 0, enr.name or "", data_format)
            sheet.write(row, 1, enr.student_id.name or "", data_format)
            sheet.write(row, 2, enr.batch_id.course_id.name or "", data_format)
            sheet.write(row, 3, enr.batch_id.name or "", data_format)
            sheet.write(row, 4, str(enr.enrollment_date or ""), data_format)
            sheet.write(row, 5, enr.state or "", data_format)

        # 5. Auto-fit Lebar Kolom (Agar teks tidak terpotong ###)
        sheet.autofit()

        # 6. Tutup Workbook
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
