# Day 5 — Integration, Deployment & Exercise

**Versi:** Odoo 18.0 · **Modul:** `academy_management`

## Tujuan Pembelajaran
- Memahami konsep integrasi Odoo lewat XML-RPC dan JSON-RPC.
- Melakukan autentikasi, mengirim request, membaca response.
- Mengakses model Odoo dari sistem eksternal.
- Menangani error dasar pada integrasi.
- Mengekspos Odoo sebagai REST API provider dengan contract yang rapi.
- Men-deploy hasil coding ke staging server.

## Yang Ditambahkan Hari Ini

```
academy_management/
├── controllers/
│   ├── __init__.py
│   └── api_controller.py     REST provider
└── data/
    └── academy_api_data.xml  API key + batch demo
```

---

## 16. Integration

### 16.1 Konsep Integrasi Odoo: XML-RPC dan JSON-RPC

Odoo mengekspos ORM-nya lewat RPC, jadi **sistem eksternal bisa memanggil method model Odoo seolah-olah kode internal.** Tidak perlu akses langsung ke PostgreSQL — dan memang jangan, karena akses DB langsung melewati semua validasi, constraint, dan access rights.

Tiga pola integrasi:

| Pola | Endpoint | Format | Kapan dipakai |
|------|----------|--------|---------------|
| **XML-RPC** | `/xmlrpc/2/common`, `/xmlrpc/2/object` | XML | Script eksternal sederhana. Library-nya ada di stdlib Python |
| **JSON-RPC** | `/web/dataset/call_kw` | JSON | Client yang JSON-nya lebih nyaman dari XML |
| **Custom REST** | route buatan sendiri, mis. `/academy/api/v1/courses` | JSON bebas | Aplikasi eksternal yang butuh contract sendiri |

Perbedaan yang menentukan pilihan:

- XML-RPC dan JSON-RPC **mengekspos ORM apa adanya.** Pemanggil harus tahu nama model, nama field, dan struktur domain Odoo. Kalau model Anda berubah, client ikut rusak.
- Custom REST **menyembunyikan itu.** Pemanggil cukup tahu kontrak API yang Anda definisikan. Perubahan internal Odoo tidak langsung merusak client.

> Untuk integrasi dengan pihak ketiga yang tidak mengenal Odoo, Custom REST hampir selalu pilihan yang lebih baik. RPC cocok untuk script internal dan tooling.

### 16.2 Authentication, Request/Response, Akses Model, Error Handling

#### A. XML-RPC — Alur Lengkap

**1. Authentication** — tukar kredensial jadi `uid`:

```python
import xmlrpc.client

url = "http://localhost:8069"
db  = "academy"
username = "admin"
password = "admin"          # lebih baik: API key

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")

# Cek versi server — tidak butuh auth, berguna untuk tes koneksi
print(common.version())

uid = common.authenticate(db, username, password, {})
if not uid:
    raise SystemExit("Autentikasi gagal — cek db, user, atau password.")
```

> `authenticate` mengembalikan `uid` (integer) kalau berhasil, dan **`False`** kalau gagal — bukan exception. Wajib dicek manual, kalau tidak error baru muncul jauh di bawah dan menyesatkan.

**2. Akses Model** — semua lewat `execute_kw`:

```python
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
# Pola: execute_kw(db, uid, password, model, method, args, kwargs)
```

**Read — `search_read`** (paling efisien, satu round-trip):
```python
courses = models.execute_kw(
    db, uid, password,
    "academy.course", "search_read",
    [[["active", "=", True]]],                              # args: domain
    {"fields": ["name", "code", "level"], "limit": 10},     # kwargs
)
for c in courses:
    print(c["code"], c["name"], c["level"])
```

**Create, Update, Delete:**
```python
new_id = models.execute_kw(
    db, uid, password, "academy.course", "create",
    [{"name": "Odoo Advanced", "code": "ODOO-201", "level": "advanced"}],
)

models.execute_kw(db, uid, password, "academy.course", "write",
                  [[new_id], {"duration_hours": 32}])

models.execute_kw(db, uid, password, "academy.course", "unlink", [[new_id]])
```

**Memanggil method custom** — method model sendiri juga bisa dipanggil:
```python
models.execute_kw(db, uid, password,
                  "academy.enrollment", "action_submit", [[enrollment_id]])
```

**Introspeksi field** — berguna saat tidak tahu struktur model:
```python
fields = models.execute_kw(
    db, uid, password, "academy.enrollment", "fields_get",
    [], {"attributes": ["string", "type", "required"]},
)
```

**Field relasi lewat RPC:**
```python
# Many2one dibaca sebagai [id, display_name]
enr = models.execute_kw(db, uid, password, "academy.enrollment", "read",
                        [[1]], {"fields": ["batch_id"]})
# → [{"id": 1, "batch_id": [3, "Python Basics - January"]}]

# Many2many/One2many ditulis pakai command
models.execute_kw(db, uid, password, "academy.course", "write",
                  [[course_id], {"tag_ids": [(6, 0, [1, 2])]}])
```

