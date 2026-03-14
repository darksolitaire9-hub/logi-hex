import { ref } from "vue";
import { fetchConfig } from "../../lib/api/logiHex";

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
      // corrupted → ignore
    }
  }
  return baseConfig;
}

const config = ref(loadStoredConfig());
let hydratedFromBackend = false;

function persist() {
  if (import.meta.client) {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config.value));
  }
}

function updateConfig(newConfig: Partial<typeof config.value>) {
  config.value = { ...config.value, ...newConfig };
  persist();
}

async function hydrateConfigFromBackend() {
  if (hydratedFromBackend) return;
  hydratedFromBackend = true;

  const backend = await fetchConfig();

  config.value = {
    ...baseConfig,
    ...config.value, // keep any local overrides as fallback
    primaryCategoryId: backend.primary_category_id,
    primaryCategoryName:
      backend.primary_category_name ?? config.value.primaryCategoryName,
    contentCategoryId: backend.content_category_id,
    contentCategoryName:
      backend.content_category_name ?? config.value.contentCategoryName,
    isSetupComplete: backend.is_setup_complete,
  };

  persist();
}

export function useConfig() {
  return { config, updateConfig, hydrateConfigFromBackend };
}
