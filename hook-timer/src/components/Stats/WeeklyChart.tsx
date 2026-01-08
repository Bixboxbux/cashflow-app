import React from 'react';
import { View, Text, Dimensions, StyleSheet } from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { Card } from '../UI/Card';
import { useStatsStore } from '../../store/useStatsStore';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

const screenWidth = Dimensions.get('window').width;

export function WeeklyChart() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const weeklyData = useStatsStore((state) => state.getWeeklyData());

  const chartData = {
    labels: weeklyData.map((d) => d.day),
    datasets: [
      {
        data: weeklyData.map((d) => d.sessions),
      },
    ],
  };

  const chartConfig = {
    backgroundColor: theme.colors.surface,
    backgroundGradientFrom: theme.colors.surface,
    backgroundGradientTo: theme.colors.surface,
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(99, 102, 241, ${opacity})`,
    labelColor: (opacity = 1) => {
      const color = theme.colors.textSecondary;
      return color;
    },
    style: {
      borderRadius: 16,
    },
    propsForBackgroundLines: {
      strokeDasharray: '',
      stroke: theme.colors.border,
      strokeWidth: 1,
    },
    barPercentage: 0.6,
  };

  return (
    <Card elevated style={styles.card}>
      <Text
        style={{
          ...theme.typography.h3,
          color: theme.colors.textPrimary,
          marginBottom: theme.spacing.md,
        }}
      >
        Cette semaine
      </Text>

      <BarChart
        data={chartData}
        width={screenWidth - 64}
        height={200}
        chartConfig={chartConfig}
        fromZero
        showValuesOnTopOfBars
        withInnerLines
        yAxisLabel=""
        yAxisSuffix=""
        style={{
          borderRadius: 16,
        }}
      />
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: 16,
  },
});
