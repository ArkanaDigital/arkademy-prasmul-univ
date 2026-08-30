# Day 3 Hands-on Lab — Constraints, Advanced Views, Security

## Objective

Di akhir lab Day 3, module `academy_management` Anda punya:

- constraint SQL & Python yang menolak data salah
- workflow approval dua tingkat dengan jejak audit
- advanced list, calendar, dan advanced search view
- empat group dengan hak berbeda, diuji dengan login user asli

---

# Prerequisite

- Lab Day 2 selesai — 5 model, relasi, computed sudah jalan

Kalau tertinggal:

```bash
rm -rf custom-addons/academy_management
cp -R materi/labs/source-checkpoints/d02/checkpoint_final_day2/academy_management \
      custom-addons/
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Checkpoint Day 3: `a_constraints` → `b_state_approval` → `c_approval_monitoring_views` → `d_security_for_approval` → `e_wizard` → `final_day3`

> `checkpoint_e_wizard` berisi wizard yang dibahas di **Day 4**. Hari ini berhenti di `checkpoint_d_security_for_approval`.

---

# Checkpoint A — Constraints

## Goal

Data yang melanggar aturan ditolak, dengan pesan yang bisa dipahami user.

## Step 1 — SQL Constraint di Batch

Tambahkan ke `models/academy_batch.py`:

```python
    _sql_constraints = [
        ("code_unique", "unique(code)", "Batch code harus unik."),
        ("capacity_positive", "CHECK (capacity > 0)",
         "Capacity harus lebih dari 0."),
    ]
```

> Odoo 19 memakai `models.Constraint(...)`. Di **Odoo 18 pakai `_sql_constraints`** seperti di atas.

## Step 2 — Python Constraint di Batch

```python
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AcademyBatch(models.Model):
    # ... definisi sebelumnya ...

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

## Step 3 — Upgrade

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

> Kalau upgrade gagal dengan pesan constraint, ada data lama yang melanggar. Cari dan bersihkan dulu:
>
> ```sql
> SELECT code, COUNT(*) FROM academy_batch
> WHERE code IS NOT NULL GROUP BY code HAVING COUNT(*) > 1;
> SELECT id, name, capacity FROM academy_batch WHERE capacity <= 0;
> ```

## Step 4 — Uji Semuanya

| Uji | Harapan |
|---|---|
| Dua batch dengan `code` sama | Ditolak |
| Batch dengan `capacity` = 0 | Ditolak |
| `start_date` setelah `end_date` | Ditolak, pesan jelas |
| Turunkan `capacity` di bawah jumlah enrollment confirmed | Ditolak |

## Step 5 — Buktikan Bedanya Dua Jenis Constraint

```bash
./odoo/odoo-bin shell -c odoo.conf -d academy
```

Python constraint bisa dilewati lewat SQL langsung:

```python
>>> env.cr.execute("""
...     INSERT INTO academy_batch (name, course_id, capacity, start_date, end_date, state)
...     VALUES ('BYPASS', 1, 10, '2026-12-31', '2026-01-01', 'draft')
... """)
>>> env.cr.commit()
```

Berhasil — tanggalnya terbalik, tapi Python constraint tidak jalan karena tidak lewat ORM.

Sekarang coba langgar SQL constraint dengan cara yang sama:

```python
>>> env.cr.execute("""
...     INSERT INTO academy_batch (name, course_id, capacity, state)
...     VALUES ('BYPASS2', 1, 0, 'draft')
... """)
```

PostgreSQL **menolak** — `CHECK (capacity > 0)` dijaga di level database.

Bersihkan:

```python
>>> env.cr.rollback()
>>> env.cr.execute("DELETE FROM academy_batch WHERE name = 'BYPASS'")
>>> env.cr.commit()
```

## Checkpoint A selesai bila:

- [ ] Batch code duplikat ditolak
- [ ] `capacity` ≤ 0 ditolak
- [ ] Tanggal terbalik ditolak dengan pesan jelas
- [ ] Capacity di bawah confirmed ditolak
- [ ] Anda sudah membuktikan sendiri SQL constraint lebih dalam daripada Python constraint

> Bandingkan: `source-checkpoints/d03/checkpoint_a_constraints`

