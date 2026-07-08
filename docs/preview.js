const summary = {
  buildable: [
    { sku: "UA-ARCADE-BLK-2TB", title: "Black 2TB Wall Arcade Cabinet", buildable_qty: 2 },
    { sku: "UA-ARCADE-WHT-2TB", title: "White 2TB Wall Arcade Cabinet", buildable_qty: 1 },
    { sku: "UA-MINI-PC-2TB", title: "2TB Outbreak Mini PC", buildable_qty: 5 },
  ],
  stock: [
    { sku: "CAB-WALL-BLK", name: "Black wall cabinet shell", category: "fabricated_part", on_hand: 2, reserved: 0, available: 2, target_stock: 4 },
    { sku: "CAB-WALL-WHT", name: "White wall cabinet shell", category: "fabricated_part", on_hand: 1, reserved: 0, available: 1, target_stock: 4 },
    { sku: "MINI-PC-BLK", name: "Black mini PC barebones", category: "pc_component", on_hand: 3, reserved: 1, available: 2, target_stock: 8 },
    { sku: "SSD-2TB-NVME", name: "2TB NVMe SSD", category: "pc_component", on_hand: 7, reserved: 2, available: 5, target_stock: 20 },
    { sku: "CTRL-8BITDO-U2", name: "8BitDo Ultimate 2 controller", category: "accessory", on_hand: 10, reserved: 4, available: 6, target_stock: 12 },
    { sku: "PWR-KIT", name: "Power strip and cabling kit", category: "component", on_hand: 6, reserved: 2, available: 4, target_stock: 10 },
  ],
  inbound: [
    { sku: "SSD-2TB-NVME", name: "2TB NVMe SSD", inbound_quantity: 8, next_expected_at: "2026-07-10" },
    { sku: "MINI-PC-BLK", name: "Black mini PC barebones", inbound_quantity: 4, next_expected_at: "2026-07-14" },
    { sku: "CAB-WALL-BLK", name: "Black wall cabinet shell", inbound_quantity: 10, next_expected_at: "2026-08-05" },
  ],
  open_orders: [
    { id: 1, channel_order_id: "SHOP-1047", customer_name: "Preview Customer", status: "open", line_count: 1, unmapped_line_count: 0, missing_bom_line_count: 0 },
    { id: 2, channel_order_id: "SHOP-1048", customer_name: "Needs Mapping", status: "blocked", line_count: 1, unmapped_line_count: 1, missing_bom_line_count: 0 },
  ],
  vendors: [
    { marketplace: "eBay", name: "Demo eBay Mini PC Seller", preferred: "yes", on_time: "92%", defects: "1.8%", avg_ship: "4.6 days", notes: "Good refurb mini PC source" },
    { marketplace: "Amazon", name: "SSD marketplace source", preferred: "watch", on_time: "fast", defects: "track DOA", avg_ship: "2 days", notes: "Price swings frequently" },
  ],
  offers: [
    { marketplace: "eBay", item: "Black mini PC barebones", listing: "DEMO-LISTING-MINI-PC", ask: "$219.99", target_offer: "$188.00", quantity: 4, status: "draft" },
    { marketplace: "eBay", item: "2TB NVMe SSD lot", listing: "search watch", ask: "varies", target_offer: "margin based", quantity: 10, status: "watching" },
  ],
};

