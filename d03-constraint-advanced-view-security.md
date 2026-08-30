# Day 3 — Model Constraints, Advanced Views, Security

**Versi:** Odoo 18.0 · **Modul:** `academy_management`

## Tujuan Pembelajaran
- Menerapkan constraint SQL & Python, dan tahu kapan pakai yang mana.
- Membangun workflow approval berjenjang.
- Membuat view lanjutan: advanced list, calendar, advanced search.
- Mengatur keamanan: group, access rights, record rules.
- Menguji security dengan user asli, bukan admin.

## Yang Ditambahkan Hari Ini

```
academy_management/
├── models/
│   ├── academy_batch.py       ← UBAH: constraint
│   └── academy_enrollment.py  ← UBAH: constraint, state approval, tombol
├── views/
│   ├── academy_batch_views.xml      ← UBAH: advanced list, calendar, search
│   └── academy_enrollment_views.xml ← UBAH: statusbar, tombol approval
└── security/
    ├── academy_groups.xml        ← BARU: 4 group
    ├── academy_record_rules.xml  ← BARU: record rules
    └── ir.model.access.csv       ← UBAH: per group
```

---

## 11. Model Constraints

Dua level validasi dengan trade-off berbeda.

### SQL Constraint

Dijalankan PostgreSQL. Cepat, dan **tidak bisa dilewati** apa pun jalur masuk datanya.

```python
class AcademyEnrollment(models.Model):
    _name = "academy.enrollment"

    _sql_constraints = [
        ("unique_student_batch",
         "unique(batch_id, student_id)",
         "Student tidak boleh terdaftar dua kali di batch yang sama."),
    ]
```

Format tiap entry: `(nama, definisi_sql, pesan_error)`.

Yang bisa dilakukan: `unique(...)`, `CHECK (...)`, `NOT NULL`.

```python
    _sql_constraints = [
        ("capacity_positive",
         "CHECK (capacity > 0)",
         "Capacity harus lebih dari 0."),
    ]
```

> **Odoo 19 mengganti ini dengan `models.Constraint(...)`.** API itu **tidak ada di Odoo 18**. Kalau menyalin contoh kode dari internet dan menemukan `_check_xxx = models.Constraint(...)`, itu kode Odoo 19 — harus dikonversi ke `_sql_constraints` seperti di atas.

### Python Constraint

Dijalankan ORM. Bisa logika kompleks dan bisa membaca relasi.

```python
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AcademyBatch(models.Model):
    _inherit = "academy.batch"

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for batch in self:
            if (batch.start_date and batch.end_date
                    and batch.start_date > batch.end_date):
                raise ValidationError(
                    "Start date harus sebelum atau sama dengan end date."
                )

    @api.constrains("capacity")
    def _check_capacity_not_below_confirmed(self):
        for batch in self:
            confirmed = self.env["academy.enrollment"].search_count([
                ("batch_id", "=", batch.id),
                ("state", "=", "confirmed"),
            ])
            if confirmed > batch.capacity:
                raise ValidationError(
                    "Capacity tidak boleh lebih kecil dari jumlah "
                    "enrollment yang sudah confirmed."
                )
```

### Mana yang Dipakai?

| | SQL constraint | Python constraint |
|---|---|---|
| Dicek di | PostgreSQL | Python (ORM) |
| Kecepatan | Lebih cepat | Lebih lambat |
| Bisa baca relasi (One2many/Many2many) | Tidak | Ya |
| Bisa logika kondisional | Tidak | Ya |
| Berlaku saat data masuk lewat SQL langsung | **Ya** | Tidak |
| Pesan error | Ditentukan di tuple ke-3 | `ValidationError` bebas |

Aturan praktis: **pakai SQL constraint kalau bisa**, Python constraint untuk sisanya.

### Dua Jebakan `@api.constrains`

**1. Hanya terpicu oleh field yang disebut.**

```python
@api.constrains("capacity")
def _check_capacity_not_below_confirmed(self):
    ...
```

