import { useState, useEffect, useCallback } from 'react';
import { healthApi } from '../services/api';
import { HealthResponse, DatabaseHealthResponse } from '../types';

export interface HealthState {
  backend: {
    data: HealthResponse | null;
    error: string | null;
    latencyMs: number;
    loading: boolean;
  };
  database: {
    data: DatabaseHealthResponse | null;
    error: string | null;
    latencyMs: number;
    loading: boolean;
  };
  lastChecked: Date | null;
  refresh: () => Promise<void>;
}

export function useHealthCheck(pollIntervalMs = 10000): HealthState {
  const [backendState, setBackendState] = useState<{
    data: HealthResponse | null;
    error: string | null;
    latencyMs: number;
    loading: boolean;
  }>({
    data: null,
    error: null,
    latencyMs: 0,
    loading: true,
  });

  const [databaseState, setDatabaseState] = useState<{
    data: DatabaseHealthResponse | null;
    error: string | null;
    latencyMs: number;
    loading: boolean;
  }>({
    data: null,
    error: null,
    latencyMs: 0,
    loading: true,
  });

  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchHealth = useCallback(async () => {
    setBackendState((prev) => ({ ...prev, loading: true }));
    setDatabaseState((prev) => ({ ...prev, loading: true }));

    const [backendRes, dbRes] = await Promise.all([
      healthApi.checkBackendHealth(),
      healthApi.checkDatabaseHealth(),
    ]);

    setBackendState({
      data: backendRes.data,
      error: backendRes.error,
      latencyMs: backendRes.latencyMs,
      loading: false,
    });

    setDatabaseState({
      data: dbRes.data,
      error: dbRes.error,
      latencyMs: dbRes.latencyMs,
      loading: false,
    });

    setLastChecked(new Date());
  }, []);

  useEffect(() => {
    fetchHealth();
    if (pollIntervalMs > 0) {
      const timer = setInterval(fetchHealth, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [fetchHealth, pollIntervalMs]);

  return {
    backend: backendState,
    database: databaseState,
    lastChecked,
    refresh: fetchHealth,
  };
}
