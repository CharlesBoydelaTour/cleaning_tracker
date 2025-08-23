import { useState, useEffect, useCallback } from 'react';
import { householdsService } from '@/services/households.service';
import type { Household } from '@/types';
import { useAuth } from '@/hooks/use-auth';

const ACTIVE_HOUSEHOLD_KEY = 'active_household_id';

export function useCurrentHousehold() {
  const [currentHousehold, setCurrentHousehold] = useState<Household | null>(null);
  const [households, setHouseholds] = useState<Household[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth(); // Récupérer l'utilisateur authentifié

  const fetchCurrentHousehold = useCallback(async () => {
    if (!user?.id) {
      // Si l'utilisateur n'est pas chargé ou n'a pas d'ID,
      // on considère qu'il n'y a pas de ménage à charger pour lui.
      setCurrentHousehold(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Récupérer les ménages pour l'utilisateur connecté.
      const all = await householdsService.getAll();
      setHouseholds(all);

      if (all.length > 0) {
        // Tenter de restaurer la sélection persistée
        const savedId = localStorage.getItem(ACTIVE_HOUSEHOLD_KEY);
        const found = savedId ? all.find(h => h.id === savedId) : null;
        setCurrentHousehold(found || all[0]);
        if (!found && all[0]) {
          localStorage.setItem(ACTIVE_HOUSEHOLD_KEY, all[0].id);
        }
      } else {
        setCurrentHousehold(null);
        localStorage.removeItem(ACTIVE_HOUSEHOLD_KEY);
      }
    } catch (err) {
      console.error('Erreur lors de la récupération du ménage:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch household');
      setCurrentHousehold(null);
    } finally {
      setLoading(false);
    }
  }, [user]); // Dépend de l'objet user

  useEffect(() => {
    fetchCurrentHousehold();
  }, [fetchCurrentHousehold]); // Appeler fetchCurrentHousehold lorsque la fonction (ou ses dépendances) change

  const selectHousehold = useCallback((householdId: string) => {
    const h = households.find(x => x.id === householdId) || null;
    setCurrentHousehold(h || null);
    if (h) {
      localStorage.setItem(ACTIVE_HOUSEHOLD_KEY, h.id);
    } else {
      localStorage.removeItem(ACTIVE_HOUSEHOLD_KEY);
    }
  }, [households]);

  return {
    currentHousehold,
    households,
    loading,
    error,
    householdId: currentHousehold?.id || null,
    householdName: currentHousehold?.name || null,
    refetch: fetchCurrentHousehold,
    selectHousehold,
  };
}