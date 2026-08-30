# Day 2 Debugging Checklist

## 1. `Field 'x' does not exist`

```text
Field "available_seats" does not exist in model "academy.batch"
```

- [ ] Nama field di XML tidak typo
- [ ] Field sudah ditambahkan di model Python
- [ ] Module sudah di-upgrade setelah field ditambah
- [ ] Field ada di model yang benar

---

## 2. `Element cannot be located in parent view`

- [ ] `inherit_id` menunjuk view yang benar
- [ ] Field target benar-benar ada di view aslinya
- [ ] Anchor stabil — pakai `//field[@name='...']`, bukan indeks posisi

Cara menemukan anchor:

1. Developer mode aktif
2. Buka form target
3. Icon bug → **View: Form**
4. Baca `arch` aslinya

---

## 3. Computed field selalu kosong / nol

- [ ] Method meng-iterasi `self`, bukan mengakses `self.field` langsung
- [ ] Setiap record diberi nilai, termasuk saat datanya kosong
- [ ] Nama method di `compute="..."` sama persis

```python
# SALAH
def _compute_available_seats(self):
    self.available_seats = self.capacity - len(self.enrollment_ids)

# BENAR
def _compute_available_seats(self):
    for batch in self:
        batch.available_seats = batch.capacity - len(batch.enrollment_ids)
```

---

## 4. Computed tidak update saat dependency berubah

Untuk field relasi, sebutkan sampai field anaknya:

```python
# Kurang — hanya terpicu saat enrollment ditambah/dikurangi
@api.depends("enrollment_ids")

# Lengkap — juga terpicu saat state enrollment berubah
@api.depends("enrollment_ids", "enrollment_ids.state")
```

---

## 5. `Expected singleton`

```text
ValueError: Expected singleton: academy.batch(1, 2, 3)
```

Kode mengakses field dari recordset berisi banyak record.

- [ ] Loop dulu (`for rec in self:`), atau
- [ ] Panggil `self.ensure_one()` kalau memang harus satu record

---

## 6. One2many tidak muncul isinya

Argumen kedua harus **nama field Many2one di model lawan**:

```python
# di academy.batch
enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
#                                  model lawan          ^^^^^^^^
```

- [ ] Field Many2one itu benar-benar ada di model lawan
- [ ] Nama field-nya tidak typo

Ingat: One2many **tidak punya kolom di database**. Kalau mencarinya di `information_schema.columns` dan tidak ketemu, itu normal.

---

## 7. Many2many tidak menyimpan data

Saat mengisi lewat kode, pakai command:

| Command | Arti |
|---|---|
| `(6, 0, [ids])` | Ganti seluruh isi |
| `(4, id)` | Tambah satu |
| `(3, id)` | Lepas satu (record tidak dihapus) |
| `(2, id)` | Lepas dan hapus record |
| `(0, 0, {vals})` | Buat record baru dan hubungkan |

```python
"tag_ids": [(6, 0, [1, 2, 3])]     # BENAR
"tag_ids": [1, 2, 3]               # SALAH
```

---

## 8. Field `Monetary` tidak tampil formatnya

Widget `monetary` butuh `currency_id` ikut dikirim ke client:

```xml
<!-- di list -->
<field name="price" widget="monetary"/>
<field name="currency_id" column_invisible="1"/>

<!-- di form -->
<field name="price"/>
<field name="currency_id" invisible="1"/>
```

---

## 9. Related field error

```text
AttributeError: 'bool' object has no attribute 'name'
```

Rantai `related` putus karena field perantaranya kosong.

- [ ] Field perantara `required=True`, atau
- [ ] Data lama masih ada yang kosong — isi dulu sebelum upgrade

---

## 10. Field lama tidak hilang dari database

Menghapus field dari Python **tidak** menghapus kolomnya di PostgreSQL. Odoo membiarkannya untuk mencegah kehilangan data. Kolom yatim tidak mengganggu.

---

## 11. Onchange tidak jalan

Cek dulu **di mana** Anda mengujinya:

| Konteks | Onchange jalan? |
|---|---|
| Form UI | Ya |
| Import CSV | Tidak |
| `create()` di kode / shell | Tidak |
| XML-RPC / API | Tidak |

Kalau di form UI juga tidak jalan:

- [ ] Decorator `@api.onchange("field")` menyebut field yang benar
- [ ] Field pemicu **ada di form view** — onchange tidak terpicu oleh field yang tidak dirender
- [ ] Module sudah di-upgrade, browser sudah di-refresh

---

## 12. Warna baris list tidak muncul

- [ ] Ekspresi `decoration-*` pakai sintaks Python, bukan domain
- [ ] Field yang dipakai ada di dalam `<list>`

```xml
<list decoration-success="state == 'confirmed'">
    <field name="state"/>
</list>
```

---

## 13. Group By atau `sum` tidak berfungsi pada computed field

Field harus `store=True`. Tanpa kolom di database, tidak ada yang bisa diagregasi atau di-group.

---

## 14. `ondelete` tidak berperilaku seperti harapan

| Nilai | Efek saat record tujuan dihapus |
|---|---|
| `restrict` | Penghapusan **dicegah** |
| `cascade` | Record ini **ikut terhapus** |
| `set null` | FK dikosongkan |

Kalau salah pilih `cascade`, data bisa hilang diam-diam. Periksa ulang tiap Many2one.

---

## Perintah Diagnostik Cepat

```bash
./odoo/odoo-bin shell -c odoo.conf -d academy
```

```python
# Cek definisi field
>>> env["academy.batch"].fields_get(["available_seats"])

# Paksa recompute
>>> recs = env["academy.batch"].search([])
>>> recs._compute_available_seats()

# Cek isi relasi
>>> b = env["academy.batch"].search([], limit=1)
>>> b.enrollment_ids
>>> b.course_id.name

# Uji domain
>>> env["academy.course"].search([("level", "=", "beginner")])

# Lihat view yang aktif untuk sebuah model
>>> env["ir.ui.view"].search([("model", "=", "academy.course")]).mapped("name")
```

```sql
-- Bentuk relasi di database
SELECT column_name FROM information_schema.columns
WHERE table_name = 'academy_enrollment';

SELECT table_name FROM information_schema.tables
WHERE table_name LIKE '%rel%';
```
