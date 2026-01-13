import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useClients } from '../hooks/useClients';
import { createOrder } from '../database/queries';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Dashboard: undefined;
  OrdersList: { status?: string };
  OrderDetail: { orderId: number };
  Clients: undefined;
  AddOrder: undefined;
};

type AddOrderScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'AddOrder'>;
};

export const AddOrderScreen: React.FC<AddOrderScreenProps> = ({ navigation }) => {
  const { clients } = useClients();
  const [formData, setFormData] = useState({
    client_id: '',
    reference: '',
    due_date: '',
    priority: 0,
  });

  const handleSave = async () => {
    if (!formData.client_id) {
      Alert.alert('Erreur', 'Veuillez sélectionner un client');
      return;
    }

    if (!formData.reference.trim()) {
      Alert.alert('Erreur', 'Veuillez entrer une référence de commande');
      return;
    }

    try {
      const orderId = await createOrder({
        client_id: parseInt(formData.client_id),
        reference: formData.reference.trim(),
        status: 'todo',
        priority: formData.priority,
        due_date: formData.due_date || undefined,
      });

      Alert.alert('Succès', 'Commande créée avec succès', [
        {
          text: 'OK',
          onPress: () => navigation.navigate('OrderDetail', { orderId }),
        },
      ]);
    } catch (error) {
      console.error('Error creating order:', error);
      Alert.alert('Erreur', 'Impossible de créer la commande');
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Nouvelle Commande</Text>

        {/* Client Selection */}
        <Text style={styles.label}>Client *</Text>
        <View style={styles.pickerContainer}>
          {clients.map((client) => (
            <TouchableOpacity
              key={client.id}
              style={[
                styles.clientOption,
                formData.client_id === String(client.id) && styles.clientOptionSelected,
              ]}
              onPress={() => setFormData({ ...formData, client_id: String(client.id) })}
            >
              <Text
                style={[
                  styles.clientOptionText,
                  formData.client_id === String(client.id) && styles.clientOptionTextSelected,
                ]}
              >
                {client.name}
                {client.code && ` (${client.code})`}
              </Text>
            </TouchableOpacity>
          ))}
          {clients.length === 0 && (
            <Text style={styles.noClientsText}>
              Aucun client disponible. Veuillez d'abord créer un client.
            </Text>
          )}
        </View>

        {/* Reference */}
        <Text style={styles.label}>Référence commande *</Text>
        <TextInput
          style={styles.input}
          value={formData.reference}
          onChangeText={(text) => setFormData({ ...formData, reference: text })}
          placeholder="Ex: CMD-2024-001"
          placeholderTextColor="#6B7280"
        />

        {/* Due Date */}
        <Text style={styles.label}>Date d'échéance</Text>
        <TextInput
          style={styles.input}
          value={formData.due_date}
          onChangeText={(text) => setFormData({ ...formData, due_date: text })}
          placeholder="AAAA-MM-JJ"
          placeholderTextColor="#6B7280"
        />

        {/* Priority */}
        <Text style={styles.label}>Priorité</Text>
        <View style={styles.priorityContainer}>
          <TouchableOpacity
            style={[
              styles.priorityButton,
              formData.priority === 0 && styles.priorityButtonSelected,
            ]}
            onPress={() => setFormData({ ...formData, priority: 0 })}
          >
            <Text
              style={[
                styles.priorityText,
                formData.priority === 0 && styles.priorityTextSelected,
              ]}
            >
              Normal
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.priorityButton,
              styles.priorityButtonUrgent,
              formData.priority === 1 && styles.priorityButtonUrgentSelected,
            ]}
            onPress={() => setFormData({ ...formData, priority: 1 })}
          >
            <Text
              style={[
                styles.priorityText,
                formData.priority === 1 && styles.priorityTextSelected,
              ]}
            >
              ⚠️ Urgent
            </Text>
          </TouchableOpacity>
        </View>

        {/* Save Button */}
        <TouchableOpacity
          style={[styles.saveButton, (!formData.client_id || !formData.reference) && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={!formData.client_id || !formData.reference}
        >
          <Text style={styles.saveButtonText}>Créer la commande</Text>
        </TouchableOpacity>
      </ScrollView>
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
    padding: 20,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '800',
    marginBottom: 24,
  },
  label: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    color: '#FFFFFF',
    fontSize: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#374151',
    minHeight: 48,
  },
  pickerContainer: {
    marginBottom: 20,
    gap: 8,
  },
  clientOption: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#374151',
    minHeight: 48,
    justifyContent: 'center',
  },
  clientOptionSelected: {
    backgroundColor: '#1E3A8A',
    borderColor: '#3B82F6',
  },
  clientOptionText: {
    color: '#9CA3AF',
    fontSize: 16,
  },
  clientOptionTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  noClientsText: {
    color: '#6B7280',
    fontSize: 16,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
  priorityContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  priorityButton: {
    flex: 1,
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#374151',
    alignItems: 'center',
    minHeight: 56,
    justifyContent: 'center',
  },
  priorityButtonSelected: {
    backgroundColor: '#1E3A8A',
    borderColor: '#3B82F6',
  },
  priorityButtonUrgent: {
    backgroundColor: '#1F2937',
  },
  priorityButtonUrgentSelected: {
    backgroundColor: '#7F1D1D',
    borderColor: '#EF4444',
  },
  priorityText: {
    color: '#9CA3AF',
    fontSize: 16,
    fontWeight: '600',
  },
  priorityTextSelected: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  saveButton: {
    backgroundColor: '#3B82F6',
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
    minHeight: 56,
    justifyContent: 'center',
  },
  saveButtonDisabled: {
    backgroundColor: '#374151',
    opacity: 0.5,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
