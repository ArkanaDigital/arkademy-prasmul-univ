# Day 4 — Wizards & Reporting

**Versi:** Odoo 18.0 · **Modul:** `academy_management`

## Tujuan Pembelajaran
- Membuat wizard (TransientModel) dan memanggilnya dari UI.
- Mengoper data dari record ke wizard lewat context.
- Membuat report PDF dengan QWeb.
- Membuat report Excel dengan `xlsxwriter`.
- Meng-inherit dan meng-custom report/printout bawaan Odoo.

## Yang Ditambahkan Hari Ini

```
academy_management/
├── wizards/
│   ├── __init__.py
│   ├── reject_enrollment_wizard.py       + views   (dialog alasan penolakan)
│   └── enrollment_export_wizard.py       + views   (export Excel)
├── reports/
│   ├── academy_enrollment_certificate_report.xml   PDF sertifikat
│   └── sale_order_report_inherit.xml               inherit report bawaan
└── security/
    └── ir.model.access.csv   ← UBAH: akses kedua model wizard
```

---

## 14. Wizards

### Apa itu Wizard

Wizard = dialog yang meminta input tambahan dari user sebelum menjalankan aksi. Modelnya `models.TransientModel` — punya tabel, tapi datanya **dibersihkan otomatis** oleh Odoo secara berkala.

| | `models.Model` | `models.TransientModel` |
|---|---|---|
| Punya tabel DB | Ya | Ya |
| Data bertahan | Permanen | Dibersihkan berkala (vacuum) |
| Dipakai untuk | Data bisnis | Input sementara / dialog |
| Butuh access rights | Ya | **Ya** — sering terlupakan |

Kapan pakai wizard vs tombol biasa:
- **Tombol biasa** — aksi tidak butuh input tambahan (Submit, Approve).
- **Wizard** — aksi butuh masukan user dulu (alasan penolakan, rentang tanggal, pilihan target).

### Wizard 1 — Reject Enrollment

Penolakan wajib disertai alasan. Itu tidak bisa dilakukan dengan tombol biasa.

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

Wizard-nya sengaja tipis — logika bisnisnya ditaruh di model:

```python
# models/academy_enrollment.py
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

**Kenapa logikanya di model, bukan di wizard?**

- Bisa dipanggil dari mana saja — tombol lain, API, cron, unit test — tanpa lewat wizard.
- Wizard adalah lapisan UI. Aturan bisnis yang hidup di lapisan UI akan terlewat begitu ada jalur masuk lain.
- Validasi hak akses dan state tetap terjaga meski wizard dilewati.

Perhatikan juga:

- `active_ids` dari context berisi record yang dipilih user — wizard ini bisa menolak banyak enrollment sekaligus.
- `{"type": "ir.actions.act_window_close"}` menutup dialog setelah selesai.

### 14.1 Launching Wizards

**View wizard** — bedanya dengan form biasa ada di `<footer>`:

```xml
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
                <button string="Batal" special="cancel" class="btn-secondary"/>
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
```

> **`target="new"` yang membuat form tampil sebagai modal**, bukan halaman penuh.
>
> `special="cancel"` = tombol tutup dialog bawaan Odoo, tidak perlu method sendiri.

**Dua cara memanggil wizard:**

**Cara 1 — binding ke dropdown Action** (dipakai wizard di atas):

```xml
<field name="binding_model_id" ref="model_academy_enrollment"/>
<field name="binding_type">action</field>
```

Wizard muncul di dropdown **Action** (icon gear). Record yang sedang dibuka atau dicentang otomatis dikirim lewat context sebagai `active_ids` — itulah yang dibaca `action_reject`.

**Cara 2 — tombol di form, dengan `default_`:**

```xml
<button name="%(action_reject_enrollment_wizard)d"
        string="Tolak"
        type="action"
        class="btn-danger"
        context="{'default_rejection_reason': 'Tidak memenuhi syarat'}"
        invisible="state not in ('submitted', 'manager_approved')"
        groups="academy_management.academy_group_approval_l1"/>
