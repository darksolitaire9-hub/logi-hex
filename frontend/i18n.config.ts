export default defineI18nConfig(() => {
  const numberFormats = {
    'en': {
      // US Format: 1,234.56
      decimal: {
        style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 4
      }
    },
    'de-DE': {
      // EU Format: 1.234,56
      decimal: {
        style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 4
      }
    }
  }

  return {
    fallbackLocale: 'en',
    numberFormats
  }
})
