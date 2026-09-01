# Day 2 Hands-on Lab — Views, Relations, Inheritance, Computed

## Objective

Di akhir lab Day 2, module `academy_management` Anda punya:

- view custom (list, form, search) untuk semua model
- tiga model baru: `academy.batch`, `academy.enrollment`, `academy.course.tag`
- relasi Many2one, One2many, Many2many yang terbukti bentuknya di database
- model & view inheritance
- computed field, default value, dan onchange

---

# Prerequisite

- Lab Day 1 selesai — `academy_management` ter-install dengan 2 model
- Menu Academy berfungsi

Kalau Day 1 belum selesai:

```bash
rm -rf custom-addons/academy_management
cp -R materi/labs/source-checkpoints/d01/checkpoint_c_final/academy_management \
      custom-addons/
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Checkpoint Day 2: `a_custom_views` → `b_relations` → `c_inheritance` → `d_computed_onchange` → `final_day2`

---

# Checkpoint A — Custom Views

## Goal

Mengganti view default Odoo dengan view buatan sendiri.

## Step 1 — List & Form Course

`views/academy_course_views.xml` — tambahkan sebelum record action:

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

> `currency_id` harus ikut dikirim ke client agar widget `monetary` tahu formatnya — tapi user tidak perlu melihatnya. Di list pakai `column_invisible="1"`, di form pakai `invisible="1"`.
>
> Karakter `&` wajib ditulis `&amp;` di XML.

## Step 2 — Search View Course

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

## Step 3 — View untuk Student

Buat pola yang sama di `views/academy_student_views.xml`: list (name, email, phone, gender), form, dan search dengan filter per gender.

## Step 4 — Upgrade dan Uji

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

1. Buka **Courses** — kolom sesuai definisi Anda, ada total jam di footer
2. Buka form — judul besar, dua kolom, tab Deskripsi
3. Search → filter Beginner berfungsi
4. Group By Level → subtotal per group

## Checkpoint A selesai bila:

- [ ] List course menampilkan kolom yang Anda tentukan
- [ ] Total `duration_hours` muncul di footer
- [ ] Harga tampil dengan format mata uang
- [ ] Form punya judul besar + 2 kolom + notebook
- [ ] Filter dan Group By berfungsi
- [ ] Filter Archived memunculkan record yang diarsipkan

> Bandingkan: `source-checkpoints/d02/checkpoint_a_custom_views`

---

# Checkpoint B — Relations

## Goal

Tiga model baru saling terhubung, dan Anda melihat sendiri bentuk tiap relasi di database.

## Step 1 — Model Batch

`models/academy_batch.py`:

```python
from odoo import fields, models


