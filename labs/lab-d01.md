# Day 1 Hands-on Lab — Academy Management

## Objective

Di akhir lab Day 1, Anda punya custom module `academy_management` dengan:

- model `academy.course`
- model `academy.student`
- seed data course
- menu **Academy** dengan submenu Courses dan Students
- akses CRUD untuk internal user

---

# Prerequisite

- Odoo 18 source install berjalan
- PostgreSQL berjalan, `odoo.conf` sudah dikonfigurasi
- DBeaver bisa connect ke database Odoo
- VS Code siap

Struktur folder:

```text
development/
├── odoo/
│   ├── odoo-bin
│   └── addons/
├── custom-addons/
└── odoo.conf
```

`addons_path` di `odoo.conf`:

```ini
addons_path = odoo/addons,custom-addons
```

Semua perintah dijalankan dari folder `development/`.

## Cara Pakai Source Checkpoint

Kalau tertinggal atau kode rusak, salin checkpoint lalu lanjutkan:

```bash
rm -rf custom-addons/academy_management
cp -R materi/labs/source-checkpoints/d01/checkpoint_b_models_ready/academy_management \
      custom-addons/
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Checkpoint Day 1: `checkpoint_a_module_only` → `checkpoint_b_models_ready` → `checkpoint_c_final`

Detail: [`source-checkpoints/README.md`](source-checkpoints/README.md)

> Ketik sendiri dulu. Checkpoint adalah jaring pengaman, bukan jalan pintas.

---

# Checkpoint A — Module Hidup

## Goal

Module kosong yang terdeteksi dan bisa di-install Odoo.

## Step 1 — Scaffold Module

```bash
./odoo/odoo-bin scaffold academy_management custom-addons
```

Expected result:

```text
custom-addons/academy_management/
├── __init__.py
├── __manifest__.py
├── controllers/
├── demo/
├── models/
├── security/
└── views/
```

Hapus isi `controllers/` dan `demo/` hasil scaffold — belum dipakai hari ini.

## Step 2 — Edit Manifest

`custom-addons/academy_management/__manifest__.py`:

```python
{
    "name": "Academy Management",
    "version": "18.0.1.0.0",
    "summary": "Academy Management System",
    "author": "Arkana Solusi Digital (ASD)",
    "website": "https://arkana.co.id",
    "category": "Education",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [],
    "application": True,
    "installable": True,
}
```

## Step 3 — Jalankan dan Install

```bash
./odoo/odoo-bin -c odoo.conf -d academy
```

Di browser (`http://localhost:8069`):

1. **Settings → Developer Tools → Activate developer mode**
2. **Apps → Update Apps List**
3. Hapus filter **Apps** di search box
4. Cari `Academy Management` → Install

## Checkpoint A selesai bila:

- [ ] Module muncul di daftar Apps
- [ ] Install berhasil tanpa error
- [ ] Tidak ada traceback di terminal

> Bandingkan: `source-checkpoints/d01/checkpoint_a_module_only`

---

# Checkpoint B — Data Ada di PostgreSQL

## Goal

Dua model terbuat dan tabelnya benar-benar ada di database.

## Step 1 — Model Course

`models/academy_course.py`:

```python
from odoo import fields, models


class AcademyCourse(models.Model):
    _name        = "academy.course"
    _description = "Academy Course"
    _order       = "name"

    name           = fields.Char(required=True)
    code           = fields.Char(copy=False)
    description    = fields.Html()
    duration_hours = fields.Float()
    price          = fields.Monetary()
    currency_id    = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    level = fields.Selection([
        ("beginner",     "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced",     "Advanced"),
    ], default="beginner")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "Kode course harus unik!"),
    ]
```

> `Monetary` **wajib** dipasangkan `currency_id` di model yang sama. Tanpa itu field error saat dirender.

## Step 2 — Model Student

`models/academy_student.py`:

```python
from odoo import fields, models


class AcademyStudent(models.Model):
    _name        = "academy.student"
    _description = "Academy Student"
    _order       = "name"

    name      = fields.Char(required=True)
    email     = fields.Char()
    phone     = fields.Char()
    birthdate = fields.Date()
    gender    = fields.Selection([
        ("male",   "Male"),
        ("female", "Female"),
        ("other",  "Other"),
    ])
    active    = fields.Boolean(default=True)
```

## Step 3 — Import Model

`models/__init__.py`:

```python
from . import academy_course
from . import academy_student
```

`__init__.py`:

```python
from . import models
```

## Step 4 — Upgrade Module

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

## Step 5 — Cek Table di DBeaver

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('academy_course', 'academy_student');
```

Expected: 2 baris.

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'academy_course'
ORDER BY ordinal_position;
```

Perhatikan kolom yang **tidak** Anda tulis: `id`, `create_date`, `create_uid`, `write_date`, `write_uid`. Itu reserved fields yang dibuat Odoo otomatis.

## Step 6 — Buktikan SQL Constraint Ada di Database

```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'academy_course'::regclass;
```

Constraint unik untuk `code` harus terdaftar. Ini bukti `_sql_constraints` benar-benar menjadi constraint PostgreSQL, bukan sekadar pengecekan di Python.

## Checkpoint B selesai bila:

- [ ] Upgrade berjalan tanpa error
- [ ] Tabel `academy_course` dan `academy_student` ada
- [ ] Kolom audit muncul otomatis
- [ ] Nama tabel memakai underscore, bukan titik
- [ ] Constraint unik `code` terdaftar di PostgreSQL

