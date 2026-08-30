# Odoo Technical Training — Arkana Academy × Prasetiya Mulya

Materi hands-on training Odoo Technical Development.

**Versi Odoo: 18.0** · 5 hari · modul studi kasus: `academy_management`

---

## Cara Pakai Repo Ini

Tiap hari punya tiga file:

| File | Isi |
|---|---|
| `dNN-*.md` | Materi — konsep dan penjelasan |
| `labs/lab-dNN.md` | Handout lab — langkah-langkah yang dikerjakan di kelas |
| `labs/debug-dNN.md` | Debugging checklist — buka ini saat error |

Alurnya: baca materi → kerjakan lab → kalau macet, buka debug checklist.

---

## Jadwal Materi

| Hari | Topik | Materi | Lab | Debug |
|---|---|---|---|---|
| 1 | Fondasi & Struktur Modul | [d01](d01-fondasi-dan-struktur-modul.md) | [lab](labs/lab-d01.md) | [debug](labs/debug-d01.md) |
| 2 | View, Relasi, Inheritance, Computed | [d02](d02-view-relasi-inheritance-computed.md) | [lab](labs/lab-d02.md) | [debug](labs/debug-d02.md) |
| 3 | Constraint, Advanced View, Security | [d03](d03-constraint-advanced-view-security.md) | [lab](labs/lab-d03.md) | [debug](labs/debug-d03.md) |
| 4 | Wizard & Reporting | [d04](d04-wizard-dan-reporting.md) | [lab](labs/lab-d04.md) | [debug](labs/debug-d04.md) |
| 5 | Integrasi, Deployment, Exercise | [d05](d05-integrasi-deployment-exercise.md) | [lab](labs/lab-d05.md) | [debug](labs/debug-d05.md) |

---

## Studi Kasus

Kita membangun **satu modul** `academy_management` yang tumbuh setiap hari — bukan banyak modul terpisah.

| Hari | Yang ditambahkan |
|---|---|
| 1 | `academy.course`, `academy.student`, menu, seed data |
| 2 | `academy.batch`, `academy.enrollment`, `academy.course.tag`, relasi, views, computed |
| 3 | Constraint, workflow approval berjenjang, security |
| 4 | Wizard, report PDF, export Excel, inherit report bawaan |
| 5 | REST API provider, integrasi RPC |

---

## Source Checkpoints

`labs/source-checkpoints/` berisi **26 snapshot kode** di setiap titik lab.

Gunanya satu: kalau Anda tertinggal atau kode rusak, langsung menyusul tanpa menunggu kelas.

```bash
# dari folder development/
rm -rf custom-addons/academy_management
cp -R <repo>/labs/source-checkpoints/d02/checkpoint_b_relations/academy_management \
      custom-addons/

./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Membandingkan dengan kode Anda sendiri saat error tapi tidak tahu di mana:

```bash
diff -ru custom-addons/academy_management \
         <repo>/labs/source-checkpoints/d02/checkpoint_b_relations/academy_management
```

Detail lengkap: [`labs/source-checkpoints/README.md`](labs/source-checkpoints/README.md)

> **Checkpoint adalah jaring pengaman, bukan jalan pintas.** Ketik sendiri dulu. Menyalin tanpa mengetik membuat Anda lulus lab tapi tidak bisa apa-apa saat kerja nyata.

---

## Catatan Versi

Materi ini untuk **Odoo 18**. Dua API berikut ada di Odoo 19 tapi **tidak jalan di Odoo 18** — kalau menemukannya di contoh kode dari internet, jangan disalin mentah:

| Odoo 19 | Odoo 18 (dipakai di sini) |
|---|---|
| `_check_x = models.Constraint(sql, msg)` | `_sql_constraints = [(nama, sql, msg)]` |
| `res.groups.privilege` + `privilege_id` | `ir.module.category` + `category_id` |

Dibahas di [materi Day 1](d01-fondasi-dan-struktur-modul.md), bagian versioning.

---

## Referensi

- Dokumentasi Odoo 18: <https://www.odoo.com/documentation/18.0/developer.html>
- External API: <https://www.odoo.com/documentation/18.0/developer/reference/external_api.html>

---

Arkana Academy — [arkana.co.id](https://arkana.co.id)
