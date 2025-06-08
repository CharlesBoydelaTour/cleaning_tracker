import axios from 'axios';
import { Room } from '../types/household.types';

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

export const roomsService = {
  // Récupérer toutes les pièces d'un foyer
  getAll: async (householdId: string): Promise<Room[]> => {
    const response = await api.get(`/households/${householdId}/rooms`);
    return response.data;
  },

  // Créer une nouvelle pièce
  create: async (householdId: string, roomData: { name: string; icon?: string }): Promise<Room> => {
    const response = await api.post(`/households/${householdId}/rooms`, roomData);
    return response.data;
  },

  // Récupérer une pièce spécifique
  getById: async (householdId: string, roomId: string): Promise<Room> => {
    const response = await api.get(`/households/${householdId}/rooms/${roomId}`);
    return response.data;
  },

  // Mettre à jour une pièce
  update: async (householdId: string, roomId: string, roomData: { name?: string; icon?: string }): Promise<Room> => {
    const response = await api.put(`/households/${householdId}/rooms/${roomId}`, roomData);
    return response.data;
  },

  // Supprimer une pièce
  delete: async (householdId: string, roomId: string): Promise<void> => {
    await api.delete(`/households/${householdId}/rooms/${roomId}`);
  }
};
