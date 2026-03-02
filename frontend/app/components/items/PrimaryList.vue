<script setup lang="ts">
import { ref } from "vue";
import { Trash2, Plus, Package } from "lucide-vue-next";
import { useApp } from "~/composables/useApp";
import { Motion, Presence } from "motion-v";

const { primaryItems, addPrimaryItem, removePrimaryItem, config } = useApp();

const label = ref("");
const error = ref("");
const pendingDelete = ref<string | null>(null);
const inputRef = ref<HTMLInputElement | null>(null);

function handleAdd(e: Event) {
    e.preventDefault();
    const trimmed = label.value.trim();

    if (!trimmed) {
        error.value = "Item name cannot be empty.";
        inputRef.value?.focus();
        return;
    }

    const isDuplicate = primaryItems.value.some(
        (i) => i.label.toLowerCase() === trimmed.toLowerCase(),
    );

    if (isDuplicate) {
        error.value = "An item with this name already exists.";
        inputRef.value?.focus();
        return;
    }

    addPrimaryItem(trimmed);
    label.value = "";
    error.value = "";
    inputRef.value?.focus();
}

function handleDeleteClick(id: string) {
    pendingDelete.value = id;
}

function confirmDelete(id: string) {
    removePrimaryItem(id);
    pendingDelete.value = null;
}
</script>

<template>
    <div>
        <!-- Header -->
        <div class="mb-6">
            <div class="flex items-center gap-2 mb-1">
                <Package class="w-5 h-5 text-[#717182]" />
                <h1 class="text-[#1a1a2e]">{{ config.primaryCategoryName }}</h1>
            </div>
            <p class="text-sm text-[#717182]">
                These are the container types you track quantities for. Changes
                take effect immediately on the dashboard.
            </p>
        </div>

        <!-- Add form -->
        <div
            class="bg-white rounded-xl border border-black/10 p-4 mb-5 shadow-sm"
        >
            <h2 class="text-[#1a1a2e] mb-3">Add new item type</h2>

            <form @submit="handleAdd" class="flex gap-2" novalidate>
                <div class="flex-1">
                    <input
                        ref="inputRef"
                        v-model="label"
                        type="text"
                        placeholder="e.g. White Box, Round Tray…"
                        :aria-invalid="!!error"
                        :aria-describedby="error ? 'add-item-error' : undefined"
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
                id="add-item-error"
                class="mt-2 text-xs text-[#d4183d]"
            >
                {{ error }}
            </p>
        </div>

        <!-- Items list -->
        <div
            class="bg-white rounded-xl border border-black/10 shadow-sm overflow-hidden"
        >
            <div class="px-4 py-3 border-b border-black/10">
                <h2 class="text-[#1a1a2e]">
                    Existing items
                    <span class="text-[#717182] font-normal ml-1">{{
                        primaryItems.length
                    }}</span>
                </h2>
            </div>

            <div
                v-if="primaryItems.length === 0"
                class="flex flex-col items-center py-12 text-center px-4"
            >
                <div
                    class="w-12 h-12 rounded-2xl bg-[#f0f0f4] flex items-center justify-center mb-3"
                >
                    <Package class="w-6 h-6 text-[#a0a0b0]" />
                </div>
                <p class="text-sm text-[#717182]">
                    No item types yet. Add your first one above.
                </p>
            </div>

            <ul v-else v-motion-group class="divide-y divide-black/10">
                <li
                    v-for="item in primaryItems"
                    :key="item.id"
                    v-motion
                    :initial="{ opacity: 0, x: -8 }"
                    :enter="{ opacity: 1, x: 0 }"
                    :leave="{ opacity: 0, x: 8, height: 0 }"
                    :transition="{ duration: 0.18 }"
                    class="flex items-center justify-between px-4 py-3"
                >
                    <div class="flex items-center gap-2.5">
                        <div class="w-2 h-2 rounded-full bg-[#1a1a2e]" />
                        <span class="text-sm text-[#1a1a2e]">{{
                            item.label
                        }}</span>
                    </div>

                    <!-- Delete -->
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
                        @click="handleDeleteClick(item.id)"
                        class="p-1.5 rounded-md text-[#d4183d] hover:bg-[#fff0f2]"
                    >
                        <Trash2 class="w-4 h-4" />
                    </button>
                </li>
            </ul>
        </div>
    </div>
</template>
