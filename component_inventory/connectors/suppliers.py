def normalize_supplier_order(supplier, order_id, status, lines, ordered_at=None, expected_at=None, tracking_number="", raw=None):
    return {
        "supplier": supplier,
        "supplier_order_id": str(order_id),
        "status": status,
        "ordered_at": ordered_at,
        "expected_at": expected_at,
        "tracking_number": tracking_number or "",
        "raw": raw or {},
        "lines": lines,
    }


def upsert_supplier_order(conn, order):
    conn.execute(
        """
        INSERT INTO supplier_orders
          (supplier, supplier_order_id, status, ordered_at, expected_at, tracking_number, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(supplier, supplier_order_id) DO UPDATE SET
          status = excluded.status,
          ordered_at = excluded.ordered_at,
          expected_at = excluded.expected_at,
          tracking_number = excluded.tracking_number,
          raw_json = excluded.raw_json
        """,
        (
            order["supplier"],
            order["supplier_order_id"],
            order["status"],
            order.get("ordered_at"),
            order.get("expected_at"),
            order.get("tracking_number", ""),
            str(order.get("raw", {})),
        ),
    )
    supplier_order_pk = conn.execute(
        "SELECT id FROM supplier_orders WHERE supplier = ? AND supplier_order_id = ?",
        (order["supplier"], order["supplier_order_id"]),
    ).fetchone()["id"]
    for line in order["lines"]:
        conn.execute(
            """
            INSERT INTO supplier_order_lines
              (supplier_order_id, item_id, supplier_sku, title, quantity, unit_cost, line_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                supplier_order_pk,
                line.get("item_id"),
                line.get("supplier_sku", ""),
                line.get("title", ""),
                int(line.get("quantity", 1)),
                line.get("unit_cost"),
                line.get("line_status", order["status"]),
            ),
        )
    conn.commit()
    return supplier_order_pk

