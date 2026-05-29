import Database from '@tauri-apps/plugin-sql'

let dbInstance: Database | null = null

export async function useDatabase(): Promise<Database> {
  if (!dbInstance) {
    dbInstance = await Database.load('sqlite:logihex.db')
  }
  return dbInstance
}
