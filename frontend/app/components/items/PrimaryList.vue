<script setup lang="ts">
import { onMounted, computed } from "vue";
import { Package, Trash2, Plus } from "lucide-vue-next";
import { useApp } from "~/composables/useApp";
import ItemListEditor from "~/components/items/ItemListEditor.vue";

const {
    config,
    containerTypes,
    loadContainerTypes,
    addContainerType,
    removeContainerType,
} = useApp();

// Adapt backend TrackingItem[] to ItemListEditor shape
const items = computed(() =>
    containerTypes.value.map((ct) => ({
        id: ct.id,
        label: ct.label,
    })),
);

onMounted(() => {
    // Lazy-load from backend only once per app lifetime
    loadContainerTypes();
});

function onAddPrimary(label: string): string | void {
    const trimmed = label.trim();
    if (!trimmed) return "Item name cannot be empty.";

    const isDuplicate = items.value.some(
        (i) => i.label.toLowerCase() === trimmed.toLowerCase(),
    );
    if (isDuplicate) {
        return "An item with this name already exists.";
    }

    // Write-through to backend; cache updates on success
    addContainerType(trimmed);
}

// Delete supported via tracking-items API
function onDeletePrimary(id: string) {
    removeContainerType(id);
}
</script>

<template>
    <ItemListEditor
        :title="config.primaryCategoryName"
        description="These are the container types you track quantities for. Changes take effect immediately on the dashboard."
        placeholder="e.g. White Box, Round Tray… or 'Large box, Small box, Medium box'"
        item-name-label="Item"
        :items="items"
        color-class="'bg-[#1a1a2e]'"
        :icon="Package"
        :delete-icon="Trash2"
        :on-add="onAddPrimary"
        :on-delete="onDeletePrimary"
    >
        <template #add-button>
            <button
                type="submit"
                class="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-[#1a1a2e] hover:bg-[#2e2e4a] text-white text-sm font-medium transition-colors"
            >
                <Plus class="w-4 h-4" />
                Add
            </button>
        </template>
    </ItemListEditor>
</template>
