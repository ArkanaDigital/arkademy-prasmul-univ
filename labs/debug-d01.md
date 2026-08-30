# Day 1 Debugging Checklist

## 1. Module tidak muncul di Apps

- [ ] Folder module ada di `custom-addons/`
- [ ] `addons_path` di `odoo.conf` mencakup `custom-addons`
- [ ] Odoo sudah di-restart
- [ ] Sudah klik **Update Apps List** (butuh developer mode)
- [ ] Filter **Apps** di search box sudah dihapus
- [ ] Nama folder tidak typo: `academy_management`
- [ ] Ada `__manifest__.py` di dalam folder module

---

## 2. Module install error

- [ ] Syntax Python valid — `python -m py_compile <file>.py`
- [ ] Syntax XML valid — tag pembuka/penutup seimbang
- [ ] Syntax CSV valid — jumlah kolom tiap baris sama dengan header
- [ ] Semua file di `"data"` manifest path-nya benar
- [ ] Dependency di manifest tersedia

Baca **baris terakhir** traceback di terminal, bukan baris pertama — di situ pesan sebenarnya.

---

## 3. Model tidak ditemukan

```text
KeyError: 'academy.course'
```

- [ ] File model sudah dibuat
- [ ] File model sudah di-import di `models/__init__.py`
- [ ] Folder `models` sudah di-import di `__init__.py` module
- [ ] Module sudah di-upgrade dengan `-u academy_management`
- [ ] `_name` tidak typo

---

## 4. Table tidak muncul di PostgreSQL

- [ ] Model punya `_name`
- [ ] Class meng-extend `models.Model`
- [ ] Module sudah upgrade
- [ ] Tidak ada error saat registry loading

Nama tabel = `_name` dengan titik jadi underscore. `academy.course` → `academy_course`.

---

## 5. Field `Monetary` error

```text
Field academy.course.price with unknown currency_field
```

`Monetary` butuh field `currency_id` di model yang sama:

```python
price       = fields.Monetary()
currency_id = fields.Many2one(
    "res.currency",
    default=lambda self: self.env.company.currency_id,
)
```

---

## 6. Access Error

```text
You are not allowed to access 'Academy Course' records.
```

- [ ] File `security/ir.model.access.csv` ada
- [ ] File sudah masuk `"data"` di manifest
- [ ] Header CSV persis: `id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink`
- [ ] External ID model benar: `model_academy_course`
- [ ] Group yang dipakai ada: `base.group_user`

---

## 7. Menu tidak muncul

- [ ] XML menu valid
- [ ] Action didefinisikan **sebelum** menu yang memakainya
- [ ] File XML sudah didaftarkan di manifest
- [ ] File menu ada di urutan **terakhir** dalam `"data"`
- [ ] Module sudah di-upgrade
- [ ] Sudah refresh browser (Cmd/Ctrl+Shift+R)

---

## 8. Seed data tidak terload

- [ ] File XML/CSV terdaftar di manifest
- [ ] External ID (`id`) ada dan unik
- [ ] Nama field persis sama dengan definisi model
- [ ] Nilai Selection memakai **key**, bukan label (`beginner`, bukan `Beginner`)

Data XML hanya di-load saat **install**. Dengan `noupdate="1"`, record tidak ditimpa lagi saat `-u`.

---

## 9. Constraint tidak aktif

```text
duplicate key value violates unique constraint
```

Ini **berhasil** — constraint bekerja.

Kalau constraint justru tidak menolak duplikat:

- [ ] `_sql_constraints` ditulis di level class, bukan di dalam method
- [ ] Module sudah di-upgrade
- [ ] Data lama yang sudah melanggar mencegah constraint terpasang — bersihkan dulu, cek log saat upgrade

Verifikasi langsung di database:

```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'academy_course'::regclass;
```

> Kalau menemukan contoh kode `_check_x = models.Constraint(...)`, itu **Odoo 19** dan tidak jalan di Odoo 18. Pakai `_sql_constraints`.

---

## 10. Perubahan tidak terlihat

| Yang diubah | Perlu |
|---|---|
| File Python | restart server |
| View / data XML | `-u academy_management` |
| Field baru di model | `-u academy_management` |
| CSV data | `-u academy_management` |

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management --dev all
```

---

## 11. Port 8069 sudah dipakai

```text
OSError: [Errno 48] Address already in use
```

Ada instance Odoo lain yang masih jalan. Matikan, atau ganti `http_port` di `odoo.conf`.

---

## Perintah Diagnostik Cepat

```bash
# Log lebih detail
./odoo/odoo-bin -c odoo.conf -d academy --log-level=debug

# ORM shell
./odoo/odoo-bin shell -c odoo.conf -d academy
```

```python
>>> env["academy.course"].search([])
>>> env["academy.course"].fields_get(["code"])
>>> env["academy.course"].search_count([])
>>> env.ref("academy_management.course_python_basics")
```
