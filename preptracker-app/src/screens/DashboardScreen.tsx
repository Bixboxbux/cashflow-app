import React, { useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { useDailyStats } from '../hooks/useDailyStats';
import { useOrders } from '../hooks/useOrders';
import { OrderCard } from '../components/OrderCard';
import { EmptyState } from '../components/EmptyState';
import { getNextStatus } from '../utils/statusHelpers';
import * as Haptics from 'expo-haptics';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  OrdersList: { status?: string };
  OrderDetail: { orderId: number };
  Clients: undefined;
  AddOrder: undefined;
};

type DashboardScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Dashboard'>;
};

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ navigation }) => {
  const { stats, loading: statsLoading, refresh: refreshStats } = useDailyStats();
  const { orders, loading: ordersLoading, refresh: refreshOrders, changeStatus } = useOrders();

  const urgentOrders = orders.filter((o) => o.priority === 1 && o.status !== 'done');
  const todayOrders = orders.filter((o) => o.status !== 'done');

  const handleRefresh = useCallback(async () => {
    await Promise.all([refreshStats(), refreshOrders()]);
  }, [refreshStats, refreshOrders]);

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

  const loading = statsLoading || ordersLoading;

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={handleRefresh} />}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Aujourd'hui</Text>
          <Text style={styles.date}>{new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}</Text>
        </View>

        {/* Stats */}
        <View style={styles.statsContainer}>
          <TouchableOpacity
            style={[styles.statCard, { backgroundColor: '#6B7280' }]}
            onPress={() => navigation.navigate('OrdersList', { status: 'todo' })}
          >
            <Text style={styles.statNumber}>{stats.todo}</Text>
            <Text style={styles.statLabel}>À faire</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statCard, { backgroundColor: '#3B82F6' }]}
            onPress={() => navigation.navigate('OrdersList', { status: 'in_progress' })}
          >
            <Text style={styles.statNumber}>{stats.in_progress}</Text>
            <Text style={styles.statLabel}>En cours</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statCard, { backgroundColor: '#10B981' }]}
            onPress={() => navigation.navigate('OrdersList', { status: 'done' })}
          >
            <Text style={styles.statNumber}>{stats.done}</Text>
            <Text style={styles.statLabel}>Terminé</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statCard, { backgroundColor: '#EF4444' }]}
            onPress={() => navigation.navigate('OrdersList', { status: 'problem' })}
          >
            <Text style={styles.statNumber}>{stats.problem}</Text>
            <Text style={styles.statLabel}>Problèmes</Text>
          </TouchableOpacity>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => navigation.navigate('Clients')}
          >
            <Text style={styles.quickActionText}>👥 Gérer les clients</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => navigation.navigate('OrdersList', {})}
          >
            <Text style={styles.quickActionText}>📋 Toutes les commandes</Text>
          </TouchableOpacity>
        </View>

        {/* Urgent Orders */}
        {urgentOrders.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>⚠️ Commandes Urgentes ({urgentOrders.length})</Text>
            {urgentOrders.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                onPress={() => navigation.navigate('OrderDetail', { orderId: order.id! })}
                onStatusChange={handleStatusChange}
              />
            ))}
          </View>
        )}

        {/* Today's Orders */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Commandes actives ({todayOrders.length})</Text>
          {todayOrders.length === 0 ? (
            <EmptyState
              title="Aucune commande"
              message="Toutes les commandes sont terminées !"
              icon="✅"
            />
          ) : (
            todayOrders.slice(0, 5).map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                onPress={() => navigation.navigate('OrderDetail', { orderId: order.id! })}
                onStatusChange={handleStatusChange}
              />
            ))
          )}
          {todayOrders.length > 5 && (
            <TouchableOpacity
              style={styles.viewAllButton}
              onPress={() => navigation.navigate('OrdersList', {})}
            >
              <Text style={styles.viewAllText}>Voir toutes les commandes ({todayOrders.length})</Text>
            </TouchableOpacity>
          )}
        </View>
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  header: {
    padding: 20,
    paddingTop: 60,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: '800',
    marginBottom: 4,
  },
  date: {
    color: '#9CA3AF',
    fontSize: 16,
    textTransform: 'capitalize',
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    minHeight: 100,
    justifyContent: 'center',
  },
  statNumber: {
    color: '#FFFFFF',
    fontSize: 36,
    fontWeight: '800',
    marginBottom: 4,
  },
  statLabel: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  quickActions: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  quickActionButton: {
    flex: 1,
    backgroundColor: '#374151',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    minHeight: 56,
    justifyContent: 'center',
  },
  quickActionText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 16,
  },
  viewAllButton: {
    backgroundColor: '#374151',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
    minHeight: 48,
    justifyContent: 'center',
  },
  viewAllText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
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