Constraint di atas mengecek jumlah enrollment, tapi hanya terpicu saat `capacity` berubah. Menambah enrollment baru **tidak** memicunya. Kalau aturannya harus berlaku dua arah, constraint-nya perlu dipasang di kedua model.

**2. `ValidationError` vs `UserError`.**

| Exception | Untuk |
|---|---|
| `ValidationError` | Data melanggar aturan validasi |
| `UserError` | Aksi tidak boleh dilakukan sekarang (misal state salah) |

Keduanya menampilkan dialog ke user dan membatalkan transaksi. Bedanya di makna — pakai yang sesuai supaya kode terbaca.

---

## Workflow Approval Berjenjang

Kasus nyata: pendaftaran harus disetujui dua tingkat sebelum resmi.

```
draft → submitted → manager_approved → confirmed → done
                 ↘ rejected ↗ (kembali ke draft)
```

`models/academy_enrollment.py`:

```python
from odoo import api, fields, models
from odoo.exceptions import UserError


class AcademyEnrollment(models.Model):
    _name        = "academy.enrollment"
    _inherit     = ["mail.thread"]
    _description = "Academy Enrollment"

    name       = fields.Char(required=True, default="New", tracking=True)
    batch_id   = fields.Many2one("academy.batch", required=True,
                                 ondelete="cascade", tracking=True)
    student_id = fields.Many2one("academy.student", required=True,
                                 ondelete="restrict")
    enrollment_date = fields.Date(default=fields.Date.context_today)
    state = fields.Selection([
        ("draft",            "Draft"),
        ("submitted",        "Submitted"),
        ("manager_approved", "Manager Approved"),
        ("confirmed",        "Confirmed"),
        ("done",             "Done"),
        ("rejected",         "Rejected"),
        ("cancelled",        "Cancelled"),
    ], default="draft", tracking=True)
    notes = fields.Text()

    # --- jejak audit ---
    submitted_by_id   = fields.Many2one("res.users", string="Submitted By",
                                        readonly=True)
    submitted_date    = fields.Datetime(readonly=True)
    manager_approved_by_id = fields.Many2one("res.users",
                                             string="Level 1 Approved By",
                                             readonly=True)
    manager_approved_date  = fields.Datetime(readonly=True)
    final_approved_by_id   = fields.Many2one("res.users",
                                             string="Final Approved By",
                                             readonly=True)
    final_approved_date    = fields.Datetime(readonly=True)
    rejection_reason  = fields.Text(readonly=True, tracking=True)

    _sql_constraints = [
        ("unique_student_batch",
         "unique(batch_id, student_id)",
         "Student tidak boleh terdaftar dua kali di batch yang sama."),
    ]

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Hanya enrollment draft yang bisa di-submit.")
            rec.write({
                "state": "submitted",
                "submitted_by_id": self.env.user.id,
                "submitted_date": fields.Datetime.now(),
            })

    def action_manager_approve(self):
        if not self.env.user.has_group(
                "academy_management.academy_group_approval_l1"):
            raise UserError("Anda tidak berhak melakukan approval level 1.")
        for rec in self:
            if rec.state != "submitted":
                raise UserError(
                    "Hanya enrollment submitted yang bisa di-approve level 1.")
            rec.write({
                "state": "manager_approved",
                "manager_approved_by_id": self.env.user.id,
                "manager_approved_date": fields.Datetime.now(),
            })

    def action_final_approve(self):
        if not self.env.user.has_group(
                "academy_management.academy_group_approval_l2"):
            raise UserError("Anda tidak berhak melakukan final approval.")
        for rec in self:
            if rec.state != "manager_approved":
                raise UserError(
                    "Hanya enrollment manager-approved yang bisa "
                    "di-final approve.")
            rec.write({
                "state": "confirmed",
                "final_approved_by_id": self.env.user.id,
                "final_approved_date": fields.Datetime.now(),
            })

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ("rejected", "cancelled"):
                raise UserError(
                    "Hanya enrollment rejected atau cancelled yang bisa "
                    "dikembalikan ke draft.")
            rec.state = "draft"
```

Tiga hal yang layak diperhatikan:

