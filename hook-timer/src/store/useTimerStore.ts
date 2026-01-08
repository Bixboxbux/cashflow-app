import { create } from 'zustand';
import { TimerState, SessionType, TimerData } from '../types/timer';
import { minutesToSeconds } from '../utils/formatTime';
import { STORAGE_KEYS } from '../utils/constants';
import { saveData, loadData } from '../utils/storage';
import { useSettingsStore } from './useSettingsStore';

interface TimerStore extends TimerData {
  // Actions
  start: () => void;
  pause: () => void;
  reset: () => void;
  skip: () => void;
  tick: () => void;
  completeSession: () => void;
  loadTimerData: () => Promise<void>;
  saveTimerData: () => Promise<void>;
}

export const useTimerStore = create<TimerStore>((set, get) => ({
  // État initial
  state: 'idle',
  sessionType: 'focus',
  timeRemaining: minutesToSeconds(25),
  currentSession: 1,
  totalSessionsToday: 0,
  startedAt: undefined,

  start: () => {
    const state = get();
    if (state.state === 'idle' || state.state === 'paused') {
      set({
        state: 'running',
        startedAt: state.state === 'idle' ? new Date() : state.startedAt,
      });
      get().saveTimerData();
    }
  },

  pause: () => {
    const state = get();
    if (state.state === 'running') {
      set({ state: 'paused' });
      get().saveTimerData();
    }
  },

  reset: () => {
    const settings = useSettingsStore.getState().settings;
    const sessionType = get().sessionType;

    let duration: number;
    if (sessionType === 'focus') {
      duration = settings.timer.focusDuration;
    } else if (sessionType === 'shortBreak') {
      duration = settings.timer.shortBreakDuration;
    } else {
      duration = settings.timer.longBreakDuration;
    }

    set({
      state: 'idle',
      timeRemaining: minutesToSeconds(duration),
      startedAt: undefined,
    });
    get().saveTimerData();
  },

  skip: () => {
    const state = get();
    const settings = useSettingsStore.getState().settings;

    // Déterminer la prochaine session
    if (state.sessionType === 'focus') {
      // Passer à la pause
      const isLongBreak = state.currentSession >= settings.timer.sessionsBeforeLongBreak;
      const nextSessionType: SessionType = isLongBreak ? 'longBreak' : 'shortBreak';
      const duration = isLongBreak
        ? settings.timer.longBreakDuration
        : settings.timer.shortBreakDuration;

      set({
        sessionType: nextSessionType,
        timeRemaining: minutesToSeconds(duration),
        state: settings.timer.autoStartBreaks ? 'running' : 'idle',
        startedAt: settings.timer.autoStartBreaks ? new Date() : undefined,
      });
    } else {
      // Passer à la prochaine session de focus
      const state = get();
      const isLongBreak = state.sessionType === 'longBreak';
      const nextSession = isLongBreak ? 1 : state.currentSession + 1;

      set({
        sessionType: 'focus',
        timeRemaining: minutesToSeconds(settings.timer.focusDuration),
        currentSession: nextSession,
        state: settings.timer.autoStartSessions ? 'running' : 'idle',
        startedAt: settings.timer.autoStartSessions ? new Date() : undefined,
      });
    }

    get().saveTimerData();
  },

  tick: () => {
    const state = get();
    if (state.state !== 'running') return;

    const newTimeRemaining = Math.max(0, state.timeRemaining - 1);

    if (newTimeRemaining === 0) {
      get().completeSession();
    } else {
      set({ timeRemaining: newTimeRemaining });
    }
  },

  completeSession: () => {
    const state = get();
    const settings = useSettingsStore.getState().settings;

    set({ state: 'completed' });

    // Si c'était une session de focus, incrémenter le compteur
    if (state.sessionType === 'focus') {
      set({ totalSessionsToday: state.totalSessionsToday + 1 });
    }

    // Auto-skip vers la prochaine session après un court délai
    setTimeout(() => {
      get().skip();
    }, 1000);
  },

  loadTimerData: async () => {
    const data = await loadData<TimerData>(STORAGE_KEYS.TIMER_DATA);
    if (data) {
      set({
        state: 'idle', // Toujours remettre à idle au chargement
        sessionType: data.sessionType,
        timeRemaining: data.timeRemaining,
        currentSession: data.currentSession,
        totalSessionsToday: data.totalSessionsToday,
      });
    }
  },

  saveTimerData: async () => {
    const state = get();
    await saveData(STORAGE_KEYS.TIMER_DATA, {
      state: state.state,
      sessionType: state.sessionType,
      timeRemaining: state.timeRemaining,
      currentSession: state.currentSession,
      totalSessionsToday: state.totalSessionsToday,
      startedAt: state.startedAt,
    });
  },
}));
