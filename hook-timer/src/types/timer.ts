export type TimerState = 'idle' | 'running' | 'paused' | 'completed';
export type SessionType = 'focus' | 'shortBreak' | 'longBreak';

export interface TimerConfig {
  focusDuration: number; // en minutes
  shortBreakDuration: number; // en minutes
  longBreakDuration: number; // en minutes
  sessionsBeforeLongBreak: number;
  autoStartBreaks: boolean;
  autoStartSessions: boolean;
}

export interface TimerData {
  state: TimerState;
  sessionType: SessionType;
  timeRemaining: number; // en secondes
  currentSession: number; // 1-4 (ou selon config)
  totalSessionsToday: number;
  startedAt?: Date;
}
