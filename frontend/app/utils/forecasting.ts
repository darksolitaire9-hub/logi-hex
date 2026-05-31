// frontend/app/utils/forecasting.ts

/**
 * Applies Linear Interpolation to mask and fill "Censored Demand" (days with 0 stock and 0 usage).
 * 
 * @param rawDemand - An array of raw demand values (number) or null if the demand was censored.
 * @returns A continuous array of numbers with censored days interpolated.
 */
export function interpolateCensoredDemand(rawDemand: (number | null)[]): number[] {
  const history: number[] = []
  
  for (let i = 0; i < rawDemand.length; i++) {
    if (rawDemand[i] !== null) {
      history.push(rawDemand[i]!)
      continue
    }
    
    // Find next known value
    let nextIdx = i + 1
    while (nextIdx < rawDemand.length && rawDemand[nextIdx] === null) {
      nextIdx++
    }
    
    // Find previous known value
    let prevIdx = i - 1
    while (prevIdx >= 0 && rawDemand[prevIdx] === null) {
      prevIdx--
    }
    
    // If no next value, flatline forward from prevVal
    // If no prev value, flatline backward from nextVal
    // If neither exists (all null), default to 0
    let nextVal = nextIdx < rawDemand.length ? rawDemand[nextIdx]! : null;
    let prevVal = prevIdx >= 0 ? rawDemand[prevIdx]! : null;
    
    if (prevVal === null && nextVal === null) {
      prevVal = 0;
      nextVal = 0;
    } else if (prevVal === null) {
      prevVal = nextVal;
    } else if (nextVal === null) {
      nextVal = prevVal;
    }
    

    
    // Calculate linear step
    const distance = nextIdx - prevIdx
    // Prevent division by zero if flatlining from the start/end
    const step = distance > 0 ? ((nextVal as number) - (prevVal as number)) / distance : 0
    
    history.push((prevVal as number) + step * (i - prevIdx))
  }
  
  return history
}

