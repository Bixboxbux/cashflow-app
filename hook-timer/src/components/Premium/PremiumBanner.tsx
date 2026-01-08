import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSettingsStore } from '../../store/useSettingsStore';
import { usePremiumStore } from '../../store/usePremiumStore';
import { themes } from '../../theme/themes';

interface PremiumBannerProps {
  onPress: () => void;
}

export function PremiumBanner({ onPress }: PremiumBannerProps) {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const isPremium = usePremiumStore((state) => state.isPremium);

  // Ne pas afficher la bannière si l'utilisateur est premium
  if (isPremium) {
    return null;
  }

  return (
    <TouchableOpacity
      style={[
        styles.banner,
        {
          backgroundColor: theme.colors.primary,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.content}>
        <MaterialCommunityIcons name="crown" size={24} color="#FFFFFF" />

        <View style={styles.textContainer}>
          <Text style={styles.title}>Passer à Premium</Text>
          <Text style={styles.subtitle}>
            Débloquez 450 hooks et bien plus !
          </Text>
        </View>

        <MaterialCommunityIcons
          name="chevron-right"
          size={24}
          color="#FFFFFF"
        />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  banner: {
    marginHorizontal: 16,
    marginVertical: 12,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  textContainer: {
    flex: 1,
    marginLeft: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  subtitle: {
    fontSize: 14,
    color: '#FFFFFF',
    opacity: 0.9,
    marginTop: 2,
  },
});
