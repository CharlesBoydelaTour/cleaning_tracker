import { useState, useEffect, useCallback } from 'react';
import { householdsService } from '@/services/households.service';
import type { Household } from '@/types';
import { useAuth } from '@/hooks/use-auth'; // Assurez-vous que useAuth est importé

export function useCurrentHousehold() {
  const [currentHousehold, setCurrentHousehold] = useState<Household | null>(null);
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
      // L'API /households utilise maintenant l'authentification JWT
      const households = await householdsService.getAll();
      
      if (households.length > 0) {
        // Le premier ménage de la liste est celui à afficher (tri alphabétique fait par l'API)
        setCurrentHousehold(households[0]);
      } else {
        // Aucun ménage n'est associé à cet utilisateur
        setCurrentHousehold(null);
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

  return {
    currentHousehold,
    loading,
    error,
    householdId: currentHousehold?.id || null,
    householdName: currentHousehold?.name || null,
    refetch: fetchCurrentHousehold,
  };
}