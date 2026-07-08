from ..db import rows


def dashboard_summary(conn):
    stock = rows(conn, "SELECT * FROM item_stock ORDER BY available ASC, sku")
    low_stock = [item for item in stock if item["available"] <= item["reorder_point"]]
    open_orders = rows(conn, """
        SELECT o.id, o.channel, o.channel_order_id, o.customer_name, o.status, o.ordered_at,
               COUNT(ol.id) AS line_count,
               COALESCE(SUM(CASE WHEN ol.id IS NOT NULL AND ol.sellable_sku_id IS NULL THEN 1 ELSE 0 END), 0) AS unmapped_line_count,
               COALESCE(SUM(CASE
                   WHEN ol.sellable_sku_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM bom_components bc
                        WHERE bc.sellable_sku_id = ol.sellable_sku_id
                    )
                   THEN 1 ELSE 0
               END), 0) AS missing_bom_line_count
        FROM orders o
        LEFT JOIN order_lines ol ON ol.order_id = o.id
        WHERE o.status IN ('open', 'reserved', 'blocked')
        GROUP BY o.id
        ORDER BY COALESCE(o.ordered_at, o.created_at) DESC
        LIMIT 25
    """)
    work_orders = rows(conn, """
        SELECT wo.id, wo.status, wo.priority, wo.notes, ss.sku, ss.title
        FROM work_orders wo
        LEFT JOIN sellable_skus ss ON ss.id = wo.sellable_sku_id
        WHERE wo.status != 'complete'
        ORDER BY wo.priority DESC, wo.created_at ASC
        LIMIT 25
    """)
    buildable = rows(conn, """
        SELECT ss.sku, ss.title,
               MIN(CAST(item_stock.available / bc.quantity AS INTEGER)) AS buildable_qty
        FROM sellable_skus ss
        JOIN bom_components bc ON bc.sellable_sku_id = ss.id
        JOIN item_stock ON item_stock.item_id = bc.item_id
        WHERE ss.status = 'active'
        GROUP BY ss.id
        ORDER BY buildable_qty ASC, ss.sku
    """)
    inbound = rows(conn, """
        SELECT inbound_stock.*, item_stock.available
        FROM inbound_stock
        JOIN item_stock ON item_stock.item_id = inbound_stock.item_id
        WHERE inbound_stock.inbound_quantity > 0
        ORDER BY inbound_stock.next_expected_at, inbound_stock.sku
    """)
    vendors = rows(
        conn,
        """
        SELECT
          v.marketplace,
          v.display_name AS name,
          v.preferred,
          COALESCE(vm.on_time_count, 0) AS on_time,
          COALESCE(vm.defect_count, 0) AS defects,
          vm.average_ship_days AS avg_ship,
          v.notes
        FROM vendors v
        LEFT JOIN vendor_metrics vm
          ON vm.vendor_id = v.id
         AND vm.metric_date = (
             SELECT MAX(metric_date)
             FROM vendor_metrics vm2
             WHERE vm2.vendor_id = v.id
         )
        ORDER BY v.preferred DESC, v.marketplace, v.display_name
        """,
    )
    offers = rows(
        conn,
        """
        WITH latest_attempt AS (
          SELECT na.*
          FROM negotiation_attempts na
          JOIN (
            SELECT listing_offer_id, MAX(id) AS latest_id
            FROM negotiation_attempts
            GROUP BY listing_offer_id
          ) latest ON latest.latest_id = na.id
        )
        SELECT
          lo.marketplace,
          COALESCE(i.sku, lo.title) AS item,
          lo.title AS listing,
          lo.price AS ask,
          COALESCE(latest_attempt.proposed_price, ROUND(COALESCE(lo.price, 0) * 0.9, 2)) AS target_offer,
          lo.quantity_available AS quantity,
          COALESCE(latest_attempt.status, CASE WHEN lo.accepts_offers = 1 THEN 'draft' ELSE 'watching' END) AS status
        FROM listing_offers lo
        LEFT JOIN items i ON i.id = lo.item_id
        LEFT JOIN latest_attempt ON latest_attempt.listing_offer_id = lo.id
        ORDER BY lo.checked_at DESC, lo.id DESC
        """,
    )
    return {
        "stock": stock,
        "low_stock": low_stock,
        "open_orders": open_orders,
        "work_orders": work_orders,
        "buildable": buildable,
        "inbound": inbound,
        "vendors": vendors,
        "offers": offers,
    }


def catalog_summary(conn):
    sellables = rows(
        conn,
        """
        SELECT
          ss.id,
          ss.sku,
          ss.title,
          ss.status,
          ss.shopify_variant_id,
          ss.shopify_inventory_item_id,
          COUNT(DISTINCT bc.id) AS bom_lines,
          COUNT(DISTINCT cm.id) AS channel_links
        FROM sellable_skus ss
        LEFT JOIN bom_components bc ON bc.sellable_sku_id = ss.id
        LEFT JOIN channel_mappings cm ON cm.sellable_sku_id = ss.id
        GROUP BY ss.id
        ORDER BY ss.sku
        """,
    )
    items = rows(conn, "SELECT * FROM items ORDER BY category, sku")
    bom_components = rows(
        conn,
        """
        SELECT
          bc.id,
          ss.sku AS sellable_sku,
          ss.title AS sellable_title,
          i.sku AS item_sku,
          i.name AS item_name,
          bc.quantity,
          bc.is_substitutable
        FROM bom_components bc
        JOIN sellable_skus ss ON ss.id = bc.sellable_sku_id
        JOIN items i ON i.id = bc.item_id
        ORDER BY ss.sku, i.sku
        """,
    )
    channel_mappings = rows(
        conn,
        """
        SELECT
          cm.id,
          cm.channel,
          cm.channel_sku,
          ss.sku AS sellable_sku,
          ss.title AS sellable_title,
          i.sku AS item_sku,
          i.name AS item_name
        FROM channel_mappings cm
        LEFT JOIN sellable_skus ss ON ss.id = cm.sellable_sku_id
        LEFT JOIN items i ON i.id = cm.item_id
        ORDER BY cm.channel, cm.channel_sku
        """,
    )
    return {
        "sellables": sellables,
        "items": items,
        "bom_components": bom_components,
        "channel_mappings": channel_mappings,
    }