```

`default_<field>` mengisi nilai awal field wizard. Sintaks `%(external_id)d` menerjemahkan external ID jadi ID numerik action.

| | Binding (Action) | Tombol + context |
|---|---|---|
| Muncul di | Dropdown Action | Form, di posisi yang Anda tentukan |
| Bisa banyak record sekaligus | Ya (`active_ids`) | Umumnya satu |
| Bisa dikontrol `invisible` / `groups` | Tidak | Ya |
| Cocok untuk | Aksi massal, utilitas | Aksi terkait state record |

Keduanya bisa dipasang bersamaan pada action yang sama.

### Membaca Record Terpilih di Wizard

Wizard yang dipanggil lewat binding menerima record terpilih lewat context:

| Key context | Isi |
|---|---|
| `active_id` | ID record yang sedang dibuka |
| `active_ids` | List ID record yang dipilih |
| `active_model` | Nama model asalnya |

```python
def action_reject(self):
    ids = self.env.context.get("active_ids", [])
    enrollments = self.env["academy.enrollment"].browse(ids)
    ...
```

> Pakai `.get("active_ids", [])` dengan nilai default, jangan `context["active_ids"]`. Kalau wizard dibuka langsung dari menu (bukan dari record), key itu tidak ada dan kode akan `KeyError`.

**Jangan lupa access rights** — wizard tetap butuh baris di `ir.model.access.csv`:

```csv
access_reject_wizard_user,reject.wizard.user,model_academy_enrollment_reject_wizard,academy_group_user,1,1,1,1
access_export_wizard_user,export.wizard.user,model_academy_enrollment_export_wizard,academy_group_user,1,1,1,1
```

> Model wizard didefinisikan di modul ini sendiri, jadi **tanpa** prefix modul. Ini yang paling sering terlupakan — wizard error `not allowed` padahal modelnya sudah benar.

---

## 15. Reporting

### 15.1 Reports (PDF)

Report PDF Odoo = **QWeb template** (HTML) yang dirender jadi PDF oleh wkhtmltopdf.

**Action report** (`reports/academy_enrollment_certificate_report.xml`):

```xml
<record id="action_report_enrollment_certificate" model="ir.actions.report">
    <field name="name">Enrollment Certificate</field>
    <field name="model">academy.enrollment</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">academy_management.report_enrollment_certificate</field>
    <field name="report_file">academy_management.report_enrollment_certificate</field>
    <field name="binding_model_id" ref="model_academy_enrollment"/>
    <field name="binding_type">report</field>
</record>
```

| Field | Fungsi |
|---|---|
| `model` | Model sumber data |
| `report_type` | `qweb-pdf` (PDF) atau `qweb-html` (preview di browser) |
| `report_name` | `<modul>.<id_template>` — **harus** cocok dengan template |
| `binding_model_id` | Model tempat report muncul di dropdown Print |
| `binding_type` | `report` → masuk menu Print |

**Template QWeb:**

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

**Direktif QWeb:**

| Direktif | Fungsi |
|---|---|
| `t-foreach` / `t-as` | Loop recordset |
| `t-field` | Render nilai field **dengan format Odoo** (mata uang, tanggal, dsb) |
| `t-esc` | Render hasil ekspresi Python, di-escape |
| `t-if` / `t-else` | Kondisi |
| `t-call` | Panggil template lain |
| `t-set` / `t-value` | Buat variabel di dalam template |
| `t-att-<attr>` | Set atribut HTML secara dinamis |

**`t-field` vs `t-esc`** — beda yang sering bikin bingung:

```xml
<span t-field="doc.enrollment_date"/>              <!-- 15/01/2026, ikut locale -->
<span t-esc="doc.enrollment_date"/>                <!-- 2026-01-15, mentah -->
<span t-esc="line.qty * line.price"/>              <!-- hasil hitungan, harus t-esc -->
<span t-field="line.qty * line.price"/>            <!-- SALAH, t-field hanya untuk field -->
```

`t-field` tahu tipe field dan memformatnya. `t-esc` mencetak nilai apa adanya, tapi bisa menerima ekspresi apa pun.

**Variabel loop otomatis:** di dalam `t-foreach ... t-as="line"`, Odoo menyediakan `line_index` (0-based), `line_first`, `line_last`, `line_size`.

**Layout wajib:**
- `web.html_container` — pembungkus HTML paling luar.
- `web.external_layout` — kop surat perusahaan (logo, alamat, footer).
- `web.basic_layout` — tanpa kop, untuk dokumen yang desainnya penuh sendiri seperti sertifikat.

**Paper format:**

```xml
<record id="paperformat_certificate" model="report.paperformat">
    <field name="name">Certificate A4 Landscape</field>
    <field name="format">A4</field>
    <field name="orientation">Landscape</field>
    <field name="margin_top">20</field>
    <field name="margin_bottom">20</field>
    <field name="header_spacing">15</field>
