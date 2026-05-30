import { useWorkspace } from '~/composables/useWorkspace'

export default defineNuxtRouteMiddleware(async (to) => {
  // Only guard dashboard routes
  if (!to.path.startsWith('/dashboard')) return

  const { currentWorkspace, restoreActiveWorkspace } = useWorkspace()

  // Attempt to restore from localStorage before checking
  if (!currentWorkspace.value) {
    await restoreActiveWorkspace()
  }

  // If still no active workspace after restore, redirect to unlock screen
  if (!currentWorkspace.value) {
    return navigateTo('/')
  }
})
