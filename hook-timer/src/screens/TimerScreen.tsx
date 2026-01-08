import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, StatusBar } from 'react-native';
import { TimerDisplay } from '../components/Timer/TimerDisplay';
import { TimerControls } from '../components/Timer/TimerControls';
import { SessionIndicator } from '../components/Timer/SessionIndicator';
import { HookUnlockModal } from '../components/Hooks/HookUnlockModal';
import { Badge } from '../components/UI/Badge';
import { useTimer } from '../hooks/useTimer';
import { useHooksStore } from '../store/useHooksStore';
import { useStatsStore } from '../store/useStatsStore';
import { useSettingsStore } from '../store/useSettingsStore';
import { themes } from '../theme/themes';
import { minutesToSeconds } from '../utils/formatTime';

export function TimerScreen() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const settings = useSettingsStore((state) => state.settings);

  const timer = useTimer();
  const lastUnlockedHook = useHooksStore((state) => state.lastUnlockedHook);
  const currentStreak = useStatsStore((state) => state.currentStreak);

  const [showUnlockModal, setShowUnlockModal] = useState(false);

  // Afficher le modal quand un nouveau hook est débloqué
  useEffect(() => {
    if (lastUnlockedHook) {
      setShowUnlockModal(true);
    }
  }, [lastUnlockedHook]);

  const getTotalTime = () => {
    if (timer.sessionType === 'focus') {
      return minutesToSeconds(settings.timer.focusDuration);
    } else if (timer.sessionType === 'shortBreak') {
      return minutesToSeconds(settings.timer.shortBreakDuration);
    } else {
      return minutesToSeconds(settings.timer.longBreakDuration);
    }
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <StatusBar
        barStyle={themeMode === 'light' ? 'dark-content' : 'light-content'}
      />

      {/* Streak badge */}
      {currentStreak > 0 && (
        <View style={styles.streakBadge}>
          <Badge
            text={`🔥 ${currentStreak} jours`}
            color={theme.colors.warning}
            textColor="#FFFFFF"
          />
        </View>
      )}

      {/* Session indicator */}
      <View style={styles.sessionIndicator}>
        <SessionIndicator
          currentSession={timer.currentSession}
          totalSessions={settings.timer.sessionsBeforeLongBreak}
        />
      </View>

      {/* Timer display */}
      <View style={styles.timerContainer}>
        <TimerDisplay
          timeRemaining={timer.timeRemaining}
          totalTime={getTotalTime()}
          sessionType={timer.sessionType}
        />
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <TimerControls
          state={timer.state}
          onStart={timer.start}
          onPause={timer.pause}
          onReset={timer.reset}
          onSkip={timer.skip}
        />
      </View>

      {/* Today's sessions count */}
      <View style={styles.todayStats}>
        <Text
          style={{
            ...theme.typography.body,
            color: theme.colors.textSecondary,
          }}
        >
          Aujourd'hui: {timer.totalSessionsToday}/{settings.goals.dailySessionGoal} sessions
        </Text>
      </View>

      {/* Hook unlock modal */}
      <HookUnlockModal
        visible={showUnlockModal}
        hook={lastUnlockedHook}
        onClose={() => setShowUnlockModal(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  streakBadge: {
    position: 'absolute',
    top: 50,
    right: 16,
    zIndex: 10,
  },
  sessionIndicator: {
    marginTop: 60,
    alignItems: 'center',
  },
  timerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  controls: {
    marginBottom: 32,
  },
  todayStats: {
    alignItems: 'center',
    marginBottom: 16,
  },
});
