export interface DailyStats {
  date: string; // YYYY-MM-DD
  sessionsCompleted: number;
  totalFocusTime: number; // en secondes
  hooksUnlocked: string[]; // IDs des hooks débloqués ce jour
}

export interface WeeklyData {
  day: string; // Lun, Mar, etc.
  sessions: number;
}

export interface StatsData {
  dailyStats: Record<string, DailyStats>;
  currentStreak: number;
  bestStreak: number;
  totalSessions: number;
  totalFocusTime: number; // en secondes
}
