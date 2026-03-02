// app/composables/useApp.ts
import { ref } from "vue";

export type Direction = "OUT" | "IN";

type PrimaryItem = { id: string; label: string };
type ContentItem = { id: string; label: string };
type ClientItem = { itemId: string | number; label: string; quantity: number };
type ClientBalance = {
  clientName: string;
  total: number;
  items: ClientItem[];
};

const config = ref({
  primaryCategoryName: "Primary containers",
  contentCategoryName: "Content tags",
  isSetupComplete: false,
});

const clientBalances = ref<ClientBalance[]>([
  {
    clientName: "Demo Client",
    total: 5,
    items: [
      { itemId: 1, label: "Large Box", quantity: 3 },
      { itemId: 2, label: "Small Box", quantity: 2 },
    ],
  },
]);

const grandTotal = ref(5);

const primaryItems = ref<PrimaryItem[]>([
  { id: "1", label: "Large Box" },
  { id: "2", label: "Small Box" },
]);

const contentItems = ref<ContentItem[]>([
  { id: "c1", label: "Frozen" },
  { id: "c2", label: "Fresh" },
]);

const allClientNames = ref<string[]>(["Demo Client"]);

function updateConfig(newConfig: Partial<typeof config.value>) {
  config.value = { ...config.value, ...newConfig };
}

function addPrimaryItem(label: string) {
  primaryItems.value.push({ id: crypto.randomUUID(), label });
}

function removePrimaryItem(id: string) {
  primaryItems.value = primaryItems.value.filter((i) => i.id !== id);
}

function addContentItem(label: string) {
  contentItems.value.push({ id: crypto.randomUUID(), label });
}

function removeContentItem(id: string) {
  contentItems.value = contentItems.value.filter((i) => i.id !== id);
}

function logMovement(payload: {
  direction: Direction;
  clientName: string;
  items: { itemId: string | number; quantity: number }[];
  contentTags: string[];
  note: string;
}) {
  console.log("Movement logged (stub):", payload);
}

export function useApp() {
  // never undefined now
  return {
    config,
    clientBalances,
    grandTotal,
    updateConfig,
    primaryItems,
    contentItems,
    allClientNames,
    addPrimaryItem,
    removePrimaryItem,
    addContentItem,
    removeContentItem,
    logMovement,
  };
}
