# Day 1 — Fondasi & Struktur Modul Odoo

**Versi:** Odoo 18.0 · **Modul:** `academy_management`

## Tujuan Pembelajaran

Di akhir hari, peserta mampu:
- Memahami layer teknis Odoo: UI, Python/ORM, dan PostgreSQL.
- Menilai sumber addon Odoo: official, custom, third-party, dan OCA.
- Memahami konsekuensi versioning, patching, dan upgrade major version.
- Memahami komposisi & struktur modul Odoo.
- Membuat model & field dasar lewat ORM.
- Membedakan simple / reserved / special fields.
- Menyiapkan data file (XML & CSV).
- Membuat action & menu agar model tampil di UI.

## Studi Kasus Sepanjang Training

Kita membangun **satu modul** bernama `academy_management` — sistem manajemen akademi pelatihan. Modul ini tumbuh setiap hari:

| Hari | Yang ditambahkan |
|---|---|
| 1 | Model `academy.course`, `academy.student`, menu, seed data |
| 2 | `academy.batch`, `academy.enrollment`, `academy.course.tag`, relasi, views, computed |
| 3 | Constraint, workflow approval berjenjang, security |
| 4 | Wizard, report PDF, report Excel, inherit report bawaan |
| 5 | REST API provider, integrasi RPC |

> Satu modul yang tumbuh, bukan banyak modul terpisah. Pemisahan modul adalah topik lanjutan — di training ini fokusnya menguasai satu modul secara utuh dulu.

---

## 1–4. Installation, Dev Tools, Config, Start/Stop Server

> **Detail langkah instalasi ada di dokumen setup environment terpisah** (Windows & macOS). Bagian ini hanya garis besar supaya peserta paham *apa* yang dipasang dan *kenapa*.

### Yang Dipasang

| Komponen | Peran |
|---|---|
| **Odoo 18 (source)** | Server aplikasi. Dijalankan lewat `odoo-bin`. |
| **PostgreSQL** | Satu-satunya database yang didukung Odoo. |
| **Python 3.12 + venv** | Runtime Odoo. venv memisahkan dependency training dari sistem. |
| **Git** | Ambil source Odoo & modul, plus kirim hasil kerja. |
| **wkhtmltopdf 0.12.5** | Render PDF report. Versi harus tepat, kalau tidak PDF rusak. |
| **VS Code** | Editor + debugger. Extension: Python, XML. |
| **DBeaver** | Lihat isi database langsung — dipakai untuk membuktikan efek kode. |

### Arsitektur Folder Kerja

```
development/
├── odoo/              source Odoo 18 (core + addons bawaan)
├── custom-addons/     modul yang kita bangun selama training
└── odoo.conf          konfigurasi server
```

### Config File — `odoo.conf`

```ini
[options]
addons_path = odoo/addons,custom-addons
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
http_port = 8069
```

- **`addons_path`** — daftar folder yang dipindai Odoo saat start. Modul yang tidak ada di sini **tidak akan muncul** di menu Apps. Ini penyebab error paling sering di hari pertama.
- Path bisa relatif terhadap folder tempat `odoo-bin` dijalankan.

### Start / Stop Server

```bash
# Jalankan (dari folder development/)
./odoo/odoo-bin -c odoo.conf -d academy

# Install modul
./odoo/odoo-bin -c odoo.conf -d academy -i academy_management

# Update modul setelah ada perubahan
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Stop: `Ctrl+C`. Akses UI: `http://localhost:8069`.

**Kapan perlu apa:**

| Yang diubah | Tindakan |
|---|---|
| File Python (`models/*.py`) | Restart server |
| File XML / CSV | `-u academy_management` |
| File controller | **Restart server** (tidak cukup `-u`) |
| Tambah modul baru | `-i <modul>` |

---

## 5. Build an Odoo Module

### Fondasi Teknis

Tiga layer yang dipakai sepanjang training:

- **UI layer** — apa yang user lihat di browser.
- **Python layer** — tempat business logic, ORM, dan model Odoo berjalan.
- **PostgreSQL layer** — satu-satunya database yang didukung Odoo.

