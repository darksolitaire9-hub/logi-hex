<script setup lang="ts">
import { onMounted } from "vue";
import { CheckCircle, X } from "lucide-vue-next";

const props = defineProps<{
    clientName: string;
    direction: "OUT" | "IN";
}>();

const emit = defineEmits(["dismiss"]);

const isOut = props.direction === "OUT";

onMounted(() => {
    const t = setTimeout(() => emit("dismiss"), 4000);
    return () => clearTimeout(t);
});
</script>

<template>
    <transition name="fade-slide">
        <div
            class="flex items-center gap-3 rounded-xl px-4 py-3 border mb-5"
            :class="
                isOut
                    ? 'bg-[#fff7ed] border-[#fed7aa] text-[#9a3412]'
                    : 'bg-[#f0fdf4] border-[#bbf7d0] text-[#166534]'
            "
            role="status"
            aria-live="polite"
        >
            <CheckCircle class="w-5 h-5 shrink-0" />

            <p class="text-sm flex-1">
                <strong>{{ isOut ? "Issued OUT" : "Received IN" }}</strong>
                — {{ props.clientName }}. Movement logged.
            </p>

            <button
                @click="emit('dismiss')"
                aria-label="Dismiss notification"
                class="p-1 rounded hover:bg-black/5 transition-colors"
            >
                <X class="w-4 h-4" />
            </button>
        </div>
    </transition>
</template>

<style>
.fade-slide-enter-from {
    opacity: 0;
    transform: translateY(-16px);
}
.fade-slide-enter-to {
    opacity: 1;
    transform: translateY(0);
}
.fade-slide-leave-from {
    opacity: 1;
    transform: translateY(0);
}
.fade-slide-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}
.fade-slide-enter-active,
.fade-slide-leave-active {
    transition: all 0.25s ease-out;
}
</style>
