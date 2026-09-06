import base64
from urllib.parse import quote

from odoo import _, models
from odoo.exceptions import AccessError, ValidationError


class PrasmulXlsxReportMixin(models.AbstractModel):
    _name = "prasmul.xlsx.report.mixin"
    _description = "Shared XLSX Report Helper"

    def _validate_report_filters(self, company, date_from, date_to):
        self.ensure_one()
        if date_from > date_to:
            raise ValidationError(_("Tanggal Awal tidak boleh setelah Tanggal Akhir."))
        if company not in self.env.companies:
            raise AccessError(_("Anda tidak memiliki akses laporan untuk company ini."))

    def _get_xlsx_formats(self, workbook):
        return {
            "title": workbook.add_format(
                {
                    "bold": True,
                    "font_size": 16,
                    "font_color": "#FFFFFF",
                    "bg_color": "#1F4E78",
                    "align": "left",
                    "valign": "vcenter",
                }
            ),
            "subtitle": workbook.add_format(
                {"font_color": "#44546A", "italic": True}
            ),
            "section": workbook.add_format(
                {
                    "bold": True,
                    "font_color": "#FFFFFF",
                    "bg_color": "#5B9BD5",
                    "bottom": 1,
                }
            ),
            "header": workbook.add_format(
                {
                    "bold": True,
                    "font_color": "#FFFFFF",
                    "bg_color": "#4472C4",
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    "text_wrap": True,
                }
            ),
            "text": workbook.add_format({"bottom": 1, "bottom_color": "#D9E2F3"}),
            "text_wrap": workbook.add_format(
                {"bottom": 1, "bottom_color": "#D9E2F3", "text_wrap": True}
            ),
            "integer": workbook.add_format(
                {"num_format": "#,##0", "bottom": 1, "bottom_color": "#D9E2F3"}
            ),
            "amount": workbook.add_format(
                {
                    "num_format": "#,##0;[Red](#,##0);-",
                    "bottom": 1,
                    "bottom_color": "#D9E2F3",
                }
            ),
            "amount_bold": workbook.add_format(
                {
                    "bold": True,
                    "num_format": "#,##0;[Red](#,##0);-",
                    "top": 1,
                }
            ),
            "date": workbook.add_format(
                {"num_format": "yyyy-mm-dd", "bottom": 1, "bottom_color": "#D9E2F3"}
            ),
            "note": workbook.add_format(
                {
                    "font_color": "#7F6000",
                    "bg_color": "#FFF2CC",
                    "text_wrap": True,
                    "valign": "top",
                }
            ),
            "status_ok": workbook.add_format(
                {"font_color": "#006100", "bg_color": "#C6EFCE"}
            ),
            "status_warning": workbook.add_format(
                {"font_color": "#9C6500", "bg_color": "#FFEB9C"}
            ),
        }

    def _return_xlsx_download(self, content, filename):
        """Store the file on the transient wizard and return a download action."""
        self.ensure_one()
        if "output_file" not in self._fields or "output_filename" not in self._fields:
            raise ValidationError(_("Wizard laporan harus mempunyai field file hasil."))
        self.write(
            {
                "output_file": base64.b64encode(content),
                "output_filename": filename,
            }
        )
        url = (
            "/web/content/?model=%s&id=%s&field=output_file"
            "&filename_field=output_filename&download=true&filename=%s"
            % (self._name, self.id, quote(filename))
        )
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}
