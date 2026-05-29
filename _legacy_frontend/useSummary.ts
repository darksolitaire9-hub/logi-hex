import { ref } from "vue";
import {
  fetchSummary,
  fetchClients,
  logMovementApi,
} from "../../lib/api/logiHex";
import type { LogMovementPayload } from "../../lib/api/types";
import type { ClientBalance } from "~/types/client";

export type Direction = "OUT" | "IN";

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
    clientId: c.client_id,
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
