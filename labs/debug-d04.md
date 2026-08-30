# Day 4 Debugging Checklist

## 1. Wizard error `You are not allowed to access`

Kesalahan nomor satu di Day 4. Model `TransientModel` **tetap butuh** access right:

```csv
access_reject_wizard_user,reject.wizard.user,model_academy_enrollment_reject_wizard,academy_group_user,1,1,1,1
```

- [ ] Model wizard didefinisikan di modul ini → **tanpa** prefix
- [ ] External ID benar: `model_` + `_name` underscore
- [ ] File CSV terdaftar di manifest

---

## 2. `KeyError: 'active_ids'`

Wizard dibuka langsung dari menu, bukan dari record.

```python
ids = self.env.context.get("active_ids", [])   # BENAR
ids = self.env.context["active_ids"]           # SALAH — crash
```

---

## 3. Wizard tidak muncul di dropdown Action

- [ ] `binding_model_id` menunjuk model yang benar
- [ ] `binding_type` = `action`
- [ ] File view wizard terdaftar di manifest
- [ ] Module di-upgrade, browser di-refresh

---

## 4. Wizard tampil sebagai halaman penuh, bukan modal

Belum ada `target="new"` di action.

---

## 5. `Expected singleton` di wizard

- [ ] `self.ensure_one()` dipanggil, atau
- [ ] Loop `for rec in self:`

Ingat: wizard record-nya satu, tapi `active_ids` bisa banyak. Yang perlu di-loop adalah recordset targetnya, bukan wizardnya.

---

## 6. Report tidak muncul di menu Print

- [ ] `binding_model_id` diisi
- [ ] `binding_type` = `report`
- [ ] File XML terdaftar di manifest
- [ ] Browser sudah di-refresh

---

## 7. `QWebException: external id not found`

```text
academy_management.report_enrollment_certificate
```

`report_name` **harus** `<nama_module>.<id_template>`:

```xml
<field name="report_name">academy_management.report_enrollment_certificate</field>
<!--                       ^module            ^id template -->
<template id="report_enrollment_certificate">
```

---

## 8. PDF kosong, rusak, atau tanpa header/footer

Hampir selalu versi wkhtmltopdf.

```bash
wkhtmltopdf --version
```

Harus `0.12.5 (with patched qt)`. Versi dari repo distro biasanya **tanpa** patched qt — header/footer tidak akan muncul.

---

## 9. Debug template lebih cepat

Buat action kedua dengan `report_type="qweb-html"` menunjuk template yang sama. Hasilnya tampil di browser tanpa menunggu wkhtmltopdf.

---

## 10. `t-field` error

```text
ValueError: Expected singleton
```

atau field tidak ter-render.

`t-field` hanya untuk **field**, bukan ekspresi:

```xml
<span t-field="doc.enrollment_date"/>          <!-- BENAR -->
<span t-esc="line_index + 1"/>                 <!-- BENAR -->
<span t-field="line_index + 1"/>               <!-- SALAH -->
```

---

## 11. Variabel di template tidak dikenali

| Variabel | Isi |
|---|---|
| `docs` | Recordset yang dipilih user |
| `doc_ids` | List ID |
| `doc_model` | Nama model |
| `env` | Environment Odoo |
| `user` | User yang mencetak |

Di dalam `t-foreach ... t-as="line"` tersedia juga `line_index` (mulai 0), `line_first`, `line_last`, `line_size`.

> Di template **inherit report bawaan**, variabelnya biasanya `doc` (satu record), bukan `docs`.

---

## 12. `Element cannot be located in parent view` di report

- [ ] `inherit_id` menunjuk template yang benar
- [ ] Anchor xpath ada di template aslinya

Cara membaca template asli:

1. Developer mode
2. **Settings → Technical → Reports** → catat Template Name
3. **Settings → Technical → User Interface → Views** → cari nama itu → baca `arch`

Pakai `hasclass('page')`, bukan `@class='page'` — Odoo sering menambah class lain.

---

## 13. Inherit report merusak dokumen lain

Bungkus tambahan Anda dengan kondisi:

```xml
<t t-set="enr" t-value="doc.env['academy.enrollment'].search([...], limit=1)"/>
<t t-if="enr">
    ...
</t>
```

Selalu uji dengan dokumen yang **tidak** berasal dari modul Anda.

---

## 14. `ModuleNotFoundError: No module named 'xlsxwriter'`

```bash
pip install xlsxwriter
```

Pastikan terpasang di venv yang dipakai Odoo, bukan Python sistem.

Deklarasikan juga di manifest:

```python
"external_dependencies": {"python": ["xlsxwriter"]},
```

---

## 15. File Excel terunduh dengan nama acak

Atribut `filename` belum dipasang:

```xml
<field name="file_data" filename="file_name"/>
<field name="file_name" invisible="1"/>
```

---

## 16. File Excel kosong atau corrupt

- [ ] `workbook.close()` dipanggil **sebelum** membaca buffer
- [ ] `buffer.seek(0)` sebelum `read()`
- [ ] Isi di-encode `base64.b64encode(...)`

```python
workbook.close()
buffer.seek(0)
self.file_data = base64.b64encode(buffer.read())
```

Urutannya tidak boleh dibalik.

---

## 17. Tautan file tidak muncul setelah Export

Method harus **mengembalikan action yang membuka ulang wizard yang sama**:

```python
return {
    "type":      "ir.actions.act_window",
    "res_model": self._name,
    "res_id":    self.id,
    "view_mode": "form",
    "target":    "new",
}
```

Kalau mengembalikan `act_window_close`, dialognya tertutup dan file tidak sempat terlihat.

---

## 18. `sale` tidak ditemukan saat inherit report

```text
External ID not found: sale.report_saleorder_document
```

Modul `sale` belum ter-install, atau belum masuk `depends` manifest.

---

## Perintah Diagnostik Cepat

```bash
./odoo/odoo-bin shell -c odoo.conf -d academy
```

```python
# Report yang terdaftar
>>> env["ir.actions.report"].search([
...     ("model", "=", "academy.enrollment")
... ]).read(["name", "report_name", "report_type"])

# Template ada?
>>> env.ref("academy_management.report_enrollment_certificate")

# Render PDF dari kode
>>> enr = env["academy.enrollment"].search([], limit=1)
>>> rep = env.ref("academy_management.action_report_enrollment_certificate")
>>> pdf, _ = rep._render_qweb_pdf(rep.report_name, enr.ids)
>>> len(pdf)

# Cek access right wizard
>>> env["ir.model.access"].search([
...     ("model_id.model", "like", "wizard")
... ]).read(["name", "group_id"])

# Uji wizard langsung
>>> w = env["academy.enrollment.reject.wizard"].create({"rejection_reason": "test"})
>>> w.with_context(active_ids=[enr.id]).action_reject()
```
