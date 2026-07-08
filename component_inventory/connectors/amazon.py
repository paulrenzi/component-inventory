import os

import requests

from .auth import amazon_sp_token


BASE_NA = "https://sellingpartnerapi-na.amazon.com"
MARKETPLACES = {
    "US": "ATVPDKIKX0DER",
    "CA": "A2EUQ1WTGCTBG2",
}


def get_listing(sku, marketplace="US"):
    seller_id = os.getenv("AMAZON_SELLER_ID", "AIXQYX7PF0CGV")
    mp_id = MARKETPLACES[marketplace]
    token = amazon_sp_token()
    resp = requests.get(
        f"{BASE_NA}/listings/2021-08-01/items/{seller_id}/{sku}",
        headers={"x-amz-access-token": token, "Accept": "application/json"},
        params={
            "marketplaceIds": mp_id,
            "includedData": "summaries,issues,offers,fulfillmentAvailability",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()

