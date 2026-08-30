# Day 5 Hands-on Lab — Integration, Deployment & Exercise

## Objective

Di akhir lab Day 5, module `academy_management` Anda punya:

- REST API provider dengan response contract yang konsisten
- endpoint dengan HTTP status code yang benar (200, 201, 401, 404)
- gerbang autentikasi API key
- script client XML-RPC dengan error handling

---

# Prerequisite

- Lab Day 4 selesai — wizard dan report sudah jalan
- Ada data: minimal 2 course, 1 batch dengan `code` terisi, beberapa student

Kalau tertinggal:

```bash
rm -rf custom-addons/academy_management
cp -R materi/labs/source-checkpoints/d04/checkpoint_c_excel_export/academy_management \
      custom-addons/
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Checkpoint Day 5: `a_controller_basics` → `b_get_courses` → `c_get_course_detail` → `d_post_enrollment_request` → `e_api_key_boundary` → `final_day5`

> **Ingat sepanjang hari ini:** perubahan file controller **tidak** ikut ter-reload dengan `-u`. Setiap kali mengubah `controllers/`, **restart server**.

---

# Checkpoint A — Controller Hidup

## Goal

Endpoint pertama merespons request.

## Step 1 — Struktur Folder

```text
academy_management/
└── controllers/
    ├── __init__.py
    └── api_controller.py
```

`controllers/__init__.py`:

```python
from . import api_controller
```

`__init__.py` module:

```python
from . import models
from . import wizards
from . import controllers
```

## Step 2 — Response Contract

Tetapkan bentuk response yang sama untuk semua endpoint, sejak awal.

`controllers/api_controller.py`:

```python
import json

from odoo import http
from odoo.http import request


def _ok(data, status=200):
    return request.make_response(
        json.dumps({"success": True, "data": data, "error": None}),
        headers=[("Content-Type", "application/json")],
        status=status,
    )


def _err(code, message, status=400):
    return request.make_response(
        json.dumps({
            "success": False,
            "data": None,
            "error": {"code": code, "message": message},
        }),
        headers=[("Content-Type", "application/json")],
        status=status,
    )


class AcademyApiController(http.Controller):

    @http.route("/academy/api/v1/ping", type="http",
                auth="public", methods=["GET"])
    def ping(self, **kw):
        return _ok({"status": "ok", "version": "1.0"})
```

## Step 3 — Restart Server

```bash
./odoo/odoo-bin -c odoo.conf -d academy -u academy_management
```

Lalu **hentikan dan jalankan ulang** — controller butuh restart penuh.

## Step 4 — Uji

```bash
curl -i http://localhost:8069/academy/api/v1/ping
```

Expected:

```
HTTP/1.1 200 OK
Content-Type: application/json

{"success": true, "data": {"status": "ok", "version": "1.0"}, "error": null}
```

## Step 5 — Pahami Kenapa `type="http"`

Ubah sementara jadi `type="json"`, restart, panggil lagi. Responsnya sekarang terbungkus:

```json
{"jsonrpc": "2.0", "id": null, "result": {...}}
```

dan status code selalu 200. Untuk REST yang benar — 404, 401, 201 — Anda butuh `type="http"` + `make_response`. Kembalikan ke `type="http"`.

## Checkpoint A selesai bila:

- [ ] `/academy/api/v1/ping` mengembalikan JSON
- [ ] HTTP status 200, Content-Type `application/json`
- [ ] Anda paham beda `type="http"` dan `type="json"`
- [ ] Anda tahu controller butuh restart, bukan `-u`

> Bandingkan: `source-checkpoints/d05/checkpoint_a_controller_basics`

---

# Checkpoint B — GET Courses + Serializer

## Goal

Daftar course keluar sebagai JSON, dengan field yang dipilih sengaja.

## Step 1 — Serializer

Tambahkan method di dalam class controller:

```python
    def _course_to_dict(self, course):
        # Hanya expose field primitif yang aman.
        # description bertipe Html — tidak disertakan, tidak JSON-safe.
        return {
            "code":           course.code or "",
            "name":           course.name,
            "level":          course.level or "",
            "duration_hours": course.duration_hours,
        }
