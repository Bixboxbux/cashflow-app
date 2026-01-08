import React from 'react';
import { View, StyleSheet, TouchableOpacity, Text } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';
import { TimerState } from '../../types/timer';
import { useHaptics } from '../../hooks/useHaptics';

interface TimerControlsProps {
  state: TimerState;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onSkip: () => void;
}

export function TimerControls({
  state,
  onStart,
  onPause,
  onReset,
  onSkip,
}: TimerControlsProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const { triggerMedium } = useHaptics();

  const handleMainButton = () => {
    triggerMedium();
    if (state === 'running') {
      onPause();
    } else {
      onStart();
    }
  };

  const handleReset = () => {
    triggerMedium();
    onReset();
  };

  const handleSkip = () => {
    triggerMedium();
    onSkip();
  };

  return (
    <View style={styles.container}>
      {/* Main Play/Pause button */}
      <TouchableOpacity
        style={[
          styles.mainButton,
          { backgroundColor: theme.colors.primary },
        ]}
        onPress={handleMainButton}
        activeOpacity={0.8}
      >
        <MaterialCommunityIcons
          name={state === 'running' ? 'pause' : 'play'}
          size={48}
          color="#FFFFFF"
        />
      </TouchableOpacity>

      {/* Secondary controls */}
      <View style={styles.secondaryControls}>
        <TouchableOpacity
          style={[
            styles.secondaryButton,
            { backgroundColor: theme.colors.surface },
          ]}
          onPress={handleReset}
          activeOpacity={0.7}
        >
          <MaterialCommunityIcons
            name="refresh"
            size={24}
            color={theme.colors.textPrimary}
          />
          <Text
            style={{
              ...theme.typography.caption,
              color: theme.colors.textSecondary,
              marginTop: 4,
            }}
          >
            Reset
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.secondaryButton,
            { backgroundColor: theme.colors.surface },
          ]}
          onPress={handleSkip}
          activeOpacity={0.7}
        >
          <MaterialCommunityIcons
            name="skip-next"
            size={24}
            color={theme.colors.textPrimary}
          />
          <Text
            style={{
              ...theme.typography.caption,
              color: theme.colors.textSecondary,
              marginTop: 4,
            }}
          >
            Skip
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    gap: 24,
  },
  mainButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  secondaryControls: {
    flexDirection: 'row',
    gap: 16,
  },
  secondaryButton: {
    width: 80,
    height: 80,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
