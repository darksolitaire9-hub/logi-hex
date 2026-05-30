import { describe, it, expect } from 'vitest'
import { interpolateCensoredDemand } from './forecasting'

describe('interpolateCensoredDemand', () => {
  it('should return identical array if there are no censored gaps', () => {
    const input = [10, 15, 20]
    const output = interpolateCensoredDemand(input)
    expect(output).toEqual([10, 15, 20])
  })

  it('should linearly interpolate a single gap between two known values', () => {
    const input = [10, null, 20]
    const output = interpolateCensoredDemand(input)
    expect(output).toEqual([10, 15, 20])
  })

  it('should linearly interpolate multiple contiguous gaps', () => {
    const input = [10, null, null, null, 50]
    // Distance = 4 steps. Step size = (50 - 10) / 4 = 10
    const output = interpolateCensoredDemand(input)
    expect(output).toEqual([10, 20, 30, 40, 50])
  })

  it('should flatline if a gap is at the very beginning', () => {
    const input = [null, null, 20, 30]
    const output = interpolateCensoredDemand(input)
    expect(output).toEqual([20, 20, 20, 30])
  })

  it('should flatline if a gap is at the very end', () => {
    const input = [20, 30, null, null]
    // If no next value, it defaults to the prevVal (30), making step size 0.
    const output = interpolateCensoredDemand(input)
    expect(output).toEqual([20, 30, 30, 30])
  })
})