```

## Step 2 — Endpoint

```python
    @http.route("/academy/api/v1/courses", type="http",
                auth="public", methods=["GET"])
    def get_courses(self, **kw):
        courses = request.env["academy.course"].sudo().search([])
        return _ok([self._course_to_dict(c) for c in courses])
```

## Step 3 — Restart dan Uji

```bash
curl -s http://localhost:8069/academy/api/v1/courses | python3 -m json.tool
```

## Step 4 — Buktikan Kenapa Serializer Perlu

Coba kembalikan record mentah:

```python
        return _ok(courses.read())
```

Restart, panggil lagi. Gagal — `TypeError: Object of type date is not JSON serializable`, atau field `Html` ikut keluar. Kembalikan ke serializer.

Dua alasan serializer penting:
- Tipe Odoo (`Date`, `Html`, `Many2one`) tidak otomatis JSON-safe
- Field internal tidak perlu dilihat dunia luar

## Checkpoint B selesai bila:

- [ ] `/academy/api/v1/courses` mengembalikan array course
- [ ] Hanya field yang Anda pilih yang keluar
- [ ] Anda sudah melihat sendiri kenapa `read()` mentah gagal

> Bandingkan: `source-checkpoints/d05/checkpoint_b_get_courses`

---

# Checkpoint C — GET Detail + 404

## Goal

Endpoint mengembalikan 404 saat data tidak ada — bukan 200 dengan isi kosong.

## Step 1 — Endpoint dengan Path Parameter

```python
    @http.route("/academy/api/v1/courses/<string:code>", type="http",
                auth="public", methods=["GET"])
    def get_course(self, code, **kw):
        course = request.env["academy.course"].sudo().search(
            [("code", "=", code)], limit=1
        )
        if not course:
            return _err("COURSE_NOT_FOUND",
                        f"Course dengan kode '{code}' tidak ditemukan.",
                        status=404)
        return _ok(self._course_to_dict(course))
```

`<string:code>` di route menjadi argumen `code` di method.

## Step 2 — Restart dan Uji Kedua Jalur

```bash
# ada
curl -i http://localhost:8069/academy/api/v1/courses/PY-101

# tidak ada
curl -i http://localhost:8069/academy/api/v1/courses/TIDAK-ADA
```

Expected: yang pertama `200`, yang kedua `404` dengan body berisi `error.code`.

## Step 3 — Kenapa Status Code Penting

Client yang baik memutuskan berdasarkan status code. Kalau semua request mengembalikan 200, client harus mengurai isi body untuk tahu berhasil atau tidak — dan itu sumber bug.

## Checkpoint C selesai bila:

- [ ] Course yang ada → 200 dengan datanya
- [ ] Course yang tidak ada → **404**, bukan 200
- [ ] Body error punya `code` dan `message` yang jelas

> Bandingkan: `source-checkpoints/d05/checkpoint_c_get_course_detail`

---

# Checkpoint D — POST Enrollment Request

## Goal

Sistem eksternal bisa mendaftarkan student, dengan validasi berlapis dan idempotensi.

## Step 1 — Endpoint

```python
    @http.route("/academy/api/v1/enrollment-requests", type="http",
                auth="public", methods=["POST"], csrf=False)
    def create_enrollment_request(self, **kw):
        # 1. Parse body
        try:
            payload = json.loads(request.httprequest.data or b"{}")
        except (json.JSONDecodeError, ValueError):
            return _err("INVALID_JSON", "Body harus JSON valid.", status=400)

        # 2. Validasi field wajib
        required = ["student_name", "student_email", "batch_code"]
        missing = [f for f in required if not (payload.get(f) or "").strip()]
        if missing:
            return _err("MISSING_FIELDS",
                        "Field wajib belum diisi: %s." % ", ".join(missing),
                        status=400)

        env = request.env

        # 3. Cari batch — JANGAN pernah auto-create
        batch = env["academy.batch"].sudo().search(
            [("code", "=", payload["batch_code"].strip())], limit=1
        )
        if not batch:
            return _err("BATCH_NOT_FOUND", "Batch tidak ditemukan.", status=404)

        # 4. Cari atau buat student berdasarkan email
        email = payload["student_email"].strip()
        student = env["academy.student"].sudo().search(
            [("email", "=", email)], limit=1
        )
        if not student:
            student = env["academy.student"].sudo().create({
                "name":  payload["student_name"].strip(),
                "email": email,
            })

        # 5. Idempotensi — request yang sama tidak membuat duplikat
        existing = env["academy.enrollment"].sudo().search([
            ("batch_id", "=", batch.id),
            ("student_id", "=", student.id),
        ], limit=1)
        if existing:
            return _ok({
                "enrollment_id": existing.id,
                "state":         existing.state,
                "note":          "Enrollment sudah ada.",
            }, status=200)

        # 6. Buat baru — state dibiarkan default "draft"
        enrollment = env["academy.enrollment"].sudo().create({
            "batch_id":   batch.id,
            "student_id": student.id,
            "notes":      (payload.get("notes") or "").strip(),
        })
        return _ok({
            "enrollment_id": enrollment.id,
            "state":         enrollment.state,
        }, status=201)
