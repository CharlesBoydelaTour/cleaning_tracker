import { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import type { ApiError } from '@/types';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
): UseApiState<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      setState({ data: null, loading: true, error: null });
      
      try {
        const data = await apiCall();
        if (!cancelled) {
          setState({ data, loading: false, error: null });
        }
      } catch (err) {
        if (!cancelled) {
          const error = err as AxiosError<ApiError>;
          setState({
            data: null,
            loading: false,
            error: error.response?.data || {
              error: {
                code: 'UNKNOWN_ERROR',
                message: 'Une erreur est survenue',
                severity: 'high'
              }
            }
          });
        }
      }
    };

    fetchData();

    return () => {
      cancelled = true;
    };
  }, dependencies);

  return state;
}