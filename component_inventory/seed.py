from .services.inventory import add_stock


def seed_demo(conn):
    items = [
        ("SSD-2TB-NVME", "2TB NVMe SSD", "pc_component", 5, 20),
        ("MINI-PC-BLK", "Black mini PC barebones", "pc_component", 2, 8),
        ("CAB-WALL-BLK", "Black wall arcade cabinet shell", "fabricated_part", 1, 4),
        ("CTRL-8BITDO-U2", "8BitDo Ultimate 2 controller", "accessory", 4, 12),
        ("PWR-KIT", "Power strip and cabling kit", "component", 3, 10),
    ]
    for sku, name, category, reorder, target in items:
        conn.execute(
            """
            INSERT OR IGNORE INTO items (sku, name, category, reorder_point, target_stock)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sku, name, category, reorder, target),
        )

    conn.execute(
        """
        INSERT OR IGNORE INTO sellable_skus (sku, title)
        VALUES ('UA-ARCADE-BLK-2TB', 'Black 2TB Wall Arcade Cabinet')
        """
    )
    sellable_id = conn.execute(
        "SELECT id FROM sellable_skus WHERE sku = 'UA-ARCADE-BLK-2TB'"
    ).fetchone()["id"]

    for sku, qty in [
        ("SSD-2TB-NVME", 1),
        ("MINI-PC-BLK", 1),
        ("CAB-WALL-BLK", 1),
        ("CTRL-8BITDO-U2", 2),
        ("PWR-KIT", 1),
    ]:
        item_id = conn.execute("SELECT id FROM items WHERE sku = ?", (sku,)).fetchone()["id"]
        conn.execute(
            """
            INSERT OR IGNORE INTO bom_components (sellable_sku_id, item_id, quantity)
            VALUES (?, ?, ?)
            """,
            (sellable_id, item_id, qty),
        )

    existing = conn.execute("SELECT COUNT(*) AS n FROM stock_movements").fetchone()["n"]
    if existing == 0:
        add_stock(conn, "SSD-2TB-NVME", 7, "demo seed")
        add_stock(conn, "MINI-PC-BLK", 3, "demo seed")
        add_stock(conn, "CAB-WALL-BLK", 2, "demo seed")
        add_stock(conn, "CTRL-8BITDO-U2", 10, "demo seed")
        add_stock(conn, "PWR-KIT", 6, "demo seed")

    ssd_id = conn.execute("SELECT id FROM items WHERE sku = 'SSD-2TB-NVME'").fetchone()["id"]
    mini_id = conn.execute("SELECT id FROM items WHERE sku = 'MINI-PC-BLK'").fetchone()["id"]
    conn.execute(
        """
        INSERT OR IGNORE INTO supplier_orders
          (supplier, supplier_order_id, status, ordered_at, expected_at, tracking_number)
        VALUES ('Amazon', 'DEMO-AMZ-1001', 'shipped', '2026-07-07', '2026-07-10', 'DEMO123')
        """
    )
    supplier_order_id = conn.execute(
        "SELECT id FROM supplier_orders WHERE supplier = 'Amazon' AND supplier_order_id = 'DEMO-AMZ-1001'"
    ).fetchone()["id"]
    supplier_line_exists = conn.execute(
        """
        SELECT 1 FROM supplier_order_lines
        WHERE supplier_order_id = ? AND supplier_sku = 'B0-DEMO-SSD'
        """,
        (supplier_order_id,),
    ).fetchone()
    if not supplier_line_exists:
        conn.execute(
            """
            INSERT INTO supplier_order_lines
              (supplier_order_id, item_id, supplier_sku, title, quantity, unit_cost, line_status)
            VALUES (?, ?, 'B0-DEMO-SSD', '2TB NVMe SSD supplier order', 8, 82.50, 'shipped')
            """,
            (supplier_order_id, ssd_id),
        )

    offer_exists = conn.execute(
        """
        SELECT 1 FROM supplier_offers
        WHERE item_id = ? AND supplier = 'eBay' AND supplier_sku = 'EBAY-DEMO-MINI-PC'
        """,
        (mini_id,),
    ).fetchone()
    if not offer_exists:
        conn.execute(
            """
            INSERT INTO supplier_offers
              (item_id, supplier, supplier_sku, url, price, shipping_cost, available_quantity, lead_time_days, confidence)
            VALUES (?, 'eBay', 'EBAY-DEMO-MINI-PC', 'https://www.ebay.com/', 219.99, 0, 4, 5, 'manual')
            """,
            (mini_id,),
        )

    conn.execute(
        """
        INSERT OR IGNORE INTO vendors
          (marketplace, vendor_key, display_name, vendor_type, profile_url, preferred, notes)
        VALUES ('eBay', 'demo-ebay-mini-pc-seller', 'Demo eBay Mini PC Seller', 'marketplace_seller',
                'https://www.ebay.com/', 1, 'Demo preferred source for mini PC barebones')
        """
    )
    vendor_id = conn.execute(
        "SELECT id FROM vendors WHERE marketplace = 'eBay' AND vendor_key = 'demo-ebay-mini-pc-seller'"
    ).fetchone()["id"]
    conn.execute(
        """
        INSERT OR IGNORE INTO listing_offers
          (item_id, vendor_id, marketplace, listing_id, title, url, condition, price, shipping_cost,
           quantity_available, accepts_offers, auto_order_allowed)
        VALUES (?, ?, 'eBay', 'DEMO-LISTING-MINI-PC', 'Demo mini PC barebones lot',
                'https://www.ebay.com/', 'used', 219.99, 0, 4, 1, 0)
        """,
        (mini_id, vendor_id),
    )

    conn.commit()
