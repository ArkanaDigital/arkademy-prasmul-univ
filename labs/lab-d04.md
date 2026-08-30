# Day 4 Hands-on Lab — Wizards & Reporting

## Objective

Di akhir lab Day 4, module `academy_management` Anda punya:

- wizard penolakan enrollment dengan alasan wajib
- wizard export Excel dengan filter
- report PDF sertifikat enrollment
- report bawaan Odoo yang sudah di-custom tanpa menyentuh source-nya

---

# Prerequisite

- Lab Day 3 selesai — constraint, approval workflow, dan security sudah jalan

Kalau tertinggal:

```bash
rm -rf custom-addons/academy_management
cp -R materi/labs/source-checkpoints/d03/checkpoint_d_security_for_approval/academy_management \
      custom-addons/
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Cek dependency:

```bash
python -c "import xlsxwriter; print(xlsxwriter.__version__)"   # kalau gagal: pip install xlsxwriter
wkhtmltopdf --version                                          # harus 0.12.5 (with patched qt)
```

> Versi wkhtmltopdf selain 0.12.5 patched qt akan menghasilkan PDF tanpa header/footer atau rusak.

Checkpoint Day 4: `a_pdf_report` → `b_report_inheritance` → `c_excel_export` → `d_rest_api_consumer` → `e_external_api` → `final_day4`

> `checkpoint_d` dan `checkpoint_e` berisi materi **Day 5**. Hari ini berhenti di `checkpoint_c_excel_export`.

Wizard reject ada di `d03/checkpoint_e_wizard`.

---

# Checkpoint A — Wizard Reject Enrollment

## Goal

Penolakan enrollment wajib disertai alasan, dan alasannya tersimpan.

## Step 1 — Helper di Model

Tambahkan ke `models/academy_enrollment.py`:

```python
    def _reject_with_reason(self, reason):
        if not (
            self.env.user.has_group("academy_management.academy_group_approval_l1")
            or self.env.user.has_group("academy_management.academy_group_approval_l2")
        ):
            raise UserError("Anda tidak berhak menolak enrollment ini.")

        for rec in self:
            if rec.state not in ("submitted", "manager_approved"):
                raise UserError(
                    "Hanya enrollment submitted atau manager-approved "
                    "yang bisa ditolak.")
            rec.write({
                "state": "rejected",
                "rejection_reason": reason,
            })
```

> Logika bisnis di **model**, bukan di wizard. Wizard cuma lapisan UI — kalau aturannya ditaruh di sana, jalur masuk lain (API, cron, tombol lain) akan melewatinya.

## Step 2 — Model Wizard

`wizards/reject_enrollment_wizard.py`:

```python
from odoo import fields, models


class RejectEnrollmentWizard(models.TransientModel):
    _name        = "academy.enrollment.reject.wizard"
    _description = "Reject Enrollment Wizard"

    rejection_reason = fields.Text(string="Alasan Penolakan", required=True)

    def action_reject(self):
        ids = self.env.context.get("active_ids", [])
        enrollments = self.env["academy.enrollment"].browse(ids)
        enrollments._reject_with_reason(self.rejection_reason)
        return {"type": "ir.actions.act_window_close"}
```

`wizards/__init__.py`:

```python
from . import reject_enrollment_wizard
```

`__init__.py` module:

```python
from . import models
from . import wizards
```

## Step 3 — View Wizard

`wizards/reject_enrollment_wizard_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_reject_enrollment_wizard_form" model="ir.ui.view">
        <field name="name">academy.enrollment.reject.wizard.form</field>
        <field name="model">academy.enrollment.reject.wizard</field>
        <field name="arch" type="xml">
            <form string="Tolak Enrollment">
                <group>
                    <field name="rejection_reason"
                           placeholder="Jelaskan alasan penolakan..."/>
                </group>
                <footer>
                    <button name="action_reject" string="Tolak"
                            type="object" class="btn-danger"/>
                    <button string="Batal" special="cancel"
                            class="btn-secondary"/>
                </footer>
            </form>
        </field>
    </record>

    <record id="action_reject_enrollment_wizard" model="ir.actions.act_window">
        <field name="name">Tolak Enrollment</field>
        <field name="res_model">academy.enrollment.reject.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
        <field name="binding_model_id" ref="model_academy_enrollment"/>
        <field name="binding_type">action</field>
    </record>
