<!-- app.vue -->
<template>
    <UApp>
        <NuxtLayout>
            <NuxtPage />
        </NuxtLayout>
    </UApp>
</template>

<script setup lang="ts">
import { onErrorCaptured } from 'vue'

onErrorCaptured((err, instance, info) => {
  console.error('[GLOBAL ERROR CAPTURED]', err)
  console.error('[ERROR INSTANCE]', instance)
  console.error('[ERROR INFO]', info)
  return false
})
</script>
