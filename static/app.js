async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function table(id, columns, rows) {
  const el = document.getElementById(id);
  const head = columns.map(col => `<th>${col.label}</th>`).join("");
  const body = rows.map(row => {
    const cells = columns.map(col => `<td>${row[col.key] ?? ""}</td>`).join("");
    return `<tr>${cells}</tr>`;
  }).join("");
  el.innerHTML = `<thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="${columns.length}">No records</td></tr>`}</tbody>`;
}

async function refresh() {
  const data = await api("/api/summary");
  table("buildable", [
    { key: "sku", label: "SKU" },
    { key: "title", label: "Title" },
    { key: "buildable_qty", label: "Buildable" },
  ], data.buildable);
  table("lowStock", [
    { key: "sku", label: "Item" },
    { key: "name", label: "Name" },
    { key: "available", label: "Available" },
    { key: "reorder_point", label: "Reorder At" },
    { key: "target_stock", label: "Target" },
  ], data.low_stock);
  table("inbound", [
    { key: "sku", label: "Item" },
    { key: "name", label: "Name" },
    { key: "available", label: "Available" },
    { key: "inbound_quantity", label: "Inbound" },
    { key: "next_expected_at", label: "Expected" },
  ], data.inbound);
  table("workOrders", [
    { key: "id", label: "#" },
    { key: "status", label: "Status" },
    { key: "sku", label: "SKU" },
    { key: "title", label: "Title" },
    { key: "notes", label: "Notes" },
  ], data.work_orders);
  table("stock", [
    { key: "sku", label: "SKU" },
    { key: "name", label: "Name" },
    { key: "category", label: "Category" },
    { key: "on_hand", label: "On Hand" },
    { key: "reserved", label: "Reserved" },
    { key: "available", label: "Available" },
  ], data.stock);
}

document.getElementById("syncShopify").addEventListener("click", async () => {
  const btn = document.getElementById("syncShopify");
  btn.disabled = true;
  btn.textContent = "Syncing...";
  try {
    const result = await api("/api/sync/shopify/products", { method: "POST" });
    btn.textContent = `Synced ${result.imported}`;
    await refresh();
  } catch (err) {
    btn.textContent = "Sync failed";
    console.error(err);
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = "Sync Shopify";
    }, 1800);
  }
});

refresh();
