<!-- components/dashboard/ClientTransactionTable.vue -->
<script setup lang="ts">
import type { ClientTransaction } from "~/lib/api/types";

defineProps<{
    transactions: ClientTransaction[];
}>();
</script>

<template>
    <div
        class="overflow-x-auto rounded-xl border border-[rgba(15,23,42,0.12)] bg-white"
    >
        <table class="w-full border-collapse">
            <thead>
                <tr
                    class="bg-[#f3f4f6] text-left text-[11px] uppercase tracking-[0.03em] text-[#6b7280]"
                >
                    <th
                        class="px-3 py-2.5 font-semibold border-b border-r border-[rgba(15,23,42,0.12)] whitespace-nowrap"
                    >
                        Date / Time
                    </th>
                    <th
                        class="px-3 py-2.5 font-semibold border-b border-r border-[rgba(15,23,42,0.12)] whitespace-nowrap"
                    >
                        Direction
                    </th>
                    <th
                        class="px-3 py-2.5 font-semibold border-b border-r border-[rgba(15,23,42,0.12)]"
                    >
                        Item
                    </th>
                    <th
                        class="px-3 py-2.5 font-semibold border-b border-r border-[rgba(15,23,42,0.12)] text-right whitespace-nowrap"
                    >
                        Qty
                    </th>
                    <th
                        class="px-3 py-2.5 font-semibold border-b border-r border-[rgba(15,23,42,0.12)]"
                    >
                        Tags
                    </th>
                    <th
                        class="px-3 py-2.5 font-semibold border-b border-[rgba(15,23,42,0.12)]"
                    >
                        Notes
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr
                    v-for="(tx, i) in transactions"
                    :key="tx.transaction_id"
                    class="transition-colors hover:bg-[#eef2ff]"
                    :class="i % 2 === 0 ? 'bg-white' : 'bg-[#f9fafb]'"
                >
                    <!-- Date / Time -->
                    <td
                        class="px-3 py-3 align-top border-b border-r border-[rgba(15,23,42,0.08)] whitespace-nowrap text-[11px] text-[#6b7280] font-medium"
                    >
                        {{ new Date(tx.timestamp).toLocaleString() }}
                    </td>

                    <!-- Direction -->
                    <td
                        class="px-3 py-3 align-top border-b border-r border-[rgba(15,23,42,0.08)]"
                    >
                        <span
                            class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold"
                            :class="
                                tx.direction === 'OUT'
                                    ? 'bg-[#fee2e2] text-[#b91c1c]'
                                    : 'bg-[#dcfce7] text-[#166534]'
                            "
                        >
                            {{ tx.direction === "OUT" ? "Issued" : "Returned" }}
                        </span>
                    </td>

                    <!-- Item -->
                    <td
                        class="px-3 py-3 align-top border-b border-r border-[rgba(15,23,42,0.08)]"
                    >
                        <div
                            v-for="item in tx.primary_items"
                            :key="item.tracking_item_id"
                            class="text-[12px] leading-5 text-[#111827]"
                        >
                            {{ item.label }}
                        </div>
                    </td>

                    <!-- Qty -->
                    <td
                        class="px-3 py-3 align-top border-b border-r border-[rgba(15,23,42,0.08)] text-right"
                    >
                        <div
                            v-for="item in tx.primary_items"
                            :key="item.tracking_item_id"
                            class="text-[12px] leading-5 text-[#111827] tabular-nums"
                        >
                            {{ item.quantity }}
                        </div>
                    </td>

                    <!-- Tags -->
                    <td
                        class="px-3 py-3 align-top border-b border-r border-[rgba(15,23,42,0.08)]"
                    >
                        <div
                            v-if="tx.secondary_items.length > 0"
                            class="flex flex-wrap gap-1"
                        >
                            <span
                                v-for="tag in tx.secondary_items"
                                :key="tag"
                                class="inline-flex items-center px-1.5 py-0.5 rounded-full bg-[#e5e7eb] text-[10px] text-[#374151] border border-[rgba(15,23,42,0.1)]"
                            >
                                {{ tag }}
                            </span>
                        </div>
                    </td>

                    <!-- Notes -->
                    <td
                        class="px-3 py-3 align-top border-b border-[rgba(15,23,42,0.08)]"
                    >
                        <p
                            v-if="tx.notes"
                            class="text-[12px] leading-5 text-[#4b5563]"
                        >
                            {{ tx.notes }}
                        </p>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>