</record>
```

Hubungkan ke action report:
```xml
<field name="paperformat_id" ref="paperformat_certificate"/>
```

**Tips debugging:** buat action kedua dengan `report_type="qweb-html"` yang menunjuk template sama. Hasilnya tampil di browser tanpa menunggu wkhtmltopdf — jauh lebih cepat saat menyusun layout.

### 15.2 Reports (Excel)

Excel tidak pakai QWeb. Ada dua pendekatan:

| | **Wizard + `Binary`** (dipakai di sini) | `report_xlsx` (OCA) |
|---|---|---|
| Dependency | `xlsxwriter` saja | modul OCA + `xlsxwriter` |
| Filter sebelum export | Ya — user isi form dulu | Tidak, ikut record terpilih |
| Muncul di menu Print | Tidak, lewat Action | Ya |
| Kerumitan | Lebih sederhana | Perlu AbstractModel dengan penamaan khusus |

Kita pakai yang pertama: user memilih rentang tanggal dan batch, lalu file dibuat dan diunduh.

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
        # 1. Susun domain dari filter yang diisi user
        domain = []
        if self.date_from:
            domain.append(("enrollment_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("enrollment_date", "<=", self.date_to))
        if self.batch_id:
            domain.append(("batch_id", "=", self.batch_id.id))
        records = self.env["academy.enrollment"].search(domain)

        # 2. Tulis workbook ke memori, bukan ke file di disk
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

        # 3. Simpan ke field Binary — Odoo menyediakan link unduhnya
        self.file_data = base64.b64encode(buffer.read())
        self.file_name = "enrollments.xlsx"

        # 4. Buka ulang wizard yang sama, sekarang berisi file
        return {
            "type":      "ir.actions.act_window",
            "res_model": self._name,
            "res_id":    self.id,
            "view_mode": "form",
            "target":    "new",
        }
```

Tiga hal yang layak diperhatikan:

- **`io.BytesIO()` + `in_memory: True`** — file dibuat di memori, tidak menulis ke disk server. Aman untuk multi-worker dan tidak meninggalkan sampah.
- **Field `Binary` + `base64`** — cara standar Odoo menyimpan file. Begitu terisi, Odoo otomatis menyediakan tautan unduh di form.
- **Return membuka wizard yang sama lagi** (`res_id: self.id`). Ini pola dua langkah: dialog pertama untuk isi filter, dialog kedua menampilkan file siap unduh.

**View wizard** — field file hanya tampil setelah terisi:

```xml
<form string="Export Enrollment">
    <group>
        <field name="date_from"/>
        <field name="date_to"/>
        <field name="batch_id"/>
        <field name="file_data" filename="file_name" invisible="not file_data"/>
        <field name="file_name" invisible="1"/>
    </group>
    <footer>
        <button name="action_export" string="Export"
                type="object" class="btn-primary"
                invisible="file_data"/>
        <button string="Tutup" special="cancel" class="btn-secondary"/>
    </footer>
</form>
```

