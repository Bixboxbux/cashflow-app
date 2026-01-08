import React from 'react';
import {
  Modal as RNModal,
  View,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  ViewStyle,
} from 'react-native';
import { useSettingsStore } from '../../store/useSettingsStore';
import { themes } from '../../theme/themes';

interface ModalProps {
  visible: boolean;
  onClose: () => void;
  children: React.ReactNode;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  style?: ViewStyle;
}

const { height } = Dimensions.get('window');

export function Modal({
  visible,
  onClose,
  children,
  size = 'medium',
  style,
}: ModalProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const sizeStyles: Record<string, ViewStyle> = {
    small: { maxHeight: height * 0.4 },
    medium: { maxHeight: height * 0.6 },
    large: { maxHeight: height * 0.8 },
    fullscreen: { height: height, borderRadius: 0, margin: 0 },
  };

  return (
    <RNModal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <TouchableOpacity
          style={styles.backdrop}
          activeOpacity={1}
          onPress={onClose}
        />
        <View
          style={[
            {
              backgroundColor: theme.colors.surface,
              borderRadius: theme.radius.xl,
              padding: theme.spacing.xl,
              margin: theme.spacing.lg,
              maxWidth: 500,
              width: '90%',
            },
            sizeStyles[size],
            style,
          ]}
        >
          {children}
        </View>
      </View>
    </RNModal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
});
