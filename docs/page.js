function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function renderTable(id, columns, rows) {
  const table = document.getElementById(id);
  const head = columns.map((column) => `<th>${column.label}</th>`).join("");
  const body = rows.map((row) => {
    const cells = columns.map((column) => `<td>${row[column.key] ?? ""}</td>`).join("");
    return `<tr>${cells}</tr>`;
  }).join("");
  table.innerHTML = `<thead><tr>${head}</tr></thead><tbody>${body}</tbody>`;
}

const data = window.demoData;

setText("buildableCount", data.buildable[0].buildable_now);
setText("inboundCount", data.inbound.reduce((total, row) => total + (Number(row.quantity) || 0), 0));
setText("vendorCount", data.vendors.length);
setText("offerCount", data.offers.filter((offer) => offer.status === "draft" || offer.status === "watching").length);

renderTable("buildable", [
  { key: "sku", label: "SKU" },
  { key: "title", label: "Product" },
  { key: "buildable_now", label: "Now" },
  { key: "buildable_after_inbound", label: "After inbound" },
  { key: "bottleneck", label: "Bottleneck" }
], data.buildable);

renderTable("stock", [
  { key: "sku", label: "SKU" },
  { key: "name", label: "Component" },
  { key: "category", label: "Type" },
  { key: "on_hand", label: "On hand" },
  { key: "reserved", label: "Reserved" },
  { key: "available", label: "Available" },
  { key: "target", label: "Target" }
], data.stock);

renderTable("inbound", [
  { key: "item", label: "Component" },
  { key: "supplier", label: "Supplier" },
  { key: "quantity", label: "Qty" },
  { key: "expected", label: "Expected" },
  { key: "status", label: "Status" }
], data.inbound);

renderTable("vendors", [
  { key: "marketplace", label: "Marketplace" },
  { key: "name", label: "Vendor" },
  { key: "preferred", label: "Preferred" },
  { key: "on_time", label: "On-time" },
  { key: "defects", label: "Defects" },
  { key: "avg_ship", label: "Avg ship" },
  { key: "notes", label: "Notes" }
], data.vendors);

renderTable("offers", [
  { key: "marketplace", label: "Marketplace" },
  { key: "item", label: "Component" },
  { key: "listing", label: "Listing" },
  { key: "ask", label: "Ask" },
  { key: "target_offer", label: "Target offer" },
  { key: "quantity", label: "Qty" },
  { key: "status", label: "Status" }
], data.offers);

