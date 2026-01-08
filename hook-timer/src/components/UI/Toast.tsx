import React, { useEffect, useRef } from 'react';
import { Animated, Text, StyleSheet } from 'react-native';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

interface ToastProps {
  message: string;
  visible: boolean;
  duration?: number;
  type?: 'info' | 'success' | 'warning' | 'error';
}

export function Toast({
  message,
  visible,
  duration = 3000,
  type = 'info',
}: ToastProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(-100)).current;

  useEffect(() => {
    if (visible) {
      // Show animation
      Animated.parallel([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.spring(translateY, {
          toValue: 0,
          useNativeDriver: true,
        }),
      ]).start();

      // Auto hide
      const timer = setTimeout(() => {
        hideToast();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [visible]);

  const hideToast = () => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: -100,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const getBackgroundColor = () => {
    switch (type) {
      case 'success':
        return theme.colors.success;
      case 'warning':
        return theme.colors.warning;
      case 'error':
        return theme.colors.error;
      default:
        return theme.colors.primary;
    }
  };

  if (!visible) return null;

  return (
    <Animated.View
      style={[
        {
          position: 'absolute',
          top: 50,
          left: theme.spacing.lg,
          right: theme.spacing.lg,
          backgroundColor: getBackgroundColor(),
          borderRadius: theme.radius.md,
          padding: theme.spacing.md,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 3.84,
          elevation: 5,
          zIndex: 1000,
          opacity,
          transform: [{ translateY }],
        },
      ]}
    >
      <Text style={{ ...theme.typography.body, color: '#FFFFFF' }}>
        {message}
      </Text>
    </Animated.View>
  );
}
