import React from 'react';
import { TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';
import { useHaptics } from '../../hooks/useHaptics';

interface IconButtonProps {
  icon: keyof typeof MaterialCommunityIcons.glyphMap;
  onPress: () => void;
  size?: number;
  color?: string;
  backgroundColor?: string;
  disabled?: boolean;
  style?: ViewStyle;
}

export function IconButton({
  icon,
  onPress,
  size = 24,
  color,
  backgroundColor,
  disabled = false,
  style,
}: IconButtonProps) {
  const { triggerLight } = useHaptics();
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const handlePress = () => {
    if (!disabled) {
      triggerLight();
      onPress();
    }
  };

  const defaultColor = color || theme.colors.textPrimary;
  const containerSize = size * 1.5;

  return (
    <TouchableOpacity
      style={[
        {
          width: containerSize,
          height: containerSize,
          borderRadius: containerSize / 2,
          backgroundColor: backgroundColor || 'transparent',
          alignItems: 'center',
          justifyContent: 'center',
        },
        style,
      ]}
      onPress={handlePress}
      disabled={disabled}
      activeOpacity={0.7}
    >
      <MaterialCommunityIcons
        name={icon}
        size={size}
        color={disabled ? theme.colors.textTertiary : defaultColor}
      />
    </TouchableOpacity>
  );
}
