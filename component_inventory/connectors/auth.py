import os

import requests

from ..config import load_env


load_env()


def shopify_access_token():
    token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    if token:
        return token

    secret = os.getenv("SHOPIFY_CLIENT_SECRET")
    client_id = os.getenv("SHOPIFY_CLIENT_ID", "36b9b1427d999084a1690e7973b25469")
    if not secret:
        raise RuntimeError("Missing SHOPIFY_ACCESS_TOKEN or SHOPIFY_CLIENT_SECRET")

    resp = requests.post(
        "https://umbrellagaming.myshopify.com/admin/oauth/access_token",
        json={
            "client_id": client_id,
            "client_secret": secret,
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def walmart_token():
    resp = requests.post(
        "https://marketplace.walmartapis.com/v3/token",
        headers={
            "WM_SVC.NAME": "Component Inventory",
            "WM_QOS.CORRELATION_ID": "component-inventory",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        auth=(os.getenv("WALMART_CLIENT_ID"), os.getenv("WALMART_CLIENT_SECRET")),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def amazon_sp_token():
    resp = requests.post(
        "https://api.amazon.com/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.getenv("AMAZON_SP_REFRESH_TOKEN"),
            "client_id": os.getenv("AMAZON_SP_CLIENT_ID"),
            "client_secret": os.getenv("AMAZON_SP_CLIENT_SECRET"),
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

