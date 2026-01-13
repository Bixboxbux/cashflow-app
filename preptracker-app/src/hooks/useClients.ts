import { useState, useEffect, useCallback } from 'react';
import { Client, getAllClients, createClient, updateClient, deleteClient } from '../database/queries';

export const useClients = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadClients = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAllClients();
      setClients(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clients');
      console.error('Error loading clients:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  const addClient = useCallback(async (client: Omit<Client, 'id' | 'created_at'>) => {
    try {
      await createClient(client);
      await loadClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add client');
      throw err;
    }
  }, [loadClients]);

  const editClient = useCallback(async (id: number, client: Partial<Client>) => {
    try {
      await updateClient(id, client);
      await loadClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update client');
      throw err;
    }
  }, [loadClients]);

  const removeClient = useCallback(async (id: number) => {
    try {
      await deleteClient(id);
      await loadClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete client');
      throw err;
    }
  }, [loadClients]);

  return {
    clients,
    loading,
    error,
    refresh: loadClients,
    addClient,
    editClient,
    removeClient,
  };
};
