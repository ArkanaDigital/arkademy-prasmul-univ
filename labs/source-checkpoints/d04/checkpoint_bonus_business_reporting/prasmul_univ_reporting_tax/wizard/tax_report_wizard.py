from collections import defaultdict
from io import BytesIO

import xlsxwriter

from odoo import fields, models
from odoo.osv import expression


class PrasmulTaxReportWizard(models.TransientModel):
    _name = "prasmul.univ.tax.report.wizard"
    _inherit = "prasmul.xlsx.report.mixin"
    _description = "Wizard Laporan Pajak Operasional"

    company_id = fields.Many2one(
        "res.company",
        string="Perusahaan",
        required=True,
        default=lambda self: self.env.company,
        domain=lambda self: [("id", "in", self.env.companies.ids)],
    )
    date_from = fields.Date(string="Tanggal Awal", required=True, default=lambda self: fields.Date.start_of(fields.Date.context_today(self), "month"))
    date_to = fields.Date(string="Tanggal Akhir", required=True, default=fields.Date.context_today)
    output_file = fields.Binary(string="File Hasil", readonly=True, attachment=False)
    output_filename = fields.Char(string="Nama File", readonly=True)

    def action_export(self):
        self.ensure_one()
        self._validate_report_filters(self.company_id, self.date_from, self.date_to)
        self.env["account.move.line"].check_access("read")

        moves = self.env["account.move"].search(self._get_move_domain())
        rows = self._get_tax_data_sql(moves.ids)
        content = self._create_tax_workbook(rows, len(moves))
        filename = "Pajak_Operasional_%s_%s_%s.xlsx" % (
            self.company_id.name.replace(" ", "_"),
            self.date_from.strftime("%Y%m%d"),
            self.date_to.strftime("%Y%m%d"),
        )
        return self._return_xlsx_download(content, filename)

    def _get_move_domain(self):
        invoice_date_domain = [
            ("invoice_date", "!=", False),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
        ]
        journal_date_domain = [
            ("invoice_date", "=", False),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]
        return expression.AND(
            [
                [
                    ("company_id", "=", self.company_id.id),
                    ("state", "=", "posted"),
                ],
                expression.OR([invoice_date_domain, journal_date_domain]),
            ]
        )

    def _get_tax_data_sql(self, move_ids):
        """Fetch tax lines for records already allowed by ORM record rules."""
        if not move_ids:
            return []
        query = """
            SELECT
                aml.id AS move_line_id,
                COALESCE(am.invoice_date, am.date) AS report_date,
                am.date AS journal_date,
                am.name AS document_number,
                COALESCE(am.ref, '') AS reference,
                am.move_type,
                COALESCE(rp.name, '') AS partner_name,
                COALESCE(rp.vat, '') AS npwp,
                COALESCE(
                    at.name ->> 'en_US',
                    at.name ->> 'id_ID',
                    at.name::text
                ) AS tax_name,
                at.type_tax_use,
                aml.debit,
                aml.credit,
                aml.balance,
                ABS(aml.balance) AS tax_amount,
                COALESCE(am.l10n_id_tax_number, '') AS tax_document_number,
                CASE WHEN COALESCE(rp.vat, '') = '' THEN 'NPWP Kosong' ELSE 'Lengkap' END AS npwp_status
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN account_tax at ON at.id = aml.tax_line_id
            LEFT JOIN res_partner rp ON rp.id = COALESCE(aml.partner_id, am.partner_id)
            WHERE am.state = 'posted'
              AND am.id = ANY(%s)
              AND aml.company_id = %s
              AND COALESCE(am.invoice_date, am.date) BETWEEN %s AND %s
            ORDER BY COALESCE(am.invoice_date, am.date), am.name, aml.id
        """
        self.env.cr.execute(
            query,
            (move_ids, self.company_id.id, self.date_from, self.date_to),
        )
        return self.env.cr.dictfetchall()

    def _create_tax_workbook(self, rows, orm_move_count):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        formats = self._get_xlsx_formats(workbook)

        detail = workbook.add_worksheet("database")
        detail.hide_gridlines(2)
        widths = [8, 13, 13, 20, 20, 14, 30, 22, 34, 14, 16, 16, 16, 18, 24, 16]
        for col, width in enumerate(widths):
            detail.set_column(col, col, width)
        headers = [
            "ID Baris", "Tanggal Laporan", "Tanggal Jurnal", "Nomor Dokumen", "Referensi",
            "Jenis Jurnal", "Partner", "NPWP", "Pajak", "Penggunaan Pajak", "Debit", "Kredit",
            "Saldo", "Nominal Absolut", "Nomor Dokumen Pajak", "Status NPWP",
        ]
        for col, header in enumerate(headers):
            detail.write(0, col, header, formats["header"])
        for row_index, row in enumerate(rows, start=1):
            values = [
                row["move_line_id"], row["report_date"], row["journal_date"],
                row["document_number"], row["reference"], row["move_type"],
                row["partner_name"], row["npwp"], row["tax_name"], row["type_tax_use"],
                float(row["debit"] or 0), float(row["credit"] or 0),
                float(row["balance"] or 0), float(row["tax_amount"] or 0),
                row["tax_document_number"], row["npwp_status"],
            ]
            for col, value in enumerate(values):
                if col in (1, 2):
                    cell_format = formats["date"]
                elif col in (0,):
                    cell_format = formats["integer"]
                elif col in (10, 11, 12, 13):
                    cell_format = formats["amount"]
                elif col == 15:
                    cell_format = formats["status_ok"] if value == "Lengkap" else formats["status_warning"]
                else:
                    cell_format = formats["text"]
                detail.write(row_index, col, value, cell_format)
        if rows:
            detail.autofilter(0, 0, len(rows), len(headers) - 1)
        detail.freeze_panes(1, 3)

        exceptions = workbook.add_worksheet("cek npwp")
        exceptions.hide_gridlines(2)
        exception_headers = ["Nomor Dokumen", "Tanggal Laporan", "Partner", "NPWP", "Pajak", "Masalah"]
        exception_widths = [22, 14, 34, 24, 34, 20]
        for col, width in enumerate(exception_widths):
            exceptions.set_column(col, col, width)
            exceptions.write(0, col, exception_headers[col], formats["header"])
        exception_rows = [row for row in rows if row["npwp_status"] != "Lengkap"]
        for row_index, row in enumerate(exception_rows, start=1):
            values = [
                row["document_number"], row["report_date"], row["partner_name"],
                row["npwp"], row["tax_name"], row["npwp_status"],
            ]
            for col, value in enumerate(values):
                exceptions.write(row_index, col, value, formats["date"] if col == 1 else formats["text"])
        if exception_rows:
            exceptions.autofilter(0, 0, len(exception_rows), len(exception_headers) - 1)
        exceptions.freeze_panes(1, 0)

        summary_data = defaultdict(lambda: {"lines": 0, "debit": 0.0, "credit": 0.0, "balance": 0.0, "absolute": 0.0, "missing": 0})
        for row in rows:
            item = summary_data[row["tax_name"]]
            item["lines"] += 1
            item["debit"] += float(row["debit"] or 0)
            item["credit"] += float(row["credit"] or 0)
            item["balance"] += float(row["balance"] or 0)
            item["absolute"] += float(row["tax_amount"] or 0)
            item["missing"] += int(row["npwp_status"] != "Lengkap")

        summary = workbook.add_worksheet("summary")
        summary.hide_gridlines(2)
        summary.set_column("A:A", 38)
        summary.set_column("B:B", 14)
        summary.set_column("C:F", 20)
        summary.set_column("G:G", 18)
        summary.merge_range("A1:G1", "Ringkasan Pajak Operasional", formats["title"])
        summary.write("A3", "Perusahaan", formats["text"])
        summary.write("B3", self.company_id.name, formats["text"])
        summary.write("A4", "Periode", formats["text"])
        summary.write("B4", "%s s.d. %s" % (self.date_from, self.date_to), formats["text"])
        summary.merge_range(
            "A6:G7",
            "Workbook ini digunakan untuk rekonsiliasi operasional, bukan pelaporan pajak resmi. "
            "Gunakan Debit, Kredit, Saldo Bersih, dan Nominal Absolut untuk meninjau reversal dan refund.",
            formats["note"],
        )
        summary_headers = ["Pajak", "Baris", "Debit", "Kredit", "Saldo Bersih", "Nominal Absolut", "NPWP Kosong"]
        for col, header in enumerate(summary_headers):
            summary.write(8, col, header, formats["header"])
        for row_index, (tax_name, item) in enumerate(sorted(summary_data.items()), start=9):
            values = [tax_name, item["lines"], item["debit"], item["credit"], item["balance"], item["absolute"], item["missing"]]
            for col, value in enumerate(values):
                cell_format = formats["amount"] if col in (2, 3, 4, 5) else formats["integer"] if col in (1, 6) else formats["text"]
                summary.write(row_index, col, value, cell_format)
        total_row = 9 + len(summary_data)
        summary.write(total_row, 0, "Total Keseluruhan", formats["amount_bold"])
        if summary_data:
            for col in range(1, 7):
                col_name = xlsxwriter.utility.xl_col_to_name(col)
                summary.write_formula(total_row, col, "=SUM(%s10:%s%s)" % (col_name, col_name, total_row), formats["amount_bold"])
        else:
            for col in range(1, 7):
                summary.write_number(total_row, col, 0, formats["amount_bold"])
        summary.freeze_panes(9, 1)

        control = workbook.add_worksheet("Kontrol")
        control.hide_gridlines(2)
        control.set_column("A:A", 35)
        control.set_column("B:B", 20)
        control.write("A1", "Kontrol dan Rekonsiliasi", formats["title"])
        control.write("A3", "Jurnal posted yang diizinkan ORM", formats["text"])
        control.write_number("B3", orm_move_count, formats["integer"])
        control.write("A4", "Baris jurnal pajak SQL", formats["text"])
        control.write_number("B4", len(rows), formats["integer"])
        control.write("A5", "Baris dengan NPWP kosong", formats["text"])
        control.write_number("B5", len(exception_rows), formats["integer"])
        control.write("A7", "Dasar tanggal", formats["section"])
        control.write(
            "A8",
            "Tanggal invoice dipakai jika tersedia; jika kosong, laporan memakai tanggal jurnal.",
            formats["note"],
        )

        workbook.close()
        output.seek(0)
        return output.getvalue()
