import apiClient from '@/lib/api-client';
import { withRequestingUserId } from './api-helpers';
import type { Household, HouseholdCreate, HouseholdMember, HouseholdMemberCreate, Room } from '@/types';

export const householdsService = {
  async getAll(userId?: string): Promise<Household[]> { // Accepter un userId optionnel
    const params = userId ? { user_id: userId } : {}; // L'API attend 'user_id'
    const response = await apiClient.get<Household[]>('/households', { params });
    return response.data;
  },

  async getById(id: string): Promise<Household> {
    const response = await apiClient.get<Household>(`/households/${id}`);
    return response.data;
  },

  async create(data: HouseholdCreate): Promise<Household> {
    const params = await withRequestingUserId({});
    const response = await apiClient.post<Household>(
      '/households',
      data,
      { params }
    );
    return response.data;
  },

  async getMembers(householdId: string): Promise<HouseholdMember[]> {
    const params = await withRequestingUserId({});
    const response = await apiClient.get<HouseholdMember[]>(
      `/households/${householdId}/members`,
      { params }
    );
    return response.data;
  },

  async addMember(householdId: string, data: HouseholdMemberCreate): Promise<HouseholdMember> {
    const params = await withRequestingUserId({});
    const response = await apiClient.post<HouseholdMember>(
      `/households/${householdId}/members`,
      data,
      { params }
    );
    return response.data;
  },

  async updateMember(householdId: string, memberId: string, role: string): Promise<HouseholdMember> {
    const params = await withRequestingUserId({});
    const response = await apiClient.put<HouseholdMember>(
      `/households/${householdId}/members/${memberId}`,
      { role },
      { params }
    );
    return response.data;
  },

  async removeMember(householdId: string, memberId: string): Promise<void> {
    const params = await withRequestingUserId({});
    await apiClient.delete(
      `/households/${householdId}/members/${memberId}`,
      { params }
    );
  },

  async getRooms(householdId: string): Promise<Room[]> {
    const response = await apiClient.get<Room[]>(
      `/households/${householdId}/rooms`
    );
    return response.data;
  },

  async createRoom(householdId: string, data: { name: string; icon?: string }): Promise<Room> {
    const response = await apiClient.post<Room>(
      `/households/${householdId}/rooms`,
      data
    );
    return response.data;
  }
};