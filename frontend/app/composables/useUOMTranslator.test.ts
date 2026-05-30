import { describe, it, expect } from 'vitest'
import { useUOMTranslator } from './useUOMTranslator'

describe('useUOMTranslator', () => {
  const { translateToBase, translateToDisplay } = useUOMTranslator()

  describe('translateToBase (Write Path)', () => {
    it('correctly multiplies and rounds discrete units', () => {
      // 3 pallets * 100 multiplier = 300 base units
      expect(translateToBase(3, 100)).toBe(300)
    })

    it('mitigates floating point poison', () => {
      // 3 units * 0.1 multiplier = 0.30000000000000004 in raw JS
      expect(translateToBase(3, 0.1)).toBe(0.3)
    })

    it('rejects negative or zero multipliers', () => {
      expect(() => translateToBase(10, 0)).toThrow()
      expect(() => translateToBase(10, -5)).toThrow()
    })

    it('protects against MAX_SAFE_INTEGER overflow', () => {
      expect(() => translateToBase(Number.MAX_SAFE_INTEGER, 10)).toThrow()
    })
  })

  describe('translateToDisplay (Read Path)', () => {
    it('handles 1:1 base mappings natively', () => {
      const result = translateToDisplay(105, 1, 'Pieces', 'Pieces')
      expect(result.whole_units).toBe(105)
      expect(result.remainder).toBe(0)
      expect(result.is_negative).toBe(false)
      expect(result.is_fractional).toBe(false)
    })

    it('correctly splits indivisible stock into whole units and remainders', () => {
      // 105 base stock, 100 multiplier (e.g. Pallets)
      const result = translateToDisplay(105, 100, 'Pallets', 'Pieces')
      expect(result.whole_units).toBe(1)
      expect(result.remainder).toBe(5)
      expect(result.is_negative).toBe(false)
      expect(result.is_fractional).toBe(true)
    })

    it('handles exact multiples gracefully', () => {
      // 200 base stock, 100 multiplier
      const result = translateToDisplay(200, 100, 'Pallets', 'Pieces')
      expect(result.whole_units).toBe(2)
      expect(result.remainder).toBe(0)
      expect(result.is_fractional).toBe(false)
    })

    it('handles negative ledger balances', () => {
      // -150 base stock, 100 multiplier
      const result = translateToDisplay(-150, 100, 'Pallets', 'Pieces')
      expect(result.whole_units).toBe(1)
      expect(result.remainder).toBe(50)
      expect(result.is_negative).toBe(true)
    })
  })
})
