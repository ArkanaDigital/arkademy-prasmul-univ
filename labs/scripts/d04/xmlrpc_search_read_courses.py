"""Contoh XML-RPC: autentikasi dan membaca academy.course."""

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
courses = models.execute_kw(
    DB, uid, PASSWORD, "academy.course", "search_read", [[]],
    {"fields": ["name", "code", "level"], "limit": 10},
)
for course in courses:
    print(course)
