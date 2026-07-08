import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .db import connect, init_db
from .seed import seed_demo
from .services.inventory import dashboard_summary


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/summary":
            self.send_json(dashboard_summary(connect()))
            return
        if parsed.path == "/health":
            self.send_json({"ok": True})
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/sync/shopify/products":
            from .connectors.shopify import import_products

            count = import_products(connect())
            self.send_json({"imported": count})
            return
        self.send_error(404, "Unknown endpoint")

    def send_json(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
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

