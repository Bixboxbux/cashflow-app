import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

interface SessionIndicatorProps {
  currentSession: number;
  totalSessions: number;
}

export function SessionIndicator({
  currentSession,
  totalSessions,
}: SessionIndicatorProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  return (
    <View style={styles.container}>
      <Text
        style={{
          ...theme.typography.body,
          color: theme.colors.textSecondary,
          marginBottom: theme.spacing.md,
        }}
      >
        Session {currentSession}/{totalSessions}
      </Text>

      <View style={styles.dotsContainer}>
        {Array.from({ length: totalSessions }).map((_, index) => (
          <View
            key={index}
            style={[
              styles.dot,
              {
                backgroundColor:
                  index < currentSession
                    ? theme.colors.primary
                    : theme.colors.border,
              },
            ]}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  dotsContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
});
