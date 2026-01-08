import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  ScrollView,
} from 'react-native';
import { StatsCard } from '../components/Stats/StatsCard';
import { WeeklyChart } from '../components/Stats/WeeklyChart';
import { StreakDisplay } from '../components/Stats/StreakDisplay';
import { PremiumBanner } from '../components/Premium/PremiumBanner';
import { PaywallModal } from '../components/Premium/PaywallModal';
import { useStatsStore } from '../store/useStatsStore';
import { useSettingsStore } from '../store/useSettingsStore';
import { usePremiumStore } from '../store/usePremiumStore';
import { themes } from '../theme/themes';
import { formatDuration } from '../utils/formatTime';

export function StatsScreen() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const isPremium = usePremiumStore((state) => state.isPremium);

  const statsStore = useStatsStore();
  const todayStats = statsStore.getTodayStats();
  const weekStats = statsStore.getThisWeekStats();

  const [showPaywall, setShowPaywall] = useState(false);

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <StatusBar
        barStyle={themeMode === 'light' ? 'dark-content' : 'light-content'}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Streak */}
        <StreakDisplay
          currentStreak={statsStore.currentStreak}
          bestStreak={statsStore.bestStreak}
        />

        {/* Today stats */}
        <View style={styles.row}>
          <StatsCard
            icon="clock-outline"
            label="Aujourd'hui"
            value={todayStats.sessionsCompleted}
            subtitle="sessions"
            color={theme.colors.primary}
          />
          <StatsCard
            icon="fire"
            label="Temps focus"
            value={formatDuration(todayStats.totalFocusTime)}
            color={theme.colors.warning}
          />
        </View>

        {/* Week stats */}
        <View style={styles.row}>
          <StatsCard
            icon="calendar-week"
            label="Cette semaine"
            value={weekStats.totalSessions}
            subtitle="sessions"
            color={theme.colors.secondary}
          />
          <StatsCard
            icon="timer-outline"
            label="Temps total"
            value={formatDuration(weekStats.totalFocusTime)}
            color={theme.colors.success}
          />
        </View>

        {/* Weekly chart */}
        <WeeklyChart />

        {/* Premium banner */}
        {!isPremium && (
          <PremiumBanner onPress={() => setShowPaywall(true)} />
        )}
      </ScrollView>

      {/* Paywall modal */}
      <PaywallModal
        visible={showPaywall}
        onClose={() => setShowPaywall(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
});