**3. Error Handling**

Error dari server datang sebagai `xmlrpc.client.Fault`:

```python
import xmlrpc.client

try:
    models.execute_kw(db, uid, password, "academy.enrollment", "create",
                      [{"batch_id": 1}])          # student_id hilang
except xmlrpc.client.Fault as e:
    # faultString berisi traceback panjang; pesan aslinya di baris terakhir
    print("Server menolak:", e.faultString.strip().splitlines()[-1])
except ConnectionError:
    print("Server tidak bisa dihubungi.")
```

Error yang paling sering ditemui:

| Pesan | Sebab | Perbaikan |
|---|---|---|
| `authenticate` return `False` | DB / user / password salah | Cek nama database, gunakan API key |
| `Access Denied` | Kredensial ditolak | Sama seperti di atas |
| `You are not allowed to access` | User tidak punya access right | Tambah baris di `ir.model.access.csv` |
| `Object ... doesn't exist` | Nama model salah ketik | Cek `_name` |
| `Invalid field ... on model` | Nama field salah | Pakai `fields_get` untuk introspeksi |
| `ValidationError` / `UserError` | Constraint bisnis menolak | Perbaiki datanya, bukan constraint-nya |
| `Expected singleton` | Method dipanggil untuk banyak record | Kirim satu ID saja |

> **Prinsip:** error dari constraint atau access right **bukan bug integrasi** — itu tanda sistem bekerja benar. Yang salah adalah datanya atau haknya.
>
> Access rights **tetap berlaku** lewat RPC. RPC bukan pintu belakang.

#### B. JSON-RPC

Endpoint dan payload berbeda, konsepnya sama:

```bash
curl -X POST http://localhost:8069/web/dataset/call_kw \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "model": "academy.course",
      "method": "search_read",
      "args": [[["active", "=", true]]],
      "kwargs": {"fields": ["name", "code", "level"]}
    },
    "id": 1
  }'
```

Response sukses berisi key `result`. Response gagal berisi key `error` — dan **HTTP status-nya tetap 200**:

```json
{"jsonrpc": "2.0", "id": 1, "error": {"code": 200, "message": "Odoo Server Error", "data": {...}}}
```

```python
resp = requests.post(url, json=payload).json()
if "error" in resp:
    raise RuntimeError(resp["error"]["data"]["message"])
data = resp["result"]
```

> Jangan mengandalkan status code untuk mendeteksi error di JSON-RPC. Selalu cek key `error` di body.

#### C. Odoo sebagai Consumer

Kebalikannya: Odoo yang memanggil sistem lain.

```python
import requests
from odoo import models
from odoo.exceptions import UserError


class AcademyCourse(models.Model):
    _inherit = "academy.course"

    def action_sync_from_lms(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param(
            "academy_management.lms_api_url"
        )
        if not base_url:
            raise UserError("URL LMS belum dikonfigurasi di System Parameters.")

        try:
            resp = requests.get(f"{base_url}/courses/{self.code}", timeout=10)
            resp.raise_for_status()
        except requests.Timeout:
            raise UserError("Server LMS tidak merespons (timeout).")
        except requests.RequestException as e:
            raise UserError(f"Gagal menghubungi LMS: {e}")

        data = resp.json()
        self.write({
            "duration_hours": data.get("duration", self.duration_hours),
            "level":          data.get("level", self.level),
        })
```

**Wajib diperhatikan:**
- Simpan URL & kredensial di `ir.config_parameter`, **jangan hardcode**.
- Selalu pasang `timeout`. Tanpa itu, worker Odoo bisa menggantung dan menghabiskan slot request untuk semua user.
- Ubah error jaringan jadi `UserError` supaya user melihat pesan yang bisa dipahami, bukan traceback.

#### D. Odoo sebagai REST Provider

**Response contract** — tetapkan bentuk response yang konsisten sejak awal:

```json
// sukses
{"success": true,  "data": {...}, "error": null}
// gagal
{"success": false, "data": null, "error": {"code": "COURSE_NOT_FOUND", "message": "..."}}
```

Client cuma perlu belajar satu bentuk. Ini yang membedakan API yang enak dipakai dari yang menyusahkan.

**Helper response** (`controllers/api_controller.py`):

```python
from odoo import http
from odoo.http import request
import json


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
```

**Controller:**

