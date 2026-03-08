<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ArrowRight, CheckCircle, Package, Tag } from "lucide-vue-next";
import { useApp } from "~/composables/useApp";
import { createTrackingCategory } from "../../../lib/api/logiHex";

const router = useRouter();
const { updateConfig } = useApp();

const step = ref(1);
const primaryName = ref("");
const contentName = ref("");
const primaryError = ref("");
const setupError = ref("");
const saved = ref(false);

const contentInput = ref<HTMLInputElement | null>(null);

watch(step, async (newStep) => {
    if (newStep === 2) {
        await nextTick();
        contentInput.value?.focus();
    }
});

function handleStep1(e: Event) {
    e.preventDefault();
    const trimmed = primaryName.value.trim();

    if (!trimmed) {
        primaryError.value = "Please enter a name for your primary category.";
        return;
    }

    primaryError.value = "";
    step.value = 2;
}

async function handleFinish(e: Event) {
    e.preventDefault();
    setupError.value = "";

    const primaryLabel = primaryName.value.trim() || "Box Types";
    const contentLabel = contentName.value.trim();

    const primaryId =
        primaryLabel.toLowerCase().replace(/\s+/g, "-") || "containers";
    const contentId =
        contentLabel.toLowerCase().replace(/\s+/g, "-") || "contents";

    try {
        // 1. Create primary category (enforce_returns = true)
        const primaryCategory = await createTrackingCategory({
            id: primaryId,
            name: primaryLabel,
            enforce_returns: true,
        });

        // 2. Optionally create content category
        let contentCategoryId: string | null = null;
        if (contentLabel) {
            const contentCategory = await createTrackingCategory({
                id: contentId,
                name: contentLabel,
                enforce_returns: false,
            });
            contentCategoryId = contentCategory.id;
        }

        updateConfig({
            primaryCategoryName: primaryCategory.name,
            contentCategoryName: contentLabel || "",
            primaryCategoryId: primaryCategory.id,
            contentCategoryId,
            isSetupComplete: true,
        });

        saved.value = true;
        setTimeout(() => {
            router.push("/primary");
        }, 1200);
    } catch (err: any) {
        setupError.value =
            err?.data?.detail ?? "Setup failed. Please try again.";
    }
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
            <h1 class="text-[#1a1a2e] mb-1">Set up logi-hex</h1>
            <p class="text-sm text-[#717182]">
                A quick 2-step setup to get you started. You can change these
                any time.
            </p>
        </div>

        <!-- Progress -->
        <div
            class="flex items-center gap-2 mb-8"
            :aria-label="`Step ${step} of 2`"
        >
            <div
                v-for="s in [1, 2]"
                :key="s"
                class="flex items-center gap-2 flex-1"
            >
                <div
                    class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors"
                    :class="{
                        'bg-[#16a34a] text-white': step > s,
                        'bg-[#1a1a2e] text-white': step === s,
                        'bg-[#f0f0f4] text-[#a0a0b0]': step < s,
                    }"
                    :aria-current="step === s ? 'step' : undefined"
                >
                    <CheckCircle v-if="step > s" class="w-4 h-4" />
                    <span v-else>{{ s }}</span>
                </div>

                <div
                    class="text-xs hidden sm:block"
                    :class="step >= s ? 'text-[#1a1a2e]' : 'text-[#a0a0b0]'"
                >
                    {{ s === 1 ? "Primary category" : "Content category" }}
                </div>

                <div
                    v-if="s < 2"
                    class="flex-1 h-0.5 rounded mx-1"
                    :class="step > s ? 'bg-[#16a34a]' : 'bg-[#e0e0e8]'"
                />
            </div>
        </div>

        <!-- Step 1 -->
        <div
            v-if="step === 1"
            class="bg-white rounded-2xl border border-[rgba(0,0,0,0.08)] p-6 shadow-sm"
        >
            <div class="flex items-center gap-2 mb-1">
                <Package class="w-5 h-5 text-[#717182]" />
                <h2 class="text-[#1a1a2e]">What do you want to track?</h2>
            </div>
            <p class="text-sm text-[#717182] mb-5">
                Give a name to your main category of containers. For example:
                <em>"Box Types"</em>, <em>"Crates"</em>, or
                <em>"Containers"</em>.
            </p>

            <form @submit="handleStep1" novalidate>
                <div class="mb-4">
                    <label
                        for="primary-category"
                        class="block text-sm font-medium text-[#1a1a2e] mb-1.5"
                    >
                        Primary category name
                        <span class="text-[#ea580c]">*</span>
                    </label>
                    <input
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
                        autofocus
                    />
                    <p
                        v-if="primaryError"
                        id="primary-error"
                        class="mt-1.5 text-xs text-[#d4183d]"
                    >
                        {{ primaryError }}
                    </p>
                </div>

                <button
                    type="submit"
                    class="w-full flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[#1a1a2e] hover:bg-[#2e2e4a] text-white text-sm font-medium transition-colors"
                >
                    Continue
                    <ArrowRight class="w-4 h-4" />
                </button>
            </form>
        </div>

        <!-- Step 2 -->
        <div
            v-if="step === 2 && !saved"
            class="bg-white rounded-2xl border border-[rgba(0,0,0,0.08)] p-6 shadow-sm"
        >
            <div class="flex items-center gap-2 mb-1">
                <Tag class="w-5 h-5 text-[#717182]" />
                <h2 class="text-[#1a1a2e]">Optional: content category</h2>
            </div>
            <p class="text-sm text-[#717182] mb-5">
                Would you like to tag movements with additional information? For
                example: <em>"Contents"</em>, <em>"Dish Name"</em>, or
                <em>"Product"</em>.
            </p>

            <form @submit="handleFinish" novalidate>
                <div class="mb-4">
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
                        ref="contentInput"
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

                <!-- Error message -->
                <p v-if="setupError" class="mb-3 text-xs text-[#d4183d]">
                    {{ setupError }}
                </p>

                <div class="flex gap-2">
                    <button
                        type="button"
                        @click="step = 1"
                        class="px-4 py-2.5 rounded-lg border border-[rgba(0,0,0,0.15)] text-[#1a1a2e] text-sm font-medium hover:bg-[#f0f0f4] transition-colors"
                    >
                        Back
                    </button>
                    <button
                        type="submit"
                        class="flex-1 flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[#16a34a] hover:bg-[#15803d] text-white text-sm font-medium transition-colors"
                    >
                        <CheckCircle class="w-4 h-4" />
                        Save & go to dashboard
                    </button>
                </div>
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
            <h2 class="text-[#166534] mb-1">Setup complete!</h2>
            <p class="text-sm text-[#15803d]">
                Redirecting you to the page where you can define items…
            </p>
        </div>
    </div>
</template>
