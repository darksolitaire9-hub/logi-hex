import { ref } from "vue";
import type { TrackingItem } from "../../lib/api/types";
import {
  fetchTrackingItems,
  createTrackingItem,
  deleteTrackingItem,
} from "../../lib/api/logiHex";
import { useConfig } from "./useConfig";

const contentItems = ref<TrackingItem[]>([]);
let contentItemsFetched = false;

async function loadContentItems() {
  if (contentItemsFetched) return;
  const { config } = useConfig();
  const contentCategoryId = config.value.contentCategoryId;
  if (!contentCategoryId) return;
  contentItems.value = await fetchTrackingItems(contentCategoryId);
  contentItemsFetched = true;
}

async function addContentItem(label: string) {
  const trimmed = label.trim();
  if (!trimmed) return;
  const id = trimmed.toLowerCase().replace(/\s+/g, "-");

  const { config } = useConfig();
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

export function useContentItems() {
  return {
    contentItems,
    loadContentItems,
    addContentItem,
    removeContentItem,
  };
}
