<script setup lang="ts">
import { ref } from "vue";
import { Trash2, Plus, Tag } from "lucide-vue-next";
import { useApp } from "~/composables/useApp";

const { contentItems, addContentItem, removeContentItem, config } = useApp();

const label = ref("");
const error = ref("");
const pendingDelete = ref<string | null>(null);
const inputRef = ref<HTMLInputElement | null>(null);

function handleAdd(e: Event) {
    e.preventDefault();
    const trimmed = label.value.trim();
    if (!trimmed) {
        error.value = "Tag name cannot be empty.";
        inputRef.value?.focus();
        return;
    }
    const isDuplicate = contentItems.value.some(
        (i) => i.label.toLowerCase() === trimmed.toLowerCase(),
    );
    if (isDuplicate) {
        error.value = "A tag with this name already exists.";
        inputRef.value?.focus();
        return;
    }
    addContentItem(trimmed);
    label.value = "";
    error.value = "";
    inputRef.value?.focus();
}

function confirmDelete(id: string) {
    removeContentItem(id);
    pendingDelete.value = null;
}
</script>

<template>
    <div>
        <div class="mb-6">
            <div class="flex items-center gap-2 mb-1">
                <Tag class="w-5 h-5 text-[#717182]" />
                <h1 class="text-[#1a1a2e]">{{ config.contentCategoryName }}</h1>
            </div>
            <p class="text-sm text-[#717182]">
                Content tags are optional labels you can attach to any movement.
            </p>
        </div>

        <div
            class="bg-white rounded-xl border border-black/10 p-4 mb-5 shadow-sm"
        >
            <h2 class="text-[#1a1a2e] mb-3">Add new tag</h2>
            <form @submit="handleAdd" class="flex gap-2" novalidate>
                <div class="flex-1">
                    <input
                        ref="inputRef"
                        v-model="label"
                        type="text"
                        placeholder="e.g. Frozen, Fresh, Urgent…"
                        :aria-invalid="!!error"
                        :aria-describedby="error ? 'add-tag-error' : undefined"
                        class="w-full px-3 py-2.5 rounded-lg border bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors"
                        :class="error ? 'border-[#d4183d]' : 'border-black/15'"
                    />
                </div>
                <button
                    type="submit"
                    class="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-[#1a1a2e] hover:bg-[#2e2e4a] text-white text-sm font-medium transition-colors"
                >
                    <Plus class="w-4 h-4" />
                    Add
                </button>
            </form>
            <p
                v-if="error"
                id="add-tag-error"
                class="mt-2 text-xs text-[#d4183d]"
            >
                {{ error }}
            </p>
        </div>

        <div
            class="bg-white rounded-xl border border-black/10 shadow-sm overflow-hidden"
        >
            <div class="px-4 py-3 border-b border-black/10">
                <h2 class="text-[#1a1a2e]">
                    Existing tags
                    <span class="text-[#717182] font-normal ml-1">{{
                        contentItems.length
                    }}</span>
                </h2>
            </div>

            <div
                v-if="contentItems.length === 0"
                class="flex flex-col items-center py-12 text-center px-4"
            >
                <div
                    class="w-12 h-12 rounded-2xl bg-[#f0f0f4] flex items-center justify-center mb-3"
                >
                    <Tag class="w-6 h-6 text-[#a0a0b0]" />
                </div>
                <p class="text-sm text-[#717182]">
                    No tags yet. Add your first one above.
                </p>
            </div>

            <ul v-else class="divide-y divide-black/10">
                <li
                    v-for="item in contentItems"
                    :key="item.id"
                    class="flex items-center justify-between px-4 py-3"
                >
                    <div class="flex items-center gap-2.5">
                        <div class="w-2 h-2 rounded-full bg-[#7c3aed]" />
                        <span class="text-sm text-[#1a1a2e]">{{
                            item.label
                        }}</span>
                    </div>

                    <div
                        v-if="pendingDelete === item.id"
                        class="flex items-center gap-2"
                    >
                        <span class="text-xs text-[#d4183d] font-medium"
                            >Confirm delete?</span
                        >
                        <button
                            @click="confirmDelete(item.id)"
                            class="px-2.5 py-1 rounded-md bg-[#d4183d] text-white text-xs font-medium hover:bg-[#b01530]"
                        >
                            Delete
                        </button>
                        <button
                            @click="pendingDelete = null"
                            class="px-2.5 py-1 rounded-md border border-black/15 text-xs font-medium hover:bg-[#f0f0f4]"
                        >
                            Cancel
                        </button>
                    </div>
                    <button
                        v-else
                        @click="pendingDelete = item.id"
                        class="p-1.5 rounded-md text-[#d4183d] hover:bg-[#fff0f2]"
                    >
                        <Trash2 class="w-4 h-4" />
                    </button>
                </li>
            </ul>
        </div>
    </div>
</template>
