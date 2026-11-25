import * as SQLite from 'expo-sqlite';

let databasePromise: Promise<SQLite.SQLiteDatabase> | null = null;

export async function getLocalDatabase(): Promise<SQLite.SQLiteDatabase> {
  if (!databasePromise) {
    databasePromise = (async () => {
      const database = await SQLite.openDatabaseAsync('krishok-ai.db');
      await database.execAsync(`
        PRAGMA journal_mode = WAL;
        CREATE TABLE IF NOT EXISTS detection_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
          image_uri TEXT NOT NULL,
          created_at TEXT NOT NULL,
          predicted_class_id INTEGER NOT NULL CHECK(predicted_class_id BETWEEN 0 AND 5),
          confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
          mode TEXT NOT NULL CHECK(mode IN ('online', 'offline'))
        );
        CREATE TABLE IF NOT EXISTS app_preferences (
          key TEXT PRIMARY KEY NOT NULL,
          value TEXT NOT NULL
        );
      `);
      return database;
    })().catch((error) => {
      databasePromise = null;
      throw error;
    });
  }
  return databasePromise;
}
