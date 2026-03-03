// lib/api/types.ts

export type Direction = "OUT" | "IN";

export interface SummaryBalance {
  container_label: string;
  container_type_id: string;
  balance: number;
}

export interface SummaryClient {
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
  items: LogMovementItem[];
  contentTags: string[];
  note?: string;
}
