import { useEffect, useRef } from 'react';
import { useTimerStore } from '../store/useTimerStore';
import { useStatsStore } from '../store/useStatsStore';
import { useHooksStore } from '../store/useHooksStore';
import { useSound } from './useSound';
import { useHaptics } from './useHaptics';
import { useNotifications } from './useNotifications';
import { minutesToSeconds } from '../utils/formatTime';

/**
 * Hook personnalisé qui gère le timer Pomodoro
 * Gère le tick, les notifications, sons et déblocage de hooks
 */
export function useTimer() {
  const timerStore = useTimerStore();
  const statsStore = useStatsStore();
  const hooksStore = useHooksStore();
  const { playSessionComplete, playBreakComplete } = useSound();
  const { triggerSuccess } = useHaptics();
  const { scheduleSessionCompleteNotification } = useNotifications();

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const previousStateRef = useRef(timerStore.state);

  // Gérer le tick du timer
  useEffect(() => {
    if (timerStore.state === 'running') {
      intervalRef.current = setInterval(() => {
        timerStore.tick();
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [timerStore.state]);

  // Gérer la completion de session
  useEffect(() => {
    if (
      previousStateRef.current !== 'completed' &&
      timerStore.state === 'completed'
    ) {
      handleSessionComplete();
    }

    previousStateRef.current = timerStore.state;
  }, [timerStore.state]);

  const handleSessionComplete = async () => {
    triggerSuccess();

    if (timerStore.sessionType === 'focus') {
      // Session de focus complétée
      playSessionComplete();

      // Enregistrer les stats
      const focusTime = minutesToSeconds(25); // TODO: utiliser la vraie durée
      statsStore.recordSession(focusTime);

      // Débloquer un hook
      const unlockedHook = hooksStore.unlockRandomHook();

      if (unlockedHook) {
        // Le modal s'affichera automatiquement via le store
        await scheduleSessionCompleteNotification(
          'Session terminée ! 🎉',
          `Nouveau hook débloqué: "${unlockedHook.text.substring(0, 50)}..."`
        );
      } else {
        await scheduleSessionCompleteNotification(
          'Session terminée ! 🎉',
          'Tous les hooks sont débloqués !'
        );
      }
    } else {
      // Pause complétée
      playBreakComplete();
      await scheduleSessionCompleteNotification(
        'Pause terminée ! ⏰',
        'Prêt pour la prochaine session ?'
      );
    }
  };

  return {
    ...timerStore,
    handleSessionComplete,
  };
}
