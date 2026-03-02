<!-- /components/CommandPalette.vue -->
<script setup lang="ts">
import {
    computed,
    nextTick,
    onBeforeUnmount,
    onMounted,
    ref,
    watch,
} from "vue";
import { useRouter } from "vue-router";
import {
    Search,
    ArrowUpRight,
    ArrowDownLeft,
    Layers,
    Package,
    Settings2,
    Users,
    Tag,
    CornerDownLeft,
    Hash,
} from "lucide-vue-next";
import { useApp } from "~/composables/useApp";

type Direction = "OUT" | "IN";

type ResultItem = {
    id: string;
    group: string;
    label: string;
    sublabel?: string;
    icon: any;
    badge?: string | number;
    action: () => void;
    shortcut?: string[];
    accentColor?: "orange" | "green" | "blue" | "purple";
};

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{
    (e: "close"): void;
    (e: "open-modal", direction: Direction): void;
}>();

const isClient =
    typeof window !== "undefined" && typeof document !== "undefined";

const { config, primaryItems, contentItems, clientBalances } = useApp();
const router = useRouter();

const query = ref("");
const activeIndex = ref(0);
const inputRef = ref<HTMLInputElement | null>(null);

const onClose = () => emit("close");
const onOpenModal = (direction: Direction) => emit("open-modal", direction);

const run = (action: () => void) => {
    onClose();
    if (isClient) window.setTimeout(action, 60);
};

const accentClasses: Record<string, string> = {
    orange: "bg-[#fff7ed] text-[#ea580c]",
    green: "bg-[#f0fdf4] text-[#16a34a]",
    blue: "bg-[#eff6ff] text-[#2563eb]",
    purple: "bg-[#f5f3ff] text-[#7c3aed]",
    default: "bg-[#f0f0f4] text-[#717182]",
};

const allItems = computed<ResultItem[]>(() => {
    const cfg = config.value;
    const primary = primaryItems.value;
    const content = contentItems.value;
    const clients = clientBalances.value;

    const items: ResultItem[] = [];

    items.push({
        id: "action-out",
        group: "Quick Actions",
        label: "Issue OUT",
        sublabel: "Log containers going out to a client",
        icon: ArrowUpRight,
        accentColor: "orange",
        shortcut: ["O"],
        action: () => run(() => onOpenModal("OUT")),
    });
    items.push({
        id: "action-in",
        group: "Quick Actions",
        label: "Receive IN",
        sublabel: "Log containers returned from a client",
        icon: ArrowDownLeft,
        accentColor: "green",
        shortcut: ["I"],
        action: () => run(() => onOpenModal("IN")),
    });

    items.push({
        id: "page-dashboard",
        group: "Pages",
        label: "Dashboard",
        sublabel: "Overview and client balances",
        icon: Layers,
        action: () => run(() => router.push("/")),
    });
    items.push({
        id: "page-primary",
        group: "Pages",
        label: cfg.primaryCategoryName,
        sublabel: `Manage ${cfg.primaryCategoryName} types`,
        icon: Package,
        action: () => run(() => router.push("/primary")),
    });
    items.push({
        id: "page-content",
        group: "Pages",
        label: cfg.contentCategoryName || "Content Items",
        sublabel: "Manage content tags",
        icon: Tag,
        action: () => run(() => router.push("/content")),
    });
    items.push({
        id: "page-setup",
        group: "Pages",
        label: "Setup",
        sublabel: "Configure category names",
        icon: Settings2,
        action: () => run(() => router.push("/setup")),
    });

    for (const client of clients) {
        items.push({
            id: `client-${client.clientName}`,
            group: "Clients with containers",
            label: client.clientName,
            sublabel: client.items
                .map((i: any) => `${i.quantity} ${i.label}`)
                .join(" · "),
            icon: Users,
            badge: client.total,
            action: () => run(() => router.push("/")),
        });
    }

    for (const pi of primary) {
        items.push({
            id: `pi-${pi.id}`,
            group: cfg.primaryCategoryName,
            label: pi.label,
            sublabel: "Container type",
            icon: Hash,
            accentColor: "blue",
            action: () => run(() => router.push("/primary")),
        });
    }

    for (const ci of content) {
        items.push({
            id: `ci-${ci.id}`,
            group: cfg.contentCategoryName || "Content",
            label: ci.label,
            sublabel: "Content tag · informational",
            icon: Tag,
            accentColor: "purple",
            action: () => run(() => router.push("/items/content")),
        });
    }

    return items;
});