> Atribut `filename="file_name"` memberi tahu Odoo nama file saat diunduh. Tanpa itu, file terunduh dengan nama acak.

Dependency di manifest:
```python
"external_dependencies": {"python": ["xlsxwriter"]},
```

**PDF vs Excel:**

| | PDF (QWeb) | Excel (xlsxwriter) |
|---|---|---|
| Cocok untuk | Dokumen resmi, dicetak | Data untuk diolah lagi |
| Dibuat dengan | Template XML | Kode Python |
| Butuh dependency luar | wkhtmltopdf | `xlsxwriter` |
| Styling | CSS / Bootstrap | Format object xlsxwriter |

### 15.3 Inherit Report (PDF) — Custom Printout yang Sudah Ada

Ini yang paling sering dibutuhkan di proyek nyata: **printout sudah ada di sistem, tinggal ditambah atau diubah isinya.** Karena report Odoo adalah QWeb template (sejenis view), aturannya sama dengan view inheritance di Day 2.

`reports/sale_order_report_inherit.xml`:

```xml
<template id="report_saleorder_document_academy_note"
          inherit_id="sale.report_saleorder_document">
    <xpath expr="//div[hasclass('page')]" position="inside">
        <div class="mt-4">
            <p><strong>Diproses oleh Arkana Academy</strong></p>
            <p>Catatan: dokumen ini dicetak untuk keperluan training Odoo.</p>
        </div>
    </xpath>
</template>
```

> `hasclass('page')` lebih tahan perubahan daripada `//div[@class='page']`, karena Odoo sering menambah class lain pada elemen yang sama. Kalau memakai `@class`, xpath akan gagal begitu class-nya bertambah.
>
> Template ini butuh modul `sale` ter-install.

**Cara menemukan template & xpath target:**

1. Aktifkan **developer mode**.
2. **Settings → Technical → Reports** — cari report yang mau diubah, lihat kolom Template Name.
3. **Settings → Technical → User Interface → Views** — cari template itu, baca `arch`-nya.
4. Pilih anchor yang stabil: berbasis `name`, `hasclass()`, atau struktur yang jelas — bukan indeks posisi.

**Mengubah elemen yang sudah ada:**

```xml
<!-- Ganti isi elemen -->
<xpath expr="//span[@t-field='doc.name']" position="replace">
    <span t-field="doc.name"/> <span>(Academy)</span>
</xpath>

<!-- Ubah atribut saja -->
<xpath expr="//table[hasclass('o_main_table')]" position="attributes">
    <attribute name="class">table table-sm o_main_table table-borderless</attribute>
</xpath>
```

**Menambah style sendiri:**

```xml
<template id="report_assets_custom" inherit_id="web.report_assets_common">
    <xpath expr="." position="inside">
        <link rel="stylesheet" type="text/scss"
              href="/academy_management/static/src/scss/report.scss"/>
    </xpath>
</template>
```

**Batasi perubahan agar tidak merusak dokumen lain:**

```xml
<xpath expr="//div[hasclass('page')]" position="inside">
    <t t-set="enrollment"
       t-value="doc.env['academy.enrollment'].search(
           [('name','=',doc.client_order_ref)], limit=1)"/>
    <t t-if="enrollment">
        <p>Enrollment: <span t-esc="enrollment.name"/></p>
    </t>
</xpath>
```

Selalu uji dengan dokumen yang **tidak** berasal dari modul Anda, untuk memastikan tidak ada yang rusak.

> **Jangan pernah mengedit template report di folder `odoo/addons/`.** Perubahan itu hilang saat update source dan tidak ikut ter-deploy. Selalu lewat inherit dari modul sendiri.

**Kapan sebaiknya bikin report baru saja?** Kalau perubahannya sampai mengganti sebagian besar isi, puluhan xpath lebih sulit dirawat dan rapuh saat upgrade. Lebih baik buat report sendiri seperti 15.1.

---

## Latihan
→ [`labs/lab-d04.md`](labs/lab-d04.md)
