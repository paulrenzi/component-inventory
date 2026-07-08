async function api(path, options) {
  const res = await fetch(path, {
    headers: options?.body ? { "Content-Type": "application/json" } : undefined,
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
}

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
    ? rows.map((row) => {
        const cells = columns.map((col) => {
          const value = col.render ? col.render(row) : escapeHtml(row[col.key]);
          return `<td>${value}</td>`;
        }).join("");
        return `<tr>${cells}</tr>`;
      }).join("")
    : `<tr><td colspan="${columns.length}">No records</td></tr>`;
  el.innerHTML = `<thead><tr>${head}</tr></thead><tbody>${body}</tbody>`;
}

function selectOptions(rows, valueKey, labelKey) {
  return rows.map((row) => `<option value="${escapeHtml(row[valueKey])}">${escapeHtml(row[labelKey])}</option>`).join("");
}

function setStatus(message, kind = "info") {
  const el = document.getElementById("syncStatus");
  el.dataset.kind = kind;
  el.textContent = message;
}

async function refresh() {
  const [summary, catalog] = await Promise.all([
    api("/api/summary"),
    api("/api/catalog"),
  ]);

  document.getElementById("buildableCount").textContent = summary.buildable.length;
  document.getElementById("inboundCount").textContent = summary.inbound.reduce((total, row) => total + (Number(row.inbound_quantity) || 0), 0);
  document.getElementById("vendorCount").textContent = summary.vendors.length;
  document.getElementById("offerCount").textContent = summary.offers.filter((offer) => offer.status === "draft" || offer.status === "watching").length;
  document.getElementById("catalogCount").textContent = catalog.sellables.length;

  table("buildable", [
    { key: "sku", label: "SKU" },
    { key: "title", label: "Product" },
    { key: "buildable_qty", label: "Now" },
  ], summary.buildable.map((row) => ({ ...row, buildable_qty: row.buildable_qty ?? row.buildable_now ?? 0 })));

  table("stock", [
    { key: "sku", label: "SKU" },
    { key: "name", label: "Component" },
    { key: "category", label: "Type" },
    { key: "on_hand", label: "On hand" },
    { key: "reserved", label: "Reserved" },
    { key: "available", label: "Available" },
    { key: "target_stock", label: "Target" },
  ], summary.stock.map((row) => ({ ...row, target_stock: row.target_stock ?? row.target ?? 0 })));

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
    {
      key: "id",
      label: "Action",
      render: (row) => {
        const blocked = Number(row.unmapped_line_count || 0) > 0 || Number(row.missing_bom_line_count || 0) > 0;
        const disabled = row.status === "reserved" || blocked ? " disabled" : "";
        return `<button class="smallButton" data-reserve-order="${escapeHtml(row.id)}"${disabled}>Reserve</button>`;
      },
    },
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
  ], summary.vendors || []);

  table("offers", [
    { key: "marketplace", label: "Marketplace" },
    { key: "item", label: "Component" },
    { key: "listing", label: "Listing" },
    { key: "ask", label: "Ask" },
    { key: "target_offer", label: "Target offer" },
    { key: "quantity", label: "Qty" },
    { key: "status", label: "Status" },
  ], summary.offers || []);

  const skuOptions = selectOptions(catalog.sellables, "sku", "sku");
  const itemOptions = selectOptions(catalog.items, "sku", "sku");
  document.getElementById("bomSellableSku").innerHTML = skuOptions;
  document.getElementById("mappingSellableSku").innerHTML = `<option value="">None</option>${skuOptions}`;
  document.getElementById("bomItemSku").innerHTML = itemOptions;
  document.getElementById("mappingItemSku").innerHTML = `<option value="">None</option>${itemOptions}`;

  if (catalog.sellables.length > 0) {
    document.getElementById("mappingSellableSku").value = catalog.sellables[0].sku;
    document.getElementById("bomSellableSku").value = catalog.sellables[0].sku;
  }
  if (catalog.items.length > 0) {
    document.getElementById("bomItemSku").value = catalog.items[0].sku;
    document.getElementById("mappingItemSku").value = "";
  }
}

document.getElementById("syncShopify").addEventListener("click", async () => {
  const btn = document.getElementById("syncShopify");
  btn.disabled = true;
  btn.textContent = "Syncing...";
  setStatus("Syncing Shopify variants...", "busy");
  try {
    const result = await api("/api/sync/shopify/products", { method: "POST" });
    setStatus(`Synced ${result.imported} Shopify variants.`, "ok");
    await refresh();
  } catch (err) {
    setStatus(`Sync failed: ${err.message}`, "error");
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = "Sync Products";
    }, 1200);
  }
});

document.getElementById("syncShopifyOrders").addEventListener("click", async () => {
  const btn = document.getElementById("syncShopifyOrders");
  btn.disabled = true;
  btn.textContent = "Syncing...";
  setStatus("Syncing Shopify open orders...", "busy");
  try {
    const result = await api("/api/sync/shopify/orders", { method: "POST" });
    setStatus(`Synced ${result.imported} Shopify orders.`, "ok");
    await refresh();
  } catch (err) {
    setStatus(`Order sync failed: ${err.message}`, "error");
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = "Sync Orders";
    }, 1200);
  }
});

document.getElementById("openOrders").addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-reserve-order]");
  if (!btn) return;
  btn.disabled = true;
  setStatus("Reserving order components...", "busy");
  try {
    const result = await api("/api/orders/reserve", {
      method: "POST",
      body: JSON.stringify({ order_id: btn.dataset.reserveOrder }),
    });
    setStatus(`Reserved ${result.reserved_components} component rows.`, "ok");
    await refresh();
  } catch (err) {
    setStatus(`Reserve failed: ${err.message}`, "error");
    await refresh();
  }
});

document.getElementById("bomForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    sellable_sku: document.getElementById("bomSellableSku").value,
    item_sku: document.getElementById("bomItemSku").value,
    quantity: Number(document.getElementById("bomQuantity").value || 1),
    is_substitutable: document.getElementById("bomSubstitutable").checked,
  };
  setStatus("Saving BOM line...", "busy");
  try {
    await api("/api/bom-components", { method: "POST", body: JSON.stringify(payload) });
    setStatus("BOM line saved.", "ok");
    await refresh();
  } catch (err) {
    setStatus(`BOM save failed: ${err.message}`, "error");
  }
});

document.getElementById("mappingForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    channel: document.getElementById("mappingChannel").value.trim(),
    channel_sku: document.getElementById("mappingChannelSku").value.trim(),
    sellable_sku: document.getElementById("mappingSellableSku").value,
    item_sku: document.getElementById("mappingItemSku").value,
  };
  setStatus("Saving channel mapping...", "busy");
  try {
    await api("/api/channel-mappings", { method: "POST", body: JSON.stringify(payload) });
    setStatus("Channel mapping saved.", "ok");
    await refresh();
  } catch (err) {
    setStatus(`Mapping save failed: ${err.message}`, "error");
  }
});

refresh().catch((err) => {
  setStatus(`Load failed: ${err.message}`, "error");
});
