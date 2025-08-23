import axios from 'axios';
import { HouseholdMember, HouseholdMemberCreate } from '../types/household.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Créer l'instance axios avec gestion d'erreur
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Intercepteur pour ajouter le token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const membersService = {
  // Récupérer tous les membres d'un foyer
  getAll: async (householdId: string): Promise<HouseholdMember[]> => {
    const response = await api.get(`/households/${householdId}/members`);
    return response.data;
  },

  // Inviter un nouveau membre par email
  invite: async (
    householdId: string,
    email: string,
    role: 'admin' | 'member' | 'guest' = 'member'
  ): Promise<{ status: 'created' | 'already_pending' }> => {
    const response = await api.post(`/households/${householdId}/members/invite`, {
      email,
      role,
    });
    return response.data as { status: 'created' | 'already_pending' };
  },

  // Mettre à jour le rôle d'un membre
  updateRole: async (householdId: string, memberId: string, role: 'admin' | 'member' | 'guest'): Promise<HouseholdMember> => {
    const response = await api.put(`/households/${householdId}/members/${memberId}`, { role });
    return response.data;
  },

  // Supprimer un membre du foyer
  remove: async (householdId: string, memberId: string): Promise<void> => {
    await api.delete(`/households/${householdId}/members/${memberId}`);
  },

  // Quitter un foyer
  leave: async (householdId: string): Promise<void> => {
    await api.delete(`/households/${householdId}/members/leave`);
  }
};
