import apiClient from '@/lib/api-client';
import type { TaskDefinition, TaskDefinitionCreate, TaskOccurrence } from '@/types';

export const tasksService = {
  async listDefinitions(householdId: string): Promise<TaskDefinition[]> {
    const response = await apiClient.get<TaskDefinition[]>(`/households/${householdId}/task-definitions`);
    return response.data;
  },
  async createDefinition(householdId: string, data: TaskDefinitionCreate): Promise<TaskDefinition> {
    const response = await apiClient.post<TaskDefinition>(`/households/${householdId}/task-definitions`, data);
    return response.data;
  },
  async listOccurrences(householdId: string, params?: { start_date?: string; end_date?: string; status?: string }): Promise<TaskOccurrence[]> {
    const response = await apiClient.get<TaskOccurrence[]>(`/households/${householdId}/occurrences`, { params });
    return response.data;
  }
};
