import { test as base, expect } from '@playwright/test'

// Custom fixture that mocks the Tauri v2 IPC layer in the browser environment.
export const test = base.extend({
  page: async ({ page }, use) => {
    // 1. Inject Tauri mock and remove animation constraints
    await page.addInitScript(() => {
      const STORAGE_KEY = 'TAURI_MOCK_STATE';
      
      const getInitialState = () => ({
        mode: 'INVENTORY',
        workspaces: [{ 
          id: 'ws-1', name: 'Test Inventory', mode: 'INVENTORY', 
          pin_hash: '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4',
          admin_pin_hash: 'f8638b979b2f4f793ddb6dbd197e0ee25a7a6ea32b0ae22f5e3c5d119d839e75'
        }],
        items: [{ id: 'item-1', workspace_id: 'ws-1', label: 'Coffee Beans', unit: 'Kg', base_unit_name: 'Kg', current_stock: 50.0, reorder_point: 10.0, created_at: '2026-05-31T20:00:00Z' }],
        clients: [{ id: 'cl-1', workspace_id: 'ws-1', name: 'Acme Corp', created_at: '2026-05-31T20:00:00Z' }],
        massiveHistory: false
      });

      // Seed initial state immediately if not present or incomplete to avoid race conditions with spec files
      const existing = sessionStorage.getItem(STORAGE_KEY);
      const initialState = getInitialState();
      if (!existing) {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(initialState));
      } else {
        const state = JSON.parse(existing);
        // Ensure all required top-level keys from initial state exist
        let changed = false;
        for (const key in initialState) {
          if (!(key in state)) {
            state[key] = (initialState as any)[key];
            changed = true;
          }
        }
        if (changed) {
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        }
      }

      const invoke = async (cmd: string, args: any) => {
        const payload = args || {};
        
        // Always read fresh from storage to allow SPEC files to mutate state
        const state = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || JSON.stringify(getInitialState()));

        let res: any = [];
        switch (cmd) {
          case 'get_workspaces': res = state.workspaces; break;
          case 'verify_pin': res = payload.pin === '1234'; break;
          case 'verify_admin_pin': res = payload.pin === '5678'; break;
          case 'get_clients': res = state.clients; break;
          case 'get_items': 
             if (payload.cursor) res = [[], []];
             else res = [state.items, []]; 
             break;
          case 'get_low_stock_items': res = state.items.filter((i: any) => i.current_stock <= (i.reorder_point || 0)); break;
          case 'fetch_items_count': res = state.items.length; break;
          case 'fetch_global_history': 
             res = state.massiveHistory ? Array.from({length: 10}, (_, i) => ({id: `m-${i}`, item_label: 'Bulk', quantity: 1, direction: 'SEND', timestamp: new Date().toISOString()})) : [];
             break;
          case 'fetch_history_count': res = state.massiveHistory ? 50000 : 0; break;
          case 'log_movement': 
             const mLines = payload.payload?.lines || [];
             const mDir = payload.payload?.direction;
             console.log(`[Tauri Mock] Logging movement: ${mDir}`, mLines);
             let error = null;
             mLines.forEach((line: any) => {
               const mvItem = state.items.find((i: any) => i.id === line.item_id);
               if (mvItem) {
                 const qty = line.multiplier ? line.quantity * line.multiplier : line.quantity;
                 if (mDir === 'SEND' || mDir === 'USE') {
                   if (mvItem.current_stock < qty) {
                     error = `Insufficient stock: have ${mvItem.current_stock}, want ${qty}`;
                   } else {
                     mvItem.current_stock -= qty;
                   }
                 } else {
                   mvItem.current_stock += qty;
                 }
                 console.log(`[Tauri Mock] Item ${mvItem.id} stock now: ${mvItem.current_stock}`);
               }
             });
             if (error) {
               console.error(`[Tauri Mock] Error: ${error}`);
               throw new Error(error);
             }
             res = 'mv-id'; break;
          case 'get_item_movement_history':
             res = Array.from({length: 30}, () => Math.floor(Math.random() * 10));
             break;
          case 'run_ml_forecast':
             res = JSON.stringify({ engine_name: 'Mock Engine', forecast: [10, 11, 12, 13, 14, 15, 16] });
             break;
          case 'update_workspace_mode':
             state.workspaces[0].mode = payload.mode;
             res = null; break;
          case 'create_workspace':
             const ws = { id: `ws-${Math.random()}`, name: payload.name, mode: payload.mode || 'INVENTORY', created_at: new Date().toISOString() };
             state.workspaces.push(ws); res = ws; break;
          case 'create_client':
             const client = { id: `cl-${Math.random()}`, workspace_id: payload.workspaceId, name: payload.name, info: payload.info, created_at: new Date().toISOString() };
             state.clients.push(client); res = client.id; break;
          case 'delete_client':
             state.clients = state.clients.filter((c: any) => c.id !== payload.id);
             res = null; break;
          case 'create_item':
             const item = { id: `item-${Math.random()}`, workspace_id: payload.workspaceId, label: payload.label, unit: payload.baseUnitName, base_unit_name: payload.baseUnitName, current_stock: 0, reorder_point: payload.reorderPoint, created_at: new Date().toISOString() };
             state.items.push(item); res = item.id; break;
          case 'update_item':
             const upItem = state.items.find((i: any) => i.id === payload.id);
             if (upItem) { upItem.label = payload.label; upItem.unit = payload.unit; upItem.base_unit_name = payload.unit; }
             res = null; break;
          case 'delete_item':
             state.items = state.items.filter((i: any) => i.id !== payload.id);
             res = null; break;
          default: res = [];
        }
        
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        return res;
      };

      // Expose a way for spec files to mutate state without race conditions
      (window as any).mutateMockState = (fn: (state: any) => void) => {
        const existing = sessionStorage.getItem(STORAGE_KEY);
        const state = existing ? JSON.parse(existing) : getInitialState();
        fn(state);
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      };

      const transformCallback = (c: any) => {
        const id = Math.floor(Math.random() * 1000000);
        (window as any)[`_${id}`] = c;
        return id;
      };

      const tauri = {
        invoke,
        transformCallback,
        core: { invoke, transformCallback },
        event: { listen: () => Promise.resolve(() => {}), emit: () => Promise.resolve() }
      };

      (window as any).__TAURI_INTERNALS__ = tauri;
      (window as any).__TAURI__ = tauri;

      // Mock expensive crypto operations to be instant for E2E
      // We overwrite them on the modules or window if possible.
      // Since Nuxt 4 uses ES modules, we might need to overwrite them differently,
      // but let's try window-level mocks first or reliance on global overrides.
      (window as any).LH_MOCK_CRYPTO = true;

      // Mock Audio to prevent NotSupportedError in headless environments
      (window as any).Audio = class {
        play() { return Promise.resolve(); }
        pause() {}
        load() {}
        addEventListener() {}
        removeEventListener() {}
      };

      const style = document.createElement('style');
      style.innerHTML = `*, *::before, *::after { transition: none !important; animation: none !important; } aside { display: flex !important; }`;
      const i = setInterval(() => { if (document.head) { document.head.appendChild(style); clearInterval(i); } }, 5);
    });

    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
    page.on('pageerror', err => console.error('BROWSER ERROR:', err.message));

    await use(page);
  },
  login: async ({ page }, use) => {
    await use(async () => {
      await page.goto('/')
      await page.waitForTimeout(1000)
      await page.locator('text=Test Inventory').click({ force: true })
      await page.locator('input[type="password"]').fill('1234')
      await page.locator('button:has-text("Unlock")').first().click({ force: true })
      await page.waitForURL(/.*dashboard/)
    })
  }
})

export { expect } from '@playwright/test'
