<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import { CheckCircle, Package, Tag } from "lucide-vue-next";
import { useApp } from "~/composables/useApp";

const { config, updateConfig } = useApp();

const primaryName = ref(config.value.primaryCategoryName);
const contentName = ref(config.value.contentCategoryName);
const primaryError = ref("");
const saved = ref(false);

const primaryInput = ref<HTMLInputElement | null>(null);

onMounted(async () => {
    await nextTick();
    primaryInput.value?.focus();
});

function handleFinish(e: Event) {
    e.preventDefault();

    const trimmedPrimary = primaryName.value.trim();
    if (!trimmedPrimary) {
        primaryError.value = "Please enter a name for your primary category.";
        return;
    }

    updateConfig({
        primaryCategoryName: trimmedPrimary || "Box Types",
        contentCategoryName: contentName.value.trim() || "Contents",
        isSetupComplete: true,
    });

    saved.value = true;
}
</script>

<template>
    <div class="max-w-[480px] mx-auto">
        <!-- Header -->
        <div class="mb-8 text-center">
            <div
                class="w-14 h-14 rounded-2xl bg-[#1a1a2e] flex items-center justify-center mx-auto mb-4"
            >
                <span class="text-white text-xl font-bold">LH</span>
            </div>
            <h1 class="text-[#1a1a2e] mb-1">Settings</h1>
            <p class="text-sm text-[#717182]">
                Update your category names below.
            </p>
        </div>

        <!-- Form -->
        <div
            v-if="!saved"
            class="bg-white rounded-2xl border border-[rgba(0,0,0,0.08)] p-6 shadow-sm"
        >
            <form @submit="handleFinish" novalidate>
                <!-- Primary category -->
                <div class="flex items-center gap-2 mb-1">
                    <Package class="w-5 h-5 text-[#717182]" />
                    <h2 class="text-[#1a1a2e]">Primary category</h2>
                </div>
                <p class="text-sm text-[#717182] mb-4">
                    The main category of containers you track. For example:
                    <em>"Box Types"</em>, <em>"Crates"</em>, or
                    <em>"Containers"</em>.
                </p>
                <div class="mb-6">
                    <label
                        for="primary-category"
                        class="block text-sm font-medium text-[#1a1a2e] mb-1.5"
                    >
                        Primary category name
                        <span class="text-[#ea580c]">*</span>
                    </label>
                    <input
                        ref="primaryInput"
                        id="primary-category"
                        type="text"
                        v-model="primaryName"
                        placeholder="e.g. Box Types"
                        :aria-invalid="!!primaryError"
                        :aria-describedby="
                            primaryError ? 'primary-error' : undefined
                        "
                        class="w-full px-3 py-2.5 rounded-lg border bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors"
                        :class="
                            primaryError
                                ? 'border-[#d4183d]'
                                : 'border-[rgba(0,0,0,0.15)]'
                        "
                    />
                    <p
                        v-if="primaryError"
                        id="primary-error"
                        class="mt-1.5 text-xs text-[#d4183d]"
                    >
                        {{ primaryError }}
                    </p>
                </div>

                <!-- Divider -->
                <div class="border-t border-[rgba(0,0,0,0.06)] mb-6" />

                <!-- Content category -->
                <div class="flex items-center gap-2 mb-1">
                    <Tag class="w-5 h-5 text-[#717182]" />
                    <h2 class="text-[#1a1a2e]">Content category</h2>
                </div>
                <p class="text-sm text-[#717182] mb-4">
                    Optional tag for movements. For example:
                    <em>"Contents"</em>, <em>"Dish Name"</em>, or
                    <em>"Product"</em>.
                </p>
                <div class="mb-6">
                    <label
                        for="content-category"
                        class="block text-sm font-medium text-[#1a1a2e] mb-1.5"
                    >
                        Content category name
                        <span class="text-[#717182] font-normal"
                            >(optional)</span
                        >
                    </label>
                    <input
                        id="content-category"
                        type="text"
                        v-model="contentName"
                        placeholder="e.g. Contents"
                        class="w-full px-3 py-2.5 rounded-lg border border-[rgba(0,0,0,0.15)] bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors"
                    />
                    <p class="mt-1.5 text-xs text-[#717182]">
                        Leave empty to disable content tagging entirely.
                    </p>
                </div>

                <button
                    type="submit"
                    class="w-full flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[#16a34a] hover:bg-[#15803d] text-white text-sm font-medium transition-colors"
                >
                    <CheckCircle class="w-4 h-4" />
                    Save changes
                </button>
            </form>
        </div>

        <!-- Saved state -->
        <div
            v-if="saved"
            class="bg-[#f0fdf4] rounded-2xl border border-[#bbf7d0] p-6 text-center"
        >
            <div
                class="w-12 h-12 rounded-full bg-[#16a34a] flex items-center justify-center mx-auto mb-3"
            >
                <CheckCircle class="w-6 h-6 text-white" />
            </div>
            <h2 class="text-[#166534] mb-1">Settings saved!</h2>
            <p class="text-sm text-[#15803d]">
                Your changes have been applied.
            </p>
        </div>

        <!-- Current settings summary -->
        <div
            class="mt-6 px-4 py-3 rounded-xl bg-[#f8f8fa] border border-[rgba(0,0,0,0.06)] text-sm text-[#717182]"
        >
            <strong class="text-[#1a1a2e]">Current settings</strong>
            <div class="mt-1.5 flex flex-col gap-0.5">
                <span>
                    Primary:
                    <em class="text-[#1a1a2e] not-italic font-medium">
                        {{ config.primaryCategoryName }}
                    </em>
                </span>
                <span>
                    Content:
                    <em class="text-[#1a1a2e] not-italic font-medium">
                        {{ config.contentCategoryName || "—" }}
                    </em>
                </span>
            </div>
        </div>
    </div>
</template>