```

## Step 2 — Siapkan Batch dengan `code`

Di UI, isi field **Batch Code** pada satu batch, misal `PY-101-JAN`.

## Step 3 — Restart dan Uji Semua Jalur

```bash
URL=http://localhost:8069/academy/api/v1/enrollment-requests

# 1. Berhasil — harus 201
curl -i -X POST $URL -H "Content-Type: application/json" \
  -d '{"student_name":"Budi","student_email":"budi@test.com","batch_code":"PY-101-JAN"}'

# 2. Kirim ulang persis sama — harus 200, bukan 201, tanpa duplikat
curl -i -X POST $URL -H "Content-Type: application/json" \
  -d '{"student_name":"Budi","student_email":"budi@test.com","batch_code":"PY-101-JAN"}'

# 3. Field kurang — harus 400
curl -i -X POST $URL -H "Content-Type: application/json" \
  -d '{"student_name":"Budi"}'

# 4. Batch tidak ada — harus 404
curl -i -X POST $URL -H "Content-Type: application/json" \
  -d '{"student_name":"Budi","student_email":"budi@test.com","batch_code":"NGAWUR"}'

# 5. JSON rusak — harus 400
curl -i -X POST $URL -H "Content-Type: application/json" -d '{bukan json}'
```

Verifikasi di UI: hanya **satu** enrollment Budi yang terbuat, statusnya `draft`.

## Step 4 — Perhatikan Dua Keputusan Desain

**Idempotensi.** Request yang sama dikirim dua kali tidak membuat dua record. Ini penting karena client bisa retry saat jaringan putus.

**State tetap `draft`.** API tidak menyetel `state` ke `confirmed`. Enrollment dari API tetap melewati approval normal — API adalah pintu masuk data, bukan jalan pintas melewati proses bisnis.

Coba langgar sebentar: tambahkan `"state": "confirmed"` di `create()`, restart, kirim request. Enrollment langsung confirmed tanpa approval siapa pun. Kembalikan seperti semula.

## Checkpoint D selesai bila:

- [ ] Request valid → 201, enrollment terbuat
- [ ] Request sama dikirim ulang → 200, tidak ada duplikat
- [ ] Field kurang → 400 dengan daftar field yang hilang
- [ ] Batch tidak ada → 404
- [ ] JSON rusak → 400
- [ ] Enrollment dari API berstatus `draft`

> Bandingkan: `source-checkpoints/d05/checkpoint_d_post_enrollment_request`

---

# Checkpoint E — API Key Boundary

## Goal

Endpoint tulis hanya bisa dipanggil pemegang kunci.

## Step 1 — Simpan API Key

`data/academy_api_data.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="academy_api_key_param" model="ir.config_parameter">
        <field name="key">academy_management.api_key</field>
        <field name="value">academy-demo-key</field>
    </record>
