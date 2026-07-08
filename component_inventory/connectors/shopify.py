import json

import requests

from ..config import shopify_api_version, shopify_store
from .auth import shopify_access_token


def _base():
    return f"https://{shopify_store()}/admin/api/{shopify_api_version()}"


def _headers():
    return {
        "X-Shopify-Access-Token": shopify_access_token(),
        "Content-Type": "application/json",
    }


def list_products(limit=250):
    resp = requests.get(
        f"{_base()}/products.json",
        headers=_headers(),
        params={"limit": limit},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("products", [])


def list_orders(status="open", limit=250):
    resp = requests.get(
        f"{_base()}/orders.json",
        headers=_headers(),
        params={"status": status, "limit": limit},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("orders", [])


def import_products(conn):
    products = list_products()
    imported = 0
    for product in products:
        for variant in product.get("variants", []):
            sku = variant.get("sku")
            if not sku:
                continue
            title = product.get("title") or sku
            if variant.get("title") and variant.get("title") != "Default Title":
                title = f"{title} - {variant['title']}"
            conn.execute(
                """
                INSERT INTO sellable_skus
                  (sku, title, shopify_variant_id, shopify_inventory_item_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                  title = excluded.title,
                  shopify_variant_id = excluded.shopify_variant_id,
                  shopify_inventory_item_id = excluded.shopify_inventory_item_id
                """,
                (
                    sku,
                    title,
                    str(variant.get("id") or ""),
                    str(variant.get("inventory_item_id") or ""),
                ),
            )
            imported += 1
    conn.commit()
    return imported


def import_orders(conn, status="open"):
    orders = list_orders(status=status)
    imported = 0
    for order in orders:
        order_id = str(order.get("id") or "")
        if not order_id:
            continue
        customer = order.get("customer") or {}
        customer_name = " ".join(
            part for part in [customer.get("first_name"), customer.get("last_name")] if part
        )
        conn.execute(
            """
            INSERT INTO orders
              (channel, channel_order_id, customer_name, status, ordered_at, raw_json)
            VALUES ('Shopify', ?, ?, 'open', ?, ?)
            ON CONFLICT(channel, channel_order_id) DO UPDATE SET
              customer_name = excluded.customer_name,
              ordered_at = excluded.ordered_at,
              raw_json = excluded.raw_json
            """,
            (
                order_id,
                customer_name,
                order.get("created_at"),
                json.dumps(order, separators=(",", ":")),
            ),
        )
        local_order_id = conn.execute(
            "SELECT id FROM orders WHERE channel = 'Shopify' AND channel_order_id = ?",
            (order_id,),
        ).fetchone()["id"]
        conn.execute("DELETE FROM order_lines WHERE order_id = ?", (local_order_id,))
        for line in order.get("line_items", []):
            sku = line.get("sku") or str(line.get("variant_id") or line.get("id") or "")
            if not sku:
                continue
            sellable = conn.execute(
                """
                SELECT ss.id
                FROM sellable_skus ss
                WHERE ss.sku = ?
                   OR ss.shopify_variant_id = ?
                   OR ss.id = (
                       SELECT cm.sellable_sku_id
                       FROM channel_mappings cm
                       WHERE cm.channel = 'Shopify'
                         AND cm.channel_sku = ?
                         AND cm.sellable_sku_id IS NOT NULL
                   )
                LIMIT 1
                """,
                (sku, str(line.get("variant_id") or ""), sku),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO order_lines
                  (order_id, sellable_sku_id, channel_sku, title, quantity)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    local_order_id,
                    sellable["id"] if sellable else None,
                    sku,
                    line.get("title") or line.get("name") or sku,
                    int(line.get("quantity") or 1),
                ),
            )
        imported += 1
    conn.commit()
    return imported
