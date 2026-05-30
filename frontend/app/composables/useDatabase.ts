import Database from '@tauri-apps/plugin-sql'

let dbInstance: Database | null = null

export async function useDatabase(): Promise<Database> {
  if (!dbInstance) {
    dbInstance = await Database.load('sqlite:logihex.db')
    
    // Enterprise Data Integrity: Strictly enforce foreign key constraints
    await dbInstance.execute('PRAGMA foreign_keys = ON;')
    
    // Concurrency Hardening: Enable Write-Ahead Logging to prevent SQLITE_BUSY crashes
    await dbInstance.execute('PRAGMA journal_mode = WAL;')
  }
  return dbInstance
}
