// app/composables/useApp.ts
import { useConfig } from "./useConfig";
import { useContainerTypes } from "./useContainerTypes";
import { useContentItems } from "./useContentItems";
import { useSummary } from "./useSummary";

export function useApp() {
  return {
    ...useConfig(),
    ...useContainerTypes(),
    ...useContentItems(),
    ...useSummary(),
  };
}