const filtered = computed(() => {
    const q = query.value.trim().toLowerCase();
    if (!q) return allItems.value;

    return allItems.value.filter(
        (item) =>
            item.label.toLowerCase().includes(q) ||
            (item.sublabel?.toLowerCase().includes(q) ?? false) ||
            item.group.toLowerCase().includes(q),
    );
});

const flat = computed(() => filtered.value);

const grouped = computed(() => {
    const map = new Map<string, Array<{ item: ResultItem; index: number }>>();
    flat.value.forEach((item, index) => {
        const arr = map.get(item.group) ?? [];
        arr.push({ item, index });
        map.set(item.group, arr);
    });
    return Array.from(map.entries()).map(([group, rows]) => ({ group, rows }));
});

const activeItemId = computed(() => {
    const item = flat.value[activeIndex.value];
    return item ? `palette-item-${item.id}` : undefined;
});

function clampActiveIndex() {
    const max = Math.max(0, flat.value.length - 1);
    activeIndex.value = Math.min(Math.max(activeIndex.value, 0), max);
}

function scrollActiveIntoView() {
    if (!isClient) return;
    const id = activeItemId.value;
    if (!id) return;
    document.getElementById(id)?.scrollIntoView({ block: "nearest" });
}

function onBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) onClose();
}

function onKeyDown(e: KeyboardEvent) {
    if (e.key === "ArrowDown") {
        e.preventDefault();
        if (flat.value.length === 0) return;
        activeIndex.value = Math.min(
            activeIndex.value + 1,
            flat.value.length - 1,
        );
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (flat.value.length === 0) return;
        activeIndex.value = Math.max(activeIndex.value - 1, 0);
    } else if (e.key === "Enter") {
        e.preventDefault();
        flat.value[activeIndex.value]?.action?.();
    }
}

function onDocumentKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") onClose();
}

watch(
    () => props.isOpen,
    async (open) => {
        if (!isClient) return;

        if (open) {
            query.value = "";
            activeIndex.value = 0;
            await nextTick();
            window.setTimeout(() => inputRef.value?.focus(), 10);
            document.addEventListener("keydown", onDocumentKeyDown);
            document.body.style.overflow = "hidden";
        } else {
            document.removeEventListener("keydown", onDocumentKeyDown);
            document.body.style.overflow = "";
        }
    },
);

onMounted(() => {
    if (!isClient) return;
    if (props.isOpen) {
        document.addEventListener("keydown", onDocumentKeyDown);
        document.body.style.overflow = "hidden";
        window.setTimeout(() => inputRef.value?.focus(), 10);
    }
});

watch(flat, clampActiveIndex);

watch(activeIndex, async () => {
    await nextTick();
    scrollActiveIntoView();
});

onBeforeUnmount(() => {
    if (!isClient) return;
    document.removeEventListener("keydown", onDocumentKeyDown);
    document.body.style.overflow = "";
});

function setQueryFromInput(v: string) {
    query.value = v;
    activeIndex.value = 0;
}

function partsFor(text: string, q: string) {
    const queryTrim = q.trim();
    if (!queryTrim) return [{ text, mark: false }];

    const idx = text.toLowerCase().indexOf(queryTrim.toLowerCase());
    if (idx === -1) return [{ text, mark: false }];

    return [
        { text: text.slice(0, idx), mark: false },
        { text: text.slice(idx, idx + queryTrim.length), mark: true },
        { text: text.slice(idx + queryTrim.length), mark: false },
    ];
}
</script>

