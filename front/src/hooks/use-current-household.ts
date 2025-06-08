import { useState, useEffect } from 'react';
import { householdsService } from '@/services/households.service';
import type { Household } from '@/types';

export function useCurrentHousehold() {
  const [currentHousehold, setCurrentHousehold] = useState<Household | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCurrentHousehold = async () => {
      try {
        const households = await householdsService.getAll();
        
        // Pour le moment, on prend le premier ménage
        // Dans une version future, on pourrait stocker l'ID du ménage sélectionné dans localStorage
        if (households.length > 0) {
          setCurrentHousehold(households[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch household');
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentHousehold();
  }, []);

  return {
    currentHousehold,
    loading,
    error,
    householdId: currentHousehold?.id || null,
    householdName: currentHousehold?.name || null,
  };
}
