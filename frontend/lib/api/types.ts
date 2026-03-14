// lib/api/types.ts

export type Direction = "OUT" | "IN";

export type Client = {
  id: string;
  name: string;
};

export interface AppConfigResponse {
  primary_category_id: string | null;
  primary_category_name: string | null;
  content_category_id: string | null;
  content_category_name: string | null;
  is_setup_complete: boolean;
}

export interface ContainerType {
  id: string;
  label: string;
}

export interface CreateContainerTypePayload {
  id: string;
  label: string;
}

export interface SummaryBalance {
  container_label: string;
  container_type_id: string;
  balance: number;
}

export interface SummaryClient {
  client_id: string;
  client_name: string;
  total_outstanding: number;
  balances: SummaryBalance[];
}

export interface SummaryResponse {
  clients: SummaryClient[];
  grand_total: number;
}

export interface LogMovementItem {
  itemId: string;
  quantity: number;
}

export interface LogMovementPayload {
  direction: Direction;
  clientName: string;
  primaryCategoryId: string;
  containerTypeId: string;
  quantity: number;
  contentTypeIds: string[];
  note?: string;
}

export type TrackingItem = {
  id: string;
  label: string;
  category_id: string;
};

export type CreateTrackingItemPayload = {
  id: string;
  label: string;
  category_id: string;
};

export type CreateTrackingCategoryPayload = {
  id: string;
  name: string;
  enforce_returns: boolean;
};

export type TrackingCategory = {
  id: string;
  name: string;
  enforce_returns: boolean;
};

// ---------------------------------------------------------------------------
// Client transactions
// ---------------------------------------------------------------------------

export interface ClientTransactionLineItem {
  tracking_item_id: string;
  label: string;
  quantity: number;
}

export interface ClientTransaction {
  transaction_id: string;
  direction: Direction;
  timestamp: string;
  notes: string | null;
  primary_items: ClientTransactionLineItem[];
  secondary_items: string[];
}

export interface ClientTransactionListResponse {
  client_id: string;
  client_name: string;
  transactions: ClientTransaction[];
}
