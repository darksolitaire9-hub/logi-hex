<script setup lang="ts">
import { onMounted } from "vue";
import { Trash2, Plus, Tags } from "lucide-vue-next";
import { useConfig } from "~/composables/useConfig";
import { useContentItems } from "~/composables/useContentItems";
import ItemListEditor from "~/components/items/ItemListEditor.vue";

const { config } = useConfig();
const { contentItems, addContentItem, removeContentItem, loadContentItems } =
    useContentItems();

onMounted(async () => {
    await loadContentItems();
});

function onAddContent(label: string): string | void {
    const trimmed = label.trim();
    if (!trimmed) return "Tag name cannot be empty.";

    const isDuplicate = contentItems.value.some(
        (i) => i.label.toLowerCase() === trimmed.toLowerCase(),
    );
    if (isDuplicate) {
        return "A tag with this name already exists.";
    }

    addContentItem(trimmed);
}

function onDeleteContent(id: string) {
    removeContentItem(id);
}
</script>

<template>
    <ItemListEditor
        :title="config.contentCategoryName"
        description="Content tags are optional labels you can attach to any movement."
        placeholder="e.g. Frozen, Fresh, Urgent… or 'Frozen, Fresh, Urgent'"
        item-name-label="Tag"
        :items="contentItems"
        color-class="'bg-[#7c3aed]'"
        :icon="Tags"
        :delete-icon="Trash2"
        :on-add="onAddContent"
        :on-delete="onDeleteContent"
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