Alurnya:

`browser → controller / RPC → ORM Python → PostgreSQL → response kembali ke browser`

Poin penting:
- Odoo adalah platform modular — tidak semua fitur diinstall sekaligus.
- Modul custom dibangun di atas `addons_path` dan dikenali lewat `__manifest__.py`.
- Hampir semua pengembangan teknis berangkat dari tiga layer ini.

### Addon Ecosystem, Versioning, dan Upgrade

Di implementasi nyata, developer jarang hanya berurusan dengan modul custom internal. Biasanya campuran:

- **official addons** — modul bawaan Odoo.
- **custom addons** — dibuat tim internal atau partner.
- **third-party addons** — dari vendor atau Odoo Apps Store.
- **OCA addons** — open source dari Odoo Community Association, dikelola per repository dan per major version.

Saat menilai addon pihak ketiga, periksa:

- versi Odoo yang didukung (`18.0`, `17.0`, dst);
- dependency modul di `__manifest__.py`;
- lisensi;
- reputasi maintainer dan aktivitas maintenance;
- kualitas kode dan risiko override pada model/view standar;
- dampak upgrade major version berikutnya.

Addon untuk satu major version **tidak otomatis aman** dipakai di major version lain — API Python, model, view XML, asset frontend, dan behavior standar bisa berubah.

> **Contoh nyata yang akan Anda temui:** Odoo 19 memperkenalkan `models.Constraint(...)` untuk menggantikan `_sql_constraints`, dan `res.groups.privilege` untuk menggantikan `category_id` pada group. Kedua API itu **tidak ada di Odoo 18**. Menyalin kode Odoo 19 ke Odoo 18 akan gagal saat install. Ini persis alasan kenapa versi addon harus dicek, bukan diasumsikan.

Prinsip versioning praktis:

- branch addon mengikuti major version Odoo, misalnya `18.0`;
- versi modul di manifest mengikuti pola `18.0.1.0.0`, naik jadi `18.0.1.0.1` saat ada perbaikan;
- patch di major version yang sama tetap perlu staging dan regression test;
- upgrade major version adalah project tersendiri, bukan sekadar update package.

Odoo memberi standard support tiga tahun per major version:

| Versi | Release | End of standard support |
|---|---|---|
| Odoo 19.0 | September 2025 | September 2028 (planned) |
| Odoo 18.0 | Oktober 2024 | September 2027 (planned) |
| Odoo 17.0 | November 2023 | September 2026 (planned) |

Strategi:
- **Patch same major version** — backup, deploy ke staging, update source, upgrade module terdampak, regression test, lalu production saat window aman.
- **Upgrade major version** — inventory semua modul, cek kompatibilitas versi target, porting custom module, siapkan upgraded test database, test proses bisnis utama, rehearsal, baru jadwalkan production.
- **Third-party addon risk** — kalau addon tidak punya versi target atau maintainer tidak aktif, biaya upgrade bisa lebih besar daripada bikin modul custom yang lebih kecil dan terkontrol.

### Modul yang Dibangun Hari Ini

```
academy_management/
├── __init__.py
├── __manifest__.py           depends: ["base"]
├── models/
│   ├── __init__.py
│   ├── academy_course.py     academy.course
│   └── academy_student.py    academy.student
├── views/
│   ├── academy_course_views.xml
│   ├── academy_student_views.xml
│   └── academy_menus.xml
├── security/
│   └── ir.model.access.csv
└── data/
    └── academy_data.xml
```

---

### 5.1 Composition of a Module

Modul Odoo = direktori Python dengan minimal 2 file:

| File | Fungsi |
|------|--------|
| `__manifest__.py` | Metadata modul: nama, versi, dependency, daftar data file |
| `__init__.py` | Entry point Python: meng-import subpackage (`models`, dll) |

Saat Odoo start, ia memindai tiap folder di `addons_path`. Folder yang punya `__manifest__.py` dianggap modul dan muncul di **Apps**.

