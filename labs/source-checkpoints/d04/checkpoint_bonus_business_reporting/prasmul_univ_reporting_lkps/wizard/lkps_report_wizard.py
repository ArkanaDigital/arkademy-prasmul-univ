from collections import defaultdict
from io import BytesIO

import xlsxwriter

from odoo import _, fields, models


class PrasmulLkpsReportWizard(models.TransientModel):
    _name = "prasmul.univ.lkps.report.wizard"
    _inherit = "prasmul.xlsx.report.mixin"
    _description = "Wizard Laporan Finansial LKPS Parsial"

    company_id = fields.Many2one(
        "res.company",
        string="Perusahaan",
        required=True,
        default=lambda self: self.env.company,
        domain=lambda self: [("id", "in", self.env.companies.ids)],
    )
    date_from = fields.Date(string="Tanggal Awal", required=True, default=lambda self: fields.Date.start_of(fields.Date.context_today(self), "year"))
    date_to = fields.Date(string="Tanggal Akhir", required=True, default=fields.Date.context_today)
    output_file = fields.Binary(string="File Hasil", readonly=True, attachment=False)
    output_filename = fields.Char(string="Nama File", readonly=True)

    def action_export(self):
        self.ensure_one()
        self._validate_report_filters(self.company_id, self.date_from, self.date_to)
        self.env["account.move.line"].check_access("read")

        moves = self.env["account.move"].search(self._get_move_domain())
        rows = self._get_lkps_data_sql(moves.ids)
        content = self._create_lkps_workbook(rows, len(moves))
        filename = "LKPS_Parsial_%s_%s_%s.xlsx" % (
            self.company_id.name.replace(" ", "_"),
            self.date_from.strftime("%Y%m%d"),
            self.date_to.strftime("%Y%m%d"),
        )
        return self._return_xlsx_download(content, filename)

    def _get_move_domain(self):
        return [
            ("company_id", "=", self.company_id.id),
            ("state", "=", "posted"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]

    def _get_lkps_data_sql(self, move_ids):
        """Return account-level data for records already allowed by ORM rules."""
        if not move_ids:
            return []
        query = """
            WITH source AS (
                SELECT
                    EXTRACT(YEAR FROM aml.date)::integer AS report_year,
                    aml.account_id,
                    COALESCE(
                        aa.code_store ->> am.company_id::text,
                        aa.code_store ->> '1',
                        ''
                    ) AS account_code,
                    COALESCE(
                        aa.name ->> 'en_US',
                        aa.name ->> 'id_ID',
                        aa.name::text
                    ) AS account_name,
                    aa.account_type,
                    COALESCE(aml.analytic_distribution::text, '') AS analytic_distribution,
                    COUNT(aml.id) AS line_count,
                    SUM(
                        CASE
                            WHEN aa.account_type IN ('income', 'income_other')
                            THEN -aml.balance
                            ELSE aml.balance
                        END
                    ) AS amount
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                JOIN account_account aa ON aa.id = aml.account_id
                WHERE am.state = 'posted'
                  AND am.id = ANY(%s)
                  AND aml.company_id = %s
                  AND aml.date BETWEEN %s AND %s
                  AND aa.account_type IN (
                      'income', 'income_other', 'expense',
                      'expense_depreciation', 'expense_direct_cost', 'asset_fixed'
                  )
                GROUP BY
                    EXTRACT(YEAR FROM aml.date), aml.account_id,
                    aa.code_store, aa.name, aa.account_type,
                    am.company_id, aml.analytic_distribution
            )
            SELECT
                report_year,
                account_code,
                account_name,
                account_type,
                analytic_distribution,
                line_count,
                amount
            FROM source
            ORDER BY report_year, account_type, account_code, analytic_distribution
        """
        self.env.cr.execute(
            query,
            (move_ids, self.company_id.id, self.date_from, self.date_to),
        )
        return self.env.cr.dictfetchall()

    @staticmethod
    def _classify_account(row):
        name = (row["account_name"] or "").lower()
        account_type = row["account_type"]

        if account_type in ("income", "income_other"):
            if any(word in name for word in ("government", "pemerintah", "hibah")):
                return "Pendapatan - Pemerintah", "Terpetakan"
            if any(word in name for word in ("student", "mahasiswa", "tuition", "spp")):
                return "Pendapatan - Mahasiswa", "Terpetakan"
            if any(word in name for word in ("training", "consult", "professional", "jasa")):
                return "Pendapatan - Kegiatan Profesional", "Terpetakan"
            return "Pendapatan - Lainnya", "Perlu Ditinjau"

        if account_type == "asset_fixed":
            return "Investasi - Sarana dan Prasarana", "Perlu Ditinjau"
        if any(word in name for word in ("research", "penelitian")):
            return "Biaya - Penelitian", "Terpetakan"
        if any(word in name for word in ("community", "pengabdian", "pkm")):
            return "Biaya - Pengabdian kepada Masyarakat", "Terpetakan"
        if any(word in name for word in ("salary", "payroll", "employee", "benefit", "overtime")):
            return "Biaya - Sumber Daya Manusia", "Terpetakan"
        if any(word in name for word in ("student", "mahasiswa", "kemahasiswaan")):
            return "Biaya - Kegiatan Mahasiswa", "Terpetakan"
        if any(word in name for word in ("learning", "course", "academic", "education", "pembelajaran")):
            return "Biaya - Operasional Pembelajaran", "Terpetakan"
        return "Biaya - Operasional Tidak Langsung", "Perlu Ditinjau"

    def _create_lkps_workbook(self, rows, orm_move_count):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        formats = self._get_xlsx_formats(workbook)

        years = sorted({row["report_year"] for row in rows})
        categories = [
            "Pendapatan - Pemerintah",
            "Pendapatan - Mahasiswa",
            "Pendapatan - Kegiatan Profesional",
            "Pendapatan - Lainnya",
            "Biaya - Sumber Daya Manusia",
            "Biaya - Operasional Pembelajaran",
            "Biaya - Operasional Tidak Langsung",
            "Biaya - Kegiatan Mahasiswa",
            "Biaya - Penelitian",
            "Biaya - Pengabdian kepada Masyarakat",
            "Investasi - Sarana dan Prasarana",
        ]
        totals = defaultdict(float)
        coverage = defaultdict(lambda: {"lines": 0, "status": "Terpetakan"})
        for row in rows:
            category, status = self._classify_account(row)
            row["lkps_category"] = category
            row["mapping_status"] = status
            totals[(category, row["report_year"])] += float(row["amount"] or 0)
            coverage[category]["lines"] += row["line_count"]
            if status != "Terpetakan" or not row["analytic_distribution"]:
                coverage[category]["status"] = "Perlu Ditinjau"

        sheet = workbook.add_worksheet("Finansial LKPS")
        sheet.hide_gridlines(2)
        sheet.set_column("A:A", 12)
        sheet.set_column("B:B", 43)
        sheet.set_column("C:C", 22)
        if years:
            sheet.set_column(3, 2 + len(years), 17)
        sheet.set_column(3 + len(years), 3 + len(years), 17)
        sheet.set_column(4 + len(years), 4 + len(years), 18)
        last_col = 4 + len(years)
        sheet.merge_range(0, 0, 0, last_col, "Laporan Finansial LKPS Parsial", formats["title"])
        sheet.set_row(0, 25)
        sheet.write(2, 0, "Perusahaan", formats["text"])
        sheet.write(2, 1, self.company_id.name, formats["text"])
        sheet.write(3, 0, "Periode", formats["text"])
        sheet.write(3, 1, "%s s.d. %s" % (self.date_from, self.date_to), formats["text"])
        sheet.merge_range(
            5,
            0,
            6,
            last_col,
            "Catatan cakupan: workbook memakai periode accounting aktual. TS, TS-1, dan TS-2 "
            "belum ditetapkan. Indikator LKPS nonfinansial berada di luar laporan ini.",
            formats["note"],
        )

        header_row = 8
        headers = ["No", "Kategori Finansial LKPS", "Dasar Mapping"] + [str(year) for year in years] + ["Rata-rata", "Cakupan"]
        for col, header in enumerate(headers):
            sheet.write(header_row, col, header, formats["header"])
        sheet.freeze_panes(header_row + 1, 3)

        first_data_row = header_row + 1
        for index, category in enumerate(categories, start=1):
            row_index = first_data_row + index - 1
            sheet.write_number(row_index, 0, index, formats["integer"])
            sheet.write(row_index, 1, category, formats["text"])
            sheet.write(row_index, 2, "Kata pada nama akun + jenis akun", formats["text_wrap"])
            for offset, year in enumerate(years):
                sheet.write_number(row_index, 3 + offset, totals[(category, year)], formats["amount"])
            average_col = 3 + len(years)
            if years:
                sheet.write_formula(
                    row_index,
                    average_col,
                    "=AVERAGE(%s:%s)" % (
                        xlsxwriter.utility.xl_col_to_name(3) + str(row_index + 1),
                        xlsxwriter.utility.xl_col_to_name(average_col - 1) + str(row_index + 1),
                    ),
                    formats["amount"],
                )
            else:
                sheet.write_number(row_index, average_col, 0, formats["amount"])
            status = coverage[category]["status"] if coverage[category]["lines"] else "Tidak Ada Data"
            sheet.write(
                row_index,
                average_col + 1,
                status,
                formats["status_ok"] if status == "Terpetakan" else formats["status_warning"],
            )

        mapping = workbook.add_worksheet("Mapping & Cakupan")
        mapping.hide_gridlines(2)
        mapping.set_column("A:A", 10)
        mapping.set_column("B:B", 18)
        mapping.set_column("C:C", 16)
        mapping.set_column("D:D", 40)
        mapping.set_column("E:E", 26)
        mapping.set_column("F:F", 15)
        mapping.set_column("G:G", 14)
        mapping_headers = ["Tahun", "Kode Akun", "Jenis Akun", "Nama Akun", "Kategori LKPS", "Baris Jurnal", "Status"]
        for col, header in enumerate(mapping_headers):
            mapping.write(0, col, header, formats["header"])
        account_coverage = defaultdict(lambda: {"lines": 0, "status": "Terpetakan"})
        for row in rows:
            key = (row["report_year"], row["account_code"], row["account_type"], row["account_name"], row["lkps_category"])
            account_coverage[key]["lines"] += row["line_count"]
            if row["mapping_status"] != "Terpetakan":
                account_coverage[key]["status"] = "Perlu Ditinjau"
        for row_index, (key, info) in enumerate(sorted(account_coverage.items()), start=1):
            values = list(key) + [info["lines"], info["status"]]
            for col, value in enumerate(values):
                cell_format = formats["integer"] if col == 5 else formats["text"]
                if col == 6:
                    cell_format = formats["status_ok"] if value == "Terpetakan" else formats["status_warning"]
                mapping.write(row_index, col, value, cell_format)
        if account_coverage:
            mapping.autofilter(0, 0, len(account_coverage), len(mapping_headers) - 1)
        mapping.freeze_panes(1, 0)

        source = workbook.add_worksheet("Data Sumber")
        source.hide_gridlines(2)
        source.set_column("A:A", 10)
        source.set_column("B:B", 18)
        source.set_column("C:C", 36)
        source.set_column("D:D", 23)
        source.set_column("E:E", 38)
        source.set_column("F:F", 14)
        source.set_column("G:G", 18)
        source.set_column("H:H", 28)
        source.set_column("I:I", 15)
        source_headers = ["Tahun", "Kode Akun", "Nama Akun", "Jenis Akun", "Distribusi Analitik", "Baris Jurnal", "Nominal", "Kategori LKPS", "Status Mapping"]
        for col, header in enumerate(source_headers):
            source.write(0, col, header, formats["header"])
        for row_index, row in enumerate(rows, start=1):
            values = [
                row["report_year"], row["account_code"], row["account_name"],
                row["account_type"], row["analytic_distribution"], row["line_count"],
                float(row["amount"] or 0), row["lkps_category"], row["mapping_status"],
            ]
            for col, value in enumerate(values):
                cell_format = formats["amount"] if col == 6 else formats["integer"] if col in (0, 5) else formats["text"]
                source.write(row_index, col, value, cell_format)
        if rows:
            source.autofilter(0, 0, len(rows), len(source_headers) - 1)
        source.freeze_panes(1, 2)

        control = workbook.add_worksheet("Kontrol")
        control.hide_gridlines(2)
        control.set_column("A:A", 34)
        control.set_column("B:B", 22)
        control.write("A1", "Kontrol dan Rekonsiliasi", formats["title"])
        control.write("A3", "Jurnal posted yang diizinkan ORM", formats["text"])
        control.write_number("B3", orm_move_count, formats["integer"])
        control.write("A4", "Baris agregasi sumber SQL", formats["text"])
        control.write_number("B4", len(rows), formats["integer"])
        control.write("A6", "Penting", formats["section"])
        control.write(
            "A7",
            "Dataset SQL hanya mencakup jenis akun pendapatan, biaya, dan aset tetap. "
            "Periksa mapping berstatus Perlu Ditinjau sebelum memakai workbook untuk akreditasi.",
            formats["note"],
        )
        control.set_row(6, 55)

        workbook.close()
        output.seek(0)
        return output.getvalue()
