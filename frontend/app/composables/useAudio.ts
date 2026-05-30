export function useAudio() {
  function playSuccess() {
    try {
      const audio = new Audio('/sounds/success.mp3')
      audio.volume = 0.5
      audio.play().catch(e => console.log('Audio disabled by browser policy', e))
    } catch(e) {}
  }

  function playWarning() {
    try {
      const audio = new Audio('/sounds/warning.mp3')
      audio.volume = 0.6
      audio.play().catch(e => console.log('Audio disabled by browser policy', e))
    } catch(e) {}
  }

  function playError() {
    try {
      const audio = new Audio('/sounds/error.mp3')
      audio.volume = 0.7
      audio.play().catch(e => console.log('Audio disabled by browser policy', e))
    } catch(e) {}
  }

  return {
    playSuccess,
    playWarning,
    playError
  }
}
