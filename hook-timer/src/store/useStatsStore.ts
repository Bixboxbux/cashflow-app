import { create } from 'zustand';
import { format, subDays } from 'date-fns';
import { DailyStats, StatsData, WeeklyData } from '../types/stats';
import { STORAGE_KEYS } from '../utils/constants';
import { saveData, loadData } from '../utils/storage';
import {
  calculateCurrentStreak,
  calculateBestStreak,
} from '../utils/calculateStreak';

interface StatsStore extends StatsData {
  // Actions
  recordSession: (focusTime: number, hookId?: string) => void;
  updateStreak: () => void;
  getWeeklyData: () => WeeklyData[];
  getTodayStats: () => DailyStats;
  getThisWeekStats: () => {
    totalSessions: number;
    totalFocusTime: number;
  };
  loadStats: () => Promise<void>;
  saveStats: () => Promise<void>;
  resetDailyCounter: () => void;
}

export const useStatsStore = create<StatsStore>((set, get) => ({
  // État initial
  dailyStats: {},
  currentStreak: 0,
  bestStreak: 0,
  totalSessions: 0,
  totalFocusTime: 0,

  recordSession: (focusTime, hookId) => {
    const today = format(new Date(), 'yyyy-MM-dd');
    const state = get();

    const todayStats = state.dailyStats[today] || {
      date: today,
      sessionsCompleted: 0,
      totalFocusTime: 0,
      hooksUnlocked: [],
    };

    const updatedStats: DailyStats = {
      ...todayStats,
      sessionsCompleted: todayStats.sessionsCompleted + 1,
      totalFocusTime: todayStats.totalFocusTime + focusTime,
      hooksUnlocked: hookId
        ? [...todayStats.hooksUnlocked, hookId]
        : todayStats.hooksUnlocked,
    };

    set({
      dailyStats: {
        ...state.dailyStats,
        [today]: updatedStats,
      },
      totalSessions: state.totalSessions + 1,
      totalFocusTime: state.totalFocusTime + focusTime,
    });

    get().updateStreak();
    get().saveStats();
  },

  updateStreak: () => {
    const state = get();
    const currentStreak = calculateCurrentStreak(state.dailyStats);
    const bestStreak = Math.max(
      calculateBestStreak(state.dailyStats),
      state.bestStreak
    );

    set({
      currentStreak,
      bestStreak,
    });
  },

  getWeeklyData: () => {
    const state = get();
    const weekDays = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
    const data: WeeklyData[] = [];

    for (let i = 6; i >= 0; i--) {
      const date = format(subDays(new Date(), i), 'yyyy-MM-dd');
      const dayIndex = (new Date(date).getDay() + 6) % 7; // Convertir dimanche=0 à lundi=0
      const stats = state.dailyStats[date];

      data.push({
        day: weekDays[dayIndex],
        sessions: stats?.sessionsCompleted || 0,
      });
    }

    return data;
  },

  getTodayStats: () => {
    const today = format(new Date(), 'yyyy-MM-dd');
    const state = get();

    return (
      state.dailyStats[today] || {
        date: today,
        sessionsCompleted: 0,
        totalFocusTime: 0,
        hooksUnlocked: [],
      }
    );
  },

  getThisWeekStats: () => {
    const state = get();
    let totalSessions = 0;
    let totalFocusTime = 0;

    for (let i = 0; i < 7; i++) {
      const date = format(subDays(new Date(), i), 'yyyy-MM-dd');
      const stats = state.dailyStats[date];

      if (stats) {
        totalSessions += stats.sessionsCompleted;
        totalFocusTime += stats.totalFocusTime;
      }
    }

    return { totalSessions, totalFocusTime };
  },

  loadStats: async () => {
    const data = await loadData<StatsData>(STORAGE_KEYS.STATS);
    if (data) {
      set(data);
      get().updateStreak();
    }
  },

  saveStats: async () => {
    const state = get();
    await saveData(STORAGE_KEYS.STATS, {
      dailyStats: state.dailyStats,
      currentStreak: state.currentStreak,
      bestStreak: state.bestStreak,
      totalSessions: state.totalSessions,
      totalFocusTime: state.totalFocusTime,
    });
  },

  resetDailyCounter: () => {
    // Cette fonction sera appelée à minuit pour reset le compteur quotidien du timer
    // Les stats restent, mais le compteur du timer se reset
  },
}));