</odoo>
```

## Step 4 — Access Rights

Tambahkan ke `security/ir.model.access.csv`:

```csv
access_reject_wizard_user,reject.wizard.user,model_academy_enrollment_reject_wizard,academy_group_user,1,1,1,1
```

## Step 5 — Manifest

```python
"data": [
    ...
    "wizards/reject_enrollment_wizard_views.xml",
    "views/academy_menus.xml",
],
```

## Step 6 — Upgrade dan Uji

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

1. Buat enrollment, Submit → state `submitted`
2. **Action → Tolak Enrollment** → dialog muncul
3. Kosongkan alasan → tombol Tolak ditolak (field `required`)
4. Isi alasan → Tolak → state jadi `rejected`, `rejection_reason` terisi
5. Chatter mencatat perubahan
6. Coba tolak enrollment yang masih `draft` → `UserError`

## Step 7 — Uji Multi-Record

Dari list, centang 2 enrollment `submitted`, lalu **Action → Tolak Enrollment**. Keduanya ditolak sekaligus — inilah gunanya `active_ids`.

## Step 8 — Uji Batas Hak

Login sebagai `user.test` (Academy User, tanpa approval), lalu jalankan wizard. Ditolak oleh `has_group()` di `_reject_with_reason`.

## Checkpoint A selesai bila:

- [ ] Wizard muncul di dropdown Action
- [ ] Alasan wajib diisi
- [ ] State jadi `rejected` dan alasan tersimpan
- [ ] Enrollment state salah ditolak dengan pesan jelas
- [ ] Bisa menolak beberapa enrollment sekaligus
- [ ] User tanpa hak approval ditolak

> Bandingkan: `source-checkpoints/d03/checkpoint_e_wizard`

---

# Checkpoint B — Report PDF Sertifikat

## Goal

Sertifikat enrollment yang bisa dicetak jadi PDF.

## Step 1 — Action Report

`reports/academy_enrollment_certificate_report.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="paperformat_certificate" model="report.paperformat">
        <field name="name">Certificate A4</field>
        <field name="format">A4</field>
        <field name="orientation">Portrait</field>
        <field name="margin_top">20</field>
        <field name="margin_bottom">20</field>
        <field name="header_spacing">15</field>
    </record>

    <record id="action_report_enrollment_certificate" model="ir.actions.report">
        <field name="name">Enrollment Certificate</field>
        <field name="model">academy.enrollment</field>
        <field name="report_type">qweb-pdf</field>
        <field name="report_name">academy_management.report_enrollment_certificate</field>
        <field name="report_file">academy_management.report_enrollment_certificate</field>
        <field name="paperformat_id" ref="paperformat_certificate"/>
        <field name="binding_model_id" ref="model_academy_enrollment"/>
        <field name="binding_type">report</field>
    </record>
</odoo>
```

## Step 2 — Template QWeb

Tambahkan di file yang sama, di dalam `<odoo>`:

```xml
    <template id="report_enrollment_certificate">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="doc">
                <t t-call="web.external_layout">
                    <div class="page">
                        <h2 class="text-center">Certificate of Enrollment</h2>

                        <div class="mt32">
                            <p>Student: <span t-field="doc.student_id.name"/></p>
                            <p>Course: <span t-field="doc.batch_id.course_id.name"/></p>
                            <p>Batch: <span t-field="doc.batch_id.name"/></p>
                            <p>Enrollment Date: <span t-field="doc.enrollment_date"/></p>
                            <p>Status: <span t-field="doc.state"/></p>
                        </div>

                        <table class="table table-sm">
                            <thead>
                                <tr><th>No</th><th>Peserta Sekelas</th></tr>
                            </thead>
                            <tbody>
                                <tr t-foreach="doc.batch_id.enrollment_ids" t-as="line">
                                    <td><span t-esc="line_index + 1"/></td>
                                    <td><span t-field="line.student_id.name"/></td>
                                </tr>
                            </tbody>
                        </table>

                        <div class="mt32">
                            <p>Certificate Reference: <span t-esc="doc.id"/></p>
                            <p>Tanda Tangan: ____________________</p>
                        </div>
                    </div>
                </t>
            </t>
        </t>
    </template>
