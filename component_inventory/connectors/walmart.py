import requests

from .auth import walmart_token


BASE = "https://marketplace.walmartapis.com/v3"


def headers(token=None):
    token = token or walmart_token()
    return {
        "WM_SEC.ACCESS_TOKEN": token,
        "WM_SVC.NAME": "Component Inventory",
        "WM_QOS.CORRELATION_ID": "component-inventory",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def set_inventory(sku, quantity, dry_run=True):
    payload = {
        "sku": sku,
        "quantity": {
            "unit": "EACH",
            "amount": int(quantity),
        },
    }
    if dry_run:
        return {"dry_run": True, "sku": sku, "quantity": int(quantity), "payload": payload}

    resp = requests.put(
        f"{BASE}/inventory",
        headers=headers(),
        params={"sku": sku},
        json=payload,
        timeout=30,
    )
    return {"status_code": resp.status_code, "body": resp.text[:500]}

