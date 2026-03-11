// lib/api/logiHex.ts
import type {
  SummaryResponse,
  LogMovementPayload,
  ContainerType,
  CreateContainerTypePayload,
  TrackingItem,
  CreateTrackingItemPayload,
  CreateTrackingCategoryPayload,
  TrackingCategory,
  Client,
} from "./types";

import { useApiClient } from "~/composables/useApiClient";
// --- SUMMARY ---
export async function fetchSummary(): Promise<SummaryResponse> {
  return await useApiClient()("/api/summary");
}

// --- MOVEMENTS ---
export async function logMovementApi(payload: LogMovementPayload) {
  const endpoint =
    payload.direction === "OUT"
      ? "/api/movements/issue"
      : "/api/movements/receive";

  return await useApiClient()(endpoint, {
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

// --- CONTAINER TYPES ---
export async function fetchContainerTypes(): Promise<ContainerType[]> {
  return await useApiClient()("/api/container-types");
}

export async function createContainerType(
  payload: CreateContainerTypePayload,
): Promise<ContainerType> {
  return await useApiClient()("/api/container-types", {
    method: "POST",
    body: payload,
  });
}

// --- TRACKING CATEGORIES ---
export async function createTrackingCategory(
  payload: CreateTrackingCategoryPayload,
): Promise<TrackingCategory> {
  return await useApiClient()("/api/tracking-categories", {
    method: "POST",
    body: payload,
  });
}

// --- TRACKING ITEMS ---
export async function fetchTrackingItems(
  categoryId: string,
): Promise<TrackingItem[]> {
  return await useApiClient()("/api/tracking-items", {
    query: { category_id: categoryId },
  });
}

export async function createTrackingItem(
  payload: CreateTrackingItemPayload,
): Promise<TrackingItem> {
  return await useApiClient()("/api/tracking-items", {
    method: "POST",
    body: payload,
  });
}

export async function deleteTrackingItem(itemId: string): Promise<void> {
  await useApiClient()(`/api/tracking-items/${itemId}`, {
    method: "DELETE",
  });
}

// --- CLIENTS ---
export async function fetchClients(): Promise<Client[]> {
  return await useApiClient()("/api/clients");
}
