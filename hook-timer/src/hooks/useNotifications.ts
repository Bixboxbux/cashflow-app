import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { useSettingsStore } from '../store/useSettingsStore';
import { NOTIFICATION_IDENTIFIERS } from '../utils/constants';

// Configuration par défaut des notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/**
 * Hook personnalisé pour gérer les notifications
 */
export function useNotifications() {
  const settings = useSettingsStore((state) => state.settings);

  useEffect(() => {
    registerForPushNotificationsAsync();
  }, []);

  const registerForPushNotificationsAsync = async () => {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#6366F1',
      });
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Permission for notifications not granted');
      return;
    }
  };

  const scheduleSessionCompleteNotification = async (
    title: string,
    body: string
  ) => {
    if (!settings.notifications.enabled) {
      return;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        sound: settings.notifications.sound === 'bell' ? 'default' : undefined,
        vibrate: settings.notifications.vibration ? [0, 250, 250, 250] : undefined,
      },
      trigger: null, // Immédiat
    });
  };

  const scheduleDailyReminder = async (time: string) => {
    // time format: "HH:mm"
    const [hours, minutes] = time.split(':').map(Number);

    await Notifications.cancelScheduledNotificationAsync(
      NOTIFICATION_IDENTIFIERS.DAILY_REMINDER
    );

    if (settings.goals.reminderEnabled && settings.goals.reminderTime) {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Hook Timer ⏱️',
          body: 'Il est temps de commencer une session productive !',
        },
        trigger: {
          hour: hours,
          minute: minutes,
          repeats: true,
        },
      });
    }
  };

  const cancelAllNotifications = async () => {
    await Notifications.cancelAllScheduledNotificationsAsync();
  };

  return {
    scheduleSessionCompleteNotification,
    scheduleDailyReminder,
    cancelAllNotifications,
  };
}
