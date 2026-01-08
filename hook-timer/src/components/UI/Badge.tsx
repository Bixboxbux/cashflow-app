import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

interface BadgeProps {
  text: string;
  color?: string;
  textColor?: string;
  style?: ViewStyle;
}

export function Badge({ text, color, textColor, style }: BadgeProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  return (
    <View
      style={[
        {
          backgroundColor: color || theme.colors.primary,
          borderRadius: theme.radius.full,
          paddingVertical: theme.spacing.xs,
          paddingHorizontal: theme.spacing.sm,
          alignSelf: 'flex-start',
        },
        style,
      ]}
    >
      <Text
        style={{
          ...theme.typography.small,
          color: textColor || '#FFFFFF',
          fontWeight: '600',
        }}
      >
        {text}
      </Text>
    </View>
  );
}