---

# Checkpoint B — State & Approval Berjenjang

## Goal

Enrollment melewati approval dua tingkat, lengkap dengan jejak siapa dan kapan.

## Step 1 — State Baru + Chatter

Ubah `models/academy_enrollment.py`:

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

    # jejak audit
    submitted_by_id        = fields.Many2one("res.users", readonly=True,
                                             string="Submitted By")
    submitted_date         = fields.Datetime(readonly=True)
    manager_approved_by_id = fields.Many2one("res.users", readonly=True,
                                             string="Level 1 Approved By")
    manager_approved_date  = fields.Datetime(readonly=True)
    final_approved_by_id   = fields.Many2one("res.users", readonly=True,
                                             string="Final Approved By")
    final_approved_date    = fields.Datetime(readonly=True)
    rejection_reason       = fields.Text(readonly=True, tracking=True)

    _sql_constraints = [
        ("unique_student_batch",
         "unique(batch_id, student_id)",
         "Student tidak boleh terdaftar dua kali di batch yang sama."),
    ]
```

Tambahkan `"mail"` ke `depends` di manifest.

## Step 2 — Method Approval

```python
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

    def action_done(self):
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(
                    "Hanya enrollment confirmed yang bisa diselesaikan.")
            rec.state = "done"

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ("rejected", "cancelled"):
                raise UserError(
                    "Hanya enrollment rejected atau cancelled yang bisa "
                    "dikembalikan ke draft.")
            rec.state = "draft"
```

> Method ini memanggil group yang **belum dibuat** (Checkpoint D). Jangan uji tombol approval dulu — kerjakan Checkpoint D lalu kembali ke sini.

## Step 3 — Header Form

Di `views/academy_enrollment_views.xml`, tambahkan ke dalam `<form>`:

```xml
<header>
    <button name="action_submit" string="Submit" type="object"
            class="btn-primary" invisible="state != 'draft'"/>
    <button name="action_manager_approve" string="Approve L1" type="object"
            class="btn-primary" invisible="state != 'submitted'"/>
    <button name="action_final_approve" string="Final Approve" type="object"
            class="btn-primary" invisible="state != 'manager_approved'"/>
    <button name="action_done" string="Done" type="object"
            invisible="state != 'confirmed'"/>
    <button name="action_reset_to_draft" string="Reset to Draft" type="object"
            invisible="state not in ('rejected', 'cancelled')"/>
    <field name="state" widget="statusbar"
           statusbar_visible="draft,submitted,manager_approved,confirmed,done"/>
</header>
```

Tambahkan chatter di akhir `<form>`, setelah `</sheet>`:

```xml
<chatter/>
```

## Step 4 — Upgrade dan Uji

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

1. Buka enrollment → statusbar muncul di atas
2. Klik **Submit** → state berubah, `submitted_by_id` dan `submitted_date` terisi
3. Chatter di bawah mencatat perubahan state
4. Klik Submit lagi lewat shell pada record yang sudah submitted → `UserError`

## Checkpoint B selesai bila:

- [ ] Statusbar tampil dengan 5 tahapan
- [ ] Submit mengisi jejak audit otomatis
- [ ] Chatter mencatat perubahan `state` dan `name`
- [ ] Submit pada state yang salah ditolak dengan pesan jelas

> Bandingkan: `source-checkpoints/d03/checkpoint_b_state_approval`

---

# Checkpoint C — Advanced Views

## Goal

List, calendar, dan search yang layak dipakai sehari-hari.

## Step 1 — Advanced List Enrollment

```xml
<list decoration-muted="state == 'cancelled'"
      decoration-success="state == 'confirmed'"
      decoration-danger="state == 'rejected'">
    <field name="name"/>
    <field name="batch_id"/>
    <field name="student_id"/>
    <field name="enrollment_date"/>
    <field name="submitted_by_id" optional="show"/>
    <field name="notes" optional="hide"/>
    <field name="state" widget="badge"/>
    <button name="action_submit" string="Submit" type="object"
            icon="fa-paper-plane" invisible="state != 'draft'"/>
