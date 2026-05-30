export type UomDefinition = {
  id: string
  item_id: string
  unit_name: string
  multiplier: number
}

export type DisplayTranslation = {
  whole_units: number
  remainder: number
  formatted: string
  is_fractional: boolean
}

export function useUOMTranslator() {
  /**
   * Write Path: UI Input -> Base Stock (Database)
   * Enforces strict validation and prevents floating point precision leaks.
   */
  const translateToBase = (input_qty: number, multiplier: number): number => {
    if (multiplier <= 0) throw new Error('UOM Multiplier must be strictly positive.')
    if (!Number.isFinite(input_qty) || !Number.isFinite(multiplier)) {
      throw new Error('Inputs must be finite numbers.')
    }

    // Floating Point Poison Mitigation
    // Using Math.round to safely eliminate JS floating point artifacts like 0.300000000004
    // Assumes base units are ultimately tracked down to the precision of 4 decimal places internally if needed,
    // but typically base units are discrete. We'll round to 4 decimal places to trap JS math errors while allowing valid fractions.
    const raw_base = input_qty * multiplier
    const safe_base = Math.round(raw_base * 10000) / 10000

    if (safe_base > Number.MAX_SAFE_INTEGER || safe_base < Number.MIN_SAFE_INTEGER) {
      throw new Error(`Input exceeds MAX_SAFE_INTEGER limits. Prevented data corruption.`)
    }

    return safe_base
  }

  /**
   * Read Path: Base Stock (Database) -> UI Display
   * Resolves the indivisible base fracture by explicitly separating whole units and remainders.
   */
  const translateToDisplay = (
    base_stock: number, 
    multiplier: number, 
    uom_name: string, 
    base_name: string
  ): DisplayTranslation => {
    if (multiplier <= 0) throw new Error('UOM Multiplier must be strictly positive.')
    if (!Number.isFinite(base_stock) || !Number.isFinite(multiplier)) {
      throw new Error('Inputs must be finite numbers.')
    }

    // Special Case: 1-to-1 mapping (e.g. Base UOM is used directly)
    if (multiplier === 1) {
      return {
        whole_units: base_stock,
        remainder: 0,
        formatted: `${base_stock} ${uom_name}`,
        is_fractional: false
      }
    }

    // Negative stock handling for ledgers that allow it
    const is_negative = base_stock < 0
    const abs_base = Math.abs(base_stock)

    const whole_units = Math.floor(abs_base / multiplier)
    // Round remainder to prevent float poison
    const raw_remainder = abs_base - (whole_units * multiplier)
    const remainder = Math.round(raw_remainder * 10000) / 10000

    let formatted = ''
    if (whole_units > 0 && remainder > 0) {
      formatted = `${is_negative ? '-' : ''}${whole_units} ${uom_name}, ${remainder} ${base_name}`
    } else if (whole_units > 0) {
      formatted = `${is_negative ? '-' : ''}${whole_units} ${uom_name}`
    } else if (remainder > 0) {
      formatted = `${is_negative ? '-' : ''}${remainder} ${base_name}`
    } else {
      formatted = `0 ${uom_name}`
    }

    return {
      whole_units: is_negative ? -whole_units : whole_units,
      remainder: is_negative ? -remainder : remainder,
      formatted,
      is_fractional: remainder > 0
    }
  }

  return {
    translateToBase,
    translateToDisplay
  }
}
