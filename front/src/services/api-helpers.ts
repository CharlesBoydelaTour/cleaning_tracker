import type { User } from '@/types';

// Helper pour obtenir l'ID de l'utilisateur actuel
export async function getCurrentUserId(): Promise<string | null> {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    // Décoder le JWT pour obtenir l'ID utilisateur
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub || null;
  } catch {
    return null;
  }
}

// Helper pour ajouter requesting_user_id aux requêtes qui en ont besoin
export async function withRequestingUserId<T extends object>(params: T): Promise<T & { requesting_user_id?: string }> {
  const userId = await getCurrentUserId();
  if (!userId) {
    throw new Error('User not authenticated');
  }
  
  return {
    ...params,
    requesting_user_id: userId
  };
}