</list>
```

## Step 2 — Calendar View Batch

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

Tambahkan `calendar` ke `view_mode` action batch:

```xml
<field name="view_mode">list,form,calendar</field>
```

## Step 3 — Advanced Search Enrollment

```xml
<record id="view_academy_enrollment_search" model="ir.ui.view">
    <field name="name">academy.enrollment.search</field>
    <field name="model">academy.enrollment</field>
    <field name="arch" type="xml">
        <search string="Cari Enrollment">
            <field name="name"/>
            <field name="student_id"
                   filter_domain="['|', ('student_id.name','ilike',self),
                                        ('student_id.email','ilike',self)]"/>
            <field name="batch_id"/>

            <filter name="draft" string="Draft"
                    domain="[('state','=','draft')]"/>
            <filter name="submitted" string="Submitted"
                    domain="[('state','=','submitted')]"/>
            <filter name="pending" string="Menunggu Approval"
                    domain="[('state','in',('submitted','manager_approved'))]"/>
            <separator/>
            <filter name="mine" string="Batch Saya"
                    domain="[('batch_id.responsible_id','=',uid)]"/>

            <group expand="0" string="Group By">
                <filter name="group_state" string="Status"
                        context="{'group_by': 'state'}"/>
                <filter name="group_batch" string="Batch"
                        context="{'group_by': 'batch_id'}"/>
            </group>

            <searchpanel>
                <field name="state" icon="fa-filter"/>
                <field name="batch_id" icon="fa-users" enable_counters="1"/>
            </searchpanel>
        </search>
    </field>
</record>
```

Aktifkan filter default lewat context action:

```xml
<field name="context">{'search_default_pending': 1}</field>
```

## Step 4 — Upgrade dan Uji

1. Buka **Enrollments** — filter "Menunggu Approval" sudah aktif otomatis
2. Icon kolom → `notes` bisa ditampilkan
3. Baris `rejected` merah, `confirmed` hijau
4. Ketik email student di search box → enrollment-nya ketemu
5. Search panel muncul di kiri
6. Pilih filter Draft **dan** Batch Saya → keduanya berlaku bersamaan (AND)
7. Pilih Draft **dan** Submitted → keduanya digabung OR

Langkah 6 dan 7 membuktikan fungsi `<separator/>`.

## Checkpoint C selesai bila:

- [ ] Warna baris sesuai state
- [ ] Kolom optional bisa show/hide
- [ ] Tombol Submit hanya muncul di baris draft
- [ ] Calendar batch muncul di switcher, warna per course
- [ ] Cari lewat email student berhasil
- [ ] Filter default aktif saat menu dibuka
- [ ] Search panel tampil
- [ ] Anda bisa menjelaskan kapan filter digabung AND vs OR

> Bandingkan: `source-checkpoints/d03/checkpoint_c_approval_monitoring_views`

---

# Checkpoint D — Security

## Goal

Empat group dengan hak berbeda, dibuktikan lewat login user asli.

## Step 1 — Groups

`security/academy_groups.xml`:

```xml
<odoo>
    <record id="module_category_academy" model="ir.module.category">
        <field name="name">Academy</field>
        <field name="sequence">10</field>
    </record>

    <record id="academy_group_user" model="res.groups">
        <field name="name">Academy User</field>
        <field name="sequence">10</field>
        <field name="category_id" ref="module_category_academy"/>
    </record>

    <record id="academy_group_approval_l1" model="res.groups">
        <field name="name">Academy Approval Level 1</field>
        <field name="sequence">20</field>
        <field name="category_id" ref="module_category_academy"/>
        <field name="implied_ids" eval="[(4, ref('academy_group_user'))]"/>
    </record>

    <record id="academy_group_approval_l2" model="res.groups">
        <field name="name">Academy Approval Level 2</field>
        <field name="sequence">30</field>
        <field name="category_id" ref="module_category_academy"/>
        <field name="implied_ids" eval="[(4, ref('academy_group_user'))]"/>
    </record>

    <record id="academy_group_manager" model="res.groups">
        <field name="name">Academy Manager</field>
        <field name="sequence">40</field>
        <field name="category_id" ref="module_category_academy"/>
        <field name="implied_ids"
               eval="[(4, ref('academy_group_user')),
                      (4, ref('academy_group_approval_l1')),
                      (4, ref('academy_group_approval_l2'))]"/>
    </record>
