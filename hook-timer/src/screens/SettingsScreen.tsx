import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  ScrollView,
  Switch,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import { Card } from '../components/UI/Card';
import { Button } from '../components/UI/Button';
import { PaywallModal } from '../components/Premium/PaywallModal';
import { useSettingsStore } from '../store/useSettingsStore';
import { usePremiumStore } from '../store/usePremiumStore';
import { usePurchases } from '../hooks/usePurchases';
import { themes } from '../theme/themes';

export function SettingsScreen() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  const settings = useSettingsStore((state) => state.settings);
  const updateTimerConfig = useSettingsStore((state) => state.updateTimerConfig);
  const updateNotifications = useSettingsStore((state) => state.updateNotifications);
  const updateAppearance = useSettingsStore((state) => state.updateAppearance);
  const updateGoals = useSettingsStore((state) => state.updateGoals);

  const isPremium = usePremiumStore((state) => state.isPremium);
  const { restorePurchases } = usePurchases();

  const [showPaywall, setShowPaywall] = useState(false);

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <StatusBar
        barStyle={themeMode === 'light' ? 'dark-content' : 'light-content'}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <Text style={[theme.typography.h1, { color: theme.colors.textPrimary }]}>
          Paramètres
        </Text>

        {/* Timer Section */}
        <Card elevated style={styles.section}>
          <Text style={[theme.typography.h3, { color: theme.colors.textPrimary, marginBottom: 16 }]}>
            Timer
          </Text>

          <View style={styles.setting}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Session focus: {settings.timer.focusDuration} min
            </Text>
            <Slider
              style={styles.slider}
              minimumValue={15}
              maximumValue={60}
              step={5}
              value={settings.timer.focusDuration}
              onValueChange={(value) => updateTimerConfig({ focusDuration: value })}
              minimumTrackTintColor={theme.colors.primary}
              maximumTrackTintColor={theme.colors.border}
            />
          </View>

          <View style={styles.setting}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Pause courte: {settings.timer.shortBreakDuration} min
            </Text>
            <Slider
              style={styles.slider}
              minimumValue={3}
              maximumValue={10}
              step={1}
              value={settings.timer.shortBreakDuration}
              onValueChange={(value) => updateTimerConfig({ shortBreakDuration: value })}
              minimumTrackTintColor={theme.colors.primary}
              maximumTrackTintColor={theme.colors.border}
            />
          </View>

          <View style={styles.setting}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Pause longue: {settings.timer.longBreakDuration} min
            </Text>
            <Slider
              style={styles.slider}
              minimumValue={10}
              maximumValue={30}
              step={5}
              value={settings.timer.longBreakDuration}
              onValueChange={(value) => updateTimerConfig({ longBreakDuration: value })}
              minimumTrackTintColor={theme.colors.primary}
              maximumTrackTintColor={theme.colors.border}
            />
          </View>

          <View style={styles.switchRow}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Démarrage auto des pauses
            </Text>
            <Switch
              value={settings.timer.autoStartBreaks}
              onValueChange={(value) => updateTimerConfig({ autoStartBreaks: value })}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            />
          </View>

          <View style={styles.switchRow}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Démarrage auto des sessions
            </Text>
            <Switch
              value={settings.timer.autoStartSessions}
              onValueChange={(value) => updateTimerConfig({ autoStartSessions: value })}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            />
          </View>
        </Card>

        {/* Notifications Section */}
        <Card elevated style={styles.section}>
          <Text style={[theme.typography.h3, { color: theme.colors.textPrimary, marginBottom: 16 }]}>
            Notifications
          </Text>

          <View style={styles.switchRow}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Activer les notifications
            </Text>
            <Switch
              value={settings.notifications.enabled}
              onValueChange={(value) => updateNotifications({ enabled: value })}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            />
          </View>

          <View style={styles.switchRow}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Vibration
            </Text>
            <Switch
              value={settings.notifications.vibration}
              onValueChange={(value) => updateNotifications({ vibration: value })}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            />
          </View>
        </Card>

        {/* Appearance Section */}
        <Card elevated style={styles.section}>
          <Text style={[theme.typography.h3, { color: theme.colors.textPrimary, marginBottom: 16 }]}>
            Apparence
          </Text>

          <View style={styles.switchRow}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Thème sombre
            </Text>
            <Switch
              value={settings.appearance.theme === 'dark'}
              onValueChange={(value) => updateAppearance({ theme: value ? 'dark' : 'light' })}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
            />
          </View>

          {!isPremium && (
            <TouchableOpacity
              style={styles.premiumRow}
              onPress={() => setShowPaywall(true)}
            >
              <MaterialCommunityIcons name="crown" size={20} color={theme.colors.warning} />
              <Text style={[theme.typography.body, { color: theme.colors.textSecondary, marginLeft: 8, flex: 1 }]}>
                5 thèmes de couleur (Premium)
              </Text>
              <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.textTertiary} />
            </TouchableOpacity>
          )}
        </Card>

        {/* Goals Section */}
        <Card elevated style={styles.section}>
          <Text style={[theme.typography.h3, { color: theme.colors.textPrimary, marginBottom: 16 }]}>
            Objectifs
          </Text>

          <View style={styles.setting}>
            <Text style={[theme.typography.body, { color: theme.colors.textPrimary }]}>
              Objectif quotidien: {settings.goals.dailySessionGoal} sessions
            </Text>
            <Slider
              style={styles.slider}
              minimumValue={1}
              maximumValue={12}
              step={1}
              value={settings.goals.dailySessionGoal}
              onValueChange={(value) => updateGoals({ dailySessionGoal: value })}
              minimumTrackTintColor={theme.colors.primary}
              maximumTrackTintColor={theme.colors.border}
            />
          </View>
        </Card>

        {/* Account Section */}
        <Card elevated style={styles.section}>
          <Text style={[theme.typography.h3, { color: theme.colors.textPrimary, marginBottom: 16 }]}>
            Compte
          </Text>

          {!isPremium && (
            <Button
              title="Passer à Premium"
              onPress={() => setShowPaywall(true)}
              variant="primary"
              style={{ marginBottom: 12 }}
            />
          )}

          <Button
            title="Restaurer mes achats"
            onPress={restorePurchases}
            variant="outline"
          />
        </Card>

        {/* About Section */}
        <Card elevated style={styles.section}>
          <Text style={[theme.typography.h3, { color: theme.colors.textPrimary, marginBottom: 16 }]}>
            À propos
          </Text>

          <Text style={[theme.typography.body, { color: theme.colors.textSecondary, marginBottom: 12 }]}>
            Version 1.0.0
          </Text>

          <TouchableOpacity
            style={styles.linkRow}
            onPress={() => Linking.openURL('https://example.com/privacy')}
          >
            <Text style={[theme.typography.body, { color: theme.colors.primary }]}>
              Politique de confidentialité
            </Text>
            <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.textTertiary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkRow}
            onPress={() => Linking.openURL('https://example.com/terms')}
          >
            <Text style={[theme.typography.body, { color: theme.colors.primary }]}>
              Conditions d'utilisation
            </Text>
            <MaterialCommunityIcons name="chevron-right" size={20} color={theme.colors.textTertiary} />
          </TouchableOpacity>
        </Card>
      </ScrollView>

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
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  section: {
    marginTop: 16,
  },
  setting: {
    marginBottom: 16,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  premiumRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  linkRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
});
