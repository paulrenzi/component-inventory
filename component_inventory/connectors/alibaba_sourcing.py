from .suppliers import normalize_supplier_order


def parse_manual_alibaba_order(order_id, lines, ordered_at=None, expected_at=None, tracking_number=""):
    return normalize_supplier_order(
        supplier="Alibaba",
        order_id=order_id,
        status="ordered",
        ordered_at=ordered_at,
        expected_at=expected_at,
        tracking_number=tracking_number,
        lines=lines,
    )