```

## Step 3 — Manifest & Upgrade

Daftarkan `reports/academy_enrollment_certificate_report.xml`, lalu upgrade.

## Step 4 — Uji

1. Buka enrollment → **Print → Enrollment Certificate**
2. PDF ter-download, ada kop surat perusahaan di atas
3. Tabel peserta sekelas terisi, nomornya urut mulai 1
4. Pilih 2 enrollment dari list → Print → satu PDF, 2 halaman

## Step 5 — Bikin Debugging Lebih Cepat

Tambahkan action kedua yang menunjuk template sama:

```xml
    <record id="action_report_certificate_html" model="ir.actions.report">
        <field name="name">Certificate (HTML preview)</field>
        <field name="model">academy.enrollment</field>
        <field name="report_type">qweb-html</field>
        <field name="report_name">academy_management.report_enrollment_certificate</field>
        <field name="binding_model_id" ref="model_academy_enrollment"/>
        <field name="binding_type">report</field>
    </record>
```

Hasilnya tampil di browser tanpa menunggu wkhtmltopdf — jauh lebih cepat saat menyusun layout.

## Step 6 — Pahami `t-field` vs `t-esc`

Ganti sementara:

```xml
<td><span t-field="line_index + 1"/></td>
```

Error. `t-field` hanya untuk **field**, bukan ekspresi. Kembalikan ke `t-esc`.

Bandingkan juga:

```xml
<p>Format Odoo: <span t-field="doc.enrollment_date"/></p>
<p>Nilai mentah: <span t-esc="doc.enrollment_date"/></p>
```

## Checkpoint B selesai bila:

- [ ] Menu Print → Enrollment Certificate muncul
- [ ] PDF ter-generate dengan kop surat
- [ ] Tabel peserta sekelas terisi, nomor urut benar
- [ ] Pilih 2 record → PDF 2 halaman
- [ ] Preview HTML berfungsi
- [ ] Anda paham kapan pakai `t-field` dan kapan `t-esc`

> Bandingkan: `source-checkpoints/d04/checkpoint_a_pdf_report`

---

# Checkpoint C — Custom Report Bawaan Odoo

## Goal

Menambah informasi ke report bawaan Odoo tanpa menyentuh `odoo/addons/`.

## Step 1 — Install Modul Sale

Report yang akan di-inherit ada di modul `sale`. Install dulu lewat Apps, atau:

```bash
./odoo/odoo-bin -c odoo.conf -d academy -i sale
```

Tambahkan `"sale"` ke `depends` di manifest.

## Step 2 — Temukan Template Target

1. Developer mode aktif
2. **Settings → Technical → Reports** → cari "Quotation / Order"
3. Catat Template Name: `sale.report_saleorder_document`
4. **Settings → Technical → User Interface → Views** → cari nama itu → baca `arch`

## Step 3 — Inherit Template

`reports/sale_order_report_inherit.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="report_saleorder_document_academy_note"
              inherit_id="sale.report_saleorder_document">
        <xpath expr="//div[hasclass('page')]" position="inside">
            <div class="mt-4">
                <p><strong>Diproses oleh Arkana Academy</strong></p>
                <p>Catatan: dokumen ini dicetak untuk keperluan training Odoo.</p>
            </div>
        </xpath>
    </template>
</odoo>
```

> `hasclass('page')` lebih tahan perubahan daripada `//div[@class='page']`. Odoo sering menambah class lain pada elemen yang sama — kalau memakai `@class`, xpath gagal begitu class-nya bertambah.

## Step 4 — Ubah Atribut, Bukan Menambah

Tambahkan xpath kedua di template yang sama:

```xml
        <xpath expr="//table[hasclass('o_main_table')]" position="attributes">
            <attribute name="class">table table-sm o_main_table table-borderless</attribute>
        </xpath>
```