class AcademyBatch(models.Model):
    _name        = "academy.batch"
    _description = "Academy Batch"
    _order       = "start_date desc"

    name       = fields.Char(required=True)
    code       = fields.Char(
        string="Batch Code", copy=False,
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

    _sql_constraints = [
        ("code_unique", "unique(code)", "Batch code harus unik."),
    ]
```

## Step 2 — Model Enrollment

`models/academy_enrollment.py`:

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

    _sql_constraints = [
        ("unique_student_batch",
         "unique(batch_id, student_id)",
         "Student tidak boleh terdaftar dua kali di batch yang sama."),
    ]
```

## Step 3 — Model Course Tag

`models/academy_course_tag.py`:

```python
from odoo import fields, models


class AcademyCourseTag(models.Model):
    _name        = "academy.course.tag"
    _description = "Academy Course Tag"
    _order       = "name"

    name  = fields.Char(required=True)
    color = fields.Integer()
```

## Step 4 — Update `models/__init__.py`

```python
from . import academy_course
from . import academy_student
from . import academy_batch
from . import academy_enrollment
from . import academy_course_tag
```

## Step 5 — Views, Access Rights, Menu

Buat `views/academy_batch_views.xml` dan `views/academy_enrollment_views.xml` (list + form + search), tambahkan 3 baris di `ir.model.access.csv`, dan tambah submenu Batches + Enrollments di `academy_menus.xml`.

Jangan lupa daftarkan file view baru di manifest, **sebelum** `academy_menus.xml`.

```
    <record id="view_academy_batch_list" model="ir.ui.view">
        <field name="name">academy.batch.list</field>
        <field name="model">academy.batch</field>
        <field name="arch" type="xml">
            <list string="batch">
                <field name="name"/>
                <field name="code"/>
                <field name="course_id"/>
                <field name="start_date"/>
                <field name="end_date"/>
                <field name="capacity"/>
                <field name="state"/>
                <field name="responsible_id"/>
            </list>
        </field>
    </record>

    <record id="view_academy_batch_form" model="ir.ui.view">
        <field name="name">academy.batch.form</field>
        <field name="model">academy.batch</field>
        <field name="arch" type="xml">
            <form string="batch">
                <header>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1><field name="name"/></h1>
                    </div>
                    <group>
                        <group>
                            <field name="code"/>
                            <field name="course_id"/>
                            <field name="start_date"/>
                            <field name="end_date"/>
                            <!-- <field name="state"/> -->
                        </group>
                        <group>
                            <field name="capacity"/>
                            <field name="responsible_id"/>
                            <field name="active"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Enrollment">
                            <field name="enrollment_ids"/>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>
```

## Step 6 — Upgrade

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

## Step 7 — Lihat Bentuk Tiap Relasi di Database

Ini inti checkpoint ini. Jalankan di DBeaver:

```sql
-- Many2one = kolom FK biasa
SELECT column_name FROM information_schema.columns
WHERE table_name = 'academy_enrollment' AND column_name = 'batch_id';

-- Many2many = tabel relasi TERPISAH
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE '%course%tag%';

-- One2many = TIDAK ADA kolomnya
SELECT column_name FROM information_schema.columns
WHERE table_name = 'academy_batch' AND column_name = 'enrollment_ids';
```

Expected:
- `batch_id` → **ada** (Many2one = kolom FK)
- tabel relasi Many2many → belum ada (dibuat di Checkpoint C, saat `tag_ids` ditambahkan)
- `enrollment_ids` → **tidak ada**, karena One2many itu virtual

## Step 8 — Uji `ondelete`

1. Buat course, batch di bawahnya, dan enrollment di bawah batch itu
2. Coba hapus **course** → ditolak (`restrict`)
3. Hapus **batch** → enrollment-nya ikut terhapus (`cascade`)
4. Coba hapus **student** yang masih punya enrollment → ditolak (`restrict`)

## Checkpoint B selesai bila:

- [ ] Tiga model baru ter-install, menu muncul
- [ ] `batch_id` ada sebagai kolom di tabel enrollment
- [ ] `enrollment_ids` **tidak** ada kolomnya — Anda paham kenapa
- [ ] Hapus course yang punya batch → ditolak
- [ ] Hapus batch → enrollment ikut terhapus
- [ ] Constraint student+batch unik menolak duplikat

> Bandingkan: `source-checkpoints/d02/checkpoint_b_relations`

---

# Checkpoint C — Inheritance

## Goal

Menambah field ke model yang sudah ada, tanpa mengubah file aslinya.

## Step 1 — Model Inherit

`models/academy_course_inherit.py`:

```python
from odoo import fields, models


class AcademyCourse(models.Model):
    _inherit = "academy.course"

    is_published   = fields.Boolean(default=False)
    internal_notes = fields.Text()
    tag_ids        = fields.Many2many("academy.course.tag", string="Tags")
```

Perhatikan: **hanya `_inherit`, tanpa `_name`**. Artinya "tambahkan ke model yang sudah ada" — tidak ada tabel baru.

Tambahkan ke `models/__init__.py`:

```python
from . import academy_course_inherit
```

## Step 2 — View Inherit

`views/academy_course_inherit_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
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
</odoo>
```

## Step 3 — Ubah Atribut, Bukan Menambah

Tambahkan xpath kedua di record yang sama:

```xml
            <xpath expr="//field[@name='code']" position="attributes">
                <attribute name="required">1</attribute>
            </xpath>
```

## Step 4 — Upgrade dan Uji

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

1. Buka form course → `is_published` dan `tag_ids` muncul setelah `level`
2. Tambahkan beberapa tag → tampil sebagai chip berwarna
3. Kosongkan `code` lalu simpan → sekarang ditolak, karena atributnya diubah jadi required

## Step 5 — Buktikan Many2many Bikin Tabel Sendiri

```sql
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE '%tag%';
```

Sekarang tabel relasi Many2many muncul. Lihat isinya:

```sql
SELECT * FROM academy_course_academy_course_tag_rel LIMIT 5;
```

Isinya cuma dua kolom FK — itulah wujud Many2many.

> Nama tabel relasi dibuat otomatis Odoo. Kalau berbeda di database Anda, cari lewat query pertama.

## Checkpoint C selesai bila:

- [ ] `is_published` dan `tag_ids` muncul di form course
- [ ] Tag tampil sebagai chip berwarna
- [ ] `code` sekarang wajib diisi
- [ ] Tabel relasi Many2many ada di database, isinya dua kolom FK
- [ ] Tidak ada file di `odoo/addons/` yang diedit

> Bandingkan: `source-checkpoints/d02/checkpoint_c_inheritance`

---

# Checkpoint D — Computed, Default, Onchange

## Goal

Nilai turunan terhitung otomatis, dan Anda tahu batas onchange.

## Step 1 — Computed Field di Batch

Tambahkan ke `models/academy_batch.py`:

```python
from odoo import api, fields, models


class AcademyBatch(models.Model):
    # ... definisi sebelumnya ...

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

Pastikan `api` sudah di-import.

## Step 2 — Tampilkan di View

Tambahkan `enrollment_count` dan `available_seats` (keduanya `readonly="1"`) ke form dan list batch.

## Step 3 — Onchange di Enrollment

Tambahkan ke `models/academy_enrollment.py`:

```python
from odoo import api, fields, models


class AcademyEnrollment(models.Model):
    # ... definisi sebelumnya ...

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

## Step 4 — Upgrade dan Uji

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

1. Buat batch dengan `capacity` = 2
2. `available_seats` = 2, `enrollment_count` = 0
3. Tambah 1 enrollment → `available_seats` jadi 1
4. Tambah lagi sampai penuh, lalu buat enrollment baru di batch itu → muncul warning

## Step 5 — Buktikan `store=True` Bekerja

```sql
SELECT name, capacity, enrollment_count, available_seats FROM academy_batch;
```

Nilainya benar-benar tersimpan sebagai kolom. Kalau `store=False`, kolomnya tidak akan ada — dan field itu tidak bisa dipakai untuk Group By atau `sum`.

Buktikan juga di UI: coba Group By `available_seats` — hanya bisa karena `store=True`.

## Step 6 — Buktikan Batas Onchange

```bash
./odoo/odoo-bin shell -c odoo.conf -d academy
```

```python
>>> batch = env["academy.batch"].search([("available_seats", "<=", 0)], limit=1)
>>> student = env["academy.student"].search([], limit=1)
>>> env["academy.enrollment"].create({
...     "name": "TEST-BYPASS",
...     "batch_id": batch.id,
...     "student_id": student.id,
... })
>>> env.cr.commit()
```

Record **berhasil dibuat** meskipun batch sudah penuh. Onchange tidak jalan di sini.

> Inilah alasan onchange tidak boleh dipakai sebagai validasi. Untuk aturan yang harus selalu berlaku, pakai constraint — dibahas Day 3.

Bersihkan record uji:

```python
>>> env["academy.enrollment"].search([("name", "=", "TEST-BYPASS")]).unlink()
>>> env.cr.commit()
```

## Checkpoint D selesai bila:

- [ ] `enrollment_count` dan `available_seats` terhitung otomatis
- [ ] Nilainya berubah saat enrollment ditambah/dikurangi
- [ ] Kolomnya ada di PostgreSQL dengan nilai terisi
- [ ] Bisa Group By `available_seats` (bukti `store=True`)
- [ ] Warning muncul saat memilih batch penuh di form
- [ ] Anda sudah membuktikan sendiri onchange dilewati saat `create()`

> Bandingkan: `source-checkpoints/d02/checkpoint_d_computed_onchange`

---

# Latihan Tambahan — Domain

Tanpa mengubah Python, cuma XML:

1. Di form enrollment, batasi `batch_id` agar hanya menampilkan batch `confirmed`
2. Buat filter di search batch: yang masih punya kursi (`available_seats > 0`)
3. Buat filter OR dalam satu filter: state `draft` **atau** `confirmed`
4. Buat filter "Batch Saya" — `responsible_id` = user yang login (petunjuk: variabel `uid`)

Ingat, operator logika ditulis **di depan** operandnya:

```python
["|", ("state", "=", "draft"), ("state", "=", "confirmed")]
```

---

# Common Mistakes

## 1. `Field 'x' does not exist`

- Nama field typo di XML?
- Module sudah di-upgrade setelah field ditambah?

## 2. `Element cannot be located in parent view`

xpath `expr` tidak cocok dengan view aslinya.

- Buka view asli lewat developer mode, baca `arch`-nya
- `inherit_id` menunjuk view yang benar?
- Pakai anchor berbasis nama field, bukan indeks posisi

## 3. Computed field selalu kosong

```python
# SALAH — self bisa berisi banyak record
def _compute_enrollment_count(self):
    self.enrollment_count = len(self.enrollment_ids)

# BENAR
def _compute_enrollment_count(self):
    for batch in self:
        batch.enrollment_count = len(batch.enrollment_ids)
```

## 4. Computed tidak update

Field pemicu belum masuk `@api.depends`. Untuk relasi, sebutkan sampai field anaknya.

## 5. One2many kosong terus

Argumen kedua harus nama field Many2one di model lawan:

```python
enrollment_ids = fields.One2many("academy.enrollment", "batch_id")
#                                 model lawan          ^^^^^^^^
```

## 6. Many2many tidak tersimpan lewat kode

```python
"tag_ids": [(6, 0, [1, 2, 3])]   # BENAR
"tag_ids": [1, 2, 3]             # SALAH
```

## 7. Onchange tidak jalan saat import

Normal — onchange memang hanya untuk form UI.

---

# Final Checklist Day 2

| Item | Status |
|---|---|
| List, form, search course dibuat sendiri | ☐ |
| Widget monetary tampil benar | ☐ |
| Model `academy.batch` created | ☐ |
| Model `academy.enrollment` created | ☐ |
| Model `academy.course.tag` created | ☐ |
| `batch_id` ada sebagai kolom FK di DB | ☐ |
| `enrollment_ids` tidak ada kolomnya di DB | ☐ |
| Tabel relasi Many2many terbentuk | ☐ |
| `ondelete=restrict` mencegah hapus course | ☐ |
| `ondelete=cascade` menghapus enrollment ikut batch | ☐ |
| Model inheritance menambah field tanpa ubah file asli | ☐ |
| View inheritance menyisipkan field | ☐ |
| `position="attributes"` mengubah `code` jadi required | ☐ |
| `enrollment_count` & `available_seats` terhitung | ☐ |
| Computed tersimpan di DB (`store=True`) | ☐ |
| Bisa Group By computed field | ☐ |
| Onchange memunculkan warning | ☐ |
| Sudah membuktikan onchange dilewati saat `create()` | ☐ |

---

Troubleshooting cepat: → [`debug-d02.md`](debug-d02.md)
