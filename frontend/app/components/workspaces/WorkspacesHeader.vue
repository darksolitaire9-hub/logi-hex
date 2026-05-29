<script setup lang="ts">
import type { PropType } from "vue";
import { Package2 } from "lucide-vue-next";

interface User {
    name: string;
    email: string;
}

const props = defineProps({
    user: {
        type: Object as PropType<User | null>,
        default: null,
    },
});

const colorMode = useColorMode();

const isDark = computed({
    get() {
        return colorMode.value === "dark";
    },
    set(value: boolean) {
        colorMode.preference = value ? "dark" : "light";
    },
});
</script>

<template>
    <header
        class="flex h-14 md:h-16 items-center justify-between border-b border-gray-800 bg-gray-950/95 px-4 md:px-6"
    >
        <div class="flex items-center gap-2 md:gap-3">
            <div
                class="flex h-8 w-8 md:h-9 md:w-9 items-center justify-center rounded-lg bg-primary-500"
            >
                <Package2 class="h-4 w-4 md:h-5 md:w-5 text-black" />
            </div>
            <span class="text-base md:text-lg font-semibold">Logi-Hex</span>
        </div>

        <div class="flex items-center gap-3">
            <div
                v-if="user"
                class="hidden sm:flex flex-col items-end text-xs md:text-sm text-gray-400"
            >
                <span>{{ user.name }}</span>
                <span class="truncate max-w-[160px] md:max-w-none">
                    {{ user.email }}
                </span>
            </div>

            <UButton
                color="neutral"
                variant="ghost"
                size="xs"
                class="flex items-center justify-center"
                :icon="isDark ? 'i-lucide-moon' : 'i-lucide-sun'"
                :aria-label="`Switch to ${isDark ? 'light' : 'dark'} mode`"
                @click="isDark = !isDark"
            />
        </div>
    </header>
</template>
