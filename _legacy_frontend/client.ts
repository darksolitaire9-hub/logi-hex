// ~/types/client.ts
import type { Direction } from "../../lib/api/types";

export type ClientBalanceItem = {
  itemId: string | number;
  label: string;
  quantity: number;
};

export type ClientBalance = {
  clientId: string;
  clientName: string;
  total: number;
  items: ClientBalanceItem[];
};
