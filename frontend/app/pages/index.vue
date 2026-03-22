<!-- frontend/app/pages/index.vue -->
<script setup lang="ts">
import { useRouter } from "vue-router";
import { onMounted } from "vue";

const router = useRouter();

onMounted(() => {
    router.push("/setup");
});
</script>

<template>
    <div class="p-4 text-sm text-gray-600">Redirecting to setup…</div>
</template>
