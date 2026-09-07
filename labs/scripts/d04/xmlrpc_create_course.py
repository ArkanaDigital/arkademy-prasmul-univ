"""Contoh XML-RPC opsional: membuat academy.course."""

import xmlrpc.client

URL = "http://localhost:8069"
DB = "odoo"
USERNAME = "admin"
PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
if not uid:
    raise SystemExit("Authentication failed; check DB, USERNAME, and PASSWORD.")

models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
course_id = models.execute_kw(
    DB, uid, PASSWORD, "academy.course", "create",
    [{"name": "Course via XML-RPC", "code": "RPC-001", "level": "beginner"}],
)
print("Created course id:", course_id)
