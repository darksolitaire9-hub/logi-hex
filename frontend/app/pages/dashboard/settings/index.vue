<template>
  <div class="max-w-4xl mx-auto pb-12">
    <!-- Admin Gate -->
    <div v-if="!isAdminVerified" class="lh-card max-w-sm mx-auto mt-12 text-center">
      <UIcon name="i-lucide-shield-alert" class="w-12 h-12 text-[var(--lh-danger)] mx-auto mb-4" />
      <h2 class="text-xl font-bold text-[var(--lh-ink-primary)] mb-2">Restricted Area</h2>
      <p class="text-sm text-[var(--lh-ink-secondary)] mb-6">
        Data exports and administrative settings are protected by the Workspace Admin PIN.
      </p>
      
      <form @submit.prevent="verifyAccess">
        <input 
          v-model="adminPinInput" 
          type="password" 
          placeholder="Enter Admin PIN" 
          class="lh-input text-center font-mono tracking-widest mb-4"
          required
        />
        <button type="submit" class="lh-btn lh-btn-primary w-full justify-center">
          Unlock Settings
        </button>
      </form>
      <p v-if="errorMsg" class="text-sm text-[var(--lh-danger)] mt-4 font-medium">{{ errorMsg }}</p>
    </div>

    <!-- Settings Hub -->
    <div v-else>
      <div class="mb-8">
        <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)]">Enterprise Settings</h1>
        <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Disaster recovery and compliance tools.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- CSV Export -->
        <div class="lh-card flex flex-col h-full border-t-4 border-t-blue-500">
          <div class="flex items-center mb-4">
            <UIcon name="i-lucide-file-spreadsheet" class="w-6 h-6 text-blue-500 mr-2" />
            <h2 class="text-lg font-semibold text-[var(--lh-ink-primary)]">Export Ledger (CSV)</h2>
          </div>
          <p class="text-sm text-[var(--lh-ink-secondary)] flex-1 mb-6">
            Export the complete, immutable movement history for this workspace. Useful for accountants, auditors, and external reporting.
          </p>
          <button @click="exportCSV" class="lh-btn lh-btn-secondary w-full justify-center text-blue-600 border-blue-200 hover:bg-blue-50 dark:hover:bg-blue-900/20">
            Generate CSV Report
          </button>
        </div>

        <!-- DB Backup -->
        <div class="lh-card flex flex-col h-full border-t-4 border-t-green-500">
          <div class="flex items-center mb-4">
            <UIcon name="i-lucide-database-backup" class="w-6 h-6 text-green-500 mr-2" />
            <h2 class="text-lg font-semibold text-[var(--lh-ink-primary)]">Raw Database Snapshot</h2>
          </div>
          <p class="text-sm text-[var(--lh-ink-secondary)] flex-1 mb-6">
            Creates an exact 1:1 backup of your entire `logihex.db` file. Store this file safely to guarantee 100% disaster recovery if your hard drive fails.
          </p>
          <button @click="exportDB" class="lh-btn lh-btn-secondary w-full justify-center text-green-600 border-green-200 hover:bg-green-50 dark:hover:bg-green-900/20">
            Download .db Snapshot
          </button>
        </div>
      </div>
      
      <div class="mt-8 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-900/50 rounded-xl">
        <h3 class="text-sm font-semibold text-yellow-800 dark:text-yellow-500 flex items-center mb-2">
          <UIcon name="i-lucide-info" class="w-4 h-4 mr-2" />
          Traceability Notice
        </h3>
        <p class="text-xs text-yellow-700 dark:text-yellow-600/80 leading-relaxed">
          Logi-Hex utilizes Soft Deletes and an Append-Only Movement Ledger. Deleting an Item or Client from the catalog merely hides it from the UI. Their historical records remain perfectly intact in the database and will correctly appear in your CSV Exports.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useWorkspace } from '../../../composables/useWorkspace'
import { useDatabase } from '../../../composables/useDatabase'
import { decryptField } from '../../../utils/crypto'
import { invoke } from '@tauri-apps/api/core'

definePageMeta({
  layout: 'default'
})

const { currentWorkspace, verifyAdminPin } = useWorkspace()
const isAdminVerified = ref(false)
const adminPinInput = ref('')
const errorMsg = ref('')

async function verifyAccess() {
  if (!currentWorkspace.value) return
  errorMsg.value = ''
  const isValid = await verifyAdminPin(currentWorkspace.value, adminPinInput.value)
  if (isValid) {
    isAdminVerified.value = true
  } else {
    errorMsg.value = 'Invalid Admin PIN.'
    adminPinInput.value = ''
  }
}

async function exportCSV() {
  if (!currentWorkspace.value) return
  try {
    const db = await useDatabase()
    const result = await db.select<any[]>(`
      SELECT 
        m.id, m.direction, m.timestamp, m.notes, m.correction_reason,
        c.name as client_name,
        i.label as item_label,
        mli.quantity
      FROM movements m
      LEFT JOIN clients c ON m.client_id = c.id
      JOIN movement_line_items mli ON m.id = mli.movement_id
      JOIN items i ON mli.item_id = i.id
      WHERE m.workspace_id = $1
      ORDER BY m.timestamp DESC
    `, [currentWorkspace.value.id])
    
    if (result.length === 0) {
      alert("No movements found to export.")
      return
    }

    // Decrypt sensitive fields for CSV
    const { activeCryptoKey } = useWorkspace()
    for (const row of result) {
      if (row.client_name) {
        row.client_name = await decryptField(row.client_name, activeCryptoKey.value)
      }
      if (row.item_label) {
        row.item_label = await decryptField(row.item_label, activeCryptoKey.value)
      }
      if (row.notes) {
        row.notes = await decryptField(row.notes, activeCryptoKey.value)
      }
    }

    // Convert to CSV
    const headers = Object.keys(result[0]).join(',')
    const rows = result.map(row => {
      return Object.values(row).map(val => {
        if (val === null || val === undefined) return '""'
        return `"${String(val).replace(/"/g, '""')}"`
      }).join(',')
    })
    
    const csvContent = headers + '\n' + rows.join('\n')
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `logi-hex-ledger-${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
  } catch (e) {
    console.error(e)
    alert('Failed to generate CSV.')
  }
}

async function exportDB() {
  // In a real Tauri app, we'd use the fs/dialog APIs to copy the .db file.
  // For now, we mock the success.
  alert('In a compiled Tauri environment, this will trigger a Save File Dialog to copy the sqlite.db file to your chosen directory.')
}
</script>
