# Day 5 Debugging Checklist

## 1. Perubahan controller tidak terasa

Penyebab kebingungan nomor satu di Day 5. Controller **tidak** ikut ter-reload dengan `-u academy_management`.

**Restart server** setiap kali mengubah file di `controllers/`.

---

## 2. Endpoint 404 Not Found

Cek rantai import:

```python
# __init__.py module
from . import models
from . import wizards
from . import controllers

# controllers/__init__.py
from . import api_controller
```

Lalu:

- [ ] Route path tidak typo
- [ ] Module ter-install, bukan cuma ada foldernya
- [ ] Server sudah di-restart
- [ ] HTTP method cocok — route `methods=["POST"]` menolak GET

Lihat route yang benar-benar terdaftar:

```python
>>> [r.rule for r in http.root.get_db_router(env.cr.dbname).iter_rules()
...  if "academy" in r.rule]
```

---

## 3. Response terbungkus `{"result": ...}`

Anda memakai `type="json"`. Itu JSON-RPC — selalu HTTP 200 dan membungkus hasil.

Untuk REST dengan status code sungguhan (201, 401, 404), pakai:

```python
@http.route("/path", type="http", auth="public", methods=["GET"])
def handler(self, **kw):
    return request.make_response(json.dumps({...}),
                                 headers=[("Content-Type", "application/json")],
                                 status=200)
```

---

## 4. `TypeError: Object of type date is not JSON serializable`

Tipe Odoo tidak otomatis JSON-safe.

| Tipe | Konversi |
|---|---|
| `Date` / `Datetime` | `str(val)` atau `val.isoformat()` |
| `Many2one` | `val.id` dan/atau `val.display_name` |
| `One2many` / `Many2many` | list of dict, bukan recordset |
| `Html` | jangan diekspos, atau bersihkan dulu |
| `Binary` | base64 string |

Selalu pakai serializer eksplisit, jangan `record.read()` mentah.

---

## 5. CSRF error di endpoint POST

Tambahkan `csrf=False` di route. Endpoint API bukan form, jadi proteksi CSRF tidak relevan.

---

## 6. Body request kosong padahal sudah dikirim

Untuk `type="http"`, body mentah dibaca dari:

```python
payload = json.loads(request.httprequest.data or b"{}")
```

Bukan dari `**kw` — `kw` berisi query string dan form data, bukan JSON body.

---

## 7. Status code selalu 200

Pastikan `status=` diteruskan sampai ke `make_response`:

```python
def _err(code, message, status=400):
    return request.make_response(..., status=status)

return _err("BATCH_NOT_FOUND", "...", status=404)   # jangan lupa status
```

---

## 8. API key selalu ditolak

- [ ] Nama header persis `X-API-Key`
- [ ] Nilai di `ir.config_parameter` sudah benar — cek di **Settings → Technical → System Parameters**
- [ ] `get_param` dipanggil dengan `.sudo()` (parameter tidak bisa dibaca user publik)
- [ ] Tidak ada spasi berlebih di nilai kunci

```python
>>> env["ir.config_parameter"].sudo().get_param("academy_management.api_key")
```

---

## 9. `authenticate` mengembalikan False

XML-RPC `authenticate` **tidak melempar exception** saat gagal.

```python
uid = common.authenticate(DB, USER, PWD, {})
if not uid:
    raise SystemExit("Autentikasi gagal — cek DB, user, password.")
```

Kalau tidak dicek, error baru muncul jauh di bawah dan menyesatkan.

---

## 10. `xmlrpc.client.Fault` — cara membaca

`faultString` berisi traceback panjang. Pesan aslinya di **baris terakhir**:

```python
except xmlrpc.client.Fault as e:
    print(e.faultString.strip().splitlines()[-1])
```

---

## 11. Error umum lewat RPC

