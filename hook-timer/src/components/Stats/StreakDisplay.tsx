import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import LottieView from 'lottie-react-native';
import { Card } from '../UI/Card';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

interface StreakDisplayProps {
  currentStreak: number;
  bestStreak: number;
}

export function StreakDisplay({ currentStreak, bestStreak }: StreakDisplayProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const isOnFire = currentStreak >= 3;

  return (
    <Card elevated style={styles.card}>
      <View style={styles.content}>
        <View style={styles.streakContainer}>
          <Text style={{ fontSize: 64 }}>
            {isOnFire ? '🔥' : '📅'}
          </Text>

          <View style={styles.textContainer}>
            <Text
              style={{
                ...theme.typography.h1,
                color: theme.colors.textPrimary,
              }}
            >
              {currentStreak}
            </Text>

            <Text
              style={{
                ...theme.typography.body,
                color: theme.colors.textSecondary,
              }}
            >
              jours consécutifs
            </Text>
          </View>
        </View>

        {currentStreak >= bestStreak && currentStreak > 0 && (
          <View
            style={[
              styles.badge,
              { backgroundColor: theme.colors.warning },
            ]}
          >
            <Text
              style={{
                ...theme.typography.small,
                color: '#FFFFFF',
                fontWeight: '600',
              }}
            >
              🏆 Nouveau record !
            </Text>
          </View>
        )}

        <View style={styles.divider} />

        <View style={styles.bestStreakContainer}>
          <Text
            style={{
              ...theme.typography.caption,
              color: theme.colors.textSecondary,
            }}
          >
            Meilleur streak
          </Text>

          <Text
            style={{
              ...theme.typography.h3,
              color: theme.colors.textPrimary,
            }}
          >
            {bestStreak} jours
          </Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: 16,
  },
  content: {
    alignItems: 'center',
  },
  streakContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  textContainer: {
    alignItems: 'flex-start',
  },
  badge: {
    marginTop: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  divider: {
    width: '100%',
    height: 1,
    backgroundColor: '#E4E4E7',
    marginVertical: 16,
  },
  bestStreakContainer: {
    alignItems: 'center',
  },
});
