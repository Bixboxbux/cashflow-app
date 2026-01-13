import { useState, useEffect, useCallback } from 'react';
import {
  Order,
  OrderStatus,
  getAllOrders,
  getOrdersByStatus,
  createOrder,
  updateOrder,
  deleteOrder,
  searchOrders,
} from '../database/queries';

export const useOrders = (status?: OrderStatus, searchQuery?: string) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      let data: Order[];
      if (searchQuery) {
        data = await searchOrders(searchQuery);
      } else if (status) {
        data = await getOrdersByStatus(status);
      } else {
        data = await getAllOrders();
      }

      setOrders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load orders');
      console.error('Error loading orders:', err);
    } finally {
      setLoading(false);
    }
  }, [status, searchQuery]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const addOrder = useCallback(async (order: Omit<Order, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      await createOrder(order);
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add order');
      throw err;
    }
  }, [loadOrders]);

  const editOrder = useCallback(async (id: number, order: Partial<Order>) => {
    try {
      await updateOrder(id, order);
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update order');
      throw err;
    }
  }, [loadOrders]);

  const removeOrder = useCallback(async (id: number) => {
    try {
      await deleteOrder(id);
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete order');
      throw err;
    }
  }, [loadOrders]);

  const changeStatus = useCallback(async (id: number, newStatus: OrderStatus) => {
    try {
      await updateOrder(id, { status: newStatus });
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change status');
      throw err;
    }
  }, [loadOrders]);

  const togglePriority = useCallback(async (id: number, currentPriority: number) => {
    try {
      await updateOrder(id, { priority: currentPriority === 1 ? 0 : 1 });
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle priority');
      throw err;
    }
  }, [loadOrders]);

  return {
    orders,
    loading,
    error,
    refresh: loadOrders,
    addOrder,
    editOrder,
    removeOrder,
    changeStatus,
    togglePriority,
  };
};
