<script setup lang="ts">
import SetupForm from "~/components/setup/SetupForm.vue";

definePageMeta({
    layout: "default",
});
</script>

<template>
    <SetupForm :edit-mode="true" />
</template>
