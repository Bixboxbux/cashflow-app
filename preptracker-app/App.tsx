import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { initDatabase } from './src/database/schema';
import { DashboardScreen } from './src/screens/DashboardScreen';
import { OrdersListScreen } from './src/screens/OrdersListScreen';
import { OrderDetailScreen } from './src/screens/OrderDetailScreen';
import { ClientsScreen } from './src/screens/ClientsScreen';
import { AddOrderScreen } from './src/screens/AddOrderScreen';

export type RootStackParamList = {
  Dashboard: undefined;
  OrdersList: { status?: string };
  OrderDetail: { orderId: number };
  Clients: undefined;
  AddOrder: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const initialize = async () => {
      try {
        await initDatabase();
        setIsReady(true);
      } catch (error) {
        console.error('Failed to initialize database:', error);
      }
    };

    initialize();
  }, []);

  if (!isReady) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Dashboard"
          screenOptions={{
            headerStyle: {
              backgroundColor: '#111827',
            },
            headerTintColor: '#FFFFFF',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
            contentStyle: {
              backgroundColor: '#111827',
            },
          }}
        >
          <Stack.Screen
            name="Dashboard"
            component={DashboardScreen}
            options={{ title: 'PrepTracker', headerShown: false }}
          />
          <Stack.Screen
            name="OrdersList"
            component={OrdersListScreen}
            options={{ title: 'Commandes' }}
          />
          <Stack.Screen
            name="OrderDetail"
            component={OrderDetailScreen}
            options={{ title: 'Détail commande' }}
          />
          <Stack.Screen
            name="Clients"
            component={ClientsScreen}
            options={{ title: 'Clients' }}
          />
          <Stack.Screen
            name="AddOrder"
            component={AddOrderScreen}
            options={{ title: 'Nouvelle commande' }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#111827',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
