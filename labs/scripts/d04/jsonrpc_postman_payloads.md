# JSON-RPC via Postman — `academy.course`

Base URL: `http://localhost:8069`
Header: `Content-Type: application/json`

Aktifkan cookie jar Postman. Cookie `session_id` dari Authenticate harus ikut ke
request selanjutnya. JSON-RPC **bukan REST**: endpoint menjalankan method Odoo,
bukan merepresentasikan resource.

## 1. Authenticate

`POST /web/session/authenticate`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {"db": "odoo", "login": "admin", "password": "admin"}
}
```

Pastikan `result.uid` tidak null.

## 2. Search read

`POST /web/dataset/call_kw/academy.course/search_read`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.course",
    "method": "search_read",
    "args": [[], ["name", "code", "level"]],
    "kwargs": {"limit": 10}
  }
}
```

## 3. Create

`POST /web/dataset/call_kw/academy.course/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "academy.course",
    "method": "create",
    "args": [{"name": "Course via JSON-RPC", "code": "JRPC-001", "level": "beginner"}],
    "kwargs": {}
  }
}
```

Simpan ID hasil Create untuk `write` dan `unlink`.

## 4. Update dan delete

Gunakan endpoint `/web/dataset/call_kw/academy.course/write` dengan
`"args": [[COURSE_ID], {"level": "advanced"}]`, lalu endpoint
`/web/dataset/call_kw/academy.course/unlink` dengan `"args": [[COURSE_ID]]`.

Kedua operasi tetap dibatasi access rights dan record rules user yang login.
