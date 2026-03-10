import { ref } from "vue";
import {
  fetchSummary,
  fetchClients,
  logMovementApi,
} from "../../lib/api/logiHex";
import type { LogMovementPayload } from "../../lib/api/types";

export type Direction = "OUT" | "IN";

type ClientItem = { itemId: string | number; label: string; quantity: number };
type ClientBalance = {
  clientName: string;
  total: number;
  items: ClientItem[];
};

const clientBalances = ref<ClientBalance[]>([]);
const grandTotal = ref(0);
const clientNames = ref<string[]>([]);

async function loadClientNames() {
  const clients = await fetchClients();
  clientNames.value = clients.map((c) => c.name);
}

async function loadSummary() {
  const data = await fetchSummary();
  clientBalances.value = data.clients.map((c) => ({
    clientName: c.client_name,
    total: c.total_outstanding,
    items: c.balances.map((b) => ({
      itemId: b.container_type_id,
      label: b.container_label,
      quantity: b.balance,
    })),
  }));
  grandTotal.value = data.grand_total;
  await loadClientNames();
}

async function logMovement(payload: LogMovementPayload) {
  await logMovementApi(payload);
  await loadSummary();
}

export function useSummary() {
  return {
    clientBalances,
    grandTotal,
    clientNames,
    loadSummary,
    logMovement,
  };
}
