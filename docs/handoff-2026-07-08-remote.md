# Component Inventory Remote Handoff - 2026-07-08

## Current Objective

Paul wants to start using real Shopify/component inventory data and be able to view the working dashboard from an iPhone while away from the PC.

## Repo

- Local: `C:\Users\paulm\component-inventory`
- GitHub: `https://github.com/paulrenzi/component-inventory`
- Public demo: `https://paulrenzi.github.io/component-inventory/`
- Public design preview: `https://paulrenzi.github.io/component-inventory/preview.html`
- Public live redirect: `https://paulrenzi.github.io/component-inventory/live.html`

## Important Security Boundary

Do not put live credentials, customer/order data, raw live inventory, or API-backed data into GitHub Pages.

GitHub Pages is okay for:

- static demo
- static design preview with demo data
- redirect page to an authenticated live endpoint

GitHub Pages is not okay for:

- `.env` values
- Shopify/Walmart/Amazon tokens
- live order data
- live inventory exports
- browser-side password gates

## Latest Remote Access State

The local Python app now supports optional server-side login:

- Env var: `COMPONENT_INVENTORY_PASSWORD`
- Optional env var: `COMPONENT_INVENTORY_SESSION_SECRET`
- Login path: `/login`
- Cookie: `ci_session`
- Basic auth still works for scripts, but browser users should use `/login`.

Current live tunnel used this session:

- `https://oil-blue-any-filter.trycloudflare.com/login`

This is a Cloudflare quick tunnel to the local Python app on port `8792`. It is temporary and only stays up while the PC, app process, and `cloudflared` process keep running.

Do not assume the quick tunnel URL is permanent. If it is down, restart the app and tunnel.

## Current Running Setup From This Session

The authenticated app was started on:

- `http://127.0.0.1:8792`

The quick tunnel was created with:

- `cloudflared tunnel --url http://127.0.0.1:8792 --no-autoupdate`

`cloudflared.exe` was downloaded to:

- `C:\Users\paulm\AppData\Local\cloudflared\cloudflared.exe`

The password was not committed to the repo. If the next session needs it, ask Paul or use the current chat context if available. Do not add it to git.

## Code Added Since Original Handoff

Local app:

- `component_inventory/app.py`
  - `/api/catalog`
  - `/api/sync/shopify/orders`
  - `/api/orders/reserve`
  - `/api/bom-components`
  - `/api/channel-mappings`
  - optional form login via `/login`
- `component_inventory/connectors/shopify.py`
  - `import_orders()`
  - imports open Shopify orders into `orders` and `order_lines`
  - maps lines by SKU, Shopify variant ID, or `channel_mappings`
- `component_inventory/services/inventory.py`
  - catalog summary
  - BOM upsert
  - channel mapping upsert
  - idempotent reservation logic
  - vendor and offer dashboard data
- `static/`
  - local dashboard now has product sync, order sync, BOM mapping, channel mapping, open order reservation, vendor and offer tables

GitHub Pages:

- `docs/preview.html`
  - static dashboard preview with demo data for mobile/desktop design review
- `docs/live.html`
  - public redirect to current quick tunnel URL

Worker scaffold:

- `worker/`
  - attempted Cloudflare Worker/D1 path
  - D1 and Worker deploy were blocked by API token permissions
  - keep scaffold as reference, but do not rely on it until token permissions are fixed

## Cloudflare API Findings

Cloudflare API token exists in:

- `C:\Users\paulm\shopify-analytics\.env`
- `C:\Users\paulm\umbrella-arcades\.env`

Verified account:

- Account ID: `83f33c67294ca2f2f0869b63c1663b0e`

Token can read account identity, but failed for:

- D1 create
- Worker secrets
- Worker deploy

Observed errors:

- Cloudflare code `10000` authentication error
- Cloudflare code `9106` memberships auth failure

Conclusion: token is not sufficient for permanent Worker/D1 deployment. Workaround used quick tunnel plus server-side login.

## Verification Completed

Local checks passed:

- `python -m compileall component_inventory`
- `node --check static/app.js`
- `node --check docs/preview.js`
- `node --check worker/src/index.js`

Remote/tunnel checks passed:

- public `/login` returns `200`
- public `/` redirects to `/login` when unauthenticated
- login form POST returns `302`
- dashboard `/` returns `200` after cookie login
- `/api/summary` returns live JSON after cookie login

GitHub Pages checks:

- `https://paulrenzi.github.io/component-inventory/preview.html` returns `200 OK`
- `https://paulrenzi.github.io/component-inventory/live.html` returns `200 OK`

## Recommended Next Step

Start a new session soon. The context now includes product direction, local app changes, remote access attempts, Cloudflare permission blockers, and live-data next steps. A fresh session should continue from this handoff.

Next implementation priority:

1. Use real Shopify data through the local authenticated app.
2. Press `Sync Products` first.
3. Press `Sync Orders` second.
4. Review unmapped open order rows.
5. Add missing BOM lines and channel mappings.
6. Reserve only orders whose lines are mapped and have BOMs.

Do not sync marketplace writes yet. Walmart and Amazon writes should remain dry-run until explicitly enabled.

## Best Permanent Remote Path

Preferred:

- Named Cloudflare Tunnel
- Cloudflare Access login
- Local Python app as origin
- No live data on GitHub Pages

Alternative:

- Worker + D1 backend after Cloudflare token permissions are fixed

Avoid:

- static GitHub Pages password gates
- committing passwords or live data to git
- exposing the local app without server-side auth

