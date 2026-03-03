// lib/api/logiHex.ts
import type { SummaryResponse, LogMovementPayload } from "./types";
import { $fetch } from "ofetch";

// Get summary (who has what)
export async function fetchSummary(): Promise<SummaryResponse> {
  return await $fetch("/api/summary");
}

// Placeholder: will wire to a real backend endpoint later
export async function logMovementApi(payload: LogMovementPayload) {
  // For now just hit /api/issue or /api/receive once you decide the mapping
  console.log("logMovementApi called with", payload);
}
