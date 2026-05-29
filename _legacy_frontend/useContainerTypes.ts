import { ref } from "vue";
import type { TrackingItem } from "../../lib/api/types";
import {
  fetchTrackingItems,
  createTrackingItem,
  deleteTrackingItem,
} from "../../lib/api/logiHex";
import { useConfig } from "./useConfig";

const containerTypes = ref<TrackingItem[]>([]);
let containerTypesFetched = false;

async function loadContainerTypes() {
  if (containerTypesFetched) return;
  const { config } = useConfig();
  const primaryCategoryId = config.value.primaryCategoryId;
  if (!primaryCategoryId) return;
  containerTypes.value = await fetchTrackingItems(primaryCategoryId);
  containerTypesFetched = true;
}

async function addContainerType(label: string) {
  const trimmed = label.trim();
  if (!trimmed) return;
  const id = trimmed.toLowerCase().replace(/\s+/g, "-");

  const { config } = useConfig();
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

export function useContainerTypes() {
  return {
    containerTypes,
    loadContainerTypes,
    addContainerType,
    removeContainerType,
  };
}