</odoo>
```

> Odoo 19 memakai `res.groups.privilege` + `privilege_id`. Di **Odoo 18 pakai `category_id`** yang menunjuk `ir.module.category`.

## Step 2 — Access Rights per Group

Ganti isi `security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_course_user,academy.course.user,model_academy_course,academy_group_user,1,0,0,0
access_course_manager,academy.course.mgr,model_academy_course,academy_group_manager,1,1,1,1
access_student_user,academy.student.user,model_academy_student,academy_group_user,1,1,1,0
access_student_manager,academy.student.mgr,model_academy_student,academy_group_manager,1,1,1,1
access_batch_user,academy.batch.user,model_academy_batch,academy_group_user,1,0,0,0
access_batch_manager,academy.batch.mgr,model_academy_batch,academy_group_manager,1,1,1,1
access_enrollment_user,academy.enrollment.user,model_academy_enrollment,academy_group_user,1,1,1,0
access_enrollment_manager,academy.enrollment.mgr,model_academy_enrollment,academy_group_manager,1,1,1,1
access_tag_user,academy.tag.user,model_academy_course_tag,academy_group_user,1,0,0,0
access_tag_manager,academy.tag.mgr,model_academy_course_tag,academy_group_manager,1,1,1,1
```

Bacalah desainnya: Academy User hanya **membaca** course dan batch, boleh mengelola enrollment tapi **tidak boleh menghapus**.

## Step 3 — Record Rules

`security/academy_record_rules.xml`:

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

    <record id="enrollment_rule_manager_all" model="ir.rule">
        <field name="name">Academy Manager: semua enrollment</field>
        <field name="model_id" ref="model_academy_enrollment"/>
        <field name="groups" eval="[(4, ref('academy_group_manager'))]"/>
        <field name="domain_force">[(1, '=', 1)]</field>
    </record>
</odoo>
```

> **Kenapa Manager butuh rule sendiri?** Manager juga anggota Academy User lewat `implied_ids`, jadi rule "hanya batch sendiri" ikut berlaku padanya. Antar group rule digabung **OR**, jadi menambahkan `[(1,'=',1)]` membuka kembali akses penuh.

## Step 4 — Tambahkan `groups` pada Tombol

```xml
<button name="action_manager_approve" string="Approve L1" type="object"
        class="btn-primary" invisible="state != 'submitted'"
        groups="academy_management.academy_group_approval_l1"/>
<button name="action_final_approve" string="Final Approve" type="object"
        class="btn-primary" invisible="state != 'manager_approved'"
        groups="academy_management.academy_group_approval_l2"/>
```

## Step 5 — Daftarkan di Manifest

```python
"data": [
    "security/academy_groups.xml",
    "security/ir.model.access.csv",
    "security/academy_record_rules.xml",
    ...
],
```

> Urutan penting: group harus ada sebelum CSV dan rule yang merujuknya.

## Step 6 — Upgrade dan Buat User Uji

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

**Settings → Users & Companies → Users → New**, buat tiga user:

| User | Group Academy |
|---|---|
| `user.test` | Academy User |
| `approver.test` | Academy Approval Level 1 |
| `manager.test` | Academy Manager |

Pastikan ketiganya juga punya group **Internal User**. Set password lewat Action → Change Password.

## Step 7 — Siapkan Data Uji

Sebagai admin: buat 2 batch, satu dengan `responsible_id` = `user.test`, satu lagi = admin. Isi masing-masing dengan enrollment.

## Step 8 — Uji dengan Login Asli

Buka **jendela incognito** untuk tiap user.

**Sebagai `user.test`:**
- [ ] Hanya melihat batch miliknya sendiri
- [ ] Hanya melihat enrollment di batch miliknya
- [ ] Tidak ada tombol Delete di enrollment
- [ ] Tidak bisa membuat course baru
- [ ] Tombol "Approve L1" tidak terlihat

**Sebagai `approver.test`:**
- [ ] Tombol "Approve L1" terlihat
- [ ] Tombol "Final Approve" tidak terlihat

