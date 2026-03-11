import type {
  SummaryResponse,
  LogMovementPayload,
  ContainerType,
  CreateContainerTypePayload,
  TrackingItem,
  CreateTrackingItemPayload,
  Client,
} from "./types";
import { $fetch } from "ofetch";

// --- AUTH ---
export async function loginApi(
  username: string,
  password: string,
): Promise<{ access_token: string; token_type: string }> {
  return await $fetch("/api/auth/login", {
    method: "POST",
    body: new URLSearchParams({ username, password }),
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
}
// ---- End of auth ----
export async function fetchSummary(): Promise<SummaryResponse> {
  return await $fetch("/api/summary");
}

export async function logMovementApi(payload: LogMovementPayload) {
  const endpoint =
    payload.direction === "OUT"
      ? "/api/movements/issue"
      : "/api/movements/receive";

  return await $fetch(endpoint, {
    method: "POST",
    body: {
      name: payload.clientName,
      primary_category_id: payload.primaryCategoryId,
      container_type_id: payload.containerTypeId,
      quantity: payload.quantity,
      content_type_ids: payload.contentTypeIds,
      note: payload.note,
    },
  });
}

// Legacy container-types API (kept for now in case anything still uses it)
export async function fetchContainerTypes(): Promise<ContainerType[]> {
  return await $fetch("/api/container-types");
}

export async function createContainerType(
  payload: CreateContainerTypePayload,
): Promise<ContainerType> {
  return await $fetch("/api/container-types", {
    method: "POST",
    body: payload,
  });
}

// --- TRACKING CATEGORIES ---

export type CreateTrackingCategoryPayload = {
  id: string;
  name: string;
  enforce_returns: boolean;
};

export type TrackingCategory = {
  id: string;
  name: string;
  enforce_returns: boolean;
};

export async function createTrackingCategory(
  payload: CreateTrackingCategoryPayload,
): Promise<TrackingCategory> {
  return await $fetch("/api/tracking-categories", {
    method: "POST",
    body: payload,
  });
}

// --- TRACKING ITEMS ---

export async function fetchTrackingItems(
  categoryId: string,
): Promise<TrackingItem[]> {
  return await $fetch("/api/tracking-items", {
    query: { category_id: categoryId },
  });
}

export async function createTrackingItem(
  payload: CreateTrackingItemPayload,
): Promise<TrackingItem> {
  return await $fetch("/api/tracking-items", {
    method: "POST",
    body: payload,
  });
}

export async function deleteTrackingItem(itemId: string): Promise<void> {
  await $fetch(`/api/tracking-items/${itemId}`, {
    method: "DELETE",
  });
}

export async function fetchClients(): Promise<Client[]> {
  return await $fetch("/api/clients");
}
