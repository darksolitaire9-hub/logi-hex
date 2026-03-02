<script setup lang="ts">
import { ref } from "vue";
import type { Component } from "vue";
import { Plus } from "lucide-vue-next";

const props = defineProps<{
    title: string;
    description: string;
    placeholder: string;
    itemNameLabel: string;
    items: Array<{ id: string; label: string }>;
    colorClass: string;
    icon: Component;
    deleteIcon: Component;
    onAdd: (label: string) => string | void;
    onDelete: (id: string) => void;
}>();

const label = ref("");
const error = ref("");
const pendingDelete = ref<string | null>(null);
const inputRef = ref<HTMLInputElement | null>(null);

function addOne(raw: string) {
    const trimmed = raw.trim();
    if (!trimmed) return;

    const maybeError = props.onAdd(trimmed);
    if (typeof maybeError === "string" && maybeError.length > 0) {
        error.value = maybeError;
        inputRef.value?.focus();
        return;
    }

    error.value = "";
}

function handleAdd(e: Event) {
    e.preventDefault();
    const value = label.value;

    const parts = value
        .split(",")
        .map((p) => p.trim())
        .filter((p) => p.length > 0);

    if (parts.length === 0) {
        error.value = `${props.itemNameLabel} name cannot be empty.`;
        inputRef.value?.focus();
        return;
    }

    for (const part of parts) {
        addOne(part);
    }

    if (!error.value) {
        label.value = "";
        inputRef.value?.focus();
    }
}

function handleDeleteClick(id: string) {
    pendingDelete.value = id;
}

function confirmDelete(id: string) {
    props.onDelete(id);
    pendingDelete.value = null;
}
</script>

<template>
    <div>
        <!-- Header -->
        <div class="mb-6">
            <div class="flex items-center gap-2 mb-1">
                <component :is="icon" class="w-5 h-5 text-[#717182]" />
                <h1 class="text-[#1a1a2e]">{{ title }}</h1>
            </div>
            <p class="text-sm text-[#717182]">
                {{ description }}
            </p>
        </div>

        <!-- Add form -->
        <div
            class="bg-white rounded-xl border border-[rgba(0,0,0,0.08)] p-4 mb-5 shadow-sm"
        >
            <h2 class="text-[#1a1a2e] mb-3">
                Add new {{ itemNameLabel.toLowerCase() }}
            </h2>

            <form @submit="handleAdd" class="flex gap-2" novalidate>
                <div class="flex-1">
                    <label :for="`new-${itemNameLabel}`" class="sr-only">
                        {{ itemNameLabel }} name
                    </label>
                    <input
                        ref="inputRef"
                        :id="`new-${itemNameLabel}`"
                        v-model="label"
                        type="text"
                        :placeholder="placeholder"
                        :aria-invalid="!!error"
                        :aria-describedby="error ? 'add-item-error' : undefined"
                        class="w-full px-3 py-2.5 rounded-lg border bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors"
                        :class="
                            error
                                ? 'border-[#d4183d]'
                                : 'border-[rgba(0,0,0,0.15)]'
                        "
                        @input="error = ''"
                    />
                </div>

                <button
                    type="submit"
                    class="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-[#1a1a2e] hover:bg-[#2e2e4a] active:bg-[#111] text-white text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] focus-visible:ring-offset-2 shrink-0"
                >
                    <Plus class="w-4 h-4" aria-hidden="true" />
                    Add
                </button>
            </form>

            <p
                v-if="error"
                id="add-item-error"
                role="alert"
                class="mt-2 text-xs text-[#d4183d]"
            >
                {{ error }}
            </p>

            <p class="mt-2 text-xs text-[#717182]">
                Tip: separate multiple names with commas —
                <span class="font-mono">Large box, Small box, Medium box</span>
            </p>
        </div>

        <!-- Items list -->
        <div
            class="bg-white rounded-xl border border-[rgba(0,0,0,0.08)] shadow-sm overflow-hidden"
        >
            <div class="px-4 py-3 border-b border-black/10">
                <h2 class="text-[#1a1a2e]">
                    Existing {{ itemNameLabel.toLowerCase() }}s
                    <span class="text-[#717182] font-normal ml-1">
                        {{ items.length }}
                    </span>
                </h2>
            </div>

            <div
                v-if="items.length === 0"
                class="flex flex-col items-center py-12 text-center px-4"
            >
                <div
                    class="w-12 h-12 rounded-2xl bg-[#f0f0f4] flex items-center justify-center mb-3"
                >
                    <component :is="icon" class="w-6 h-6 text-[#a0a0b0]" />
                </div>
                <p class="text-sm text-[#717182]">
                    No {{ itemNameLabel.toLowerCase() }}s yet. Add your first
                    one above.
                </p>
            </div>

            <ul v-else class="divide-y divide-black/10">
                <li
                    v-for="item in items"
                    :key="item.id"
                    class="flex items-center justify-between px-4 py-3"
                >
                    <div class="flex items-center gap-2.5">
                        <div :class="['w-2 h-2 rounded-full', colorClass]" />
                        <span class="text-sm text-[#1a1a2e]">
                            {{ item.label }}
                        </span>
                    </div>

                    <div
                        v-if="pendingDelete === item.id"
                        class="flex items-center gap-2"
                    >
                        <span class="text-xs text-[#d4183d] font-medium">
                            Confirm delete?
                        </span>
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
                        <span class="sr-only">Delete {{ item.label }}</span>
                        <component :is="deleteIcon" class="w-4 h-4" />
                    </button>
                </li>
            </ul>
        </div>
    </div>
</template>
