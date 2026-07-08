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

