<script setup lang="ts">
import {
    computed,
    nextTick,
    onMounted,
    onUnmounted,
    reactive,
    ref,
    watch,
    watchEffect,
} from "vue";
import { X, ArrowUpRight, ArrowDownLeft } from "lucide-vue-next";
import { useApp } from "~/composables/useApp";
import LogPrimaryPicker from "~/components/log/LogPrimaryPicker.vue";

type Direction = "OUT" | "IN";

const props = defineProps<{
    direction: Direction;
}>();

const emit = defineEmits<{
    (e: "close"): void;
    (e: "success", clientName: string, direction: Direction): void;
}>();

const {
    containerTypes,
    loadContainerTypes,
    logMovement,
    config,
    contentItems,
    loadContentItems,
} = useApp();

// Global errors (field + submit)
const errors = reactive<Record<string, string>>({});

// Derive primary items from containerTypes for LogPrimaryPicker
const primaryItems = computed(() =>
    containerTypes.value.map((ct) => ({
        id: ct.id,
        label: ct.label,
    })),
);

const dialogRef = ref<HTMLDivElement | null>(null);
const clientInputRef = ref<HTMLInputElement | null>(null);

const clientName = ref("");
const showSuggestions = ref(false);
const note = ref("");
const isSubmitting = ref(false);

// quantities keyed by primary item id
const quantities = reactive<Record<string, string>>({});
watchEffect(() => {
    for (const pi of primaryItems.value) {
        if (!(pi.id in quantities)) quantities[pi.id] = "";
    }
});

// selected primary item (single)
const selectedPrimaryId = ref<string | null>(null);

// computed proxy for the selected primary's quantity
const primaryQuantity = computed({
    get() {
        if (!selectedPrimaryId.value) return "";
        return quantities[selectedPrimaryId.value] ?? "";
    },
    set(v: string) {
        if (!selectedPrimaryId.value) return;
        quantities[selectedPrimaryId.value] = v;
    },
});

const selectedContent = ref<Set<string>>(new Set());
const toggleContent = (id: string) => {
    const next = new Set(selectedContent.value);
    next.has(id) ? next.delete(id) : next.add(id);
    selectedContent.value = next;
};

const isOut = computed(() => props.direction === "OUT");

const headerBg = computed(() =>
    isOut.value ? "bg-[#ea580c]" : "bg-[#16a34a]",
);
const headerText = "text-white";
const accentBg = computed(() =>
    isOut.value ? "bg-[#fff7ed]" : "bg-[#f0fdf4]",
);
const accentBorder = computed(() =>
    isOut.value ? "border-[#fed7aa]" : "border-[#bbf7d0]",
);
const btnBg = computed(() =>
    isOut.value
        ? "bg-[#ea580c] hover:bg-[#c2410c] active:bg-[#9a3412]"
        : "bg-[#16a34a] hover:bg-[#15803d] active:bg-[#166534]",
);
const focusRing = computed(() =>
    isOut.value
        ? "focus-visible:ring-[#ea580c]"
        : "focus-visible:ring-[#16a34a]",
);

// Suggestions (currently disabled)
const filteredSuggestions = computed(() => {
    const q = clientName.value.toLowerCase();
    return []; // temporary no-suggestions fallback
});

// validate client + selected primary quantity
const validate = () => {
    const errs: Record<string, string> = {};
    if (!clientName.value.trim()) errs.clientName = "Client name is required.";

    const hasQty =
        selectedPrimaryId.value != null &&
        primaryQuantity.value !== "" &&
        parseInt(primaryQuantity.value, 10) > 0;

    if (!hasQty) errs.quantities = "Enter a quantity for the selected item.";
    return errs;
};

const handleClose = () => emit("close");