def add_stock(conn, item_sku, quantity, reason="manual adjustment", reference_type="", reference_id=""):
    item = conn.execute("SELECT id FROM items WHERE sku = ?", (item_sku,)).fetchone()
    if not item:
        raise ValueError(f"Unknown item SKU: {item_sku}")
    conn.execute(
        """
        INSERT INTO stock_movements (item_id, quantity_delta, reason, reference_type, reference_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (item["id"], quantity, reason, reference_type, reference_id),
    )
    conn.commit()


def upsert_bom_component(conn, sellable_sku, item_sku, quantity, is_substitutable=False):
    sellable = conn.execute(
        "SELECT id FROM sellable_skus WHERE sku = ?",
        (sellable_sku,),
    ).fetchone()
    if not sellable:
        raise ValueError(f"Unknown sellable SKU: {sellable_sku}")
    item = conn.execute(
        "SELECT id FROM items WHERE sku = ?",
        (item_sku,),
    ).fetchone()
    if not item:
        raise ValueError(f"Unknown item SKU: {item_sku}")
    conn.execute(
        """
        INSERT INTO bom_components (sellable_sku_id, item_id, quantity, is_substitutable)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sellable_sku_id, item_id) DO UPDATE SET
          quantity = excluded.quantity,
          is_substitutable = excluded.is_substitutable
        """,
        (sellable["id"], item["id"], quantity, 1 if is_substitutable else 0),
    )
    conn.commit()


def upsert_channel_mapping(conn, channel, channel_sku, sellable_sku="", item_sku=""):
    sellable_id = None
    item_id = None
    if sellable_sku:
        sellable = conn.execute(
            "SELECT id FROM sellable_skus WHERE sku = ?",
            (sellable_sku,),
        ).fetchone()
        if not sellable:
            raise ValueError(f"Unknown sellable SKU: {sellable_sku}")
        sellable_id = sellable["id"]
    if item_sku:
        item = conn.execute(
            "SELECT id FROM items WHERE sku = ?",
            (item_sku,),
        ).fetchone()
        if not item:
            raise ValueError(f"Unknown item SKU: {item_sku}")
        item_id = item["id"]
    conn.execute(
        """
        INSERT INTO channel_mappings (channel, channel_sku, sellable_sku_id, item_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(channel, channel_sku) DO UPDATE SET
          sellable_sku_id = excluded.sellable_sku_id,
          item_id = excluded.item_id
        """,
        (channel, channel_sku, sellable_id, item_id),
    )
    conn.commit()


def reserve_order(conn, order_id):
    order = conn.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        raise ValueError(f"Unknown order ID: {order_id}")

    unmapped = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM order_lines
        WHERE order_id = ? AND sellable_sku_id IS NULL
        """,
        (order_id,),
    ).fetchone()["n"]
    if unmapped:
        conn.execute("UPDATE orders SET status = 'blocked' WHERE id = ?", (order_id,))
        conn.commit()
        raise ValueError(f"Order has {unmapped} unmapped line(s)")

    missing_bom = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM order_lines ol
        WHERE ol.order_id = ?
          AND ol.sellable_sku_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM bom_components bc
              WHERE bc.sellable_sku_id = ol.sellable_sku_id
          )
        """,
        (order_id,),
    ).fetchone()["n"]
    if missing_bom:
        conn.execute("UPDATE orders SET status = 'blocked' WHERE id = ?", (order_id,))
        conn.commit()
        raise ValueError(f"Order has {missing_bom} mapped line(s) without a BOM")

    conn.execute(
        """
        DELETE FROM reservations
        WHERE order_line_id IN (
            SELECT id FROM order_lines WHERE order_id = ?
        )
        """,
        (order_id,),
    )
    lines = conn.execute(
        """
        SELECT ol.id AS order_line_id, ol.quantity AS line_qty, bc.item_id, bc.quantity AS component_qty
        FROM order_lines ol
        JOIN bom_components bc ON bc.sellable_sku_id = ol.sellable_sku_id
        WHERE ol.order_id = ?
        """,
        (order_id,),
    ).fetchall()
    for line in lines:
        conn.execute(
            """
            INSERT INTO reservations (order_line_id, item_id, quantity)
            VALUES (?, ?, ?)
            """,
            (line["order_line_id"], line["item_id"], line["line_qty"] * line["component_qty"]),
        )
    conn.execute("UPDATE orders SET status = 'reserved' WHERE id = ?", (order_id,))
    conn.commit()
    return {"reserved_components": len(lines)}