<template>
    <Teleport to="body">
        <Transition name="cp" appear>
            <div
                v-if="isOpen"
                class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] px-4 pb-8"
                :style="{
                    background: 'rgba(10,10,20,0.55)',
                    backdropFilter: 'blur(2px)',
                }"
                aria-label="Command palette backdrop"
                @click="onBackdropClick"
            >
                <div
                    role="dialog"
                    aria-modal="true"
                    aria-label="Command palette"
                    class="cp-dialog w-full max-w-[560px] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col"
                    :style="{ maxHeight: '70vh' }"
                    @click.stop
                >
                    <div
                        class="flex items-center gap-3 px-4 py-3.5 border-b border-[rgba(0,0,0,0.08)]"
                    >
                        <component
                            :is="Search"
                            class="w-4 h-4 text-[#a0a0b0] shrink-0"
                            aria-hidden="true"
                        />
                        <input
                            ref="inputRef"
                            type="text"
                            role="combobox"
                            aria-expanded="true"
                            aria-autocomplete="list"
                            aria-controls="palette-results"
                            :aria-activedescendant="activeItemId"
                            :value="query"
                            placeholder="Search actions, clients, items…"
                            class="flex-1 bg-transparent text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none text-sm"
                            @input="
                                setQueryFromInput(
                                    ($event.target as HTMLInputElement).value,
                                )
                            "
                            @keydown="onKeyDown"
                        />
                        <kbd
                            class="hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-[rgba(0,0,0,0.12)] text-[10px] text-[#a0a0b0] shrink-0"
                        >
                            Esc
                        </kbd>
                    </div>

                    <ul
                        id="palette-results"
                        role="listbox"
                        aria-label="Search results"
                        class="overflow-y-auto flex-1 py-2"
                    >
                        <li
                            v-if="filtered.length === 0"
                            class="flex flex-col items-center justify-center py-12 text-center px-4"
                        >
                            <component
                                :is="Search"
                                class="w-8 h-8 text-[#d0d0dc] mb-3"
                                aria-hidden="true"
                            />
                            <p class="text-sm text-[#717182]">
                                No results for <strong>"{{ query }}"</strong>
                            </p>
                            <p class="text-xs text-[#a0a0b0] mt-1">
                                Try a client name, action, or page
                            </p>
                        </li>

                        <template v-else>
                            <li
                                v-for="g in grouped"
                                :key="g.group"
                                role="presentation"
                            >
                                <div class="px-4 pt-3 pb-1">
                                    <span
                                        class="text-[10px] font-semibold uppercase tracking-widest text-[#a0a0b0]"
                                    >
                                        {{ g.group }}
                                    </span>
                                </div>

                                <ul role="group" :aria-label="g.group">
                                    <li
                                        v-for="row in g.rows"
                                        :key="row.item.id"
                                        :id="`palette-item-${row.item.id}`"
                                        role="option"
                                        :aria-selected="
                                            row.index === activeIndex
                                        "
                                        class="flex items-center gap-3 mx-2 px-3 py-2.5 rounded-xl cursor-pointer transition-colors"
                                        :class="
                                            row.index === activeIndex
                                                ? 'bg-[#f0f0f4]'
                                                : 'hover:bg-[#f8f8fa]'
                                        "
                                        @mouseenter="activeIndex = row.index"
                                        @click="row.item.action()"
                                    >
                                        <div
                                            class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                                            :class="
                                                accentClasses[
                                                    row.item.accentColor ??
                                                        'default'
                                                ]
                                            "
                                            aria-hidden="true"
                                        >
                                            <component
                                                :is="row.item.icon"
                                                class="w-4 h-4"
                                            />
                                        </div>

                                        <div class="flex-1 min-w-0">
                                            <div
                                                class="text-sm text-[#1a1a2e] truncate"
                                            >
                                                <template
                                                    v-for="(p, i) in partsFor(
                                                        row.item.label,
                                                        query,
                                                    )"
                                                    :key="i"
                                                >
                                                    <mark
                                                        v-if="p.mark"
                                                        class="bg-[#fef08a] text-[#1a1a2e] rounded-sm not-italic font-semibold px-0.5"
                                                    >
                                                        {{ p.text }}
                                                    </mark>
                                                    <span v-else>{{
                                                        p.text
                                                    }}</span>
                                                </template>
                                            </div>

                                            <div
                                                v-if="row.item.sublabel"
                                                class="text-xs text-[#a0a0b0] truncate mt-0.5"
                                            >
                                                <template
                                                    v-for="(p, i) in partsFor(
                                                        row.item.sublabel,
                                                        query,
                                                    )"
                                                    :key="i"
                                                >
                                                    <mark
                                                        v-if="p.mark"
                                                        class="bg-[#fef08a] text-[#1a1a2e] rounded-sm not-italic font-semibold px-0.5"
                                                    >
                                                        {{ p.text }}
                                                    </mark>
                                                    <span v-else>{{
                                                        p.text
                                                    }}</span>
                                                </template>
                                            </div>
                                        </div>

                                        <span
                                            v-if="row.item.badge !== undefined"
                                            class="shrink-0 px-2 py-0.5 rounded-full bg-[#1a1a2e] text-white text-xs font-semibold"
                                        >
                                            {{ row.item.badge }}
                                        </span>

                                        <div
                                            v-if="
                                                row.item.shortcut &&
                                                row.index === activeIndex
                                            "
                                            class="shrink-0 flex items-center gap-1"
                                        >
                                            <kbd
                                                v-for="k in row.item.shortcut"
                                                :key="k"
                                                class="px-1.5 py-0.5 rounded border border-[rgba(0,0,0,0.12)] text-[10px] text-[#717182] bg-white"
                                            >
                                                {{ k }}
                                            </kbd>
                                        </div>

                                        <component
                                            v-if="row.index === activeIndex"
                                            :is="CornerDownLeft"
                                            class="w-3.5 h-3.5 text-[#a0a0b0] shrink-0"
                                            aria-hidden="true"
                                        />
                                    </li>
                                </ul>
                            </li>
                        </template>
                    </ul>

                    <div
                        class="border-t border-[rgba(0,0,0,0.06)] px-4 py-2.5 flex items-center gap-4 text-[10px] text-[#a0a0b0]"
                    >
                        <span class="flex items-center gap-1">
                            <kbd
                                class="px-1 py-0.5 rounded border border-[rgba(0,0,0,0.1)] text-[10px]"
                                >↑</kbd
                            >
                            <kbd
                                class="px-1 py-0.5 rounded border border-[rgba(0,0,0,0.1)] text-[10px]"
                                >↓</kbd
                            >
                            navigate
                        </span>
                        <span class="flex items-center gap-1">
                            <kbd
                                class="px-1.5 py-0.5 rounded border border-[rgba(0,0,0,0.1)] text-[10px]"
                                >Enter</kbd
                            >
                            select
                        </span>
                        <span class="flex items-center gap-1">
                            <kbd
                                class="px-1.5 py-0.5 rounded border border-[rgba(0,0,0,0.1)] text-[10px]"
                                >Esc</kbd
                            >
                            close
                        </span>
                        <span class="ml-auto">
                            {{ flat.length }} result<span
                                v-if="flat.length !== 1"
                                >s</span
                            >
                        </span>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.cp-enter-active,
.cp-leave-active {
    transition: opacity 120ms ease;
}
.cp-enter-from,
.cp-leave-to {
    opacity: 0;
}

.cp-enter-active :deep(.cp-dialog),
.cp-leave-active :deep(.cp-dialog) {
    transition:
        transform 160ms cubic-bezier(0.16, 1, 0.3, 1),
        opacity 160ms cubic-bezier(0.16, 1, 0.3, 1);
}
.cp-enter-from :deep(.cp-dialog),
.cp-leave-to :deep(.cp-dialog) {
    opacity: 0;
    transform: translateY(-12px) scale(0.97);
}
</style>
