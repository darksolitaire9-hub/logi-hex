// frontend/lib/constants/language/inventory.ts

export enum StockState {
  IN_STOCK = "IN_STOCK",
  LOW = "LOW",
  EMPTY = "EMPTY",
}

export const STOCK_STATE_LABELS = {
  [StockState.IN_STOCK]: "In Stock",
  [StockState.LOW]: "Low",
  [StockState.EMPTY]: "Empty",
} as const;

export const LOW_STOCK_THRESHOLD = 3;

export const INVENTORY_DASHBOARD_LABELS = {
  in_stock: "In Stock", // Current quantity on hand
  low: "Low", // Stock is near zero and needs attention
  empty: "Empty", // Stock is exactly zero
  shrinkage: "Shrinkage",
} as const;
