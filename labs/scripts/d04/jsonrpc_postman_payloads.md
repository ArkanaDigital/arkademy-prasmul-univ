# JSON-RPC via Postman — Academy Management

Referensi ini mencakup model Day 4: academy.course, academy.course.tag,
academy.student, academy.batch, dan academy.enrollment.

Base URL: http://localhost:8069
Header: Content-Type: application/json

Aktifkan cookie jar Postman. Cookie session_id dari Authenticate harus ikut ke
request berikutnya. Ganti placeholder seperti COURSE_ID atau TAG_ID dengan angka ID
dari database. JSON-RPC menjalankan method Odoo, bukan REST resource.

## 1. Authenticate

POST /web/session/authenticate

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "db": "v18_prasmul_dev",
    "login": "admin",
    "password": "admin"
  }
}
~~~

Pastikan result.uid tidak null. Sesuaikan database dan kredensial lokal bila berbeda.

## 2. Pola umum request

Contoh membaca course:

POST /web/dataset/call_kw/academy.course/search_read

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.course",
    "method": "search_read",
    "args": [[], ["name", "code", "level", "tag_ids"]],
    "kwargs": {"limit": 10}
  }
}
~~~

Untuk create, write, atau method workflow, ganti bagian akhir URL dan nilai method
dengan nama method yang sama. Hak akses dan record rule user login tetap berlaku.

## 3. Siapkan ID untuk relasi

Field Many2one dan Many2many memakai ID integer, bukan nama. Contoh mencari IDR:

POST /web/dataset/call_kw/res.currency/search_read

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "res.currency",
    "method": "search_read",
    "args": [[["name", "=", "IDR"]], ["id", "name"]],
    "kwargs": {"limit": 1}
  }
}
~~~

Ambil nilai id dari response sebagai CURRENCY_ID.

## 4. Char dan Integer — buat tag

academy.course.tag memiliki name (Char) dan color (Integer).

POST /web/dataset/call_kw/academy.course.tag/create

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.course.tag",
    "method": "create",
    "args": [{"name": "Data", "color": 4}],
    "kwargs": {}
  }
}
~~~

Simpan hasilnya sebagai TAG_ID.

## 5. Course — Char, Html, Float, Monetary, Selection, Boolean, Text, Many2one, Many2many

POST /web/dataset/call_kw/academy.course/create

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.course",
    "method": "create",
    "args": [{
      "name": "Analisis Data Dasar",
      "code": "JRPC-COURSE-001",
      "description": "<p>Belajar <strong>JSON-RPC</strong> dari Odoo.</p>",
      "duration_hours": 16.5,
      "price": 1500000,
      "currency_id": 12,
      "level": "beginner",
      "active": true,
      "is_published": false,
      "internal_notes": "Contoh field Text.",
      "tag_ids": [[6, 0, [7]]]
    }],
    "kwargs": {}
  }
}
~~~

description adalah Html; price adalah Monetary dan perlu currency_id; currency_id
adalah Many2one. Ganti 12 dan 7 dengan ID valid.

Command Many2many:

- [[6, 0, [ID1, ID2]]]: ganti seluruh tag.
- [[4, TAG_ID]]: tambahkan satu tag.
- [[3, TAG_ID]]: lepas satu tag.
- [[5, 0, 0]]: kosongkan seluruh tag.

## 6. Update course — write dan Boolean/Many2many

POST /web/dataset/call_kw/academy.course/write

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.course",
    "method": "write",
    "args": [[101], {
      "level": "advanced",
      "active": false,
      "tag_ids": [[4, 8]]
    }],
    "kwargs": {}
  }
}
~~~

Ganti 101 dengan COURSE_ID dan 8 dengan TAG_ID. Response true berarti update
berhasil.

## 7. Student — Date dan Selection

POST /web/dataset/call_kw/academy.student/create

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.student",
    "method": "create",
    "args": [{
      "name": "Siti JSONRPC",
      "email": "siti@example.test",
      "phone": "+628123456789",
      "birthdate": "2001-05-15",
      "gender": "female",
      "active": true
    }],
    "kwargs": {}
  }
}
~~~