| Pesan | Sebab | Perbaikan |
|---|---|---|
| `authenticate` → `False` | DB / user / password salah | Cek nama DB, coba API key |
| `Access Denied` | Kredensial ditolak | Sama seperti di atas |
| `You are not allowed to access` | User tidak punya access right | Tambah baris `ir.model.access.csv` |
| `Object ... doesn't exist` | Nama model salah | Cek `_name` |
| `Invalid field ... on model` | Nama field salah | Pakai `fields_get` |
| `ValidationError` / `UserError` | Constraint bisnis menolak | Perbaiki datanya |
| `Expected singleton` | Method dipanggil untuk banyak record | Kirim satu ID |

> Error constraint atau access right lewat RPC **bukan bug integrasi** — itu sistem bekerja benar. RPC bukan pintu belakang.

---

## 12. Many2many lewat RPC tidak tersimpan

```python
"tag_ids": [(6, 0, [1, 2, 3])]   # BENAR
"tag_ids": [1, 2, 3]             # SALAH
```

---

## 13. JSON-RPC gagal tapi HTTP status 200

Response JSON-RPC selalu 200, meski error:

```python
resp = requests.post(url, json=payload).json()
if "error" in resp:
    raise RuntimeError(resp["error"]["data"]["message"])
data = resp["result"]
```

Jangan mengandalkan status code untuk deteksi error di JSON-RPC.

---

## 14. `sudo()` dipakai untuk menambal error akses

Kalau endpoint error "not allowed", cari dulu **kenapa**. Menempel `sudo()` menghilangkan pesan errornya sekaligus membuka data yang seharusnya tertutup.

`sudo()` sah untuk integrasi sistem-ke-sistem yang autentikasinya sudah dijamin. Konsekuensinya: access rights tidak berlaku, jadi **serializer Anda** yang menentukan data mana yang boleh keluar.

Jangan pernah `sudo()` di endpoint `auth="public"` tanpa gerbang autentikasi.

---

## 15. Duplikat record dari request yang di-retry

Endpoint tulis harus idempoten — cek dulu apakah datanya sudah ada:

```python
existing = env["academy.enrollment"].sudo().search([...], limit=1)
if existing:
    return _ok({...}, status=200)     # 200, bukan 201
```

---

## 16. Install bersih gagal padahal di lokal jalan

Database Anda sudah menumpuk upgrade; server memulai dari nol.

```bash
createdb academy_fresh
./odoo/odoo-bin -c odoo.conf -d academy_fresh -i academy_management --stop-after-init
```

Penyebab paling sering:

- [ ] Urutan file di `"data"` manifest salah — menu/action dipakai sebelum didefinisikan
- [ ] Dependency kurang di `depends` (`mail`, `sale`)
- [ ] File data merujuk external ID yang belum ada
- [ ] Group didaftarkan setelah CSV yang memakainya

---

## 17. `__pycache__` ikut ter-commit

```
__pycache__/
*.pyc
```

Masukkan ke `.gitignore`.

---

## Perintah Diagnostik Cepat

```bash
# Lihat request RPC yang masuk
./odoo/odoo-bin -c odoo.conf -d academy --log-level=debug_rpc

# Uji verbose — lihat header & status code
curl -v http://localhost:8069/academy/api/v1/ping

# Formatkan output JSON
curl -s http://localhost:8069/academy/api/v1/courses | python3 -m json.tool
```

```bash
./odoo/odoo-bin shell -c odoo.conf -d academy
```

```python
# Cek API key tersimpan
>>> env["ir.config_parameter"].sudo().get_param("academy_management.api_key")

# Introspeksi field sebelum kirim lewat RPC
>>> env["academy.enrollment"].fields_get([], ["string", "type", "required"])

# Cek batch punya code (dibutuhkan endpoint POST)
>>> env["academy.batch"].search([("code", "!=", False)]).mapped("code")

# Cek enrollment yang dibuat lewat API
>>> env["academy.enrollment"].search([], order="id desc", limit=5).read(
...     ["name", "state", "student_id"])
```