const handleSubmit = async () => {
    const errs = validate();
    if (Object.keys(errs).length > 0) {
        for (const k of Object.keys(errors)) delete errors[k];
        Object.assign(errors, errs);
        return;
    }

    isSubmitting.value = true;
    delete errors.submit; // clear previous submit error

    try {
        const qty = parseInt(primaryQuantity.value || "0", 10);

        await logMovement({
            direction: props.direction,
            clientName: clientName.value.trim(),
            primaryCategoryId: config.value.primaryCategoryId!,
            containerTypeId: selectedPrimaryId.value!,
            quantity: qty,
            contentTypeIds: Array.from(selectedContent.value),
            note: note.value.trim() || undefined,
        });

        window.setTimeout(() => {
            emit("success", clientName.value.trim(), props.direction);
        }, 200);
    } catch (err: any) {
        const detail =
            err?.data?.detail ??
            err?.message ??
            "Something went wrong. Please try again.";
        errors.submit = detail;
    } finally {
        isSubmitting.value = false;
    }
};

// Focus trap + Escape close
const getFocusable = () => {
    const root = dialogRef.value;
    if (!root) return [];
    return Array.from(
        root.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        ),
    ).filter(
        (el) => !el.hasAttribute("disabled") && !el.getAttribute("aria-hidden"),
    );
};

const onKeydown = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
        e.preventDefault();
        handleClose();
        return;
    }
    if (e.key !== "Tab") return;

    const focusable = getFocusable();
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement;

    if (e.shiftKey) {
        if (active === first) {
            e.preventDefault();
            last.focus();
        }
    } else {
        if (active === last) {
            e.preventDefault();
            first.focus();
        }
    }
};

// Suggestions blur timer (to allow click)
const blurTimer = ref<number | null>(null);
const onClientBlur = () => {
    if (blurTimer.value) window.clearTimeout(blurTimer.value);
    blurTimer.value = window.setTimeout(
        () => (showSuggestions.value = false),
        120,
    );
};
const onClientFocus = () => {
    if (blurTimer.value) window.clearTimeout(blurTimer.value);
    showSuggestions.value = true;
};

onMounted(async () => {
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeydown);
    await loadContainerTypes();
    await loadContentItems();
    await nextTick();
    clientInputRef.value?.focus();
});

onUnmounted(() => {
    document.body.style.overflow = "";
    document.removeEventListener("keydown", onKeydown);
    if (blurTimer.value) window.clearTimeout(blurTimer.value);
});

// If direction changes while open, reset form
watch(
    () => props.direction,
    () => {
        clientName.value = "";
        note.value = "";
        selectedContent.value = new Set();
        selectedPrimaryId.value = null;
        primaryQuantity.value = "";
        for (const k of Object.keys(errors)) delete errors[k];
        for (const id of Object.keys(quantities)) quantities[id] = "";
        isSubmitting.value = false;
        nextTick(() => clientInputRef.value?.focus());
    },
);
</script>