> Kalau anchor ini tidak ketemu di versi Anda, baca `arch` aslinya dan pilih elemen lain. Jangan menebak.

## Step 5 — Upgrade dan Uji

1. Buat satu Sales Order
2. **Print → Quotation** → catatan Academy muncul di bawah
3. Tabel item berubah gaya sesuai atribut baru

## Step 6 — Buktikan Tidak Merusak Dokumen Lain

Cetak report bawaan lain yang tidak Anda sentuh (misal Invoice). Harus normal sepenuhnya.

## Step 7 — Buktikan Reversibel

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Uninstall `academy_management` lewat Apps, lalu cetak Quotation lagi — kembali seperti semula. Inilah bedanya inherit dengan mengedit source: perubahan Anda bisa dicabut bersih.

Install lagi setelah selesai menguji.

## Checkpoint C selesai bila:

- [ ] Catatan Academy muncul di Quotation
- [ ] Atribut tabel berubah sesuai xpath
- [ ] Report bawaan lain tidak terpengaruh
- [ ] Uninstall mengembalikan report seperti semula
- [ ] Tidak ada file di `odoo/addons/` yang diedit

> Bandingkan: `source-checkpoints/d04/checkpoint_b_report_inheritance`

---

# Checkpoint D — Export Excel

## Goal

User memilih filter, lalu mengunduh file `.xlsx`.

## Step 1 — Model Wizard

`wizards/enrollment_export_wizard.py`:

```python
import base64
import io

import xlsxwriter

from odoo import fields, models


class EnrollmentExportWizard(models.TransientModel):
    _name        = "academy.enrollment.export.wizard"
    _description = "Enrollment Export Wizard"

    date_from = fields.Date()
    date_to   = fields.Date()
    batch_id  = fields.Many2one("academy.batch")
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

        bold = workbook.add_format({"bold": True, "bg_color": "#DDDDDD"})
        headers = ["Enrollment", "Student", "Course",
                   "Batch", "Tanggal", "Status"]
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)
        sheet.set_column(1, 3, 28)
        sheet.freeze_panes(1, 0)

        for row, enr in enumerate(records, start=1):
            sheet.write(row, 0, enr.name or "")
            sheet.write(row, 1, enr.student_id.name or "")
            sheet.write(row, 2, enr.batch_id.course_id.name or "")
            sheet.write(row, 3, enr.batch_id.name or "")
            sheet.write(row, 4, str(enr.enrollment_date or ""))
            sheet.write(row, 5, enr.state or "")

        workbook.close()
        buffer.seek(0)

        self.file_data = base64.b64encode(buffer.read())
        self.file_name = "enrollments.xlsx"

        return {
            "type":      "ir.actions.act_window",
            "res_model": self._name,
            "res_id":    self.id,
            "view_mode": "form",
            "target":    "new",
        }
```

Tambahkan ke `wizards/__init__.py`.

## Step 2 — View Wizard

`wizards/enrollment_export_wizard_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_enrollment_export_wizard_form" model="ir.ui.view">
        <field name="name">academy.enrollment.export.wizard.form</field>
        <field name="model">academy.enrollment.export.wizard</field>
        <field name="arch" type="xml">
            <form string="Export Enrollment">
                <group>
                    <field name="date_from"/>
                    <field name="date_to"/>
                    <field name="batch_id"/>
                    <field name="file_data" filename="file_name"
                           invisible="not file_data"/>
                    <field name="file_name" invisible="1"/>
                </group>
                <footer>
                    <button name="action_export" string="Export"
                            type="object" class="btn-primary"
                            invisible="file_data"/>
                    <button string="Tutup" special="cancel"
                            class="btn-secondary"/>
                </footer>
            </form>
        </field>
    </record>

    <record id="action_enrollment_export_wizard" model="ir.actions.act_window">
        <field name="name">Export Enrollment</field>
        <field name="res_model">academy.enrollment.export.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
        <field name="binding_model_id" ref="model_academy_enrollment"/>
        <field name="binding_type">action</field>
    </record>
</odoo>
```

## Step 3 — Access Rights & Manifest

```csv
access_export_wizard_user,export.wizard.user,model_academy_enrollment_export_wizard,academy_group_user,1,1,1,1
```

