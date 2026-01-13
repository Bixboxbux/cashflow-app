import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { useOrders } from '../hooks/useOrders';
import { OrderCard } from '../components/OrderCard';
import { SearchBar } from '../components/SearchBar';
import { EmptyState } from '../components/EmptyState';
import { OrderStatus } from '../database/queries';
import { getNextStatus, getAllStatuses, getStatusConfig } from '../utils/statusHelpers';
import * as Haptics from 'expo-haptics';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

type RootStackParamList = {
  Dashboard: undefined;
  OrdersList: { status?: string };
  OrderDetail: { orderId: number };
  Clients: undefined;
  AddOrder: undefined;
};

type OrdersListScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'OrdersList'>;
  route: RouteProp<RootStackParamList, 'OrdersList'>;
};

export const OrdersListScreen: React.FC<OrdersListScreenProps> = ({ navigation, route }) => {
  const initialStatus = route.params?.status as OrderStatus | undefined;
  const [selectedStatus, setSelectedStatus] = useState<OrderStatus | undefined>(initialStatus);
  const [searchQuery, setSearchQuery] = useState('');

  const { orders, loading, refresh, changeStatus } = useOrders(selectedStatus, searchQuery);

  const handleRefresh = useCallback(async () => {
    await refresh();
  }, [refresh]);

  const handleStatusChange = useCallback(
    async (orderId: number) => {
      const order = orders.find((o) => o.id === orderId);
      if (order) {
        const nextStatus = getNextStatus(order.status);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        await changeStatus(orderId, nextStatus);
      }
    },
    [orders, changeStatus]
  );

  const handleFilterChange = (status: OrderStatus | undefined) => {
    setSelectedStatus(status);
    setSearchQuery('');
  };

  const statuses = getAllStatuses();

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <SearchBar
        value={searchQuery}
        onChangeText={setSearchQuery}
        placeholder="Rechercher par référence ou client..."
        onClear={() => setSearchQuery('')}
      />

      {/* Status Filters */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filtersContainer}
        contentContainerStyle={styles.filtersContent}
      >
        <TouchableOpacity
          style={[styles.filterButton, !selectedStatus && styles.filterButtonActive]}
          onPress={() => handleFilterChange(undefined)}
        >
          <Text style={[styles.filterText, !selectedStatus && styles.filterTextActive]}>
            Toutes
          </Text>
        </TouchableOpacity>

        {statuses.map((status) => {
          const config = getStatusConfig(status);
          const isActive = selectedStatus === status;

          return (
            <TouchableOpacity
              key={status}
              style={[
                styles.filterButton,
                isActive && { backgroundColor: config.backgroundColor },
              ]}
              onPress={() => handleFilterChange(status)}
            >
              <Text style={[styles.filterText, isActive && styles.filterTextActive]}>
                {config.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Orders List */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={handleRefresh} />}
      >
        {orders.length === 0 ? (
          <EmptyState
            title="Aucune commande"
            message={
              searchQuery
                ? 'Aucun résultat pour cette recherche'
                : selectedStatus
                ? `Aucune commande avec ce statut`
                : 'Commencez par ajouter une commande'
            }
            icon={searchQuery ? '🔍' : '📦'}
          />
        ) : (
          orders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              onPress={() => navigation.navigate('OrderDetail', { orderId: order.id! })}
              onStatusChange={handleStatusChange}
            />
          ))
        )}
      </ScrollView>

      {/* Floating Action Button */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('AddOrder')}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  filtersContainer: {
    maxHeight: 60,
  },
  filtersContent: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1F2937',
    borderWidth: 1,
    borderColor: '#374151',
    minHeight: 40,
    justifyContent: 'center',
  },
  filterButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  filterText: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '600',
  },
  filterTextActive: {
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  fabText: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: '300',
  },
});
