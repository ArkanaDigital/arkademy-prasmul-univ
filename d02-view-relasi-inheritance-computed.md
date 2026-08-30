# Day 2 — Basic Views, Relations, Inheritance, Computed

**Versi:** Odoo 18.0 · **Modul:** `academy_management`

## Tujuan Pembelajaran
- Mendeklarasikan & menyesuaikan view (list, form, search).
- Membuat relasi antar model (Many2one, One2many, Many2many).
- Menerapkan model & view inheritance.
- Memahami domain sebagai filter record.
- Membuat computed field, default value, dan onchange.

## Yang Ditambahkan Hari Ini

```
academy_management/
├── models/
│   ├── academy_course.py          ← tidak berubah
│   ├── academy_student.py         ← tidak berubah
│   ├── academy_batch.py           ← BARU: academy.batch
│   ├── academy_enrollment.py      ← BARU: academy.enrollment
│   ├── academy_course_tag.py      ← BARU: academy.course.tag
│   └── academy_course_inherit.py  ← BARU: extend academy.course
├── views/
│   ├── academy_course_views.xml   ← UBAH: list + form + search
│   ├── academy_student_views.xml  ← UBAH: list + form + search
│   ├── academy_batch_views.xml    ← BARU
│   ├── academy_enrollment_views.xml ← BARU
│   ├── academy_course_inherit_views.xml ← BARU
│   └── academy_menus.xml          ← UBAH: tambah menu
└── security/
    └── ir.model.access.csv        ← UBAH: model baru
```

Model akhir hari ini:

```
academy.course ──1..n──> academy.batch ──1..n──> academy.enrollment
      │                                                  │
      └──n..n──> academy.course.tag        academy.student <┘
```

---

## 6. Basic Views

### 6.1 Generic View Declaration

Setiap view adalah record `ir.ui.view` dengan field `arch` (XML struktur tampilan).

```xml
<record id="view_academy_course_list" model="ir.ui.view">
    <field name="name">academy.course.list</field>
    <field name="model">academy.course</field>
    <field name="arch" type="xml">
        <list> ... </list>
    </field>
</record>
```

| Field | Fungsi |
|---|---|
| `name` | Label teknis. Konvensi: `<model>.<tipe>` |
| `model` | Model yang ditampilkan |
| `arch` | Struktur XML view-nya |
| `inherit_id` | Kalau diisi, view ini meng-extend view lain |
| `priority` | Kalau ada beberapa view sejenis, yang angkanya terkecil dipakai |

Tipe view ditentukan tag root di `arch`: `<list>`, `<form>`, `<search>`, `<kanban>`, `<calendar>`, `<graph>`, `<pivot>`.

> Odoo 18 memakai `<list>`. Versi sebelumnya memakai `<tree>`.

### 6.2 List Views

```xml
<record id="view_academy_course_list" model="ir.ui.view">
    <field name="name">academy.course.list</field>
    <field name="model">academy.course</field>
    <field name="arch" type="xml">
        <list string="Courses">
            <field name="code"/>
            <field name="name"/>
            <field name="level"/>
            <field name="duration_hours" sum="Total Jam"/>
            <field name="price" widget="monetary"/>
            <field name="currency_id" column_invisible="1"/>
        </list>
    </field>
</record>
```

Atribut yang sering dipakai:

| Atribut | Efek |
|---|---|
| `sum="Label"` | Total di footer kolom |
| `avg="Label"` | Rata-rata di footer |
| `optional="hide"` / `"show"` | Kolom bisa di-toggle user |
| `decoration-info="..."` | Warna baris kondisional |
| `widget="..."` | Cara render (`monetary`, `badge`, `progressbar`) |
| `column_invisible="1"` | Kolom disembunyikan tapi datanya tetap dikirim |

> `currency_id` di atas dipasang `column_invisible="1"` karena widget `monetary` membutuhkannya untuk tahu format mata uang, tapi user tidak perlu melihat kolomnya.

### 6.3 Form Views

