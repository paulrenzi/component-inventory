# Component Inventory

Lightweight inventory, sourcing, and work-order system for Shopify-first sellers who build with hard-to-source components.

The first target use case is PC-component-heavy commerce: mini PCs, arcade cabinets, custom computers, kits, bundles, and refurbished hardware where stock availability depends on parts, substitutes, inbound purchases, and build capacity.

## Current MVP

- SQLite inventory ledger
- Component and sellable SKU model
- Bundle / bill-of-materials support
- Order reservations
- Work orders
- Purchase orders
- Supplier offers for sourcing decisions
- Supplier order tracking for Amazon, eBay, and Alibaba purchases
- Shopify import connector
- Walmart inventory update connector with dry-run default
- Amazon listing/inventory read connector
- Vanilla dashboard served by a Python stdlib HTTP server

## Quick Start

```powershell
python -m component_inventory.app --init-db --seed-demo
python -m component_inventory.app
```

Then open:

```text
http://127.0.0.1:8787
```

## Environment

Credentials are loaded from `.env` in this repo. You can also set `COMPONENT_INVENTORY_EXTRA_ENV` to point at another local env file.

Expected variables:

- `SHOPIFY_STORE`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `SHOPIFY_ACCESS_TOKEN`
- `WALMART_CLIENT_ID`
- `WALMART_CLIENT_SECRET`
- `AMAZON_SP_REFRESH_TOKEN`
- `AMAZON_SP_CLIENT_ID`
- `AMAZON_SP_CLIENT_SECRET`
- `AMAZON_SELLER_ID`

Marketplace writes must remain dry-run until explicitly enabled.

## Sourcing Channels

Amazon, eBay, and Alibaba are treated as supplier channels as well as possible sales channels. The app tracks supplier orders and inbound components separately from customer orders so hard-to-source PC parts can be reserved, replenished, and tied to build capacity.
