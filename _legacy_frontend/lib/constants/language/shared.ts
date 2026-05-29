// frontend/lib/constants/language/shared.ts

export enum WorkspaceMode {
  ACCOUNTS = "ACCOUNTS",
  INVENTORY = "INVENTORY",
}

export enum MovementDirection {
  SEND = "SEND",
  COLLECT = "COLLECT",
  RECEIVE = "RECEIVE",
  USE = "USE",
  CORRECT = "CORRECT",
}

export enum CorrectionReason {
  SHRINKAGE = "SHRINKAGE",
  COUNT_CORRECTION = "COUNT_CORRECTION",
  // _OPENING_BALANCE intentionally omitted — internal only
}

export const MODE_LABELS = {
  [WorkspaceMode.ACCOUNTS]: "Accounts",
  [WorkspaceMode.INVENTORY]: "Inventory",
} as const;

export const DIRECTION_LABELS = {
  [MovementDirection.SEND]: "Send",
  [MovementDirection.COLLECT]: "Collect",
  [MovementDirection.RECEIVE]: "Receive",
  [MovementDirection.USE]: "Use",
  [MovementDirection.CORRECT]: "Correct",
} as const;

export const DIRECTION_PAST_TENSE = {
  [MovementDirection.SEND]: "Sent",
  [MovementDirection.COLLECT]: "Collected",
  [MovementDirection.RECEIVE]: "Received",
  [MovementDirection.USE]: "Used",
  [MovementDirection.CORRECT]: "Corrected",
} as const;

export const CORRECTION_REASON_LABELS = {
  [CorrectionReason.SHRINKAGE]: "Shrinkage",
  [CorrectionReason.COUNT_CORRECTION]: "Count Correction",
} as const;