```xml
<record id="view_academy_course_form" model="ir.ui.view">
    <field name="name">academy.course.form</field>
    <field name="model">academy.course</field>
    <field name="arch" type="xml">
        <form string="Course">
            <sheet>
                <div class="oe_title">
                    <h1><field name="name" placeholder="Nama course"/></h1>
                </div>
                <group>
                    <group string="Informasi">
                        <field name="code"/>
                        <field name="level"/>
                        <field name="active"/>
                    </group>
                    <group string="Durasi &amp; Biaya">
                        <field name="duration_hours"/>
                        <field name="price"/>
                        <field name="currency_id" invisible="1"/>
                    </group>
                </group>
                <notebook>
                    <page string="Deskripsi">
                        <field name="description"/>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

Struktur form: `<header>` (tombol & statusbar) → `<sheet>` (isi utama) → `<group>` (kolom) → `<notebook>`/`<page>` (tab).

> Dua `<group>` yang bersarang di dalam satu `<group>` menghasilkan tata letak **dua kolom**. Ini pola standar Odoo.
>
> Karakter `&` harus ditulis `&amp;` di dalam XML.

### 6.4 Search Views

```xml
<record id="view_academy_course_search" model="ir.ui.view">
    <field name="name">academy.course.search</field>
    <field name="model">academy.course</field>
    <field name="arch" type="xml">
        <search string="Cari Course">
            <field name="name"/>
            <field name="code"/>
            <filter name="beginner" string="Beginner"
                    domain="[('level','=','beginner')]"/>
            <filter name="advanced" string="Advanced"
                    domain="[('level','=','advanced')]"/>
            <separator/>
            <filter name="inactive" string="Archived"
                    domain="[('active','=',False)]"/>
            <group expand="0" string="Group By">
                <filter name="group_level" string="Level"
                        context="{'group_by': 'level'}"/>
            </group>
        </search>
    </field>
</record>
```

- `<field>` → kolom yang bisa diketik user di search box.
- `<filter domain=...>` → filter siap pakai.
- `<filter context="{'group_by': ...}">` → opsi Group By.
- `<separator/>` → pemisah grup filter. **Ini bukan hiasan** — lihat 8.3.

> Filter `Archived` di atas perlu ditulis eksplisit karena Odoo otomatis menyembunyikan record `active = False`.

---

## 7. Relations between Models

### 7.1 Relational Fields

| Field | Arti | Wujud di DB |
|-------|------|----------|
| `Many2one` | banyak → satu | Kolom FK di tabel ini |
| `One2many` | satu → banyak | **Tidak ada kolom** — virtual, butuh `inverse_name` |
| `Many2many` | banyak ↔ banyak | Tabel relasi terpisah |

**`models/academy_batch.py`** — kelas/angkatan dari sebuah course:

```python
from odoo import fields, models


class AcademyBatch(models.Model):
    _name        = "academy.batch"
    _description = "Academy Batch"
    _order       = "start_date desc"

    name       = fields.Char(required=True)
    code       = fields.Char(
        string="Batch Code",
        copy=False,
        help="Referensi unik yang dipakai REST API (contoh: PY-101-JAN).",
    )
    course_id  = fields.Many2one(
        "academy.course", required=True, ondelete="restrict"
    )
    start_date = fields.Date()
    end_date   = fields.Date()
    capacity   = fields.Integer()
    state      = fields.Selection([
        ("draft",     "Draft"),
        ("confirmed", "Confirmed"),
        ("done",      "Done"),
        ("cancelled", "Cancelled"),
    ], default="draft")
    enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
    responsible_id = fields.Many2one(
        "res.users", string="Responsible",
        default=lambda self: self.env.user,
    )
    active = fields.Boolean(default=True)
```

**`models/academy_enrollment.py`** — pendaftaran student ke batch:

```python
from odoo import fields, models


