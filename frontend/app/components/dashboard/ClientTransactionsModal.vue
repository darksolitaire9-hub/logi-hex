<!-- components/dashboard/ClientTransactionsModal.vue -->
<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from "vue";
import type { ClientTransaction } from "~/lib/api/types";
import ClientTransactionTable from "~/components/dashboard/ClientTransactionTable.vue";

const props = defineProps<{
    open: boolean;
    clientName: string | null;
    transactions: ClientTransaction[];
    loading: boolean;
    error: string | null;
}>();

const emit = defineEmits<{
    (e: "close"): void;
}>();

const hasTransactions = computed(
    () => !props.loading && props.transactions.length > 0,
);

function onKeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && props.open) {
        emit("close");
    }
}

onMounted(() => {
    window.addEventListener("keydown", onKeydown);
});

onBeforeUnmount(() => {
    window.removeEventListener("keydown", onKeydown);
});
</script>

<template>
    <Teleport to="body">
        <div
            v-if="open"
            class="fixed inset-0 z-40 flex items-end sm:items-center justify-center bg-black/40 px-2 sm:px-4"
            @click.self="emit('close')"
        >
            <div
                class="bg-white rounded-t-2xl sm:rounded-2xl shadow-xl w-full max-h-[100vh] sm:max-h-[85vh] flex flex-col overflow-hidden sm:max-w-5xl"
            >
                <!-- Header -->
                <header
                    class="flex items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4 border-b border-[rgba(0,0,0,0.12)] bg-[#1a1a2e] text-white"
                >
                    <div class="min-w-0">
                        <h2 class="text-sm sm:text-base font-semibold truncate">
                            {{ clientName || "Client transactions" }}
                        </h2>
                        <p
                            class="mt-0.5 text-xs sm:text-sm text-white/60 truncate"
                        >
                            Movement history with items, tags, and notes
                        </p>
                    </div>
                    <button
                        type="button"
                        class="text-white/70 hover:text-white text-sm px-2 py-1 rounded-md hover:bg-white/10 transition-colors"
                        @click="emit('close')"
                    >
                        Close
                    </button>
                </header>

                <!-- Body -->
                <div class="flex-1 overflow-y-auto">
                    <!-- Loading state -->
                    <div
                        v-if="loading"
                        class="flex items-center justify-center py-10 text-sm text-[#717182]"
                    >
                        Loading transactions…
                    </div>

                    <!-- Error state -->
                    <div
                        v-else-if="error"
                        class="px-4 py-3 sm:px-6 sm:py-4 text-sm text-red-700 bg-red-50 border-b border-red-100"
                    >
                        {{ error }}
                    </div>

                    <!-- Empty state -->
                    <div
                        v-else-if="!hasTransactions"
                        class="flex flex-col items-center justify-center py-10 text-center px-4 sm:px-6"
                    >
                        <p class="text-sm text-[#717182]">
                            No transactions recorded for this client yet.
                        </p>
                    </div>

                    <!-- Transactions table -->
                    <div v-else class="px-2 py-3 sm:px-4 sm:py-4">
                        <ClientTransactionTable :transactions="transactions" />
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>
