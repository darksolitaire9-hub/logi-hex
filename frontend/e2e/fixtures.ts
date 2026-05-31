import { test as base } from '@playwright/test'

// Custom fixture that mocks the Tauri v2 IPC layer in the browser environment.
export const test = base.extend({
  page: async ({ page }, use) => {
    // Inject Tauri mock object before document loads
    await page.addInitScript(() => {
      // Mock window.__TAURI_INTERNALS__
      const internals: any = {};
      
      // Implement transformCallback exactly as Tauri v2 does in mocks.js
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
        console.log(`[Tauri Mock invoke] cmd=${cmd}`, payload);

        switch (cmd) {
          case 'get_workspaces':
            return [
              {
                id: 'ws-test-1',
                name: 'Test Inventory',
                mode: 'INVENTORY',
                pin_hash: null,
                admin_pin_hash: null,
                timezone: 'UTC',
                created_at: '2026-05-31T20:00:00Z'
              }
            ];
          case 'create_workspace':
            return {
              id: 'ws-test-2',
              name: payload.name || 'Mock Workspace',
              mode: payload.mode || 'INVENTORY',
              timezone: payload.timezone || 'UTC',
              created_at: '2026-05-31T20:00:00Z'
            };
          case 'get_clients':
            return [
              {
                id: 'client-1',
                workspace_id: 'ws-test-1',
                name: 'Acme Corp',
                info: 'E2E Client',
                created_at: '2026-05-31T20:00:00Z',
                deleted_at: null,
                total_items_held: 0
              }
            ];
          case 'get_items':
            return [
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
            ];
          case 'plugin:event|listen':
            // Mock event subscription
            return 0; // return a subscription ID
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
  }
})

export { expect } from '@playwright/test'
