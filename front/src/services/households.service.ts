import apiClient from '@/lib/api-client';
import { withRequestingUserId } from './api';
import type { Household, HouseholdCreate, HouseholdMember, HouseholdMemberCreate, Room } from '@/types';

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
    const response = await apiClient.get<HouseholdMember[]>(`/households/${householdId}/members`);
    return response.data;
  },

  async addMember(householdId: string, data: HouseholdMemberCreate): Promise<HouseholdMember> {
    const response = await apiClient.post<HouseholdMember>(
      `/households/${householdId}/members`,
      data
    );
    return response.data;
  },

  async updateMember(householdId: string, memberId: string, role: string): Promise<HouseholdMember> {
    const response = await apiClient.put<HouseholdMember>(
      `/households/${householdId}/members/${memberId}`,
      { role }
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
  },

  async leave(householdId: string): Promise<void> {
    await apiClient.post(`/households/${householdId}/leave`);
  },

  async delete(householdId: string): Promise<void> {
    await apiClient.delete(`/households/${householdId}`);
  }
};