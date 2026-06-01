import { test as base, expect } from '@playwright/test'

// Custom fixture that mocks the Tauri v2 IPC layer in the browser environment.
export const test = base.extend({
  page: async ({ page }, use) => {
    // Inject Tauri mock object before document loads
    await page.addInitScript(() => {
      // Clear state for fresh start if it's the first load in this context
      if (!window.name) {
        sessionStorage.removeItem('TAURI_MOCK_STATE');
        window.name = 'playwright-context';
      }
      // Mock window.__TAURI_INTERNALS__
      const internals: any = {};
      
      internals.transformCallback = (callback: any, once = false) => {
        const identifier = window.crypto.getRandomValues(new Uint32Array(1))[0];
        const prop = `_${identifier}`;
        Object.defineProperty(window, prop, {
          value: (result: any) => {
            if (once) {
              Reflect.deleteProperty(window, prop);
            }
            return callback && callback(result);
          },
          writable: false,
          configurable: true
        });
        return identifier;
      };

      // Implement invoke interceptor
      internals.invoke = async (cmd: string, args: any) => {
        const payload = args || {};
        
        // Load state from sessionStorage
        const savedState = sessionStorage.getItem('TAURI_MOCK_STATE');
        const state = savedState ? JSON.parse(savedState) : {
          workspaces: [
            {
              id: 'ws-test-1',
              name: 'Test Inventory',
              mode: 'INVENTORY',
              pin_hash: '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', // SHA-256 of '1234'
              admin_pin_hash: 'ef7276432e1966c0584882e3f4c60f27914942e617d9198642a8b9e6924840e5', // SHA-256 of '5678'
              timezone: 'UTC',
              created_at: '2026-05-31T20:00:00Z'
            }
          ],
          clients: [
            {
              id: 'client-1',
              workspace_id: 'ws-test-1',
              name: 'Acme Corp',
              info: 'E2E Client',
              created_at: '2026-05-31T20:00:00Z',
              deleted_at: null,
              total_items_held: 0
            }
          ],
          items: [
            {
              id: 'item-1',
              workspace_id: 'ws-test-1',
              label: 'Coffee Beans',
              unit: 'Kg',
              current_stock: 50.0,
              reorder_point: 10.0,
              created_at: '2026-05-31T20:00:00Z',
              deleted_at: null,
              base_unit_name: 'Kg',
              primary_uom_id: null
            }
          ]
        };

        const saveState = () => sessionStorage.setItem('TAURI_MOCK_STATE', JSON.stringify(state));

        // Apply mode override from window flag if present
        if ((window as any).STRESS_TEST_MODE) {
          state.workspaces[0].mode = (window as any).STRESS_TEST_MODE;
        }

        console.log(`[Tauri Mock invoke] cmd=${cmd}`, payload);

        switch (cmd) {
          case 'get_workspaces':
            return state.workspaces;
          case 'create_workspace':
            const ws = {
              id: `ws-${Math.random()}`,
              name: payload.name || 'Mock Workspace',
              mode: payload.mode || 'INVENTORY',
              timezone: payload.timezone || 'UTC',
              created_at: '2026-05-31T20:00:00Z'
            };
            state.workspaces.push(ws);
            saveState();
            return ws;
          case 'update_workspace_mode':
            const targetWs = state.workspaces.find((w: any) => w.id === payload.id);
            if (targetWs) targetWs.mode = payload.mode;
            saveState();
            return null;
          case 'get_clients':
            return state.clients;
          case 'create_client':
            const newClient = {
              id: `client-${Math.random()}`,
              workspace_id: payload.workspaceId || 'ws-test-1',
              name: payload.name,
              info: payload.notes || '',
              created_at: new Date().toISOString(),
              deleted_at: null,
              total_items_held: 0
            };
            state.clients.push(newClient);
            saveState();
            return newClient.id;
          case 'get_items':
            if ((window as any).STRESS_TEST_MASSIVE_ITEMS) {
              const bulkItems = Array.from({ length: 5000 }, (_, i) => ({
                id: `item-${i}`,
                workspace_id: 'ws-test-1',
                label: `Bulk Item ${i}`,
                unit: 'pcs',
                current_stock: 100.0,
                reorder_point: 5.0,
                created_at: '2026-05-31T20:00:00Z',
                deleted_at: null,
                base_unit_name: 'pcs',
                primary_uom_id: null
              }));
              return [bulkItems, []];
            }
            return [state.items, []];
          case 'create_item':
            const newItem = {
              id: `item-${Math.random()}`,
              workspace_id: payload.workspaceId || 'ws-test-1',
              label: payload.label,
              unit: payload.unit,
              current_stock: 0,
              reorder_point: payload.reorderPoint || null,
              created_at: new Date().toISOString(),
              deleted_at: null,
              base_unit_name: payload.unit,
              primary_uom_id: null
            };
            state.items.push(newItem);
            saveState();
            return newItem.id;
          case 'update_item':
            const item = state.items.find((i: any) => i.id === payload.id);
            if (item) {
              item.label = payload.label;
              item.unit = payload.unit;
              item.base_unit_name = payload.unit;
            }
            saveState();
            return null;
          case 'log_movement':
            await new Promise(resolve => setTimeout(resolve, 50));
            console.log(`[Tauri Mock] log_movement notes: "${payload.payload?.notes}"`);
            if (payload.payload?.notes === 'STRESS_TEST_LOCK') throw new Error('Database is locked');
            
            // Update stock in state
            if (payload.payload?.lines) {
              for (const line of payload.payload.lines) {
                const item = state.items.find((i: any) => i.id === line.item_id);
                if (item) {
                  if (payload.payload.direction === 'SEND' || payload.payload.direction === 'USE') {
                    if (line.quantity > 1000) throw new Error(`Insufficient stock for ${item.label}`);
                    item.current_stock -= line.quantity;
                  } else {
                    item.current_stock += line.quantity;
                  }
                }
              }
            }
            saveState();
            return 'mv-test-uuid';
          case 'get_low_stock_items':
            return state.items.filter((i: any) => i.reorder_point !== null && i.current_stock <= i.reorder_point);
          case 'fetch_global_history':
            if ((window as any).STRESS_TEST_MASSIVE_HISTORY) {
              return Array.from({ length: 50000 }, (_, i) => ({
                id: `mv-${i}`,
                timestamp: new Date(Date.now() - i * 60000).toISOString(),
                item_label: `Bulk Item ${i % 100}`,
                quantity: Math.floor(Math.random() * 10) + 1,
                direction: i % 2 === 0 ? 'SEND' : 'RECEIVE',
                notes: `Bulk record ${i}`
              }));
            }
            return [];
          case 'fetch_client_history':
            return [];
          case 'run_ml_forecast':
            return JSON.stringify({
              forecast: Array.from({ length: payload.horizon || 30 }, () => Math.random() * 100),
              engine_name: 'Mock Engine'
            });
          case 'plugin:event|listen':
            return 0;
          default:
            console.warn(`[Tauri Mock] Unmocked command: ${cmd}`, payload);
            return null;
        }
      };

      // Mock window metadata for window label checking
      internals.metadata = {
        windows: [{ label: 'main' }],
        currentWindow: { label: 'main' },
        webviews: [{ windowLabel: 'main', label: 'main' }],
        currentWebview: { windowLabel: 'main', label: 'main' }
      };

      (window as any).__TAURI_INTERNALS__ = internals;
      (window as any).__TAURI__ = {
        core: {
          invoke: internals.invoke,
          transformCallback: internals.transformCallback
        }
      };
    });

    await use(page);
  },
  login: async ({ page }, use) => {
    await use(async () => {
      await page.goto('/')
      // Wait for workspace to appear
      await page.waitForSelector('text=Test Inventory')
      await page.locator('text=Test Inventory').click()
      await page.locator('input[type="password"]').fill('1234')
      await page.locator('button:has-text("Unlock")').click()
      // Use the page.waitForURL instead of expect for easier referencing inside fixture
      await page.waitForURL(/.*dashboard/)
    })
  }
})

export { expect } from '@playwright/test'
