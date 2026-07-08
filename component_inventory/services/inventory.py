from ..db import rows


def dashboard_summary(conn):
    stock = rows(conn, "SELECT * FROM item_stock ORDER BY available ASC, sku")
    low_stock = [item for item in stock if item["available"] <= item["reorder_point"]]
    open_orders = rows(conn, """
        SELECT o.id, o.channel, o.channel_order_id, o.customer_name, o.status, o.ordered_at,
               COUNT(ol.id) AS line_count
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
    return {
        "stock": stock,
        "low_stock": low_stock,
        "open_orders": open_orders,
        "work_orders": work_orders,
        "buildable": buildable,
        "inbound": inbound,
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


def reserve_order(conn, order_id):
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