**`__manifest__.py`:**
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
    "data": [
        "security/ir.model.access.csv",
        "data/academy_data.xml",
        "views/academy_course_views.xml",
        "views/academy_student_views.xml",
        "views/academy_menus.xml",
    ],
    "application": True,
    "installable": True,
}
```

> **Urutan di `"data"` penting.** File diproses dari atas ke bawah. Menu memakai action, jadi `academy_menus.xml` harus diletakkan **setelah** file view yang mendefinisikan action-nya.

**Scaffold** (jalankan dari folder `development/`):
```bash
./odoo/odoo-bin scaffold academy_management custom-addons
```

### 5.2 Module Structure

```
models/__init__.py:
    from . import academy_course
    from . import academy_student
```

Folder yang lazim dipakai:

| Folder | Isi |
|---|---|
| `models/` | File Python untuk model & business logic |
| `views/` | XML definisi view backend & menu |
| `security/` | Access rights (`ir.model.access.csv`) & record rules |
| `data/` | Data default / master data |
| `reports/` | Python & XML untuk report |
| `wizards/` | Model transient + view untuk dialog modal |
| `controllers/` | Route HTTP / API |

Semua folder itu akan terisi sampai Day 5. Hari ini baru `models`, `views`, `security`, `data`.

### 5.3 Object-Relational Mapping (ORM)

Odoo ORM memetakan **class Python → tabel PostgreSQL**. Developer hampir tidak pernah menulis SQL langsung.

```python
from odoo import fields, models


class AcademyCourse(models.Model):
    _name        = "academy.course"
    _description = "Academy Course"
    _order       = "name"
```

#### 5.3.1 Hubungan model, table, field, dan record

| Konsep Odoo | Padanan database |
|---|---|
| Model (`academy.course`) | Tabel (`academy_course`) |
| Field (`name`, `code`) | Kolom |
| Record | Baris |
| Recordset | Kumpulan baris hasil query |

Titik pada `_name` diubah jadi underscore untuk nama tabel: `academy.course` → `academy_course`.

**Konvensi penamaan:** pola `_name` Odoo adalah `<namespace>.<model>`. Kita pakai namespace `academy` untuk semua model modul ini, sehingga langsung terlihat model mana milik siapa: `academy.course`, `academy.student`, `academy.batch`. Odoo core memakai pola yang sama — `sale.order`, `res.partner`, `account.move`.

| Atribut | Fungsi |
|---------|--------|
| `_name` | Identitas teknis → nama tabel DB |
| `_description` | Label manusiawi, wajib |
| `_order` | Sort default |
| `_rec_name` | Field display name (default `name`) |

**Tipe model:**
- `models.Model` — persisten, punya tabel.
- `models.TransientModel` — sementara, dibersihkan berkala (dipakai wizard, Day 4).
- `models.AbstractModel` — basis reusable, tanpa tabel (dipakai report Excel, Day 4).

### 5.4 Model Fields

#### 5.4.1 Common Attributes

| Atribut | Arti |
|---------|------|
| `string` | Label di UI |
| `required=True` | NOT NULL |
| `default` | Nilai default |
| `index=True` | Index DB |
| `readonly=True` | Read-only di UI |
| `copy=False` | Tidak ikut saat duplicate |
| `help` | Tooltip di UI |

> Kalau `string` tidak diisi, Odoo membuat label otomatis dari nama field: `duration_hours` → "Duration Hours". Itu sebabnya banyak field di bawah tidak menulis `string`.

#### 5.4.2 Simple Fields

**`models/academy_course.py`:**
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
    level = fields.Selection(
        [
            ("beginner",     "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced",     "Advanced"),
        ],
        default="beginner",
    )
    active = fields.Boolean(default=True)
```

Tipe field yang dipakai di atas:

| Tipe | Untuk |
|---|---|
| `Char` | Teks pendek satu baris |
| `Text` | Teks panjang polos |
| `Html` | Teks kaya (rich text editor) |
| `Integer` | Bilangan bulat |
| `Float` | Bilangan desimal |
| `Monetary` | Nilai uang — **wajib** dipasangkan `currency_id` |
| `Boolean` | Ya/tidak |
| `Date` / `Datetime` | Tanggal / tanggal-waktu |
| `Selection` | Pilihan terbatas, disimpan sebagai key |