```python
class AcademyApiController(http.Controller):

    # -- security ---------------------------------------------------------
    def _check_api_key(self):
        """Bandingkan header X-API-Key dengan ir.config_parameter."""
        incoming = request.httprequest.headers.get("X-API-Key", "")
        stored = (
            request.env["ir.config_parameter"].sudo()
            .get_param("academy_management.api_key", "")
        )
        return bool(incoming and incoming == stored)

    # -- serializer -------------------------------------------------------
    def _course_to_dict(self, course):
        # Hanya expose field primitif yang aman.
        # description bertipe Html — tidak disertakan, tidak JSON-safe.
        return {
            "code":           course.code or "",
            "name":           course.name,
            "level":          course.level or "",
            "duration_hours": course.duration_hours,
        }

    # -- endpoints --------------------------------------------------------
    @http.route("/academy/api/v1/ping", type="http",
                auth="public", methods=["GET"])
    def ping(self, **kw):
        return _ok({"status": "ok", "version": "1.0"})

    @http.route("/academy/api/v1/courses", type="http",
                auth="public", methods=["GET"])
    def get_courses(self, **kw):
        courses = request.env["academy.course"].sudo().search([])
        return _ok([self._course_to_dict(c) for c in courses])

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

    @http.route("/academy/api/v1/enrollment-requests", type="http",
                auth="public", methods=["POST"], csrf=False)
    def create_enrollment_request(self, **kw):
        # 0. Gerbang keamanan — dicek PALING AWAL
        if not self._check_api_key():
            return _err("UNAUTHORIZED", "API key salah atau tidak ada.",
                        status=401)

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
            return _err("BATCH_NOT_FOUND", "Batch tidak ditemukan.",
                        status=404)

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

**Parameter `@http.route`:**

| Param | Arti |
|-------|------|
| `type` | `"http"` (kontrol penuh atas response) atau `"json"` (JSON-RPC, dibungkus `result`) |
| `auth` | `"user"` (wajib login), `"public"` (anonim), `"none"` |
| `methods` | `["GET"]`, `["POST"]`, dst |
| `csrf` | `False` untuk endpoint API non-form |

> **Kenapa `type="http"` dan bukan `type="json"`?** `type="json"` membungkus hasil Anda di dalam `{"result": ...}` dan selalu mengembalikan HTTP 200. Untuk REST yang benar — 404 saat tidak ketemu, 401 saat tidak berhak, 201 saat berhasil membuat — Anda butuh `type="http"` + `make_response`.

**Empat keputusan desain yang layak ditiru:**

1. **Cek API key paling awal**, sebelum parsing atau query apa pun. Jangan bocorkan informasi ke pemanggil yang belum lolos autentikasi.
2. **Serializer eksplisit.** Jangan kembalikan semua field. Field `Html` tidak JSON-safe, dan field internal tidak perlu dilihat dunia luar.
3. **Idempotensi.** Request yang sama dikirim dua kali tidak boleh membuat dua record. Kembalikan yang sudah ada dengan status 200, bukan 201.
4. **Jangan set `state` dari API.** Enrollment masuk sebagai `draft` dan tetap melewati approval normal. API adalah pintu masuk data, bukan jalan pintas melewati proses bisnis.

**API key disimpan di `ir.config_parameter`:**

```xml
<odoo noupdate="1">
    <record id="academy_api_key_param" model="ir.config_parameter">
        <field name="key">academy_management.api_key</field>
        <field name="value">academy-demo-key</field>
    </record>
</odoo>
```

Rotasi lewat **Settings → Technical → System Parameters**.

> **Batas pendekatan ini:** shared key = satu kunci untuk semua pemanggil, tanpa identitas per-user. Cukup untuk training dan integrasi internal sederhana. Untuk produksi, pakai `res.users.apikeys` bawaan Odoo (identitas per user, access rights ikut berlaku) atau OAuth2.

**`sudo()` di controller** dipakai di atas karena endpoint melayani sistem eksternal yang sudah lolos gerbang API key, bukan user Odoo. Konsekuensinya: access rights dan record rules **tidak berlaku**. Karena itu serializer harus eksplisit — `sudo()` berarti Anda sendiri yang bertanggung jawab menentukan data mana yang boleh keluar.

---

## 17. Deploy Code ke Sandbox

> **Bagian ini disampaikan trainer**, mengikuti workflow repository dan staging server Prasmul yang berlaku.

Cakupan:
- 17.1 Alur deployment code dari development ke sandbox sesuai workflow repository Prasmul
- 17.2 Validasi hasil deployment dan troubleshooting dasar

Yang perlu peserta siapkan sebelum sesi ini:

- Modul hasil kerja Day 1–5 bisa di-install **bersih dari database kosong**
- Tidak ada `__pycache__` atau `*.pyc` yang ikut ter-commit
- Akses repository aktif, perubahan sudah di-commit di branch sendiri

Uji install bersih — ini kondisi yang dialami server, bukan database Anda yang sudah menumpuk upgrade:

```bash
createdb academy_fresh
./odoo/odoo-bin -c odoo.conf -d academy_fresh -i academy_management --stop-after-init
```

Kalau gagal di sini, akan gagal juga di staging. Perbaiki dulu.

---

## 18. Exercise

Exercise mencakup empat komponen sesuai silabus: **model/table**, **existing report/printout**, **integration RPC**, dan **deployment ke sandbox**.

Brief lengkap dan kriteria penilaian: → [`labs/lab-d05.md`](labs/lab-d05.md)

---

## Referensi

- Dokumentasi Odoo 18: <https://www.odoo.com/documentation/18.0/developer.html>
- External API: <https://www.odoo.com/documentation/18.0/developer/reference/external_api.html>
- API key: Settings → Users → tab Account Security → New API Key
