CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY,
  sku TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'component',
  unit TEXT NOT NULL DEFAULT 'each',
  reorder_point INTEGER NOT NULL DEFAULT 0,
  target_stock INTEGER NOT NULL DEFAULT 0,
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sellable_skus (
  id INTEGER PRIMARY KEY,
  sku TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  shopify_variant_id TEXT,
  shopify_inventory_item_id TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bom_components (
  id INTEGER PRIMARY KEY,
  sellable_sku_id INTEGER NOT NULL REFERENCES sellable_skus(id) ON DELETE CASCADE,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  is_substitutable INTEGER NOT NULL DEFAULT 0,
  UNIQUE (sellable_sku_id, item_id)
);

CREATE TABLE IF NOT EXISTS channel_mappings (
  id INTEGER PRIMARY KEY,
  channel TEXT NOT NULL,
  channel_sku TEXT NOT NULL,
  sellable_sku_id INTEGER REFERENCES sellable_skus(id) ON DELETE CASCADE,
  item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
  UNIQUE (channel, channel_sku)
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY,
  channel TEXT NOT NULL,
  channel_order_id TEXT NOT NULL,
  customer_name TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open',
  ordered_at TEXT,
  raw_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (channel, channel_order_id)
);

CREATE TABLE IF NOT EXISTS order_lines (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  sellable_sku_id INTEGER REFERENCES sellable_skus(id) ON DELETE SET NULL,
  channel_sku TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  quantity INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS stock_movements (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
  quantity_delta INTEGER NOT NULL,
  reason TEXT NOT NULL,
  reference_type TEXT NOT NULL DEFAULT '',
  reference_id TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reservations (
  id INTEGER PRIMARY KEY,
  order_line_id INTEGER NOT NULL REFERENCES order_lines(id) ON DELETE CASCADE,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  status TEXT NOT NULL DEFAULT 'reserved',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS work_orders (
  id INTEGER PRIMARY KEY,
  order_line_id INTEGER REFERENCES order_lines(id) ON DELETE SET NULL,
  sellable_sku_id INTEGER REFERENCES sellable_skus(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'open',
  priority INTEGER NOT NULL DEFAULT 0,
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS supplier_orders (
  id INTEGER PRIMARY KEY,
  supplier TEXT NOT NULL,
  supplier_order_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ordered',
  ordered_at TEXT,
  expected_at TEXT,
  tracking_number TEXT NOT NULL DEFAULT '',
  raw_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (supplier, supplier_order_id)
);

CREATE TABLE IF NOT EXISTS supplier_order_lines (
  id INTEGER PRIMARY KEY,
  supplier_order_id INTEGER NOT NULL REFERENCES supplier_orders(id) ON DELETE CASCADE,
  item_id INTEGER REFERENCES items(id) ON DELETE SET NULL,
  supplier_sku TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_cost REAL,
  line_status TEXT NOT NULL DEFAULT 'ordered'
);

CREATE TABLE IF NOT EXISTS vendors (
  id INTEGER PRIMARY KEY,
  marketplace TEXT NOT NULL,
  vendor_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  vendor_type TEXT NOT NULL DEFAULT 'seller',
  profile_url TEXT NOT NULL DEFAULT '',
  country TEXT NOT NULL DEFAULT '',
  preferred INTEGER NOT NULL DEFAULT 0,
  blocked INTEGER NOT NULL DEFAULT 0,
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (marketplace, vendor_key)
);

CREATE TABLE IF NOT EXISTS vendor_metrics (
  id INTEGER PRIMARY KEY,
  vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  metric_date TEXT NOT NULL DEFAULT CURRENT_DATE,
  orders_count INTEGER NOT NULL DEFAULT 0,
  items_count INTEGER NOT NULL DEFAULT 0,
  on_time_count INTEGER NOT NULL DEFAULT 0,
  defect_count INTEGER NOT NULL DEFAULT 0,
  cancellation_count INTEGER NOT NULL DEFAULT 0,
  average_ship_days REAL,
  average_landed_cost REAL,
  return_rate REAL,
  notes TEXT NOT NULL DEFAULT '',
  UNIQUE (vendor_id, metric_date)
);

CREATE TABLE IF NOT EXISTS listing_offers (
  id INTEGER PRIMARY KEY,
  item_id INTEGER REFERENCES items(id) ON DELETE SET NULL,
  vendor_id INTEGER REFERENCES vendors(id) ON DELETE SET NULL,
  marketplace TEXT NOT NULL,
  listing_id TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  url TEXT NOT NULL DEFAULT '',
  condition TEXT NOT NULL DEFAULT '',
  price REAL,
  shipping_cost REAL,
  quantity_available INTEGER,
  accepts_offers INTEGER NOT NULL DEFAULT 0,
  auto_order_allowed INTEGER NOT NULL DEFAULT 0,
  listing_status TEXT NOT NULL DEFAULT 'active',
  checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (marketplace, listing_id)
);

CREATE TABLE IF NOT EXISTS negotiation_attempts (
  id INTEGER PRIMARY KEY,
  listing_offer_id INTEGER NOT NULL REFERENCES listing_offers(id) ON DELETE CASCADE,
  vendor_id INTEGER REFERENCES vendors(id) ON DELETE SET NULL,
  proposed_price REAL NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'draft',
  message TEXT NOT NULL DEFAULT '',
  response_price REAL,
  response_message TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  responded_at TEXT
);