class AcademyEnrollment(models.Model):
    _name        = "academy.enrollment"
    _description = "Academy Enrollment"

    name            = fields.Char(required=True, default="New")
    batch_id        = fields.Many2one(
        "academy.batch", required=True, ondelete="cascade"
    )
    student_id      = fields.Many2one(
        "academy.student", required=True, ondelete="restrict"
    )
    enrollment_date = fields.Date(default=fields.Date.context_today)
    state           = fields.Selection([
        ("draft",     "Draft"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ], default="draft")
    notes = fields.Text()
```

**`models/academy_course_tag.py`:**

```python
from odoo import fields, models


class AcademyCourseTag(models.Model):
    _name        = "academy.course.tag"
    _description = "Academy Course Tag"
    _order       = "name"

    name  = fields.Char(required=True)
    color = fields.Integer()
```

### `ondelete` — Apa yang Terjadi Saat Record Tujuan Dihapus

| Nilai | Efek | Dipakai di atas |
|---|---|---|
| `restrict` | Cegah penghapusan selama masih direferensi | `course_id`, `student_id` |
| `cascade` | Record ini ikut terhapus | `batch_id` |
| `set null` | FK dikosongkan | — |

Alasan pilihannya:
- Hapus **course** yang masih punya batch → **dicegah**, karena batch tanpa course tidak bermakna.
- Hapus **batch** → enrollment-nya ikut terhapus, karena enrollment tidak punya arti tanpa batch.
- Hapus **student** yang masih terdaftar → **dicegah**, karena data pendaftarannya harus tetap utuh.

> `ondelete` adalah keputusan desain, bukan formalitas. Salah pilih `cascade` bisa menghapus data yang seharusnya dipertahankan.

### One2many Butuh Pasangannya

```python
# di academy.batch
enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
#                                 model lawan          ^^^^^^^^
#                                 nama field Many2one di model lawan
```

One2many **tidak punya kolom sendiri di database**. Ia hanya "membalik" pandangan dari Many2one yang ada di model lawan. Kalau `batch_id` di `academy.enrollment` tidak ada, One2many ini error.

---

## 8. Inheritance

### 8.1 Model Inheritance

Tiga mekanisme:

| Cara | Ditulis | Efek |
|---|---|---|
| **Extension** | `_inherit` saja | Tambah field/method ke model yang sama, tabel sama |
| **Prototype** | `_inherit` + `_name` baru | Salin struktur ke model baru, tabel terpisah |
| **Delegation** | `_inherits` (pakai s) | Komposisi — field model lain tampil seolah milik sendiri |

**Extension** adalah yang paling sering dipakai. `models/academy_course_inherit.py`:

```python
from odoo import fields, models


class AcademyCourse(models.Model):
    _inherit = "academy.course"

    is_published   = fields.Boolean(default=False)
    internal_notes = fields.Text()
    tag_ids        = fields.Many2many("academy.course.tag", string="Tags")
```

Perhatikan: **hanya `_inherit`, tanpa `_name`**. Artinya "tambahkan ke model yang sudah ada". Tidak ada tabel baru — kolom `is_published`, `internal_notes` masuk ke tabel `academy_course` yang sudah ada.

> Di sini kita meng-extend model milik sendiri, hanya untuk memisahkan file. Pola yang **sama persis** dipakai untuk meng-extend model bawaan Odoo — cukup ganti `_inherit = "res.partner"`. Yang penting: source Odoo tidak pernah disentuh.

### 8.2 View Inheritance

Modifikasi view tanpa menimpa, pakai `inherit_id` + `xpath`:

```xml
<record id="view_academy_course_form_inherit" model="ir.ui.view">
    <field name="name">academy.course.form.inherit</field>
    <field name="model">academy.course</field>
    <field name="inherit_id" ref="academy_management.view_academy_course_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='level']" position="after">
            <field name="is_published"/>
            <field name="tag_ids" widget="many2many_tags"
                   options="{'color_field': 'color'}"/>
        </xpath>
    </field>
</record>
```

Nilai `position`:

| Nilai | Efek |
|---|---|
| `after` | Sisipkan setelah elemen target |
| `before` | Sisipkan sebelum elemen target |
| `inside` | Sisipkan di dalam elemen target (paling akhir) |
| `replace` | Ganti elemen target |
| `attributes` | Ubah atribut elemen target, bukan isinya |

**Mengubah atribut:**

```xml
<xpath expr="//field[@name='code']" position="attributes">
    <attribute name="required">1</attribute>
</xpath>
```

**Cara menemukan `expr` yang benar:**
1. Aktifkan developer mode
2. Buka form target
3. Icon bug → **View: Form**
4. Baca `arch` aslinya, pilih anchor yang stabil

> Pilih anchor berdasarkan **nama field** (`//field[@name='level']`), bukan posisi (`//group[2]/field[3]`). Anchor berbasis posisi akan pecah begitu ada modul lain yang menyisipkan sesuatu.

### 8.3 Domains

Domain adalah filter record, ditulis sebagai list of tuple `(field, operator, value)`.

```python
[("level", "=", "beginner")]
[("level", "=", "beginner"), ("active", "=", True)]     # implisit AND
["|", ("level", "=", "beginner"), ("level", "=", "advanced")]   # OR
["!", ("level", "=", "beginner")]                        # NOT
```

**Operator logika ditulis prefix** — di depan operand yang digabungkannya, bukan di antaranya. Ini bagian yang paling sering membingungkan:

```python
# Baca: OR( A, B )
["|", ("a", "=", 1), ("b", "=", 2)]

# Baca: OR( A, AND(B, C) )
["|", ("a", "=", 1), "&", ("b", "=", 2), ("c", "=", 3)]
```

Operator perbandingan yang sering dipakai:

| Operator | Arti |
|---|---|
| `=`, `!=` | Sama dengan / tidak |
| `>`, `>=`, `<`, `<=` | Perbandingan |
| `in`, `not in` | Ada di dalam list |
| `like`, `ilike` | Mengandung teks (`ilike` = abaikan huruf besar/kecil) |
| `child_of` | Termasuk turunan (untuk struktur hierarki) |

**Domain menembus relasi** dengan titik:

```python
[("batch_id.course_id.level", "=", "beginner")]
```

**Domain di view** — batasi pilihan Many2one:

```xml
<field name="batch_id" domain="[('state','=','confirmed')]"/>
```

**Domain dinamis** — merujuk field lain di record yang sama:

```xml
<field name="batch_id" domain="[('course_id','=',course_id)]"/>
```

**Domain di action** — batasi record yang tampil saat menu dibuka:

```xml
<field name="domain">[('state','!=','cancelled')]</field>
```

---

## 9. Computed Fields and Default Values

### 9.1 Dependencies

Tambahkan ke `academy.batch`:

```python
from odoo import api, fields, models


class AcademyBatch(models.Model):
    _inherit = "academy.batch"     # atau langsung di class utama

    enrollment_count = fields.Integer(
        compute="_compute_enrollment_count", store=True)
    available_seats = fields.Integer(
        compute="_compute_available_seats", store=True)

    @api.depends("enrollment_ids")
    def _compute_enrollment_count(self):
        for batch in self:
            batch.enrollment_count = len(batch.enrollment_ids)

    @api.depends("capacity", "enrollment_ids")
    def _compute_available_seats(self):
        for batch in self:
            batch.available_seats = batch.capacity - len(batch.enrollment_ids)
```

Aturan yang wajib dipatuhi:

1. **Loop `self`.** Compute dipanggil untuk banyak record sekaligus. `self.field = x` akan error `Expected singleton`.
2. **Setiap record harus diberi nilai**, termasuk saat datanya kosong. Kalau ada cabang `if` yang tidak mengisi nilai, record itu error.
3. **`@api.depends` harus lengkap.** Untuk field relasi, sebutkan sampai field anaknya (`enrollment_ids.state`), bukan cuma relasinya.

| | `store=True` | `store=False` (default) |
|---|---|---|
| Disimpan di DB | Ya | Tidak, dihitung saat dibaca |
| Bisa di-search / group by / sum | Ya | Tidak |
| Biaya | Kolom DB + recompute saat dependency berubah | Hitung ulang tiap akses |

> Kalau field perlu di-`sum` di list view atau dipakai di filter, ia **harus** `store=True`.

### 9.2 Default Values

Empat cara:

```python
# 1. Nilai statis
level = fields.Selection([...], default="beginner")

# 2. Lambda — dievaluasi saat record dibuat
enrollment_date = fields.Date(default=fields.Date.context_today)
responsible_id  = fields.Many2one("res.users",
                                  default=lambda self: self.env.user)

# 3. Method
name = fields.Char(default=lambda self: self._default_name())

def _default_name(self):
    return self.env["ir.sequence"].next_by_code("academy.enrollment") or "New"

# 4. Lewat context dari luar
# <field name="context">{'default_level': 'advanced'}</field>
```

> **Jangan** pakai nilai yang dievaluasi saat import: `default=fields.Date.today()` (dengan kurung) dievaluasi sekali saat server start, jadi tanggalnya membeku. Pakai `default=fields.Date.context_today` (tanpa kurung) supaya dievaluasi tiap kali record dibuat.

---

## 10. Onchange

```python
from odoo import api, fields, models


class AcademyEnrollment(models.Model):
    _inherit = "academy.enrollment"

    @api.onchange("batch_id")
    def _onchange_batch_id(self):
        if self.batch_id and self.batch_id.available_seats <= 0:
            return {
                "warning": {
                    "title": "Batch Penuh",
                    "message": "Batch ini sudah tidak punya kursi tersisa.",
                }
            }
```

Onchange dipakai untuk mengisi, memfilter, atau memperingatkan **saat user mengubah sesuatu di form**.

Yang bisa dikembalikan onchange:
- `{"warning": {...}}` — peringatan, tidak memblokir
- `{"domain": {...}}` — ubah pilihan field lain
- Mengubah `self.field = ...` langsung — mengisi field lain

> **Batasannya penting:** onchange hanya jalan di form UI. Data yang masuk lewat import, API/RPC, atau `create()` di kode **tidak** memicu onchange.

Perbandingan tiga mekanisme:

| Kebutuhan | Pakai | Jalan saat import/API? |
|---|---|---|
| Nilai turunan yang selalu konsisten | computed field | Ya |
| Bantu user isi form, boleh diubah manual | onchange | Tidak |
| Aturan yang tidak boleh dilanggar | constraint (Day 3) | Ya |

Onchange **bukan** validasi. Kalau aturannya mutlak, itu tugas constraint.

---

## Latihan
→ [`labs/lab-d02.md`](labs/lab-d02.md)
