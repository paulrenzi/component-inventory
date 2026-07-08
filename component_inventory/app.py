import argparse
import base64
import hmac
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

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


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self):
        if not self.require_auth():
            return
        parsed = urlparse(self.path)
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
        if not self.require_auth():
            return
        parsed = urlparse(self.path)
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
        auth = self.headers.get("Authorization", "")
        prefix = "Basic "
        if not auth.startswith(prefix):
            self.send_auth_required()
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
