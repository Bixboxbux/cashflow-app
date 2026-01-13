import { useState, useEffect, useCallback } from 'react';
import { DailyStats, getDailyStats } from '../database/queries';

export const useDailyStats = (date?: string) => {
  const [stats, setStats] = useState<DailyStats>({
    todo: 0,
    in_progress: 0,
    done: 0,
    problem: 0,
    urgent: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDailyStats(date);
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
      console.error('Error loading stats:', err);
    } finally {
      setLoading(false);
    }
  }, [date]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return {
    stats,
    loading,
    error,
    refresh: loadStats,
  };
};
