import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

const FEATURES = [
  { label: 'Timer Pomodoro', free: true, premium: true },
  { label: '50 hooks gratuits', free: true, premium: true },
  { label: '450 hooks premium', free: false, premium: true },
  { label: 'Statistiques de base', free: true, premium: true },
  { label: 'Statistiques avancées', free: false, premium: true },
  { label: 'Thème par défaut', free: true, premium: true },
  { label: '5 thèmes de couleur', free: false, premium: true },
  { label: 'Widget Android', free: false, premium: true },
];

export function FeatureComparison() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.surfaceElevated,
          borderColor: theme.colors.border,
        },
      ]}
    >
      {/* Header */}
      <View style={styles.headerRow}>
        <View style={styles.featureColumn} />
        <View style={styles.planColumn}>
          <Text
            style={{
              ...theme.typography.bodyBold,
              color: theme.colors.textSecondary,
            }}
          >
            Gratuit
          </Text>
        </View>
        <View style={styles.planColumn}>
          <Text
            style={{
              ...theme.typography.bodyBold,
              color: theme.colors.primary,
            }}
          >
            Premium
          </Text>
        </View>
      </View>

      {/* Features */}
      {FEATURES.map((feature, index) => (
        <View
          key={index}
          style={[
            styles.featureRow,
            {
              borderTopColor: theme.colors.border,
            },
          ]}
        >
          <View style={styles.featureColumn}>
            <Text
              style={{
                ...theme.typography.caption,
                color: theme.colors.textPrimary,
              }}
            >
              {feature.label}
            </Text>
          </View>

          <View style={styles.planColumn}>
            {feature.free ? (
              <MaterialCommunityIcons
                name="check-circle"
                size={20}
                color={theme.colors.success}
              />
            ) : (
              <MaterialCommunityIcons
                name="close-circle"
                size={20}
                color={theme.colors.textTertiary}
              />
            )}
          </View>

          <View style={styles.planColumn}>
            {feature.premium ? (
              <MaterialCommunityIcons
                name="check-circle"
                size={20}
                color={theme.colors.success}
              />
            ) : (
              <MaterialCommunityIcons
                name="close-circle"
                size={20}
                color={theme.colors.textTertiary}
              />
            )}
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 16,
    marginVertical: 16,
  },
  headerRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  featureRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    borderTopWidth: 1,
  },
  featureColumn: {
    flex: 2,
  },
  planColumn: {
    flex: 1,
    alignItems: 'center',
  },
});
