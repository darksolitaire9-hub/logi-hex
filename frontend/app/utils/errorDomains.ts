import { useAudio } from '../composables/useAudio'

import { useI18n } from 'vue-i18n'

// Replace standard alerts and console.error with this Toast handler
export function useSelfHealingUI() {
  const toast = useToast()
  const audio = useAudio()
  const { t } = useI18n()

  function handleUXError(domain: 'AUTH' | 'DATABASE_LOCKED' | 'VALIDATION' | 'UNKNOWN', customMessage?: string) {
    audio.playError()
    
    let title = t('errors.unknown.title')
    let description = customMessage || t('errors.unknown.desc')
    
    switch(domain) {
      case 'AUTH':
        title = t('errors.auth.title')
        description = customMessage || t('errors.auth.desc')
        break
      case 'DATABASE_LOCKED':
        title = t('errors.db_locked.title')
        description = t('errors.db_locked.desc')
        break
      case 'VALIDATION':
        title = t('errors.validation.title')
        description = customMessage || t('errors.validation.desc')
        break
    }

    toast.add({
      title,
      description,
      color: 'error',
      icon: 'i-lucide-alert-octagon'
    })
  }

  function handleUXSuccess(title: string, description?: string) {
    audio.playSuccess()
    toast.add({
      title,
      description,
      color: 'success',
      icon: 'i-lucide-check-circle'
    })
  }

  return {
    handleUXError,
    handleUXSuccess
  }
}
