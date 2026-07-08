import argparse
import base64
import hashlib
import hmac
import json
import os
import time
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .db import connect, init_db
from .seed import seed_demo
from .services.inventory import (
    catalog_summary,
    dashboard_summary,
    reserve_order,
    upsert_bom_component,
    upsert_channel_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
SESSION_COOKIE = "ci_session"
SESSION_TTL_SECONDS = 60 * 60 * 12


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/login":
            self.send_login()
            return
        if parsed.path == "/logout":
            self.send_logout()
            return
        if not self.require_auth():
            return
        if parsed.path == "/api/summary":
            self.send_json(dashboard_summary(connect()))
            return
        if parsed.path == "/api/catalog":
            self.send_json(catalog_summary(connect()))
            return
        if parsed.path == "/health":
            self.send_json({"ok": True})
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/login":
            self.handle_login()
            return
        if not self.require_auth():
            return
        if parsed.path == "/api/sync/shopify/products":
            from .connectors.shopify import import_products

            count = import_products(connect())
            self.send_json({"imported": count})
            return
        if parsed.path == "/api/sync/shopify/orders":
            from .connectors.shopify import import_orders

            count = import_orders(connect())
            self.send_json({"imported": count})
            return
        if parsed.path == "/api/orders/reserve":
            payload = self.read_json()
            if payload is None:
                return
            try:
                result = reserve_order(connect(), int(payload["order_id"]))
            except (KeyError, TypeError, ValueError) as exc:
                self.send_json({"error": str(exc)}, status=400)
                return
            self.send_json(result, status=201)
            return
        if parsed.path == "/api/bom-components":
            payload = self.read_json()
            if payload is None:
                return
            try:
                upsert_bom_component(
                    connect(),
                    payload["sellable_sku"],
                    payload["item_sku"],
                    int(payload["quantity"]),
                    bool(payload.get("is_substitutable", False)),
                )
            except (KeyError, TypeError, ValueError) as exc:
                self.send_json({"error": str(exc)}, status=400)
                return
            self.send_json({"ok": True}, status=201)
            return
        if parsed.path == "/api/channel-mappings":
            payload = self.read_json()
            if payload is None:
                return
            try:
                upsert_channel_mapping(
                    connect(),
                    payload["channel"],
                    payload["channel_sku"],
                    payload.get("sellable_sku", ""),
                    payload.get("item_sku", ""),
                )
            except (KeyError, TypeError, ValueError) as exc:
                self.send_json({"error": str(exc)}, status=400)
                return
            self.send_json({"ok": True}, status=201)
            return
        self.send_error(404, "Unknown endpoint")

    def send_json(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            return json.loads(raw.decode())
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON body"}, status=400)
            return None

    def require_auth(self):
        password = os.getenv("COMPONENT_INVENTORY_PASSWORD")
        if not password:
            return True
        if self.has_valid_session():
            return True
        auth = self.headers.get("Authorization", "")
        prefix = "Basic "
        if not auth.startswith(prefix):
            self.redirect_login()
            return False
        try:
            decoded = base64.b64decode(auth[len(prefix):]).decode()
        except ValueError:
            self.send_auth_required()
            return False
        username, sep, supplied_password = decoded.partition(":")
        if sep and username == "admin" and hmac.compare_digest(supplied_password, password):
            return True
        self.send_auth_required()
        return False

    def has_valid_session(self):
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return False
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        morsel = cookies.get(SESSION_COOKIE)
        if not morsel:
            return False
        expires_text, sep, signature = morsel.value.partition(".")
        if not sep:
            return False
        try:
            expires = int(expires_text)
        except ValueError:
            return False
        if expires < int(time.time()):
            return False
        expected = self.session_signature(expires_text)
        return hmac.compare_digest(signature, expected)

    def session_signature(self, value):
        secret = os.getenv("COMPONENT_INVENTORY_SESSION_SECRET") or os.getenv("COMPONENT_INVENTORY_PASSWORD", "")
        return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()

    def handle_login(self):
        password = os.getenv("COMPONENT_INVENTORY_PASSWORD")
        if not password:
            self.redirect("/")
            return
        length = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(length).decode()) if length else {}
        supplied = form.get("password", [""])[0]
        if not hmac.compare_digest(supplied, password):
            self.send_login("Invalid password.")
            return
        expires = str(int(time.time()) + SESSION_TTL_SECONDS)
        value = f"{expires}.{self.session_signature(expires)}"
        self.send_response(302)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", f"{SESSION_COOKIE}={value}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age={SESSION_TTL_SECONDS}")
        self.end_headers()

    def send_login(self, error=""):
        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Component Inventory Login</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; --bg:#f5f6f8; --panel:#fff; --ink:#1f2328; --muted:#667085; --line:#d9dee7; --accent:#0f766e; --danger:#a12f2f; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); }}
    main {{ min-height: 100vh; display: grid; place-items: center; padding: 20px; }}
    form {{ width: min(360px, 100%); display: grid; gap: 14px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px; }}
    h1, p {{ margin: 0; }} h1 {{ font-size: 24px; }} .lede {{ color: var(--muted); font-size: 14px; }} .error {{ color: var(--danger); font-size: 13px; }}
    label {{ display: grid; gap: 6px; font-size: 12px; font-weight: 700; }}
    input {{ min-height: 40px; border: 1px solid var(--line); border-radius: 6px; padding: 0 10px; font: inherit; }}
    button {{ min-height: 40px; border: 0; border-radius: 6px; background: var(--accent); color: #fff; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <form method="post" action="/login">
      <h1>Component Inventory</h1>
      <p class="lede">Remote live dashboard</p>
      {f'<p class="error">{error}</p>' if error else ''}
      <label>Password<input name="password" type="password" autocomplete="current-password" autofocus required></label>
      <button type="submit">Sign in</button>
    </form>
  </main>
</body>
</html>""".encode()
        self.send_response(401 if error else 200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_logout(self):
        self.send_response(302)
        self.send_header("Location", "/login")
        self.send_header("Set-Cookie", f"{SESSION_COOKIE}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0")
        self.end_headers()

    def redirect_login(self):
        self.redirect("/login")

    def redirect(self, path):
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def send_auth_required(self):
        body = b"Authentication required"
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Component Inventory"')
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--init-db", action="store_true")
    parser.add_argument("--seed-demo", action="store_true")
    args = parser.parse_args()

    conn = connect()
    if args.init_db:
        init_db(conn)
    if args.seed_demo:
        seed_demo(conn)

    if args.init_db or args.seed_demo:
        print("Database ready.")
        if not args.port:
            return

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Component Inventory running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
