import type { DetectionMode } from '@/domain/disease';
import { getLocalDatabase } from './localDatabase';

export type AppLanguage = 'en' | 'bn';
export type PreferenceKey = 'language' | 'detectionMode' | 'onboardingComplete';

export interface PreferencesRepository {
  get(key: PreferenceKey): Promise<string | null>;
  set(key: PreferenceKey, value: string): Promise<void>;
}

export const preferencesRepository: PreferencesRepository = {
  async get(key) {
    const db = await getLocalDatabase();
    const row = await db.getFirstAsync<{ value: string }>(
      'SELECT value FROM app_preferences WHERE key = ?',
      key,
    );
    return row?.value ?? null;
  },
  async set(key, value) {
    const db = await getLocalDatabase();
    await db.runAsync(
      'INSERT INTO app_preferences (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value',
      key,
      value,
    );
  },
};

export async function saveLanguage(language: AppLanguage) {
  return preferencesRepository.set('language', language);
}

export async function saveDetectionMode(mode: DetectionMode) {
  return preferencesRepository.set('detectionMode', mode);
}
