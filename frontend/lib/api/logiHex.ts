// lib/api/logiHex.ts
import type {
  SummaryResponse,
  LogMovementPayload,
  ContainerType,
  CreateContainerTypePayload,
} from "./types";
import { $fetch } from "ofetch";

export async function fetchSummary(): Promise<SummaryResponse> {
  return await $fetch("/api/summary");
}

export async function logMovementApi(payload: LogMovementPayload) {
  const endpoint = payload.direction === "OUT" ? "/api/issue" : "/api/receive";

  return await Promise.all(
    payload.items.map((item) =>
      $fetch(endpoint, {
        method: "POST",
        body: {
          name: payload.clientName,
          container_type_id: item.itemId,
          quantity: item.quantity,
        },
      }),
    ),
  );
}

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
