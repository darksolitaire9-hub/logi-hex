// app/composables/useConfig.ts
import { ref } from "vue";

const CONFIG_KEY = "logi-hex-config";

const baseConfig = {
  primaryCategoryName: "Primary containers",
  contentCategoryName: "Content tags",
  primaryCategoryId: null as string | null,
  contentCategoryId: null as string | null,
  isSetupComplete: false,
};

function loadStoredConfig() {
  if (!import.meta.client) return baseConfig;

  const stored = localStorage.getItem(CONFIG_KEY);
  if (stored) {
    try {
      return { ...baseConfig, ...JSON.parse(stored) };
    } catch {
      // corrupted storage → fall back
    }
  }
  return baseConfig;
}

const config = ref(loadStoredConfig());

function updateConfig(newConfig: Partial<typeof config.value>) {
  config.value = { ...config.value, ...newConfig };
  if (import.meta.client) {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config.value));
  }
}

export function useConfig() {
  return { config, updateConfig };
}
