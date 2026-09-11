"""A synthetic counter demonstrating durable SQLite data and a bounded HTTP app."""
import json
import os
import sqlite3
import threading
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class CounterStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.write_lock = threading.Lock()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS counter (id INTEGER PRIMARY KEY CHECK(id=1), value INTEGER NOT NULL)")
            db.execute("INSERT OR IGNORE INTO counter VALUES (1, 0)")

    def read(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT value FROM counter WHERE id=1").fetchone()[0]

    def increment(self):
        # Serialize this process's writers so busy retries cannot starve a request.
        with self.write_lock, closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE counter SET value=value+1 WHERE id=1")
            return db.execute("SELECT value FROM counter WHERE id=1").fetchone()[0]


PAGE = b'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local App Blueprint | Durable counter</title>
<style>body{font:18px/1.6 system-ui;max-width:640px;margin:10vh auto;padding:24px;background:#10191e;color:#edf5f7}h1{line-height:1.1}button{font:inherit;padding:12px 24px;background:#ade7c5;border:0;border-radius:8px;cursor:pointer}button:focus-visible{outline:3px solid white;outline-offset:4px}output{display:block;font-size:64px;font-weight:700}p{color:#c1d1d7}small{display:block;margin-top:24px}</style>
<main><small>LOCAL APP BLUEPRINT</small><h1>A small app. Durable data.</h1>
<p>This synthetic counter stores its value in SQLite. Restart the app and the count stays.</p>
<output id="count" aria-live="polite">Loading...</output>
<button id="increment" type="button">Add one</button>
<p id="status" role="status">Connecting to local storage.</p>
<small>Example only. Contains no personal data or account system.</small></main>
<script src="/app.js" defer></script></html>'''

SCRIPT = b'''const count=document.querySelector('#count'),status=document.querySelector('#status'),button=document.querySelector('#increment');
async function update(increment=false){button.disabled=true;try{const response=await fetch(increment?'/api/increment':'/api/counter',increment?{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}:{});if(!response.ok)throw new Error('Request failed');const data=await response.json();count.value=data.value;status.textContent='Saved in local SQLite storage.';}catch(error){status.textContent='Could not reach storage. Please try again.';}finally{button.disabled=false;}}
button.addEventListener('click',()=>update(true));update();'''


def make_server(store, bind="127.0.0.1", port=8080, allowed_host=None):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, body, content_type="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def local_request(self):
            host = self.server.allowed_host
            if (self.headers.get("Host") != host
                    or self.headers.get("Origin", "http://" + host) != "http://" + host
                    or self.headers.get("Sec-Fetch-Site") == "cross-site"):
                self.respond(403, b'{"error":"host or origin rejected"}')
                return False
            return True

        def do_GET(self):
            if not self.local_request():
                return
            if self.path == "/":
                self.respond(200, PAGE, "text/html; charset=utf-8")
            elif self.path == "/favicon.ico":
                self.respond(204, b"")
            elif self.path == "/app.js":
                self.respond(200, SCRIPT, "text/javascript; charset=utf-8")
            elif self.path in ("/api/counter", "/health"):
                # Reading the durable store makes health fail if storage is broken.
                self.respond(200, json.dumps({"value": store.read()}).encode())
            else:
                self.respond(404, b'{"error":"not found"}')

        def do_POST(self):
            if not self.local_request():
                return
            if self.path != "/api/increment":
                self.respond(404, b'{"error":"not found"}')
                return
            if self.headers.get("Content-Type") != "application/json":
                self.respond(415, b'{"error":"JSON required"}')
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1024 or self.headers.get("Transfer-Encoding"):
                    raise ValueError("invalid body length")
                if json.loads(self.rfile.read(length)) != {}:
                    raise ValueError("expected an empty JSON object")
            except (ValueError, UnicodeDecodeError):
                self.respond(400, b'{"error":"expected an empty JSON object"}')
                return
            self.respond(200, json.dumps({"value": store.increment()}).encode())

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer((bind, port), Handler)
    server.allowed_host = allowed_host or f"{bind}:{server.server_port}"
    return server


if __name__ == "__main__":
    store = CounterStore(Path(os.environ.get("APP_DATA_DIR", "./data")) / "counter.sqlite3")
    server = make_server(store, os.environ.get("APP_BIND", "127.0.0.1"),
                         int(os.environ.get("APP_PORT", "8080")), os.environ.get("APP_ALLOWED_HOST"))
    print(f"Counter listening at http://{server.allowed_host}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
