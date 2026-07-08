# Product Plan

## Positioning

Component Inventory is for Shopify-first sellers whose inventory is constrained by parts, sourcing, and build labor. The initial wedge is PC components because availability, substitutions, and vendor pricing are painful enough to justify daily use.

## First Customer

Umbrella Arcades is the reference customer:

- Shopify source of truth
- Amazon and Walmart channel pressure
- PC components with unstable supply
- Amazon, eBay, and Alibaba as primary sourcing channels
- Bundled/custom products
- Build-before-ship workflow
- Manual sourcing decisions

## MVP Promise

Know what you can sell, what you can build, and what is blocking fulfillment.

## Near-Term Features

1. Shopify product and order import
2. Component-level BOMs
3. Inventory ledger
4. Reservations against open orders
5. Buildable quantity by sellable SKU
6. Low-stock and target-stock views
7. Purchase order tracking
8. Supplier offer tracking
9. Supplier order tracking for Amazon, eBay, and Alibaba
10. Walmart inventory sync in dry-run mode
11. Amazon listing/inventory read mode

## Sourcing Workflow

Amazon, eBay, and Alibaba purchases should feed inbound inventory. A seller needs to know not only what is on hand, but what is already ordered, when it arrives, what builds it unblocks, and whether a supplier is reliable enough to use again.

The practical workflow:

1. Capture supplier order.
2. Map supplier line item to internal component.
3. Track expected arrival and tracking number.
4. Show buildable quantity now and after inbound stock.
5. Receive the order into the stock ledger.
6. Keep supplier price and lead-time history for reorder suggestions.

## Vendor Intelligence

The app should build a master vendor list over time, especially for eBay where seller quality varies widely and listings disappear. Vendor records should be durable, while listing offers should be treated as temporary opportunities.

Track these over time:

- Vendor marketplace, seller ID, display name, profile URL, country, preferred/blocked status
- On-time delivery rate
- Cancellation rate
- Defect/damaged/wrong-item rate
- Return/refund friction
- Average actual ship time
- Average landed cost by component
- Minimum reliable order quantity
- Whether the vendor accepts offers or bulk negotiation
- Whether repeat purchases are available
- Whether the seller uses consistent product titles/part numbers
- Notes about packaging quality, substitutions, and communication

For eBay specifically:

- Listing ID and URL
- Seller ID and feedback snapshot
- Item condition
- Quantity available
- Accepts-offers flag
- Best-offer history
- Counteroffer history
- Auto-order allowed flag
- Maximum allowed price
- Maximum allowed quantity
- Whether manual approval is required

Auto negotiation should start as draft-only:

1. Detect listings that accept offers.
2. Calculate target offer from price history, urgency, and available margin.
3. Draft the offer and message.
4. Require approval before submit.
5. Record accepted, rejected, expired, and countered attempts.

One-button ordering should only be enabled when:

- The item maps confidently to an internal component.
- Vendor is preferred or has enough positive history.
- Condition is allowed.
- Landed cost is below the configured ceiling.
- Quantity is within a configured limit.
- The listing has not changed since the last check.
- The order is still shown as a dry-run preview before final submission.

## Arcade Cabinet Component History

For wall-mounted arcade cabinets, the useful long-term data is broader than the BOM. Track:

- Cabinet shell source, finish/color, batch, defect rate
- Display model, panel size, resolution, mount pattern, dead-pixel/return history
- PC model/specs, CPU/GPU/RAM, thermal behavior, failure rate
- Storage brand/model/capacity, imaging success rate, DOA rate
- Control board, joysticks/buttons, encoder, wiring harness, firmware notes
- Controllers/accessories included per SKU
- Power supply, power strip, cabling, adapters
- Mounting hardware and packaging materials
- Labor time by build step
- Test results before shipment
- Substitutions used and whether they caused support tickets
- Component cost at time of order versus current replacement cost

## Later SaaS Requirements

- Shopify OAuth install flow
- Multi-tenant database
- User accounts and roles
- Billing
- Per-shop credentials
- Webhook ingestion
- Background jobs
- Audit log UI
- Safer marketplace write approvals
