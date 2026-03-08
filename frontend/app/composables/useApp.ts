// app/composables/useApp.ts
import { ref } from "vue";
import {
  fetchSummary,
  fetchContainerTypes,
  createContainerType,
  logMovementApi,
} from "../../lib/api/logiHex";

import type { ContainerType, LogMovementPayload } from "../../lib/api/types";

export type Direction = "OUT" | "IN";

type ContentItem = { id: string; label: string };
type ClientItem = { itemId: string | number; label: string; quantity: number };
type ClientBalance = {
  clientName: string;
  total: number;
  items: ClientItem[];
};

const contentItems = ref<ContentItem[]>([]);

// --- CONTAINER TYPES (backend-backed) ---
const containerTypes = ref<ContainerType[]>([]);
let containerTypesFetched = false;

async function loadContainerTypes() {
  if (containerTypesFetched) return;
  containerTypes.value = await fetchContainerTypes();
  containerTypesFetched = true;
}

async function addContainerType(label: string) {
  const trimmed = label.trim();
  if (!trimmed) return;

  // Simple ID derivation for now;  refine later
  const id = trimmed.toLowerCase().replace(/\s+/g, "-");
  const ct = await createContainerType({ id, label: trimmed });
  containerTypes.value.push(ct);
}

// --- CONFIG (persisted) ---
const CONFIG_KEY = "logi-hex-config";

function loadStoredConfig() {
  const base = {
    primaryCategoryName: "Primary containers",
    contentCategoryName: "Content tags",
    primaryCategoryId: null as string | null,
    contentCategoryId: null as string | null,
    isSetupComplete: false,
  };

  if (!import.meta.client) {
    return base;
  }

  const stored = localStorage.getItem(CONFIG_KEY);
  if (stored) {
    try {
      return { ...base, ...JSON.parse(stored) };
    } catch {
      // corrupted storage → fall back to base
    }
  }

  return base;
}

const config = ref(loadStoredConfig());

function updateConfig(newConfig: Partial<typeof config.value>) {
  config.value = { ...config.value, ...newConfig };
  if (import.meta.client) {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config.value));
  }
}

// --- SUMMARY ---
const clientBalances = ref<ClientBalance[]>([]);
const grandTotal = ref(0);

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
}

async function logMovement(payload: LogMovementPayload) {
  await logMovementApi(payload);
  await loadSummary();
}

export function useApp() {
  return {
    config,
    clientBalances,
    grandTotal,
    updateConfig,

    // container types
    containerTypes,
    loadContainerTypes,
    addContainerType,
    contentItems,
    // movements + summary
    logMovement,
    loadSummary,
  };
}