> Bandingkan: `source-checkpoints/d01/checkpoint_b_models_ready`

---

# Checkpoint C — Menu Berfungsi

## Goal

Model bisa diakses dan diisi lewat UI.

## Step 1 — Access Rights

`security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_academy_course,academy.course,model_academy_course,base.group_user,1,1,1,1
access_academy_student,academy.student,model_academy_student,base.group_user,1,1,1,1
```

> External ID model dibuat otomatis: `model_` + `_name` dengan titik jadi underscore. Model di modul ini sendiri → tanpa prefix.

## Step 2 — Seed Data

`data/academy_data.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="course_python_basics" model="academy.course">
        <field name="name">Python Basics</field>
        <field name="code">PY-101</field>
        <field name="level">beginner</field>
        <field name="duration_hours">24</field>
        <field name="price">1500000</field>
    </record>

    <record id="course_odoo_fundamental" model="academy.course">
        <field name="name">Odoo Fundamental</field>
        <field name="code">ODOO-101</field>
        <field name="level">intermediate</field>
        <field name="duration_hours">40</field>
        <field name="price">3500000</field>
    </record>
</odoo>
```

> Nilai Selection ditulis pakai **key** (`beginner`), bukan label (`Beginner`).

## Step 3 — Actions

`views/academy_course_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="action_academy_course" model="ir.actions.act_window">
        <field name="name">Courses</field>
        <field name="res_model">academy.course</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
```

`views/academy_student_views.xml` — pola sama untuk `academy.student`, dengan id `action_academy_student`.

## Step 4 — Menus

`views/academy_menus.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <menuitem id="menu_academy_root" name="Academy" sequence="10"/>

    <menuitem id="menu_academy_course" name="Courses"
              parent="menu_academy_root"
              action="action_academy_course" sequence="10"/>
    <menuitem id="menu_academy_student" name="Students"
              parent="menu_academy_root"
              action="action_academy_student" sequence="20"/>
</odoo>
```

## Step 5 — Update Manifest

```python
"data": [
    "security/ir.model.access.csv",
    "data/academy_data.xml",
    "views/academy_course_views.xml",
    "views/academy_student_views.xml",
    "views/academy_menus.xml",
],
```

> **Urutan penting.** File diproses dari atas ke bawah, dan menu memakai action — jadi `academy_menus.xml` harus **paling akhir**.

## Step 6 — Upgrade dan Test

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Di UI:

1. Menu **Academy** muncul
2. **Courses** → 2 course dari seed data sudah ada
3. Buat course baru dengan `code` yang sudah dipakai → constraint error muncul
4. Buat student baru
5. Arsipkan satu course (Action → Archive) → hilang dari list
6. Filter **Archived** di search → course tadi muncul lagi

## Checkpoint C selesai bila:

- [ ] Menu Academy + 2 submenu muncul
- [ ] Seed data course terload
- [ ] Create / edit berjalan di kedua model
- [ ] Constraint `code` unik menolak duplikat
- [ ] Archive menyembunyikan record dari list default
- [ ] Filter Archived memunculkannya kembali

> Bandingkan: `source-checkpoints/d01/checkpoint_c_final`

---

# Common Mistakes

## 1. Module tidak muncul di Apps

- `addons_path` sudah mencakup `custom-addons`?
- Sudah klik **Update Apps List**?
- Filter **Apps** di search box sudah dihapus?
- Ada `__manifest__.py` di dalam folder module?

## 2. Model tidak terdaftar

```text
KeyError: 'academy.course'
```

Cek rantai import:

```python
# academy_management/__init__.py
from . import models

# academy_management/models/__init__.py
from . import academy_course
from . import academy_student
```

## 3. Field `Monetary` error

Butuh `currency_id` di model yang sama. Ini kesalahan pemula yang sering terjadi.

## 4. Access Error

```text
You are not allowed to access 'Academy Course' records.
```

- File `ir.model.access.csv` ada dan sudah masuk manifest?
- External ID model benar: `model_academy_course`?
- Header CSV persis 8 kolom?

## 5. Menu tidak muncul

- Action didefinisikan sebelum menu yang memakainya?
- `academy_menus.xml` ada di urutan **terakhir** manifest?
- Sudah refresh browser?

## 6. Perubahan tidak terlihat

| Yang diubah | Perlu |
|---|---|
| File Python | restart server |
| XML / CSV | `-u academy_management` |
| Field baru | `-u academy_management` |

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management --dev all
```

---

# Final Checklist Day 1

| Item | Status |
|---|---|
| Module `academy_management` installed | ☐ |
| Model `academy.course` created | ☐ |
| Model `academy.student` created | ☐ |
| Table `academy_course` exists | ☐ |
| Table `academy_student` exists | ☐ |
| Kolom audit muncul otomatis | ☐ |
| SQL constraint `code` terdaftar di PostgreSQL | ☐ |
| Access rights configured | ☐ |
| Seed data loaded | ☐ |
| Menu Academy appears | ☐ |
| Submenu Courses & Students works | ☐ |
| Create/edit record berjalan | ☐ |
| Constraint menolak `code` duplikat | ☐ |
| Archive menyembunyikan record | ☐ |

---

Troubleshooting cepat: → [`debug-d01.md`](debug-d01.md)
