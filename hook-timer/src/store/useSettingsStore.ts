import { create } from 'zustand';
import { AppSettings, SoundType, ThemeType, ColorTheme } from '../types/settings';
import { DEFAULT_SETTINGS, STORAGE_KEYS } from '../utils/constants';
import { saveData, loadData } from '../utils/storage';

interface SettingsStore {
  settings: AppSettings;

  // Actions
  updateTimerConfig: (config: Partial<AppSettings['timer']>) => void;
  updateNotifications: (notifications: Partial<AppSettings['notifications']>) => void;
  updateAppearance: (appearance: Partial<AppSettings['appearance']>) => void;
  updateGoals: (goals: Partial<AppSettings['goals']>) => void;
  setOnboardingComplete: () => void;
  loadSettings: () => Promise<void>;
  saveSettings: () => Promise<void>;
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  settings: DEFAULT_SETTINGS,

  updateTimerConfig: (config) => {
    set((state) => ({
      settings: {
        ...state.settings,
        timer: { ...state.settings.timer, ...config },
      },
    }));
    get().saveSettings();
  },

  updateNotifications: (notifications) => {
    set((state) => ({
      settings: {
        ...state.settings,
        notifications: { ...state.settings.notifications, ...notifications },
      },
    }));
    get().saveSettings();
  },

  updateAppearance: (appearance) => {
    set((state) => ({
      settings: {
        ...state.settings,
        appearance: { ...state.settings.appearance, ...appearance },
      },
    }));
    get().saveSettings();
  },

  updateGoals: (goals) => {
    set((state) => ({
      settings: {
        ...state.settings,
        goals: { ...state.settings.goals, ...goals },
      },
    }));
    get().saveSettings();
  },

  setOnboardingComplete: () => {
    set((state) => ({
      settings: {
        ...state.settings,
        hasCompletedOnboarding: true,
      },
    }));
    get().saveSettings();
  },

  loadSettings: async () => {
    const data = await loadData<AppSettings>(STORAGE_KEYS.SETTINGS);
    if (data) {
      set({ settings: { ...DEFAULT_SETTINGS, ...data } });
    }
  },

  saveSettings: async () => {
    const { settings } = get();
    await saveData(STORAGE_KEYS.SETTINGS, settings);
  },

  resetSettings: () => {
    set({ settings: DEFAULT_SETTINGS });
    get().saveSettings();
  },
}));