1. **Setiap method mengecek state dulu.** Tanpa itu, user bisa melompati tahapan lewat API atau tombol yang lolos dari `invisible`.
2. **Cek hak pakai `has_group()`,** bukan hanya menyembunyikan tombol. Menyembunyikan tombol itu kosmetik — API tetap bisa dipanggil.
3. **`_inherit = ["mail.thread"]` + `tracking=True`** memberi chatter dan riwayat perubahan otomatis. Siapa mengubah apa, kapan — tercatat tanpa kode tambahan.

Tombol di form:

```xml
<header>
    <button name="action_submit" string="Submit" type="object"
            class="btn-primary" invisible="state != 'draft'"/>
    <button name="action_manager_approve" string="Approve L1" type="object"
            class="btn-primary" invisible="state != 'submitted'"
            groups="academy_management.academy_group_approval_l1"/>
    <button name="action_final_approve" string="Final Approve" type="object"
            class="btn-primary" invisible="state != 'manager_approved'"
            groups="academy_management.academy_group_approval_l2"/>
    <field name="state" widget="statusbar"
           statusbar_visible="draft,submitted,manager_approved,confirmed,done"/>
</header>
```

> Atribut `groups="..."` pada tombol menyembunyikannya dari user yang tidak berhak. Itu lapisan UI. Pengecekan `has_group()` di Python adalah lapisan sebenarnya. Keduanya dipakai bersama.

---

## 12. Advanced Views

### 12.1 Advanced List Views

**Optional columns** — user bisa show/hide dari icon kolom:
```xml
<list>
    <field name="name"/>
    <field name="batch_id"/>
    <field name="state" widget="badge"/>
    <field name="notes" optional="hide"/>
    <field name="submitted_by_id" optional="show"/>
</list>
```

**Inline button:**
```xml
<list>
    <field name="name"/>
    <field name="state" widget="badge"/>
    <button name="action_submit" string="Submit"
            type="object" icon="fa-paper-plane"
            invisible="state != 'draft'"/>
</list>
```

**Editable list** — edit tanpa buka form:
```xml
<list editable="bottom">
    <field name="name"/>
    <field name="capacity"/>
</list>
```

**Warna baris & agregasi:**
```xml
<list decoration-muted="state == 'cancelled'"
      decoration-success="state == 'confirmed'"
      decoration-danger="state == 'rejected'">
    <field name="batch_id"/>
    <field name="capacity" sum="Total Kapasitas" avg="Rata-rata"/>
</list>
```

> Agregasi (`sum`, `avg`) hanya jalan untuk field yang tersimpan di DB. Computed field tanpa `store=True` tidak bisa diagregasi.

### 12.2 Calendar Views

```xml
<record id="view_academy_batch_calendar" model="ir.ui.view">
    <field name="name">academy.batch.calendar</field>
    <field name="model">academy.batch</field>
    <field name="arch" type="xml">
        <calendar string="Jadwal Batch"
                  date_start="start_date"
                  date_stop="end_date"
                  color="course_id"
                  mode="month">
            <field name="name"/>
            <field name="course_id"/>
            <field name="state"/>
        </calendar>
    </field>
</record>
```

| Atribut | Fungsi |
|---------|--------|
| `date_start` | Field tanggal mulai (**wajib**) |
| `date_stop` | Field tanggal selesai (opsional — kalau kosong, event = 1 hari) |
| `color` | Field many2one/selection untuk warna per kategori |
| `mode` | Default tampilan: `month`, `week`, `day` |

Tambahkan ke `view_mode` action agar muncul di switcher:
```xml
<field name="view_mode">list,form,calendar</field>
```

> `academy.batch` cocok untuk calendar karena punya `start_date` dan `end_date` yang bermakna secara bisnis. Memasang calendar pada `create_date` secara teknis bisa, tapi tidak berguna bagi user.

### 12.3 Advanced Search Views

**`filter_domain`** — ubah cara Odoo mencari saat user mengetik:
```xml
<search>
    <field name="student_id"
           filter_domain="['|', ('student_id.name','ilike',self),
                                ('student_id.email','ilike',self)]"/>
</search>
```
`self` = teks yang diketik user. Satu kotak pencarian, dua field dicari sekaligus.

