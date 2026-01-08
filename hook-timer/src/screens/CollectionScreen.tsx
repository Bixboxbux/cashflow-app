import React, { useState } from 'react';
import { View, StyleSheet, SafeAreaView, StatusBar } from 'react-native';
import { HookList } from '../components/Hooks/HookList';
import { PremiumBanner } from '../components/Premium/PremiumBanner';
import { PaywallModal } from '../components/Premium/PaywallModal';
import { useSettingsStore } from '../store/useSettingsStore';
import { usePremiumStore } from '../store/usePremiumStore';
import { themes } from '../theme/themes';

export function CollectionScreen() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];
  const isPremium = usePremiumStore((state) => state.isPremium);

  const [showPaywall, setShowPaywall] = useState(false);

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <StatusBar
        barStyle={themeMode === 'light' ? 'dark-content' : 'light-content'}
      />

      {/* Premium banner */}
      {!isPremium && <PremiumBanner onPress={() => setShowPaywall(true)} />}

      {/* Hooks list */}
      <HookList />

      {/* Paywall modal */}
      <PaywallModal
        visible={showPaywall}
        onClose={() => setShowPaywall(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
