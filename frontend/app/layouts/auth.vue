<template>
  <div class="min-h-screen bg-gray-50 dark:bg-slate-950 flex flex-col items-center justify-center p-4">
    <!-- Subtle background decoration -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none -z-10">
      <div class="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-blue-500/10 dark:bg-blue-500/5 blur-3xl"></div>
      <div class="absolute top-[60%] -right-[10%] w-[40%] h-[40%] rounded-full bg-indigo-500/10 dark:bg-indigo-500/5 blur-3xl"></div>
    </div>
    
    <div class="w-full max-w-md w-full">
      <!-- App Branding -->
      <div class="flex flex-col items-center mb-8">
        <div class="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
          <UIcon name="i-lucide-box" class="text-white w-6 h-6" />
        </div>
        <h1 class="text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Logi-Hex</h1>
      </div>

      <!-- Page Content -->
      <slot />
    </div>
  </div>
</template>
