import os
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("COMPONENT_INVENTORY_DB", ROOT / "component_inventory.db"))


def load_env():
    paths = [ROOT / ".env"]
    extra_env = os.getenv("COMPONENT_INVENTORY_EXTRA_ENV")
    if extra_env:
        paths.append(Path(extra_env))
    for path in paths:
        if path.exists():
            load_dotenv(path)
            return path
    return None


def shopify_store():
    return os.getenv("SHOPIFY_STORE", "umbrellagaming.myshopify.com")


def shopify_api_version():
    return os.getenv("SHOPIFY_API_VERSION", "2024-10")
