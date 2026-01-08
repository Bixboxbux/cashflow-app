import { TimerConfig } from '../types/timer';
import { AppSettings } from '../types/settings';

export const DEFAULT_TIMER_CONFIG: TimerConfig = {
  focusDuration: 25,
  shortBreakDuration: 5,
  longBreakDuration: 15,
  sessionsBeforeLongBreak: 4,
  autoStartBreaks: false,
  autoStartSessions: false,
};

export const DEFAULT_SETTINGS: AppSettings = {
  timer: DEFAULT_TIMER_CONFIG,
  notifications: {
    enabled: true,
    sound: 'bell',
    vibration: true,
  },
  appearance: {
    theme: 'dark',
    colorTheme: 'default',
  },
  goals: {
    dailySessionGoal: 8,
    reminderEnabled: false,
  },
  hasCompletedOnboarding: false,
};

export const PREMIUM_PRODUCT_ID = 'hook_timer_premium';
export const PREMIUM_PRICE = '4.99€';

export const STORAGE_KEYS = {
  SETTINGS: '@hook_timer/settings',
  TIMER_DATA: '@hook_timer/timer_data',
  HOOKS: '@hook_timer/hooks',
  STATS: '@hook_timer/stats',
  PREMIUM: '@hook_timer/premium',
} as const;

export const NOTIFICATION_IDENTIFIERS = {
  SESSION_COMPLETE: 'session-complete',
  BREAK_COMPLETE: 'break-complete',
  DAILY_REMINDER: 'daily-reminder',
} as const;