<template>
    <Teleport to="body">
        <Transition name="fade">
            <div
                class="fixed inset-0 bg-black/40 z-40 flex items-end sm:items-center justify-center p-0 sm:p-4"
                aria-hidden="true"
                @click="$event.target === $event.currentTarget && handleClose()"
            >
                <Transition name="pop">
                    <div
                        ref="dialogRef"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="modal-title"
                        class="w-full sm:max-w-lg bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[92vh] sm:max-h-[85vh] overflow-hidden"
                        @click.stop
                    >
                        <!-- Header -->
                        <div
                            :class="[
                                headerBg,
                                headerText,
                                'px-5 py-4 flex items-center justify-between shrink-0',
                            ]"
                        >
                            <div class="flex items-center gap-2">
                                <ArrowUpRight
                                    v-if="isOut"
                                    class="w-5 h-5"
                                    aria-hidden="true"
                                />
                                <ArrowDownLeft
                                    v-else
                                    class="w-5 h-5"
                                    aria-hidden="true"
                                />
                                <h2
                                    id="modal-title"
                                    class="text-lg font-semibold"
                                >
                                    {{ isOut ? "Issue OUT" : "Receive IN" }}
                                </h2>
                            </div>

                            <button
                                type="button"
                                @click="handleClose"
                                aria-label="Close modal"
                                class="p-1.5 rounded-lg hover:bg-white/20 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
                            >
                                <X class="w-5 h-5" />
                            </button>
                        </div>

                        <!-- Body -->
                        <form
                            class="flex flex-col overflow-y-auto flex-1"
                            @submit.prevent="handleSubmit"
                            novalidate
                        >
                            <div
                                class="px-5 pt-5 pb-4 flex flex-col gap-5 flex-1 overflow-y-auto"
                            >
                                <!-- Global error -->
                                <div
                                    v-if="errors.quantities"
                                    role="alert"
                                    :class="[
                                        accentBg,
                                        accentBorder,
                                        'border rounded-lg px-4 py-3 text-sm font-medium',
                                        isOut
                                            ? 'text-[#9a3412]'
                                            : 'text-[#166534]',
                                    ]"
                                >
                                    {{ errors.quantities }}
                                </div>

                                <!-- Submit error (e.g. over-return) -->
                                <div
                                    v-if="errors.submit"
                                    role="alert"
                                    :class="[
                                        accentBg,
                                        accentBorder,
                                        'border rounded-lg px-4 py-3 text-sm font-medium',
                                        isOut
                                            ? 'text-[#9a3412]'
                                            : 'text-[#166534]',
                                    ]"
                                >
                                    {{ errors.submit }}
                                </div>

                                <!-- Client name -->
                                <div class="relative">
                                    <label
                                        for="clientName"
                                        class="block text-sm font-medium text-[#1a1a2e] mb-1.5"
                                    >
                                        Who
                                        <span
                                            aria-hidden="true"
                                            class="text-[#ea580c]"
                                            >*</span
                                        >
                                    </label>

                                    <input
                                        ref="clientInputRef"
                                        id="clientName"
                                        v-model="clientName"
                                        type="text"
                                        autocomplete="off"
                                        placeholder="Client or location name…"
                                        :aria-invalid="!!errors.clientName"
                                        :aria-describedby="
                                            errors.clientName
                                                ? 'clientName-error'
                                                : undefined
                                        "
                                        @input="
                                            showSuggestions = true;
                                            errors.clientName = '';
                                        "
                                        @focus="onClientFocus"
                                        @blur="onClientBlur"
                                        :class="[
                                            'w-full px-3 py-2.5 rounded-lg border bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 transition-colors',
                                            focusRing,
                                            errors.clientName
                                                ? 'border-[#d4183d]'
                                                : 'border-[rgba(0,0,0,0.15)]',
                                        ]"
                                    />

                                    <p
                                        v-if="errors.clientName"
                                        id="clientName-error"
                                        role="alert"
                                        class="mt-1 text-xs text-[#d4183d]"
                                    >
                                        {{ errors.clientName }}
                                    </p>

                                    <!-- Autocomplete -->
                                    <ul
                                        v-if="
                                            showSuggestions &&
                                            filteredSuggestions.length > 0
                                        "
                                        role="listbox"
                                        aria-label="Client suggestions"
                                        class="absolute z-10 left-0 right-0 mt-1 bg-white border border-[rgba(0,0,0,0.12)] rounded-lg shadow-lg overflow-hidden"
                                    >
                                        <li
                                            v-for="name in filteredSuggestions.slice(
                                                0,
                                                5,
                                            )"
                                            :key="name"
                                        >
                                            <button
                                                type="button"
                                                role="option"
                                                :aria-selected="
                                                    clientName === name
                                                "
                                                class="w-full text-left px-3 py-2.5 text-sm text-[#1a1a2e] hover:bg-[#f0f0f4] focus:outline-none focus-visible:bg-[#f0f0f4] transition-colors"
                                                @mousedown.prevent="
                                                    clientName = name;
                                                    showSuggestions = false;
                                                "
                                            >
                                                {{ name }}
                                            </button>
                                        </li>
                                    </ul>
                                </div>

                                <!-- Primary item dropdown + quantity -->
                                <LogPrimaryPicker
                                    :primary-items="primaryItems"
                                    :selected-id="selectedPrimaryId"
                                    :quantity="primaryQuantity"
                                    :primary-category-name="
                                        config.primaryCategoryName
                                    "
                                    :error="errors.quantities"
                                    :focus-ring="focusRing"
                                    @update:selected-id="
                                        (id) => (selectedPrimaryId = id)
                                    "
                                    @update:quantity="
                                        (v) => (primaryQuantity = v)
                                    "
                                    @clear-error="errors.quantities = ''"
                                />

                                <!-- Content tags -->
                                <fieldset v-if="contentItems.length > 0">
                                    <legend
                                        class="text-sm font-medium text-[#1a1a2e] mb-2"
                                    >
                                        {{ config.contentCategoryName }}
                                        <span class="text-[#717182] font-normal"
                                            >(optional)</span
                                        >
                                    </legend>

                                    <div class="flex flex-wrap gap-2">
                                        <button
                                            v-for="ci in contentItems"
                                            :key="ci.id"
                                            type="button"
                                            role="checkbox"
                                            :aria-checked="
                                                selectedContent.has(ci.id)
                                            "
                                            @click="toggleContent(ci.id)"
                                            class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm border transition-colors focus:outline-none focus-visible:ring-2"
                                            :class="[
                                                focusRing,
                                                selectedContent.has(ci.id)
                                                    ? isOut
                                                        ? 'bg-[#ea580c] text-white border-[#ea580c]'
                                                        : 'bg-[#16a34a] text-white border-[#16a34a]'
                                                    : 'bg-white text-[#1a1a2e] border-[rgba(0,0,0,0.15)] hover:border-[rgba(0,0,0,0.3)]',
                                            ]"
                                        >
                                            <svg
                                                v-if="
                                                    selectedContent.has(ci.id)
                                                "
                                                class="w-3 h-3"
                                                viewBox="0 0 12 12"
                                                fill="none"
                                                aria-hidden="true"
                                            >
                                                <path
                                                    d="M2 6l3 3 5-5"
                                                    stroke="currentColor"
                                                    stroke-width="1.5"
                                                    stroke-linecap="round"
                                                    stroke-linejoin="round"
                                                />
                                            </svg>
                                            {{ ci.label }}
                                        </button>
                                    </div>
                                </fieldset>

                                <!-- Note -->
                                <div>
                                    <label
                                        for="note"
                                        class="block text-sm font-medium text-[#1a1a2e] mb-1.5"
                                    >
                                        Note
                                        <span class="text-[#717182] font-normal"
                                            >(optional)</span
                                        >
                                    </label>

                                    <textarea
                                        id="note"
                                        v-model="note"
                                        rows="2"
                                        placeholder="Any extra context…"
                                        class="w-full px-3 py-2.5 rounded-lg border bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] resize-none focus:outline-none focus-visible:ring-2 transition-colors border-[rgba(0,0,0,0.15)]"
                                        :class="focusRing"
                                    />
                                </div>
                            </div>

                            <!-- Footer -->
                            <div
                                class="px-5 py-4 border-t border-[rgba(0,0,0,0.08)] flex flex-col-reverse sm:flex-row gap-3 shrink-0 bg-white"
                            >
                                <button
                                    type="button"
                                    @click="handleClose"
                                    class="flex-1 sm:flex-none px-5 py-2.5 rounded-lg border border-[rgba(0,0,0,0.15)] text-[#1a1a2e] hover:bg-[#f0f0f4] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] text-sm font-medium"
                                >
                                    Cancel
                                </button>

                                <button
                                    type="submit"
                                    :disabled="isSubmitting"
                                    class="flex-1 sm:flex-none px-6 py-2.5 rounded-lg text-white text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-60 flex items-center justify-center gap-2"
                                    :class="[focusRing, btnBg]"
                                >
                                    <ArrowUpRight
                                        v-if="isOut"
                                        class="w-4 h-4"
                                        aria-hidden="true"
                                    />
                                    <ArrowDownLeft
                                        v-else
                                        class="w-4 h-4"
                                        aria-hidden="true"
                                    />
                                    {{ isOut ? "Log OUT" : "Log IN" }}
                                </button>
                            </div>
                        </form>
                    </div>
                </Transition>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.pop-enter-active {
    transition:
        transform 0.2s cubic-bezier(0.16, 1, 0.3, 1),
        opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.pop-leave-active {
    transition:
        transform 0.15s ease,
        opacity 0.15s ease;
}
.pop-enter-from,
.pop-leave-to {
    transform: translateY(20px) scale(0.98);
    opacity: 0;
}
</style>
