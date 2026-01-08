import * as Haptics from 'expo-haptics';
import { useSettingsStore } from '../store/useSettingsStore';

/**
 * Hook personnalisé pour gérer les retours haptiques
 */
export function useHaptics() {
  const settings = useSettingsStore((state) => state.settings);

  const triggerLight = () => {
    if (settings.notifications.vibration) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const triggerMedium = () => {
    if (settings.notifications.vibration) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
  };

  const triggerHeavy = () => {
    if (settings.notifications.vibration) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    }
  };

  const triggerSuccess = () => {
    if (settings.notifications.vibration) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
  };

  const triggerWarning = () => {
    if (settings.notifications.vibration) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    }
  };

  const triggerError = () => {
    if (settings.notifications.vibration) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  };

  return {
    triggerLight,
    triggerMedium,
    triggerHeavy,
    triggerSuccess,
    triggerWarning,
    triggerError,
  };
}
