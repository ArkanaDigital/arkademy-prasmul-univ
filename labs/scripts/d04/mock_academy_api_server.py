"""API mock lokal untuk checkpoint REST API consumer Day 4."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


COURSES = {
    "courses": [
        {"code": "EXT-PY-101", "name": "Python for ERP Developers", "level": "beginner", "duration_hours": 16, "price": 2500000},
        {"code": "EXT-ODOO-201", "name": "Odoo Technical Integration", "level": "advanced", "duration_hours": 24, "price": 3500000},
    ]
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/api/courses":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(COURSES).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9090), Handler)
    print("Mock Academy API running on http://localhost:9090/api/courses")
    server.serve_forever()