**Sebagai `manager.test`:**
- [ ] Melihat **semua** batch dan enrollment
- [ ] Tombol Delete tersedia
- [ ] Kedua tombol approval terlihat

> **Jangan uji pakai admin.** Admin melewati hampir semua aturan, jadi hasilnya menyesatkan.

## Step 9 — Buktikan Lapisan UI Bukan Lapisan Keamanan

Sebagai `user.test`, di shell:

```python
>>> u = env["res.users"].search([("login", "=", "user.test")])
>>> enr = env(user=u)["academy.enrollment"].search([], limit=1)
>>> enr.action_manager_approve()
```

Tombolnya disembunyikan `groups=`, tapi method tetap bisa dipanggil. Yang menolak adalah `has_group()` di Python.

Coba juga hapus:

```python
>>> env(user=u)["academy.enrollment"].search([]).unlink()
```

Ditolak oleh access right, bukan oleh UI.

## Checkpoint D selesai bila:

- [ ] Empat group terbuat, Manager mewarisi ketiganya
- [ ] Academy User tidak bisa delete
- [ ] Academy User hanya melihat batch miliknya
- [ ] Manager melihat semua
- [ ] Tombol approval muncul sesuai group
- [ ] Anda sudah menguji dengan login user asli
- [ ] Anda sudah membuktikan `groups=` di tombol hanya kosmetik
- [ ] Anda bisa menjelaskan beda access right dan record rule

> Bandingkan: `source-checkpoints/d03/checkpoint_d_security_for_approval`

---

# Common Mistakes

## 1. `implied_ids` tidak berefek

Group tidak akan terpasang ke user yang sudah ada sebelumnya. Buka ulang form user dan centang manual.

## 2. External ID model tidak ketemu

Model di modul ini sendiri → **tanpa** prefix (`model_academy_batch`). Model dari modul lain → dengan prefix (`base.model_res_partner`).

## 3. Record rule tidak berefek

Login sebagai admin. Admin melewati record rule.

## 4. Manager malah ikut terbatas

Manager mewarisi Academy User, jadi kena rule-nya juga. Butuh rule `[(1,'=',1)]` khusus Manager.

## 5. Upgrade gagal karena constraint

Data lama melanggar aturan baru. Bersihkan dulu.

## 6. Python constraint tidak jalan

Field pemicunya tidak disebut di `@api.constrains`.

## 7. `has_group()` selalu False

Nama group harus lengkap dengan nama modul: `academy_management.academy_group_approval_l1`.

## 8. User uji tidak melihat menu sama sekali

Belum punya group **Internal User** (`base.group_user`).

## 9. Chatter tidak muncul

`"mail"` sudah masuk `depends`? `_inherit = ["mail.thread"]` sudah ditulis? Tag `<chatter/>` sudah ditambahkan setelah `</sheet>`?

---

# Final Checklist Day 3

| Item | Status |
|---|---|
| SQL constraint `code` unik bekerja | ☐ |
| SQL constraint `capacity > 0` bekerja | ☐ |
| Python constraint tanggal bekerja | ☐ |
| Python constraint capacity vs confirmed bekerja | ☐ |
| Sudah membuktikan SQL constraint lebih dalam dari Python | ☐ |
| State approval 7 nilai terpasang | ☐ |
| Statusbar tampil | ☐ |
| Jejak audit terisi otomatis | ☐ |
| Chatter mencatat perubahan | ☐ |
| Transisi state yang salah ditolak | ☐ |
| Advanced list: warna, optional, inline button | ☐ |
| Calendar view batch tampil | ☐ |
| `filter_domain` cari nama atau email | ☐ |
| Filter default aktif dari context | ☐ |
| Search panel tampil | ☐ |
| Paham AND vs OR antar filter | ☐ |
| Empat group terbuat dengan pewarisan | ☐ |
| Academy User tidak bisa delete | ☐ |
| Record rule membatasi ke batch sendiri | ☐ |
| Manager melihat semua | ☐ |
| Diuji dengan user asli, bukan admin | ☐ |
| Sudah membuktikan `groups=` cuma kosmetik | ☐ |

---

Troubleshooting cepat: → [`debug-d03.md`](debug-d03.md)