</odoo>
```

Daftarkan di manifest.

> `noupdate="1"` — kunci tidak ditimpa kembali ke nilai demo setiap upgrade.

## Step 2 — Gerbang Pengecekan

```python
    def _check_api_key(self):
        """Bandingkan header X-API-Key dengan ir.config_parameter."""
        incoming = request.httprequest.headers.get("X-API-Key", "")
        stored = (
            request.env["ir.config_parameter"].sudo()
            .get_param("academy_management.api_key", "")
        )
        return bool(incoming and incoming == stored)
```

## Step 3 — Pasang di Endpoint Tulis

Tambahkan sebagai **baris pertama** di `create_enrollment_request`, sebelum parsing:

```python
        # 0. Gerbang keamanan — dicek PALING AWAL
        if not self._check_api_key():
            return _err("UNAUTHORIZED", "API key salah atau tidak ada.",
                        status=401)
```

> Cek kunci **sebelum** parsing atau query apa pun. Jangan bocorkan informasi apa pun ke pemanggil yang belum lolos autentikasi — termasuk pesan error yang membocorkan struktur data.

## Step 4 — Restart dan Uji

```bash
URL=http://localhost:8069/academy/api/v1/enrollment-requests
BODY='{"student_name":"Siti","student_email":"siti@test.com","batch_code":"PY-101-JAN"}'

# Tanpa key — harus 401
curl -i -X POST $URL -H "Content-Type: application/json" -d "$BODY"

# Key salah — harus 401
curl -i -X POST $URL -H "Content-Type: application/json" \
  -H "X-API-Key: salah" -d "$BODY"

# Key benar — harus 201
curl -i -X POST $URL -H "Content-Type: application/json" \
  -H "X-API-Key: academy-demo-key" -d "$BODY"

# GET tetap terbuka
curl -i http://localhost:8069/academy/api/v1/courses
```

## Step 5 — Rotasi Kunci

**Settings → Technical → System Parameters** → cari `academy_management.api_key` → ubah nilainya. Uji lagi dengan kunci lama → 401.

## Step 6 — Pahami Batasnya

Pendekatan ini **shared key**: satu kunci untuk semua pemanggil, tanpa identitas per-user. Konsekuensinya:

- Tidak tahu siapa yang memanggil
- Tidak bisa mencabut akses satu pihak saja
- `sudo()` melewati semua access rights — Anda sendiri yang bertanggung jawab lewat serializer

Cukup untuk training dan integrasi internal sederhana. Untuk produksi: `res.users.apikeys` bawaan Odoo (identitas per user, access rights ikut berlaku) atau OAuth2.

## Checkpoint E selesai bila:

- [ ] POST tanpa key → 401
- [ ] POST dengan key salah → 401
- [ ] POST dengan key benar → 201
- [ ] GET tetap bisa diakses tanpa key
- [ ] Rotasi kunci lewat System Parameters bekerja
- [ ] Anda bisa menjelaskan batas pendekatan shared key

> Bandingkan: `source-checkpoints/d05/checkpoint_e_api_key_boundary`

---

# Checkpoint F — Client XML-RPC

## Goal

Script Python eksternal bicara ke Odoo, lengkap dengan penanganan error.

## Step 1 — Script

Buat `test_rpc.py` di **luar** folder Odoo:

```python
import xmlrpc.client

URL = "http://localhost:8069"
DB  = "academy"
USERNAME = "admin"
PASSWORD = "admin"

# --- 1. Cek koneksi (tanpa auth) ---
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
print("Server version:", common.version()["server_version"])

# --- 2. Authenticate ---
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
if not uid:
    raise SystemExit("Autentikasi gagal — cek DB, user, atau password.")
print("Authenticated, uid =", uid)

models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

# --- 3. Read ---
courses = models.execute_kw(
    DB, uid, PASSWORD,
    "academy.course", "search_read",
    [[["active", "=", True]]],
    {"fields": ["name", "code", "level", "duration_hours"], "limit": 5},
)
for c in courses:
    print(f"  {c['code'] or '-':10} {c['name']:30} {c['level']}")

