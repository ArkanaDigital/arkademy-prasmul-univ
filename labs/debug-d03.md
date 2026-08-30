# Day 3 Debugging Checklist

## 1. Upgrade gagal karena constraint

```text
could not create unique index "academy_batch_code_unique"
```

Data lama sudah melanggar. Cari dulu:

```sql
-- duplikat code
SELECT code, COUNT(*) FROM academy_batch
WHERE code IS NOT NULL GROUP BY code HAVING COUNT(*) > 1;

-- capacity tidak valid
SELECT id, name, capacity FROM academy_batch WHERE capacity <= 0;

-- duplikat student+batch
SELECT batch_id, student_id, COUNT(*) FROM academy_enrollment
GROUP BY batch_id, student_id HAVING COUNT(*) > 1;
```

Perbaiki, lalu upgrade lagi.

---

## 2. `models.Constraint` error

```text
AttributeError: module 'odoo.models' has no attribute 'Constraint'
```

Itu API **Odoo 19**. Di Odoo 18 pakai `_sql_constraints`:

```python
_sql_constraints = [
    ("code_unique", "unique(code)", "Batch code harus unik."),
]
```

---

## 3. `res.groups.privilege` error

```text
ValueError: Invalid model name 'res.groups.privilege'
```

Juga API **Odoo 19**. Di Odoo 18:

```xml
<record id="module_category_academy" model="ir.module.category">
    <field name="name">Academy</field>
</record>

<record id="academy_group_user" model="res.groups">
    <field name="name">Academy User</field>
    <field name="category_id" ref="module_category_academy"/>
</record>
```

---

## 4. Python constraint tidak jalan

- [ ] Field pemicu disebut di `@api.constrains(...)`
- [ ] Method meng-iterasi `self`
- [ ] `ValidationError` di-import dari `odoo.exceptions`

> `@api.constrains` hanya terpicu kalau field yang terdaftar ikut diubah. Constraint yang mengecek enrollment tapi hanya `@api.constrains("capacity")` **tidak** akan terpicu saat enrollment ditambah.

---

## 5. Constraint dilewati saat SQL langsung

Bukan bug:

| | SQL constraint | Python constraint |
|---|---|---|
| Lewat ORM | Jalan | Jalan |
| Lewat SQL langsung | Jalan | **Dilewati** |

Kalau aturannya mutlak, pakai SQL constraint.

---

## 6. External ID model tidak ditemukan

```text
ValueError: External ID not found: academy_management.model_academy_batch
```

- [ ] Model di modul ini sendiri → **tanpa** prefix: `model_academy_batch`
- [ ] Model dari modul lain → dengan prefix: `base.model_res_partner`

Format: `model_` + `_name` dengan titik jadi underscore.

---

## 7. Record rule tidak berefek

- [ ] **Tidak** sedang login sebagai admin/superuser
- [ ] `groups` diisi — kalau kosong, rule jadi global dan berlaku ke semua
- [ ] `domain_force` sintaksnya benar
- [ ] Module sudah di-upgrade

Uji lewat shell dengan user lain:

```python
>>> u = env["res.users"].search([("login", "=", "user.test")])
>>> env(user=u)["academy.batch"].search([])
```

---

## 8. Manager malah ikut terbatas

Manager mewarisi Academy User lewat `implied_ids`, jadi kena rule-nya juga. Antar group rule digabung **OR**, jadi Manager butuh rule sendiri:

```xml
<field name="domain_force">[(1, '=', 1)]</field>
```

---

## 9. `You are not allowed to access`

Urutan pengecekan Odoo:

```
1. Group   → user masuk group itu?
2. Access  → group punya baris di ir.model.access.csv?
3. Rule    → record lolos domain rule?
```

Cek dari atas:

- [ ] User punya group yang dimaksud
- [ ] Ada baris CSV untuk model + group itu
- [ ] `perm_*` yang dibutuhkan bernilai 1
- [ ] File CSV terdaftar di manifest
- [ ] Group didaftarkan **sebelum** CSV di manifest

---

## 10. `has_group()` selalu False

Nama group harus lengkap dengan nama modul:

```python
# BENAR
self.env.user.has_group("academy_management.academy_group_approval_l1")

# SALAH
self.env.user.has_group("academy_group_approval_l1")
```

---

## 11. `implied_ids` tidak terpasang ke user lama

Perubahan `implied_ids` tidak retroaktif ke user yang sudah ada. Buka ulang form user dan centang group-nya manual.

---

## 12. User uji tidak melihat menu apa pun

Belum punya group **Internal User** (`base.group_user`). Group custom saja tidak cukup untuk masuk backend.

---

## 13. Chatter tidak muncul

- [ ] `"mail"` ada di `depends` manifest
- [ ] `_inherit = ["mail.thread"]` di model
- [ ] Tag `<chatter/>` ada setelah `</sheet>` di form
- [ ] Field yang ingin dilacak punya `tracking=True`
- [ ] Module sudah di-upgrade

---

## 14. Calendar view tidak muncul di switcher

- [ ] `calendar` ada di `view_mode` action
- [ ] `date_start` menunjuk field Date/Datetime yang ada
- [ ] Module di-upgrade, browser di-refresh

---

## 15. Filter default tidak aktif

Nama di context = `search_default_` + `name` filter:

```xml
<filter name="pending" .../>
<field name="context">{'search_default_pending': 1}</field>
```

---

## 16. Inline button di list tidak muncul

- [ ] `type="object"`, `name` menunjuk method yang ada
- [ ] Field yang dipakai di `invisible` ikut ditampilkan di `<list>`
- [ ] Ekspresi `invisible` pakai sintaks Python

---

## 17. Tombol tersembunyi tapi method tetap bisa dipanggil

Itu memang perilakunya. `groups=` dan `invisible=` adalah lapisan **UI**. Pengaman sebenarnya:

```python
if not self.env.user.has_group("academy_management.academy_group_approval_l1"):
    raise UserError("Anda tidak berhak melakukan approval level 1.")
```

Selalu pasang keduanya.

---

## Perintah Diagnostik Cepat

```bash
./odoo/odoo-bin shell -c odoo.conf -d academy
```

```python
# Group user
>>> u = env["res.users"].search([("login", "=", "user.test")])
>>> u.groups_id.mapped("name")

# Access right yang berlaku
>>> env["ir.model.access"].search([
...     ("model_id.model", "=", "academy.enrollment")
... ]).read(["name", "group_id", "perm_unlink"])

# Record rule
>>> env["ir.rule"].search([
...     ("model_id.model", "=", "academy.batch")
... ]).read(["name", "domain_force", "groups"])

# Simulasi sebagai user lain
>>> env(user=u)["academy.batch"].search([])
>>> env(user=u)["academy.enrollment"].check_access_rights("unlink", raise_exception=False)

# Riwayat chatter
>>> enr = env["academy.enrollment"].search([], limit=1)
>>> enr.message_ids.mapped("body")
```
