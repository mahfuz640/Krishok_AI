import { create } from 'zustand';
import i18n from '@/core/localization/i18n';
import type { DetectionMode } from '@/domain/disease';
import { preferencesRepository, type AppLanguage } from '@/data/preferencesRepository';

interface AppState {
  language: AppLanguage;
  detectionMode: DetectionMode;
  onboardingComplete: boolean;
  hydrated: boolean;
  storageError: boolean;
  hydrate: () => Promise<void>;
  setLanguage: (language: AppLanguage) => Promise<void>;
  setDetectionMode: (mode: DetectionMode) => Promise<void>;
  finishOnboarding: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  language: 'bn',
  detectionMode: 'offline',
  onboardingComplete: false,
  hydrated: false,
  storageError: false,
  async hydrate() {
    try {
      const [language, mode, onboarding] = await Promise.all([
        preferencesRepository.get('language'),
        preferencesRepository.get('detectionMode'),
        preferencesRepository.get('onboardingComplete'),
      ]);
      const safeLanguage: AppLanguage = language === 'en' ? 'en' : 'bn';
      const safeMode: DetectionMode = mode === 'online' ? 'online' : 'offline';
      await i18n.changeLanguage(safeLanguage);
      set({
        language: safeLanguage,
        detectionMode: safeMode,
        onboardingComplete: onboarding === 'true',
        hydrated: true,
      });
    } catch {
      set({ hydrated: true, storageError: true });
    }
  },
  async setLanguage(language) {
    await i18n.changeLanguage(language);
    set({ language });
    try {
      await preferencesRepository.set('language', language);
    } catch {
      set({ storageError: true });
    }
  },
  async setDetectionMode(detectionMode) {
    set({ detectionMode });
    try {
      await preferencesRepository.set('detectionMode', detectionMode);
    } catch {
      set({ storageError: true });
    }
  },
  async finishOnboarding() {
    set({ onboardingComplete: true });
    try {
      await preferencesRepository.set('onboardingComplete', 'true');
    } catch {
      set({ storageError: true });
    }
  },
}));
