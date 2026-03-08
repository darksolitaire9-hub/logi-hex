// app/composables/useApp.ts
import { ref } from "vue";
import {
  fetchSummary,
  fetchTrackingItems,
  createTrackingItem,
  deleteTrackingItem,
  logMovementApi,
  fetchClients,
} from "../../lib/api/logiHex";
import type { TrackingItem, LogMovementPayload } from "../../lib/api/types";

export type Direction = "OUT" | "IN";

type ClientItem = { itemId: string | number; label: string; quantity: number };
type ClientBalance = {
  clientName: string;
  total: number;
  items: ClientItem[];
};

const clientNames = ref<string[]>([]);

async function loadClientNames() {
  const clients = await fetchClients();
  clientNames.value = clients.map((c) => c.name);
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

// --- PRIMARY ITEMS (container types) via tracking items ---
const containerTypes = ref<TrackingItem[]>([]);
let containerTypesFetched = false;

async function loadContainerTypes() {
  if (containerTypesFetched) return;
  const primaryCategoryId = config.value.primaryCategoryId;
  if (!primaryCategoryId) return; // setup not complete yet
  containerTypes.value = await fetchTrackingItems(primaryCategoryId);
  containerTypesFetched = true;
}

async function addContainerType(label: string) {
  const trimmed = label.trim();
  if (!trimmed) return;
  const id = trimmed.toLowerCase().replace(/\s+/g, "-");

  const primaryCategoryId = config.value.primaryCategoryId;
  if (!primaryCategoryId) return;

  const item = await createTrackingItem({
    id,
    label: trimmed,
    category_id: primaryCategoryId,
  });
  containerTypes.value.push(item);
}

async function removeContainerType(id: string) {
  await deleteTrackingItem(id);
  containerTypes.value = containerTypes.value.filter((ct) => ct.id !== id);
}

// --- CONTENT ITEMS via tracking items ---
const contentItems = ref<TrackingItem[]>([]);
let contentItemsFetched = false;

async function loadContentItems() {
  if (contentItemsFetched) return;
  const contentCategoryId = config.value.contentCategoryId;
  if (!contentCategoryId) return; // setup not complete yet
  contentItems.value = await fetchTrackingItems(contentCategoryId);
  contentItemsFetched = true;
}

async function addContentItem(label: string) {
  const trimmed = label.trim();
  if (!trimmed) return;
  const id = trimmed.toLowerCase().replace(/\s+/g, "-");

  const contentCategoryId = config.value.contentCategoryId;
  if (!contentCategoryId) return;

  const item = await createTrackingItem({
    id,
    label: trimmed,
    category_id: contentCategoryId,
  });
  contentItems.value.push(item);
}

async function removeContentItem(id: string) {
  await deleteTrackingItem(id);
  contentItems.value = contentItems.value.filter((ci) => ci.id !== id);
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
  await loadClientNames();
}

// --- MOVEMENTS ---
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
    clientNames,

    // primary container types
    containerTypes,
    loadContainerTypes,
    addContainerType,
    removeContainerType,

    // content items
    contentItems,
    loadContentItems,
    addContentItem,
    removeContentItem,

    // movements + summary
    logMovement,
    loadSummary,
  };
}
