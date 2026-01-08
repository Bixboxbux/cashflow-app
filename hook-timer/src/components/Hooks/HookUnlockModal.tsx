import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import LottieView from 'lottie-react-native';
import { Hook } from '../../types/hook';
import { Modal } from '../UI/Modal';
import { Button } from '../UI/Button';
import { Badge } from '../UI/Badge';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

interface HookUnlockModalProps {
  visible: boolean;
  hook: Hook | null;
  onClose: () => void;
}

export function HookUnlockModal({
  visible,
  hook,
  onClose,
}: HookUnlockModalProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const scaleAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible && hook) {
      // Reset animations
      scaleAnim.setValue(0);
      fadeAnim.setValue(0);

      // Start animations
      Animated.parallel([
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 50,
          friction: 7,
          useNativeDriver: true,
        }),
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, hook]);

  if (!hook) return null;

  const categoryColor = theme.categoryColors[hook.category];

  return (
    <Modal visible={visible} onClose={onClose} size="medium">
      <View style={styles.container}>
        {/* Confetti animation - Dans une vraie app, ajoutez le fichier confetti.json */}
        {/* <LottieView
          source={require('../../../assets/animations/confetti.json')}
          autoPlay
          loop={false}
          style={styles.lottie}
        /> */}

        <Text
          style={{
            ...theme.typography.h1,
            color: theme.colors.textPrimary,
            textAlign: 'center',
            marginBottom: theme.spacing.md,
          }}
        >
          🎉 Nouveau Hook !
        </Text>

        <Animated.View
          style={{
            transform: [{ scale: scaleAnim }],
            opacity: fadeAnim,
            alignItems: 'center',
          }}
        >
          <Badge
            text={hook.category.toUpperCase()}
            color={categoryColor}
            textColor="#FFFFFF"
            style={{ marginBottom: theme.spacing.lg }}
          />

          <Text
            style={{
              ...theme.typography.h3,
              color: theme.colors.textPrimary,
              textAlign: 'center',
              marginBottom: theme.spacing.xl,
            }}
          >
            "{hook.text}"
          </Text>
        </Animated.View>

        <Button
          title="Super !"
          onPress={onClose}
          variant="primary"
          size="large"
          style={{ width: '100%' }}
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  lottie: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: -1,
  },
});