const catalog = {
  sellables: [
    { sku: "UA-ARCADE-BLK-2TB", title: "Black 2TB Wall Arcade Cabinet", status: "active", bom_lines: 5, channel_links: 2 },
    { sku: "UA-ARCADE-WHT-2TB", title: "White 2TB Wall Arcade Cabinet", status: "active", bom_lines: 5, channel_links: 1 },
    { sku: "UA-MINI-PC-2TB", title: "2TB Outbreak Mini PC", status: "active", bom_lines: 2, channel_links: 1 },
  ],
  items: [
    { sku: "CAB-WALL-BLK", name: "Black wall cabinet shell" },
    { sku: "CAB-WALL-WHT", name: "White wall cabinet shell" },
    { sku: "MINI-PC-BLK", name: "Black mini PC barebones" },
    { sku: "SSD-2TB-NVME", name: "2TB NVMe SSD" },
    { sku: "CTRL-8BITDO-U2", name: "8BitDo Ultimate 2 controller" },
    { sku: "PWR-KIT", name: "Power strip and cabling kit" },
  ],
  bom_components: [
    { sellable_sku: "UA-ARCADE-BLK-2TB", item_sku: "CAB-WALL-BLK", quantity: 1, is_substitutable: 0 },
    { sellable_sku: "UA-ARCADE-BLK-2TB", item_sku: "MINI-PC-BLK", quantity: 1, is_substitutable: 1 },
    { sellable_sku: "UA-ARCADE-BLK-2TB", item_sku: "SSD-2TB-NVME", quantity: 1, is_substitutable: 1 },
    { sellable_sku: "UA-ARCADE-BLK-2TB", item_sku: "CTRL-8BITDO-U2", quantity: 2, is_substitutable: 0 },
    { sellable_sku: "UA-ARCADE-BLK-2TB", item_sku: "PWR-KIT", quantity: 1, is_substitutable: 0 },
  ],
  channel_mappings: [
    { channel: "Shopify", channel_sku: "UA-ARCADE-BLK-2TB", sellable_sku: "UA-ARCADE-BLK-2TB", item_sku: "" },
    { channel: "Walmart", channel_sku: "black-2tb-wall-arcade", sellable_sku: "UA-ARCADE-BLK-2TB", item_sku: "" },
  ],
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function table(id, columns, rows) {
  const el = document.getElementById(id);
  const head = columns.map((col) => `<th>${escapeHtml(col.label)}</th>`).join("");
  const body = rows.length
    ? rows.map((row) => `<tr>${columns.map((col) => `<td>${col.render ? col.render(row) : escapeHtml(row[col.key])}</td>`).join("")}</tr>`).join("")
    : `<tr><td colspan="${columns.length}">No records</td></tr>`;
  el.innerHTML = `<thead><tr>${head}</tr></thead><tbody>${body}</tbody>`;
}

function selectOptions(rows, valueKey) {
  return rows.map((row) => `<option value="${escapeHtml(row[valueKey])}">${escapeHtml(row[valueKey])}</option>`).join("");
}

function setStatus(message, kind = "info") {
  const el = document.getElementById("syncStatus");
  el.dataset.kind = kind;
  el.textContent = message;
}

function render() {
  document.getElementById("buildableCount").textContent = summary.buildable.length;
  document.getElementById("inboundCount").textContent = summary.inbound.reduce((total, row) => total + Number(row.inbound_quantity || 0), 0);
  document.getElementById("vendorCount").textContent = summary.vendors.length;
  document.getElementById("offerCount").textContent = summary.offers.filter((offer) => offer.status === "draft" || offer.status === "watching").length;
  document.getElementById("catalogCount").textContent = catalog.sellables.length;

  table("buildable", [
    { key: "sku", label: "SKU" },
    { key: "title", label: "Product" },
    { key: "buildable_qty", label: "Now" },
  ], summary.buildable);

  table("stock", [
    { key: "sku", label: "SKU" },
    { key: "name", label: "Component" },
    { key: "category", label: "Type" },
    { key: "on_hand", label: "On hand" },
    { key: "reserved", label: "Reserved" },
    { key: "available", label: "Available" },
    { key: "target_stock", label: "Target" },
  ], summary.stock);

  table("inbound", [
    { key: "name", label: "Component" },
    { key: "sku", label: "SKU" },
    { key: "inbound_quantity", label: "Qty" },
    { key: "next_expected_at", label: "Expected" },
  ], summary.inbound);

  table("sellables", [
    { key: "sku", label: "SKU" },
    { key: "title", label: "Title" },
    { key: "status", label: "Status" },
    { key: "bom_lines", label: "BOM lines" },
    { key: "channel_links", label: "Channel links" },
  ], catalog.sellables);

  table("openOrders", [
    { key: "channel_order_id", label: "Order" },
    { key: "customer_name", label: "Customer" },
    { key: "status", label: "Status" },
    { key: "line_count", label: "Lines" },
    { key: "unmapped_line_count", label: "Unmapped" },
    { key: "missing_bom_line_count", label: "Missing BOM" },
    { key: "id", label: "Action", render: (row) => `<button class="smallButton"${row.status === "blocked" ? " disabled" : ""}>Reserve</button>` },
  ], summary.open_orders);

  table("bomComponents", [
    { key: "sellable_sku", label: "Sellable SKU" },
    { key: "item_sku", label: "Component SKU" },
    { key: "quantity", label: "Qty" },
    { key: "is_substitutable", label: "Sub?" },
  ], catalog.bom_components);

  table("channelMappings", [
    { key: "channel", label: "Channel" },
    { key: "channel_sku", label: "Channel SKU" },
    { key: "sellable_sku", label: "Sellable" },
    { key: "item_sku", label: "Component" },
  ], catalog.channel_mappings);

  table("vendors", [
    { key: "marketplace", label: "Marketplace" },
    { key: "name", label: "Vendor" },
    { key: "preferred", label: "Preferred" },
    { key: "on_time", label: "On-time" },
    { key: "defects", label: "Defects" },
    { key: "avg_ship", label: "Avg ship" },
    { key: "notes", label: "Notes" },
  ], summary.vendors);

  table("offers", [
    { key: "marketplace", label: "Marketplace" },
    { key: "item", label: "Component" },
    { key: "listing", label: "Listing" },
    { key: "ask", label: "Ask" },
    { key: "target_offer", label: "Target offer" },
    { key: "quantity", label: "Qty" },
    { key: "status", label: "Status" },
  ], summary.offers);

  document.getElementById("bomSellableSku").innerHTML = selectOptions(catalog.sellables, "sku");
  document.getElementById("mappingSellableSku").innerHTML = `<option value="">None</option>${selectOptions(catalog.sellables, "sku")}`;
  document.getElementById("bomItemSku").innerHTML = selectOptions(catalog.items, "sku");
  document.getElementById("mappingItemSku").innerHTML = `<option value="">None</option>${selectOptions(catalog.items, "sku")}`;
}

document.getElementById("bomForm").addEventListener("submit", (event) => {
  event.preventDefault();
  setStatus("Preview only: BOM save is disabled.", "busy");
});

document.getElementById("mappingForm").addEventListener("submit", (event) => {
  event.preventDefault();
  setStatus("Preview only: mapping save is disabled.", "busy");
});

render();
