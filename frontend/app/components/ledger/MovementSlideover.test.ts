import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MovementSlideover from './MovementSlideover.vue'

// Mock the Nuxt composables
vi.mock('../../composables/useItems', () => ({
  useItems: () => ({
    items: [
      { id: '1', label: 'Coffee Beans', base_unit_name: 'Kg', uoms: [] },
      { id: '2', label: 'Euro Pallet', base_unit_name: 'Pieces', primary_uom_id: 'uom1', uoms: [{ id: 'uom1', unit_name: 'Pallets', multiplier: 100 }] }
    ],
    loading: false,
    fetchItems: vi.fn()
  })
}))

vi.mock('../../composables/useLedger', () => ({
  useLedger: () => ({
    logMovement: vi.fn(),
    loading: false
  })
}))

vi.mock('../../utils/errorDomains', () => ({
  useSelfHealingUI: () => ({
    handleUXError: vi.fn(),
    handleUXSuccess: vi.fn()
  })
}))

// Mock UIcon and Nuxt UI components
const globalMocks = {
  stubs: {
    USlideover: {
      template: '<div><slot></slot></div>',
      props: ['modelValue']
    },
    UIcon: { template: '<span></span>' },
    UButton: { template: '<button></button>' },
    NuxtLink: { template: '<a><slot></slot></a>' }
  }
}

describe('MovementSlideover.vue', () => {
  it('renders structural elements correctly using data-testid', () => {
    const wrapper = mount(MovementSlideover, {
      props: {
        modelValue: true,
        clientId: 'client-1',
        clientName: 'Test Client',
        isSending: true
      },
      global: globalMocks
    })

    // The component should render the item labels structurally, without depending on translation
    expect(wrapper.find('[data-testid="item-label-1"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="item-label-1"]').text()).toBe('Coffee Beans')

    expect(wrapper.find('[data-testid="item-label-2"]').exists()).toBe(true)
    
    // Check if the UOM select renders for items with alternate UOMs
    expect(wrapper.find('[data-testid="uom-select-2"]').exists()).toBe(true)
    
    // Check if the confirm button exists
    expect(wrapper.find('[data-testid="confirm-movement-btn"]').exists()).toBe(true)
  })

  it('binds quantities accurately to inputs', async () => {
    const wrapper = mount(MovementSlideover, {
      props: {
        modelValue: true,
        clientId: 'client-1',
        clientName: 'Test Client',
        isSending: true
      },
      global: globalMocks
    })

    const input = wrapper.find('[data-testid="qty-input-1"]')
    expect(input.exists()).toBe(true)
    
    await input.setValue(50)
    expect((input.element as HTMLInputElement).value).toBe('50')
  })
})
