<script setup lang="ts">
import { computed, ref } from "vue";

type PrimaryItem = { id: string; label: string };

const props = defineProps<{
    primaryItems: PrimaryItem[];
    selectedId: string | null;
    quantity: string;
    primaryCategoryName: string;
    error?: string;
    focusRing: string;
}>();

const emit = defineEmits<{
    (e: "update:selectedId", v: string | null): void;
    (e: "update:quantity", v: string): void;
    (e: "clear-error"): void;
}>();

const primarySearch = ref("");
const isOpen = ref(false);

const availablePrimary = computed(() => {
    const q = primarySearch.value.trim().toLowerCase();
    const all = props.primaryItems;
    if (!q) return all; // show full list when nothing typed
    return all.filter((pi) => pi.label.toLowerCase().includes(q));
});

function selectPrimary(pi: PrimaryItem) {
    emit("update:selectedId", pi.id);
    primarySearch.value = pi.label; // fill with name
    isOpen.value = false;
    emit("clear-error");
}

function onQuantityInput(e: Event) {
    const v = (e.target as HTMLInputElement).value;
    emit("update:quantity", v);
    emit("clear-error");
}

function onFocus() {
    if (props.primaryItems.length > 0) isOpen.value = true;
}

function onBlur() {
    // small delay to allow click on list items
    window.setTimeout(() => {
        isOpen.value = false;
    }, 120);
}
</script>

<template>
    <fieldset>
        <legend class="text-sm font-medium text-[#1a1a2e] mb-2">
            {{ primaryCategoryName }} — Item and quantity
        </legend>

        <p
            v-if="primaryItems.length === 0"
            class="text-sm text-[#717182] italic"
        >
            No items configured. Add some in the items settings.
        </p>

        <div v-else class="flex flex-col gap-3">
            <!-- Dropdown / search -->
            <div class="relative">
                <label
                    for="primarySearch"
                    class="block text-xs font-medium text-[#717182] mb-1"
                >
                    Choose item
                </label>
                <input
                    id="primarySearch"
                    v-model="primarySearch"
                    type="text"
                    autocomplete="off"
                    placeholder="Type to search items…"
                    class="w-full px-3 py-2.5 rounded-lg border bg-white text-sm text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 transition-colors border-[rgba(0,0,0,0.15)]"
                    :class="focusRing"
                    @focus="onFocus"
                    @blur="onBlur"
                    @input="isOpen = true"
                />

                <!-- Dropdown list: always shows when open, filtered by search -->
                <ul
                    v-if="isOpen && availablePrimary.length > 0"
                    class="absolute z-10 left-0 right-0 mt-1 bg-white border border-[rgba(0,0,0,0.12)] rounded-lg shadow-lg overflow-hidden max-h-56 overflow-y-auto"
                    role="listbox"
                    aria-label="Primary items"
                >
                    <li v-for="pi in availablePrimary" :key="pi.id">
                        <button
                            type="button"
                            class="w-full text-left px-3 py-2.5 text-sm text-[#1a1a2e] hover:bg-[#f0f0f4] transition-colors"
                            :aria-selected="selectedId === pi.id"
                            @mousedown.prevent="selectPrimary(pi)"
                        >
                            {{ pi.label }}
                        </button>
                    </li>
                </ul>
            </div>

            <!-- Selected item + quantity -->
            <div
                v-if="selectedId"
                class="flex items-center gap-3 bg-[#f8f8fa] border border-[rgba(0,0,0,0.08)] rounded-lg px-3 py-2.5"
            >
                <div class="flex-1">
                    <p class="text-sm text-[#1a1a2e] font-medium">
                        {{
                            primaryItems.find((pi) => pi.id === selectedId)
                                ?.label
                        }}
                    </p>
                </div>

                <input
                    :id="`qty-${selectedId}`"
                    :value="quantity"
                    type="number"
                    min="0"
                    step="1"
                    inputmode="numeric"
                    placeholder="0"
                    class="w-20 px-2 py-1.5 text-center rounded-md border bg-white text-[#1a1a2e] focus:outline-none focus-visible:ring-2 transition-colors border-[rgba(0,0,0,0.15)]"
                    :class="focusRing"
                    @input="onQuantityInput"
                />
            </div>

            <p v-else class="text-xs text-[#717182]">
                Select an item above to enter a quantity.
            </p>

            <p v-if="error" class="text-xs text-[#d4183d]" role="alert">
                {{ error }}
            </p>
        </div>
    </fieldset>
</template>
