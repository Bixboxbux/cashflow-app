import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { OrderStatus } from '../database/queries';
import { getAllStatuses, getStatusConfig } from '../utils/statusHelpers';
import * as Haptics from 'expo-haptics';

interface QuickStatusBarProps {
  currentStatus: OrderStatus;
  onStatusChange: (status: OrderStatus) => void;
}

export const QuickStatusBar: React.FC<QuickStatusBarProps> = ({ currentStatus, onStatusChange }) => {
  const statuses = getAllStatuses();

  const handlePress = (status: OrderStatus) => {
    if (status !== currentStatus) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      onStatusChange(status);
    }
  };

  return (
    <View style={styles.container}>
      {statuses.map((status) => {
        const config = getStatusConfig(status);
        const isActive = status === currentStatus;

        return (
          <TouchableOpacity
            key={status}
            style={[
              styles.button,
              { backgroundColor: config.backgroundColor },
              isActive && styles.activeButton,
            ]}
            onPress={() => handlePress(status)}
          >
            <Text style={styles.buttonText}>{config.label}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: 8,
    padding: 16,
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    alignItems: 'center',
    minHeight: 48,
    justifyContent: 'center',
  },
  activeButton: {
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
});
