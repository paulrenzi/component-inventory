window.demoData = {
  buildable: [
    {
      sku: "UA-ARCADE-BLK-2TB",
      title: "Black 2TB Wall Arcade Gaming PC",
      buildable_now: 2,
      buildable_after_inbound: 3,
      bottleneck: "Black wall arcade cabinet shell"
    }
  ],
  stock: [
    { sku: "CAB-WALL-BLK", name: "Black wall arcade cabinet shell", category: "fabricated part", on_hand: 2, reserved: 0, available: 2, target: 4 },
    { sku: "MINI-PC-BLK", name: "Black mini PC barebones", category: "PC component", on_hand: 3, reserved: 0, available: 3, target: 8 },
    { sku: "PWR-KIT", name: "Power strip and cabling kit", category: "component", on_hand: 6, reserved: 0, available: 6, target: 10 },
    { sku: "SSD-2TB-NVME", name: "2TB NVMe SSD", category: "PC component", on_hand: 7, reserved: 0, available: 7, target: 20 },
    { sku: "CTRL-8BITDO-U2", name: "8BitDo Ultimate 2 controller", category: "accessory", on_hand: 10, reserved: 0, available: 10, target: 12 }
  ],
  inbound: [
    { item: "2TB NVMe SSD", supplier: "Amazon", quantity: 8, expected: "2026-07-10", status: "shipped" },
    { item: "Black mini PC barebones", supplier: "eBay", quantity: 4, expected: "quote pending", status: "negotiating" },
    { item: "Cabinet shell batch", supplier: "Alibaba", quantity: 10, expected: "lead time needed", status: "sourcing" }
  ],
  vendors: [
    { marketplace: "eBay", name: "Demo eBay Mini PC Seller", preferred: "yes", on_time: "92%", defects: "1.8%", avg_ship: "4.6 days", notes: "Good refurb mini PC source" },
    { marketplace: "Amazon", name: "SSD marketplace source", preferred: "watch", on_time: "fast", defects: "track DOA", avg_ship: "2 days", notes: "Price swings frequently" },
    { marketplace: "Alibaba", name: "Cabinet fabrication supplier", preferred: "candidate", on_time: "unknown", defects: "track batch", avg_ship: "30+ days", notes: "Useful for planned batches" }
  ],
  offers: [
    { marketplace: "eBay", item: "Black mini PC barebones", listing: "DEMO-LISTING-MINI-PC", ask: "$219.99", target_offer: "$188.00", quantity: 4, status: "draft" },
    { marketplace: "eBay", item: "2TB NVMe SSD lot", listing: "search watch", ask: "varies", target_offer: "margin based", quantity: 10, status: "watching" }
  ]
};