Format Date adalah YYYY-MM-DD. Nilai gender: male, female, atau other.

## 8. Batch — Many2one, Date, Integer, Selection, Boolean, computed, One2many

POST /web/dataset/call_kw/academy.batch/create

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.batch",
    "method": "create",
    "args": [{
      "name": "Batch JSON-RPC Mei 2026",
      "course_id": 101,
      "start_date": "2026-05-01",
      "end_date": "2026-05-31",
      "capacity": 20,
      "state": "draft",
      "responsible_id": 2,
      "active": true
    }],
    "kwargs": {}
  }
}
~~~

course_id dan responsible_id adalah Many2one. Jangan mengirim enrollment_ids
(One2many), enrollment_count, atau available_seats: relasi dan field computed
tersebut dibentuk Odoo.

## 9. Enrollment — relasi wajib, Date, Selection, Text, dan Datetime readonly

POST /web/dataset/call_kw/academy.enrollment/create

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.enrollment",
    "method": "create",
    "args": [{
      "name": "ENR-JRPC-001",
      "batch_id": 201,
      "student_id": 301,
      "enrollment_date": "2026-05-02",
      "state": "draft",
      "notes": "Contoh catatan pendaftaran."
    }],
    "kwargs": {}
  }
}
~~~

batch_id dan student_id wajib diisi. Jangan mengirim field audit readonly
submitted_by_id, submitted_date, manager_approved_by_id, manager_approved_date,
final_approved_by_id, final_approved_date, atau rejection_reason. Field Datetime
audit dibuat Odoo lewat workflow.

## 10. Workflow enrollment — object method

POST /web/dataset/call_kw/academy.enrollment/action_submit

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.enrollment",
    "method": "action_submit",
    "args": [[401]],
    "kwargs": {}
  }
}
~~~

Ganti 401 dengan ENROLLMENT_ID. Lanjutkan dengan action_manager_approve,
action_final_approve, atau action_done hanya bila state dan grup approval user
memenuhi aturan workflow. action_reset_to_draft hanya berlaku untuk rejected atau
cancelled.

## 11. Baca relasi, waktu, dan field hitung

POST /web/dataset/call_kw/academy.enrollment/search_read

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.enrollment",
    "method": "search_read",
    "args": [[], [
      "name", "batch_id", "student_id", "state", "notes",
      "submitted_by_id", "submitted_date"
    ]],
    "kwargs": {"limit": 10}
  }
}
~~~

Di response, Many2one biasanya [id, "Nama"]; Many2many dan One2many berupa daftar
ID; Date berupa YYYY-MM-DD; dan Datetime berupa string waktu Odoo. Tambahkan
enrollment_count dan available_seats pada academy.batch/search_read untuk melihat
field computed.

## 12. Delete record latihan

POST /web/dataset/call_kw/academy.course/unlink

~~~json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.course",
    "method": "unlink",
    "args": [[101]],
    "kwargs": {}
  }
}
~~~

Jalankan hanya untuk record latihan. Delete bisa ditolak bila course masih dipakai
batch karena relasi itu memakai ondelete="restrict".

## Ringkasan tipe field

| Tipe | Contoh | Bentuk JSON |
|---|---|---|
| Char | academy.course.name | string |
| Text | academy.enrollment.notes | string |
| Html | academy.course.description | string HTML |
| Integer | academy.batch.capacity | angka bulat |
| Float | academy.course.duration_hours | angka desimal |
| Monetary | academy.course.price | angka + currency_id |
| Boolean | academy.course.active | true atau false |
| Date | academy.student.birthdate | YYYY-MM-DD |
| Datetime | academy.enrollment.submitted_date | readonly, workflow |
| Selection | academy.course.level | technical value |
| Many2one | academy.batch.course_id | satu ID |
| Many2many | academy.course.tag_ids | command Odoo |
| One2many | academy.batch.enrollment_ids | daftar ID di response |
| Computed | academy.batch.available_seats | readonly, dihitung Odoo |
