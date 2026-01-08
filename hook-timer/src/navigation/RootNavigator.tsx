import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { OnboardingScreen } from '../screens/OnboardingScreen';
import { TabNavigator } from './TabNavigator';
import { useSettingsStore } from '../store/useSettingsStore';
import { useHooksStore } from '../store/useHooksStore';
import { useStatsStore } from '../store/useStatsStore';
import { usePremiumStore } from '../store/usePremiumStore';
import { RootStackParamList } from './types';
import { View, ActivityIndicator } from 'react-native';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const [isLoading, setIsLoading] = useState(true);
  const hasCompletedOnboarding = useSettingsStore(
    (state) => state.settings.hasCompletedOnboarding
  );
  const setOnboardingComplete = useSettingsStore(
    (state) => state.setOnboardingComplete
  );

  const loadSettings = useSettingsStore((state) => state.loadSettings);
  const loadHooks = useHooksStore((state) => state.loadHooks);
  const loadStats = useStatsStore((state) => state.loadStats);
  const loadPremium = usePremiumStore((state) => state.loadPremium);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Charger toutes les données persistantes
      await Promise.all([
        loadSettings(),
        loadHooks(),
        loadStats(),
        loadPremium(),
      ]);
    } catch (error) {
      console.error('Error initializing app:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!hasCompletedOnboarding ? (
          <Stack.Screen name="Onboarding">
            {(props) => (
              <OnboardingScreen
                {...props}
                onComplete={setOnboardingComplete}
              />
            )}
          </Stack.Screen>
        ) : (
          <Stack.Screen name="Main" component={TabNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