**Filter default aktif** — lewat `context` di action:
```xml
<record id="action_academy_enrollment" model="ir.actions.act_window">
    <field name="name">Enrollments</field>
    <field name="res_model">academy.enrollment</field>
    <field name="view_mode">list,form</field>
    <field name="context">{'search_default_pending': 1}</field>
</record>
```
Pola: `search_default_<nama_filter>`. Untuk group by: `search_default_group_state`.

**AND vs OR antar filter:**
```xml
<search>
    <filter name="draft"     string="Draft"     domain="[('state','=','draft')]"/>
    <filter name="submitted" string="Submitted" domain="[('state','=','submitted')]"/>
    <separator/>
    <filter name="mine" string="Batch Saya"
            domain="[('batch_id.responsible_id','=',uid)]"/>
</search>
```

Filter dalam blok yang sama (tanpa `<separator/>`) digabung **OR**. Antar blok yang dipisah `<separator/>` digabung **AND**.

Jadi contoh di atas: user bisa memilih Draft **atau** Submitted, **dan** sekaligus membatasi ke batch miliknya sendiri. Ini perilaku yang benar — dan alasan kenapa `<separator/>` bukan sekadar garis pemisah visual.

> `uid` adalah variabel bawaan di domain view = ID user yang sedang login.

**Search panel** — filter sidebar kiri:
```xml
<search>
    <searchpanel>
        <field name="state" icon="fa-filter"/>
        <field name="batch_id" icon="fa-users" enable_counters="1"/>
    </searchpanel>
</search>
```

---

## 13. Security

Odoo punya tiga lapis. Urutannya penting: kalau lapis sebelumnya menolak, lapis berikutnya tidak pernah dievaluasi.

```
1. Group          → user masuk kelompok apa
2. Access Rights  → kelompok itu boleh CRUD model apa   (per MODEL)
3. Record Rules   → dari model itu, baris mana saja      (per RECORD)
```

### 13.1 Group-based Access Control

`security/academy_groups.xml`:

```xml
<odoo>
    <record id="module_category_academy" model="ir.module.category">
        <field name="name">Academy</field>
        <field name="sequence">10</field>
    </record>

    <record id="academy_group_user" model="res.groups">
        <field name="name">Academy User</field>
        <field name="category_id" ref="module_category_academy"/>
    </record>

    <record id="academy_group_approval_l1" model="res.groups">
        <field name="name">Academy Approval Level 1</field>
        <field name="category_id" ref="module_category_academy"/>
        <field name="implied_ids" eval="[(4, ref('academy_group_user'))]"/>
    </record>

    <record id="academy_group_approval_l2" model="res.groups">
        <field name="name">Academy Approval Level 2</field>
        <field name="category_id" ref="module_category_academy"/>
        <field name="implied_ids" eval="[(4, ref('academy_group_user'))]"/>
    </record>

    <record id="academy_group_manager" model="res.groups">
        <field name="name">Academy Manager</field>
        <field name="category_id" ref="module_category_academy"/>
        <field name="implied_ids"
               eval="[(4, ref('academy_group_user')),
                      (4, ref('academy_group_approval_l1')),
                      (4, ref('academy_group_approval_l2'))]"/>
    </record>
</odoo>
```

**`implied_ids` = pewarisan group.** User yang masuk Manager otomatis mendapat semua hak User, Approval L1, dan L2. Ini mencegah duplikasi aturan — hak cukup didefinisikan sekali di group terbawah.

> **Perhatian versi:** Odoo 19 memperkenalkan model `res.groups.privilege` dan field `privilege_id` untuk mengelompokkan group. Di **Odoo 18 pakai `category_id`** yang menunjuk `ir.module.category`, seperti contoh di atas. Kode Odoo 19 akan gagal install di sini.

### 13.2 Access Rights

