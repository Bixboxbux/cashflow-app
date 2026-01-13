import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { getOrderById, updateOrder, DailyNote, getNotesForOrder, createNote } from '../database/queries';
import { QuickStatusBar } from '../components/QuickStatusBar';
import { formatDate, formatDateTime } from '../utils/dateHelpers';
import * as Haptics from 'expo-haptics';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import { Order, OrderStatus } from '../database/queries';

type RootStackParamList = {
  Dashboard: undefined;
  OrdersList: { status?: string };
  OrderDetail: { orderId: number };
  Clients: undefined;
  AddOrder: undefined;
};

type OrderDetailScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'OrderDetail'>;
  route: RouteProp<RootStackParamList, 'OrderDetail'>;
};

export const OrderDetailScreen: React.FC<OrderDetailScreenProps> = ({ navigation, route }) => {
  const { orderId } = route.params;
  const [order, setOrder] = useState<Order | null>(null);
  const [notes, setNotes] = useState<DailyNote[]>([]);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(true);

  const loadOrder = useCallback(async () => {
    try {
      setLoading(true);
      const orderData = await getOrderById(orderId);
      if (orderData) {
        setOrder(orderData);
        const notesData = await getNotesForOrder(orderId);
        setNotes(notesData);
      } else {
        Alert.alert('Erreur', 'Commande introuvable');
        navigation.goBack();
      }
    } catch (error) {
      console.error('Error loading order:', error);
      Alert.alert('Erreur', 'Impossible de charger la commande');
    } finally {
      setLoading(false);
    }
  }, [orderId, navigation]);

  useEffect(() => {
    loadOrder();
  }, [loadOrder]);

  const handleStatusChange = async (newStatus: OrderStatus) => {
    if (!order) return;

    try {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      await updateOrder(orderId, { status: newStatus });
      await loadOrder();
    } catch (error) {
      Alert.alert('Erreur', 'Impossible de changer le statut');
    }
  };

  const handleTogglePriority = async () => {
    if (!order) return;

    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      const newPriority = order.priority === 1 ? 0 : 1;
      await updateOrder(orderId, { priority: newPriority });
      await loadOrder();
    } catch (error) {
      Alert.alert('Erreur', 'Impossible de changer la priorité');
    }
  };

  const handleAddNote = async () => {
    if (!newNote.trim() || !order) return;

    try {
      await createNote({
        order_id: orderId,
        client_id: order.client_id,
        content: newNote.trim(),
      });
      setNewNote('');
      await loadOrder();
    } catch (error) {
      Alert.alert('Erreur', "Impossible d'ajouter la note");
    }
  };

  if (loading || !order) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Order Info */}
        <View style={styles.section}>
          <Text style={styles.reference}>{order.reference}</Text>
          <Text style={styles.client}>
            {order.client_name}
            {order.client_code && ` (${order.client_code})`}
          </Text>
          {order.due_date && (
            <Text style={styles.dueDate}>Échéance: {formatDate(order.due_date)}</Text>
          )}
        </View>

        {/* Priority Toggle */}
        <TouchableOpacity
          style={[styles.priorityButton, order.priority === 1 && styles.priorityButtonActive]}
          onPress={handleTogglePriority}
        >
          <Text style={styles.priorityText}>
            {order.priority === 1 ? '⚠️ URGENT' : 'Marquer comme urgent'}
          </Text>
        </TouchableOpacity>

        {/* Status Bar */}
        <Text style={styles.sectionTitle}>Statut</Text>
        <QuickStatusBar currentStatus={order.status} onStatusChange={handleStatusChange} />

        {/* Notes */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notes</Text>

          <View style={styles.noteInputContainer}>
            <TextInput
              style={styles.noteInput}
              value={newNote}
              onChangeText={setNewNote}
              placeholder="Ajouter une note..."
              placeholderTextColor="#6B7280"
              multiline
              numberOfLines={3}
            />
            <TouchableOpacity
              style={[styles.addNoteButton, !newNote.trim() && styles.addNoteButtonDisabled]}
              onPress={handleAddNote}
              disabled={!newNote.trim()}
            >
              <Text style={styles.addNoteButtonText}>Ajouter</Text>
            </TouchableOpacity>
          </View>

          {notes.length === 0 ? (
            <Text style={styles.noNotes}>Aucune note pour cette commande</Text>
          ) : (
            notes.map((note) => (
              <View key={note.id} style={styles.noteCard}>
                <Text style={styles.noteContent}>{note.content}</Text>
                <Text style={styles.noteDate}>{formatDateTime(note.created_at)}</Text>
              </View>
            ))
          )}
        </View>

        {/* Timestamps */}
        <View style={styles.timestampsContainer}>
          <Text style={styles.timestamp}>Créée: {formatDateTime(order.created_at)}</Text>
          <Text style={styles.timestamp}>Modifiée: {formatDateTime(order.updated_at)}</Text>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#111827',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  reference: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '800',
    marginBottom: 8,
  },
  client: {
    color: '#9CA3AF',
    fontSize: 18,
    marginBottom: 8,
  },
  dueDate: {
    color: '#6B7280',
    fontSize: 16,
  },
  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
  },
  priorityButton: {
    backgroundColor: '#374151',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 2,
    borderColor: '#374151',
    minHeight: 56,
    justifyContent: 'center',
  },
  priorityButtonActive: {
    backgroundColor: '#7F1D1D',
    borderColor: '#EF4444',
  },
  priorityText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  noteInputContainer: {
    marginBottom: 16,
  },
  noteInput: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    color: '#FFFFFF',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#374151',
    marginBottom: 8,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  addNoteButton: {
    backgroundColor: '#3B82F6',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    minHeight: 48,
    justifyContent: 'center',
  },
  addNoteButtonDisabled: {
    backgroundColor: '#374151',
    opacity: 0.5,
  },
  addNoteButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  noNotes: {
    color: '#6B7280',
    fontSize: 16,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 24,
  },
  noteCard: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  noteContent: {
    color: '#FFFFFF',
    fontSize: 16,
    marginBottom: 8,
    lineHeight: 24,
  },
  noteDate: {
    color: '#6B7280',
    fontSize: 14,
  },
  timestampsContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#374151',
  },
  timestamp: {
    color: '#6B7280',
    fontSize: 14,
    marginBottom: 4,
  },
});
