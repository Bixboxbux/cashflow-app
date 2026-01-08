import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { TimerScreen } from '../screens/TimerScreen';
import { CollectionScreen } from '../screens/CollectionScreen';
import { StatsScreen } from '../screens/StatsScreen';
import { SettingsScreen } from '../screens/SettingsScreen';
import { useSettingsStore } from '../store/useSettingsStore';
import { themes } from '../theme/themes';
import { TabParamList } from './types';

const Tab = createBottomTabNavigator<TabParamList>();

export function TabNavigator() {
  const themeMode = useSettingsStore((state) => state.settings.appearance.theme);
  const theme = themes[themeMode === 'light' ? 'light' : 'dark'];

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textTertiary,
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
      }}
    >
      <Tab.Screen
        name="Timer"
        component={TimerScreen}
        options={{
          tabBarLabel: 'Timer',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="timer-outline" size={size} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Collection"
        component={CollectionScreen}
        options={{
          tabBarLabel: 'Collection',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="cards-heart" size={size} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Stats"
        component={StatsScreen}
        options={{
          tabBarLabel: 'Stats',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="chart-bar" size={size} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarLabel: 'Réglages',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="cog-outline" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}