Per model, per group, empat operasi CRUD. Ditulis di CSV:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_course_user,academy.course.user,model_academy_course,academy_group_user,1,0,0,0
access_course_manager,academy.course.mgr,model_academy_course,academy_group_manager,1,1,1,1
access_batch_user,academy.batch.user,model_academy_batch,academy_group_user,1,0,0,0
access_batch_manager,academy.batch.mgr,model_academy_batch,academy_group_manager,1,1,1,1
access_enrollment_user,academy.enrollment.user,model_academy_enrollment,academy_group_user,1,1,1,0
access_enrollment_manager,academy.enrollment.mgr,model_academy_enrollment,academy_group_manager,1,1,1,1
```

Membaca desain di atas:
- **Academy User** hanya boleh **membaca** course dan batch — itu data master, bukan urusannya.
- **Academy User** boleh membuat dan mengubah enrollment, tapi **tidak boleh menghapus** (`perm_unlink=0`).
- **Academy Manager** punya kendali penuh.

Cara membaca `model_id:id`:
- Odoo otomatis membuat external ID untuk tiap model: `model_` + `_name` dengan titik jadi underscore.
- `academy.enrollment` → `model_academy_enrollment`.
- Kalau model didefinisikan di modul **lain**, tambahkan prefix modulnya: `base.model_res_partner`.

> Model tanpa satu pun baris access right = tidak ada yang bisa mengaksesnya, kecuali superuser. Ini penyebab error "You are not allowed to access..." yang paling sering.

### 13.3 Record Rules

Membatasi **baris mana** yang terlihat, lewat domain. `security/academy_record_rules.xml`:

```xml
<odoo>
    <record id="batch_rule_user_own" model="ir.rule">
        <field name="name">Academy User: hanya batch sendiri</field>
        <field name="model_id" ref="model_academy_batch"/>
        <field name="groups" eval="[(4, ref('academy_group_user'))]"/>
        <field name="domain_force">[('responsible_id', '=', user.id)]</field>
    </record>

    <record id="batch_rule_manager_all" model="ir.rule">
        <field name="name">Academy Manager: semua batch</field>
        <field name="model_id" ref="model_academy_batch"/>
        <field name="groups" eval="[(4, ref('academy_group_manager'))]"/>
        <field name="domain_force">[(1, '=', 1)]</field>
    </record>

    <record id="enrollment_rule_user_own" model="ir.rule">
        <field name="name">Academy User: enrollment di batch sendiri</field>
        <field name="model_id" ref="model_academy_enrollment"/>
        <field name="groups" eval="[(4, ref('academy_group_user'))]"/>
        <field name="domain_force">[('batch_id.responsible_id', '=', user.id)]</field>
    </record>
</odoo>
```

**Kenapa perlu `batch_rule_manager_all`?**

| Jenis rule | Ciri | Cara digabung |
|---|---|---|
| **Group rule** | `groups` diisi | Antar group rule digabung **OR** |
| **Global rule** | `groups` kosong | Digabung **AND** ke semua, tidak bisa dilewati |

Manager juga anggota Academy User (lewat `implied_ids`), jadi rule "hanya batch sendiri" ikut berlaku padanya. Karena antar group rule digabung **OR**, menambahkan rule `[(1,'=',1)]` untuk Manager membuka kembali akses penuh.

> `[(1, '=', 1)]` adalah domain yang selalu benar — cara idiomatik menulis "semua record".
>
> Variabel yang tersedia di `domain_force`: `user` (record user aktif), `company_id`, `company_ids`, `time`.

### `sudo()` — dan Kapan Tidak Boleh

`sudo()` menjalankan operasi sebagai superuser, melewati access rights **dan** record rules:

```python
self.env["academy.batch"].sudo().search([])
```

Boleh dipakai untuk: proses sistem yang memang harus lintas user (cron, webhook, endpoint integrasi yang autentikasinya sudah dijamin), atau saat user perlu efek samping pada data yang tidak boleh ia akses langsung.

**Jangan** dipakai untuk menutupi error "not allowed" tanpa memahami sebabnya. Itu membuka data yang seharusnya tertutup. Perbaiki access right-nya, bukan tempel `sudo()`.

---

## Latihan
→ [`labs/lab-d03.md`](labs/lab-d03.md)
