import apiClient from '@/lib/api-client';
import type { Household, HouseholdCreate, HouseholdMember, Room } from '@/types';

export const householdsService = {
  async getAll(): Promise<Household[]> {
    const response = await apiClient.get<Household[]>('/households');
    return response.data;
  },

  async getById(id: string): Promise<Household> {
    const response = await apiClient.get<Household>(`/households/${id}`);
    return response.data;
  },

  async create(data: HouseholdCreate): Promise<Household> {
    const response = await apiClient.post<Household>('/households', data);
    return response.data;
  },

  async getMembers(householdId: string): Promise<HouseholdMember[]> {
    const response = await apiClient.get<HouseholdMember[]>(
      `/households/${householdId}/members`
    );
    return response.data;
  },

  async getRooms(householdId: string): Promise<Room[]> {
    const response = await apiClient.get<Room[]>(
      `/households/${householdId}/rooms`
    );
    return response.data;
  }
};