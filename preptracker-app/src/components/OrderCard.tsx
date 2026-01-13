import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Pressable } from 'react-native';
import { Order } from '../database/queries';
import { StatusBadge } from './StatusBadge';
import { formatDate, isPast } from '../utils/dateHelpers';
import * as Haptics from 'expo-haptics';

interface OrderCardProps {
  order: Order;
  onPress: () => void;
  onStatusChange?: (orderId: number) => void;
}

export const OrderCard: React.FC<OrderCardProps> = ({ order, onPress, onStatusChange }) => {
  const handleStatusChange = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onStatusChange?.(order.id!);
  };

  const isOverdue = order.due_date && isPast(order.due_date) && order.status !== 'done';

  return (
    <Pressable
      style={({ pressed }) => [
        styles.card,
        pressed && styles.cardPressed,
        order.priority === 1 && styles.urgentCard,
      ]}
      onPress={onPress}
    >
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <StatusBadge status={order.status} size="small" />
          {order.priority === 1 && (
            <View style={styles.urgentBadge}>
              <Text style={styles.urgentText}>URGENT</Text>
            </View>
          )}
        </View>
        {onStatusChange && (
          <TouchableOpacity
            style={styles.statusButton}
            onPress={handleStatusChange}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={styles.statusButtonText}>Changer</Text>
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.reference}>{order.reference}</Text>
      <Text style={styles.client}>
        {order.client_name}
        {order.client_code && ` (${order.client_code})`}
      </Text>

      {order.due_date && (
        <Text style={[styles.dueDate, isOverdue && styles.overdue]}>
          Échéance: {formatDate(order.due_date)}
          {isOverdue && ' ⚠️'}
        </Text>
      )}
    </Pressable>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  cardPressed: {
    opacity: 0.7,
  },
  urgentCard: {
    borderColor: '#EF4444',
    borderWidth: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  urgentBadge: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  urgentText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  statusButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    minHeight: 32,
    justifyContent: 'center',
  },
  statusButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  reference: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  client: {
    color: '#9CA3AF',
    fontSize: 16,
    marginBottom: 8,
  },
  dueDate: {
    color: '#6B7280',
    fontSize: 14,
  },
  overdue: {
    color: '#EF4444',
    fontWeight: '600',
  },
});