> **`Monetary` butuh `currency_id`.** Tanpa itu Odoo tidak tahu format mata uangnya dan field akan error saat dirender. Ini kesalahan pemula yang sering terjadi.

**`models/academy_student.py`:**
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

#### 5.4.3 Reserved Fields

Field dengan nama khusus yang diperlakukan istimewa oleh Odoo:

| Field | Fungsi |
|-------|--------|
| `id` | Primary key (auto) |
| `name` | Display name default |
| `active` | Soft delete / arsip — record bernilai `False` disembunyikan dari view |
| `state` | Status workflow |
| `create_date`, `write_date` | Audit waktu (auto) |
| `create_uid`, `write_uid` | Audit user (auto) |

> `active` bukan sekadar Boolean biasa. Begitu field bernama `active` ada di model, Odoo otomatis menambahkan `('active','=',True)` ke setiap pencarian. Record lama tidak hilang, hanya tersembunyi — itulah arsip.

#### 5.4.4 Special Fields

Class-level attributes (bukan instance `fields.*`) yang mengontrol perilaku model:

| Atribut | Default | Fungsi |
|---------|---------|--------|
| `_name` | — | **Wajib** — technical name model, jadi nama tabel DB |
| `_description` | `_name` | Label human-readable di UI & log |
| `_rec_name` | `"name"` | Field yang ditampilkan sebagai display name |
| `_order` | `"id"` | Default sort order |
| `_sql_constraints` | `[]` | SQL-level unique/check constraint |

**Contoh:**
```python
class AcademyCourse(models.Model):
    _name        = "academy.course"
    _description = "Academy Course"
    _order       = "name"
    _sql_constraints = [
        ("code_uniq", "unique(code)", "Kode course harus unik!"),
    ]
```

> Odoo 19 mengganti `_sql_constraints` dengan `models.Constraint(...)`. Di **Odoo 18 pakai `_sql_constraints`** seperti di atas.

### 5.5 Data Files

**`data/academy_data.xml`:**
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

**External ID** (`id="course_python_basics"`) adalah identitas unik record lintas modul. Gunanya:
- Merujuk record dari file lain (`ref="course_python_basics"`)
- Mencegah duplikasi saat modul di-upgrade — Odoo mengenali "record ini sudah ada"

**`noupdate="1"`** berarti record tidak ditimpa saat upgrade modul. Pakai ini untuk data yang boleh diedit user. Tanpa `noupdate`, setiap `-u` akan mengembalikan nilai ke isi file.

Format alternatif — CSV, cocok untuk data banyak:

```csv
id,name,code,level,duration_hours,price
course_py101,Python Basics,PY-101,beginner,24,1500000
course_odoo101,Odoo Fundamental,ODOO-101,intermediate,40,3500000
```

> Nilai Selection ditulis pakai **key**, bukan label: `beginner`, bukan `Beginner`.

### 5.6 Actions and Menus

Model tidak otomatis muncul di UI. Butuh **action** (apa yang dibuka) dan **menu** (di mana user mengkliknya).

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

| Field action | Fungsi |
|---|---|
| `name` | Judul yang tampil di breadcrumb |
| `res_model` | Model yang dibuka |
| `view_mode` | Urutan view yang tersedia — yang pertama jadi default |
| `domain` | Filter record yang ditampilkan (opsional) |
| `context` | Nilai default & filter aktif (opsional) |

> `view_mode="list,form"` — Odoo 18 memakai tag `<list>`. Versi lama memakai `<tree>`; kalau menemukan contoh kode lama, itu yang perlu diganti.

Tanpa view eksplisit, Odoo membuat view default otomatis dari definisi model. Cukup untuk hari ini — Day 2 kita buat view sendiri.

---

## Latihan
→ [`labs/lab-d01.md`](labs/lab-d01.md)
