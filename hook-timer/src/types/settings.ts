import { TimerConfig } from './timer';

export type SoundType = 'bell' | 'chime' | 'gong';
export type ThemeType = 'dark' | 'light' | 'system';
export type ColorTheme = 'default' | 'ocean' | 'forest' | 'sunset' | 'midnight';

export interface NotificationSettings {
  enabled: boolean;
  sound: SoundType;
  vibration: boolean;
}

export interface AppearanceSettings {
  theme: ThemeType;
  colorTheme: ColorTheme; // Premium feature
}

export interface GoalSettings {
  dailySessionGoal: number; // 1-12
  reminderTime?: string; // Format HH:mm
  reminderEnabled: boolean;
}

export interface AppSettings {
  timer: TimerConfig;
  notifications: NotificationSettings;
  appearance: AppearanceSettings;
  goals: GoalSettings;
  hasCompletedOnboarding: boolean;
}
