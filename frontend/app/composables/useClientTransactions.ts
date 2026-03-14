// composables/useClientTransactions.ts
import { ref } from "vue";
import { fetchClientTransactions } from "../../lib/api/logiHex";
import type { ClientTransaction } from "../../lib/api/types";

const selectedClientId = ref<string | null>(null);
const selectedClientName = ref<string | null>(null);
const transactions = ref<ClientTransaction[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

async function open(clientId: string, clientName: string) {
  selectedClientId.value = clientId;
  selectedClientName.value = clientName;
  loading.value = true;
  error.value = null;
  transactions.value = [];

  try {
    const res = await fetchClientTransactions(clientId);
    transactions.value = res.transactions;
  } catch (err: unknown) {
    if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = "Failed to load client transactions";
    }
  } finally {
    loading.value = false;
  }
}

function close() {
  selectedClientId.value = null;
  selectedClientName.value = null;
  transactions.value = [];
  error.value = null;
}

export function useClientTransactions() {
  return {
    selectedClientId,
    selectedClientName,
    transactions,
    loading,
    error,
    open,
    close,
  };
}