# --- 4. Create ---
new_id = models.execute_kw(
    DB, uid, PASSWORD, "academy.course", "create",
    [{"name": "RPC Test Course", "code": "RPC-001", "level": "advanced"}],
)
print("Created course id:", new_id)

# --- 5. Error: langgar SQL constraint (code duplikat) ---
try:
    models.execute_kw(
        DB, uid, PASSWORD, "academy.course", "create",
        [{"name": "Duplikat", "code": "RPC-001"}],
    )
    print("BUG: seharusnya ditolak")
except xmlrpc.client.Fault as e:
    print("Constraint bekerja:", e.faultString.strip().splitlines()[-1])

# --- 6. Error: model salah ---
try:
    models.execute_kw(DB, uid, PASSWORD, "tidak.ada", "search", [[]])
except xmlrpc.client.Fault:
    print("Model tidak ada — tertangkap dengan benar.")

# --- 7. Error: field salah ---
try:
    models.execute_kw(DB, uid, PASSWORD, "academy.course", "search_read",
                      [[]], {"fields": ["field_ngawur"]})
except xmlrpc.client.Fault:
    print("Field tidak ada — tertangkap dengan benar.")

# --- 8. Introspeksi ---
fields = models.execute_kw(
    DB, uid, PASSWORD, "academy.course", "fields_get",
    [], {"attributes": ["string", "type", "required"]},
)
print("Jumlah field academy.course:", len(fields))

# --- 9. Cleanup ---
models.execute_kw(DB, uid, PASSWORD, "academy.course", "unlink", [[new_id]])
print("Cleanup selesai.")
```

## Step 2 — Jalankan

```bash
python3 test_rpc.py
```

## Step 3 — Uji Kegagalan Auth

Ubah `PASSWORD` jadi nilai salah, jalankan lagi. Harus berhenti dengan pesan "Autentikasi gagal", bukan traceback panjang.

> `authenticate` mengembalikan `False` saat gagal, **bukan** exception. Itu sebabnya harus dicek manual.

## Step 4 — Buktikan Access Rights Berlaku Lewat RPC

Ganti `USERNAME`/`PASSWORD` jadi `user.test` (Academy User dari Day 3), lalu tambahkan:

```python
try:
    models.execute_kw(DB, uid, PASSWORD, "academy.course", "create",
                      [{"name": "Harusnya Ditolak", "code": "X-001"}])
    print("BUG: seharusnya ditolak")
except xmlrpc.client.Fault as e:
    print("Access right bekerja:", e.faultString.strip().splitlines()[-1])