Daftarkan view wizard di manifest, dan tambahkan:

```python
"external_dependencies": {"python": ["xlsxwriter"]},
```

## Step 4 — Upgrade dan Uji

1. **Action → Export Enrollment**
2. Isi rentang tanggal dan/atau batch → **Export**
3. Dialog terbuka lagi, sekarang ada tautan file
4. Klik → `enrollments.xlsx` terunduh dengan nama yang benar
5. Buka file → header bold, kolom lebar, baris terkunci saat di-scroll
6. Ulangi tanpa filter apa pun → semua enrollment ikut

## Step 5 — Perhatikan Pola Dua Langkah

Sebelum Export, field file tersembunyi dan tombol Export terlihat. Sesudah Export, kebalikannya. Itu efek dari:

```xml
<field name="file_data" invisible="not file_data"/>
<button name="action_export" invisible="file_data"/>
```

Method-nya membuka ulang wizard yang sama (`res_id: self.id`), jadi record transient-nya tetap dan file-nya terbawa.

## Checkpoint D selesai bila:

- [ ] Wizard export muncul di dropdown Action
- [ ] Filter tanggal dan batch mempengaruhi isi file
- [ ] File terunduh dengan nama `enrollments.xlsx`
- [ ] Header bold, kolom lebar, freeze panes bekerja
- [ ] Tombol Export hilang setelah file dibuat
- [ ] Tanpa filter, semua enrollment ikut ter-export

> Bandingkan: `source-checkpoints/d04/checkpoint_c_excel_export`

---

# Common Mistakes

## 1. Wizard error `not allowed`

Model `TransientModel` tetap butuh baris di `ir.model.access.csv`. Ini kesalahan paling sering di Day 4.

## 2. `KeyError: 'active_ids'`

Pakai `.get("active_ids", [])` dengan default, jangan `context["active_ids"]`.

## 3. Report tidak muncul di menu Print

`binding_model_id` + `binding_type="report"` belum diisi.

## 4. `QWebException: external id not found`

`report_name` harus `<nama_module>.<id_template>` dan cocok persis dengan `<template id="...">`.

## 5. PDF kosong atau tanpa header

Versi wkhtmltopdf salah. Harus 0.12.5 patched qt.

## 6. `t-field` error

`t-field` hanya untuk field. Untuk hasil ekspresi pakai `t-esc`.

## 7. `Element cannot be located in parent view`

xpath tidak cocok. Baca `arch` template aslinya lewat Settings → Technical → Views.

## 8. File Excel terunduh dengan nama acak

Atribut `filename="file_name"` belum dipasang di field Binary.

## 9. Inherit report merusak dokumen lain

Bungkus tambahan dengan `t-if` supaya hanya berlaku untuk dokumen yang relevan. Selalu uji dengan dokumen yang tidak berasal dari modul Anda.

---

# Final Checklist Day 4

| Item | Status |
|---|---|
| Wizard reject muncul di dropdown Action | ☐ |
| Alasan penolakan wajib diisi | ☐ |
| State jadi `rejected`, alasan tersimpan | ☐ |
| Reject multi-record bekerja | ☐ |
| User tanpa hak approval ditolak | ☐ |
| Logika bisnis ada di model, bukan di wizard | ☐ |
| PDF sertifikat ter-generate | ☐ |
| PDF memakai kop surat (`external_layout`) | ☐ |
| Paper format terpasang | ☐ |
| Multi-record → multi-halaman | ☐ |
| Preview HTML berfungsi | ☐ |
| Paham `t-field` vs `t-esc` | ☐ |
| Report Sale Order bawaan berubah | ☐ |
| Atribut tabel berubah via `position="attributes"` | ☐ |
| Report bawaan lain tidak terpengaruh | ☐ |
| Uninstall mengembalikan report semula | ☐ |
| Wizard export Excel berfungsi | ☐ |
| Filter mempengaruhi isi file | ☐ |
| File terunduh dengan nama benar | ☐ |
| Tidak ada file `odoo/addons/` yang diedit | ☐ |

---

Troubleshooting cepat: → [`debug-d04.md`](debug-d04.md)
