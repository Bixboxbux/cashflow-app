import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';
import { formatTime } from '../../utils/formatTime';
import { CircularProgress } from './CircularProgress';
import { SessionType } from '../../types/timer';

interface TimerDisplayProps {
  timeRemaining: number; // en secondes
  totalTime: number; // en secondes
  sessionType: SessionType;
}

export function TimerDisplay({
  timeRemaining,
  totalTime,
  sessionType,
}: TimerDisplayProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const progress = 1 - timeRemaining / totalTime;

  const getSessionLabel = () => {
    switch (sessionType) {
      case 'focus':
        return 'FOCUS';
      case 'shortBreak':
        return 'PAUSE COURTE';
      case 'longBreak':
        return 'PAUSE LONGUE';
    }
  };

  const getSessionColor = () => {
    switch (sessionType) {
      case 'focus':
        return theme.colors.primary;
      case 'shortBreak':
      case 'longBreak':
        return theme.colors.success;
    }
  };

  return (
    <View style={styles.container}>
      <CircularProgress size={300} strokeWidth={12} progress={progress}>
        <View style={styles.content}>
          <Text
            style={{
              ...theme.typography.caption,
              color: getSessionColor(),
              fontWeight: '600',
              marginBottom: theme.spacing.sm,
            }}
          >
            {getSessionLabel()}
          </Text>
          <Text
            style={{
              ...theme.typography.timer,
              color: theme.colors.textPrimary,
            }}
          >
            {formatTime(timeRemaining)}
          </Text>
        </View>
      </CircularProgress>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    alignItems: 'center',
  },
});
