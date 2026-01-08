import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Card } from '../UI/Card';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

interface StatsCardProps {
  icon: keyof typeof MaterialCommunityIcons.glyphMap;
  label: string;
  value: string | number;
  subtitle?: string;
  color?: string;
}

export function StatsCard({
  icon,
  label,
  value,
  subtitle,
  color,
}: StatsCardProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const iconColor = color || theme.colors.primary;

  return (
    <Card elevated style={styles.card}>
      <View style={styles.content}>
        <View
          style={[
            styles.iconContainer,
            { backgroundColor: `${iconColor}20` },
          ]}
        >
          <MaterialCommunityIcons
            name={icon}
            size={24}
            color={iconColor}
          />
        </View>

        <View style={styles.textContainer}>
          <Text
            style={{
              ...theme.typography.caption,
              color: theme.colors.textSecondary,
            }}
          >
            {label}
          </Text>

          <Text
            style={{
              ...theme.typography.h2,
              color: theme.colors.textPrimary,
              marginTop: 4,
            }}
          >
            {value}
          </Text>

          {subtitle && (
            <Text
              style={{
                ...theme.typography.small,
                color: theme.colors.textTertiary,
                marginTop: 2,
              }}
            >
              {subtitle}
            </Text>
          )}
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  textContainer: {
    flex: 1,
  },
});
