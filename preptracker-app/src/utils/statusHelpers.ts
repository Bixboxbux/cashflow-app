import { OrderStatus } from '../database/queries';

export interface StatusConfig {
  label: string;
  color: string;
  backgroundColor: string;
}

export const STATUS_CONFIGS: Record<OrderStatus, StatusConfig> = {
  todo: {
    label: 'À faire',
    color: '#F9FAFB',
    backgroundColor: '#6B7280',
  },
  in_progress: {
    label: 'En cours',
    color: '#DBEAFE',
    backgroundColor: '#3B82F6',
  },
  done: {
    label: 'Terminé',
    color: '#D1FAE5',
    backgroundColor: '#10B981',
  },
  problem: {
    label: 'Problème',
    color: '#FEE2E2',
    backgroundColor: '#EF4444',
  },
};

export const getStatusConfig = (status: OrderStatus): StatusConfig => {
  return STATUS_CONFIGS[status];
};

export const getNextStatus = (currentStatus: OrderStatus): OrderStatus => {
  const statusFlow: OrderStatus[] = ['todo', 'in_progress', 'done'];
  const currentIndex = statusFlow.indexOf(currentStatus);

  if (currentIndex === -1 || currentIndex === statusFlow.length - 1) {
    return 'todo';
  }

  return statusFlow[currentIndex + 1];
};

export const getAllStatuses = (): OrderStatus[] => {
  return ['todo', 'in_progress', 'done', 'problem'];
};
