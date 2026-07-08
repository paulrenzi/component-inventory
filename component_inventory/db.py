import sqlite3
from pathlib import Path

from .config import DB_PATH


def connect(path=DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    conn.executescript(schema_path.read_text())
    migrate(conn)
    conn.commit()


def migrate(conn):
    order_cols = {
        row["name"] for row in conn.execute("PRAGMA table_info(orders)").fetchall()
    }
    if "created_at" not in order_cols:
        conn.execute(
            "ALTER TABLE orders ADD COLUMN created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
        )
    supplier_offer_cols = {
        row["name"] for row in conn.execute("PRAGMA table_info(supplier_offers)").fetchall()
    }
    if supplier_offer_cols and "supplier_sku" not in supplier_offer_cols:
        conn.execute("ALTER TABLE supplier_offers ADD COLUMN supplier_sku TEXT NOT NULL DEFAULT ''")
    if supplier_offer_cols and "shipping_cost" not in supplier_offer_cols:
        conn.execute("ALTER TABLE supplier_offers ADD COLUMN shipping_cost REAL")
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    conn.executescript(schema_path.read_text())


def rows(conn, sql, params=()):
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def one(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None