```

Academy User hanya punya `perm_read` untuk course, jadi create ditolak.

> RPC **bukan pintu belakang**. Access rights dan record rules tetap berlaku penuh.

## Checkpoint F selesai bila:

- [ ] Script authenticate dan mendapat `uid`
- [ ] `search_read` mengembalikan daftar course
- [ ] `create` membuat record baru
- [ ] Pelanggaran constraint tertangkap sebagai `xmlrpc.client.Fault`
- [ ] Model dan field salah tertangkap
- [ ] Password salah ditangani dengan pesan jelas
- [ ] Access rights terbukti berlaku lewat RPC
- [ ] Cleanup berjalan, tidak ada sampah data

---

# 17. Deploy ke Sandbox

Dipandu trainer, mengikuti workflow repository dan staging server yang berlaku.

## Uji Install Bersih Dulu

Database Anda sudah menumpuk upgrade; server memulai dari nol.

```bash
createdb academy_fresh
./odoo/odoo-bin -c odoo.conf -d academy_fresh -i academy_management --stop-after-init
```

Kalau gagal di sini, akan gagal juga di staging.

Penyebab paling sering:
- Urutan file di `"data"` manifest salah — action dipakai sebelum didefinisikan
- Dependency kurang di `depends` (`mail`, `sale`)
- File data merujuk external ID yang belum ada

## Checklist Sebelum Deploy

- [ ] Install bersih dari database kosong berhasil
- [ ] Tidak ada `__pycache__` atau `*.pyc` ter-commit
- [ ] Akses repository aktif
- [ ] Perubahan di-commit di branch sendiri dengan konvensi penamaan yang benar

---

# 18. Exercise — Sistem Peminjaman Peralatan Lab

Dikerjakan mandiri. Domain berbeda, pola sama.

**Konteks:** Akademi punya peralatan lab yang bisa dipinjam. Setiap peminjaman dicatat, ada batas waktu pengembalian, keterlambatan kena denda.

Referensi: [`d01`](../d01-fondasi-dan-struktur-modul.md) s/d [`d05`](../d05-integrasi-deployment-exercise.md)

Bangun **satu modul** `academy_lab` — bukan banyak modul, mengikuti pola training.

## Model (Day 1–2)

**`lab.equipment`:**
- `name` (Char, required), `code` (Char, unique)
- `category` (Selection: `tools`/`measurement`/`safety`/`electronic`)
- `daily_rate` (Monetary — denda per hari, jangan lupa `currency_id`)
- `status` (Selection: `available`/`borrowed`, default `available`, readonly)
- `active` (Boolean)

**`lab.borrower`:**
- `partner_id` (Many2one `res.partner`, required)
- `name` (related `partner_id.name`, store)
- `employee_code` (Char), `department` (Char), `active`

**`lab.borrowing`:**
- `name` (Char, default "New")
- `borrower_id` (Many2one, required)
- `equipment_ids` (Many2many)
- `borrow_date` (Date, default today)
- `return_date_plan` (Date, required), `return_date_actual` (Date)
- `overdue_days` (Integer, computed, minimal 0)
- `fine_amount` (Monetary, computed `overdue_days × sum(daily_rate)`, `store=True`)
- `state` (Selection: `draft`/`submitted`/`approved`/`borrowed`/`returned`/`rejected`)
- `notes` (Text)

Views lengkap (list, form, search) untuk ketiganya. Extend `res.partner` dengan `is_borrower`.

## Constraint & Security (Day 3)

- SQL constraint: `code` equipment unik
- Python constraint: `return_date_plan` harus setelah `borrow_date`
- Python constraint: equipment yang sedang `borrowed` tidak boleh dipinjam lagi
- Workflow approval: `draft` → `submitted` → `approved` → `borrowed` → `returned`
- Chatter (`mail.thread`) dengan `tracking=True` pada `state`
- State → `borrowed`: equipment jadi `borrowed`. State → `returned`: jadi `available`
- Group `Lab User` (tanpa delete) dan `Lab Manager` (full CRUD)
- Record rule: Lab User hanya melihat peminjaman departemennya sendiri
- Advanced list (optional column + inline button), calendar (`borrow_date` → `return_date_plan`), advanced search (`filter_domain` nama atau kode karyawan)

## Wizard & Report (Day 4)

- Wizard tolak peminjaman dengan alasan wajib (logika di model, bukan wizard)
- Wizard export Excel dengan filter tanggal & departemen
- Report PDF "Bukti Peminjaman": data peminjam, tabel equipment, tanggal, denda kalau ada. Pakai `web.external_layout` + paper format sendiri
- **Existing report/printout:** pilih satu report bawaan Odoo, inherit — tambah satu baris informasi dan ubah satu atribut dengan `position="attributes"`

## API (Day 5)

Tiga endpoint dengan response contract yang sama:

- `GET /lab/api/v1/equipment` — daftar peralatan & ketersediaan
- `GET /lab/api/v1/borrowings/<string:name>` — detail peminjaman, **404** kalau tidak ada
- `POST /lab/api/v1/borrow-requests` — buat peminjaman, gerbang API key, **201** saat berhasil, idempoten

Ditambah script client XML-RPC dengan error handling.

## Deployment

Deploy ke staging sesuai workflow yang dijelaskan trainer.

## Acceptance Criteria

**Model & views:**
- [ ] Tiga model ter-install, views lengkap
- [ ] `overdue_days` = 0 kalau tepat waktu, positif kalau terlambat
- [ ] `fine_amount` = `overdue_days × sum(daily_rate)`, bisa di-`sum` di list
- [ ] Form `res.partner` menampilkan `is_borrower`

**Constraint & security:**
- [ ] Code equipment duplikat ditolak
- [ ] Tanggal terbalik ditolak
- [ ] Equipment yang sedang dipinjam tidak bisa dipinjam lagi
- [ ] State `borrowed` mengubah status equipment, `returned` mengembalikannya
- [ ] Lab User tidak bisa delete, hanya lihat departemen sendiri
- [ ] Diuji dengan login user asli, bukan admin

**Wizard & report:**
- [ ] Wizard tolak butuh alasan, logikanya di model
- [ ] Excel ter-download dengan nama benar
- [ ] PDF Bukti Peminjaman pakai kop surat
- [ ] Report bawaan berubah sesuai inherit
- [ ] Dokumen lain tidak terpengaruh
- [ ] Tidak ada file `odoo/addons/` yang diedit

**API:**
- [ ] Ketiga endpoint berfungsi dengan response contract sama
- [ ] Detail tidak ketemu → 404
- [ ] POST tanpa API key → 401
- [ ] POST berhasil → 201, request ulang → 200 tanpa duplikat
- [ ] Script XML-RPC jalan dengan error handling

**Deployment:**
- [ ] Install bersih dari database kosong berhasil
- [ ] Branch mengikuti konvensi penamaan
- [ ] Ter-install di staging dan divalidasi di UI

## Tips

- Kerjakan bertahap seperti lab: model dulu, pastikan install bersih, baru lanjut
- `status` equipment jangan diupdate manual dari UI — ubah lewat method transisi state
- Bingung? Lihat pola yang sama di `academy_management`
- Restart server tiap kali mengubah controller

---

# Common Mistakes

## 1. Perubahan controller tidak terasa

Controller tidak ikut ter-reload dengan `-u`. **Restart server.**

## 2. Endpoint 404

Cek `controllers/__init__.py` sudah meng-import file, dan `__init__.py` module sudah meng-import `controllers`.

## 3. `authenticate` return False, bukan exception

Wajib dicek manual.

## 4. Response terbungkus `result`

Anda memakai `type="json"`. Untuk kontrol status code, pakai `type="http"`.

## 5. `TypeError: Object of type date is not JSON serializable`

Tipe Odoo tidak otomatis JSON-safe. Pakai serializer eksplisit, konversi `Date` dengan `str()` atau `.isoformat()`.

## 6. CSRF error di endpoint POST

Tambahkan `csrf=False` di route.

## 7. `sudo()` dipakai untuk menutupi error akses

Kalau endpoint error "not allowed", cari dulu penyebabnya. `sudo()` menghilangkan pesan errornya sekaligus membuka data yang seharusnya tertutup.

---

# Final Checklist Day 5

| Item | Status |
|---|---|
| `/ping` mengembalikan JSON | ☐ |
| Paham beda `type="http"` vs `type="json"` | ☐ |
| Tahu controller butuh restart, bukan `-u` | ☐ |
| `/courses` mengembalikan array dengan serializer | ☐ |
| Sudah melihat kenapa `read()` mentah gagal | ☐ |
| Detail course tidak ada → 404 | ☐ |
| POST valid → 201 | ☐ |
| POST ulang → 200, tanpa duplikat | ☐ |
| Field kurang → 400 | ☐ |
| Batch tidak ada → 404 | ☐ |
| Enrollment dari API berstatus `draft` | ☐ |
| POST tanpa API key → 401 | ☐ |
| Rotasi kunci lewat System Parameters bekerja | ☐ |
| Paham batas pendekatan shared key | ☐ |
| Script XML-RPC authenticate & create berhasil | ☐ |
| `xmlrpc.client.Fault` tertangkap | ☐ |
| Access rights terbukti berlaku lewat RPC | ☐ |
| Install bersih dari DB kosong berhasil | ☐ |
| Brief exercise sudah dipahami | ☐ |

---

Troubleshooting cepat: → [`debug-d05.md`](debug-d05.md)
