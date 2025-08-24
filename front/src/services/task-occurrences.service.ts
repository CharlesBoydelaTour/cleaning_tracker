import apiClient from '@/lib/api-client';
import type { TaskOccurrence, TaskOccurrenceWithDefinition, TaskStatus } from '@/types/task.types';

export interface TaskOccurrenceFilters {
  start_date?: string;
  end_date?: string;
  status?: TaskStatus;
  assigned_to?: string;
  room_id?: string;
}

export interface TaskOccurrenceStats {
  total: number;
  by_status: {
    pending: number;
    snoozed: number;
    done: number;
    skipped: number;
    overdue: number;
  };
  completion_rate: number;
  by_room: Record<string, { total: number; done: number }>;
  by_assignee: Record<string, { total: number; done: number }>;
}

export const taskOccurrencesService = {
  /**
   * Récupérer les occurrences d'un ménage
   */
  async getByHousehold(
    householdId: string, 
    filters?: TaskOccurrenceFilters
  ): Promise<TaskOccurrenceWithDefinition[]> {
    const response = await apiClient.get<TaskOccurrenceWithDefinition[]>(
      `/households/${householdId}/occurrences`,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Récupérer les occurrences du jour pour un ménage
   */
  async getTodayTasks(householdId: string): Promise<TaskOccurrenceWithDefinition[]> {
    const today = new Date().toISOString().split('T')[0];
    return this.getByHousehold(householdId, {
      start_date: today,
      end_date: today
    });
  },

  /**
   * Récupérer les occurrences de la semaine pour un ménage
   */
  async getWeekTasks(householdId: string): Promise<TaskOccurrenceWithDefinition[]> {
    const today = new Date();
    const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
    const endOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 6));
    
    return this.getByHousehold(householdId, {
      start_date: startOfWeek.toISOString().split('T')[0],
      end_date: endOfWeek.toISOString().split('T')[0]
    });
  },

  /**
   * Récupérer les détails d'une occurrence
   */
  async getById(occurrenceId: string): Promise<TaskOccurrenceWithDefinition> {
    const response = await apiClient.get<TaskOccurrenceWithDefinition>(
      `/occurrences/${occurrenceId}`
    );
    return response.data;
  },

  /**
   * Marquer une occurrence comme complétée
   */
  async complete(
    occurrenceId: string,
    data: {
      duration_minutes?: number;
      comment?: string;
      photo_url?: string;
    }
  ): Promise<void> {
    await apiClient.put(`/occurrences/${occurrenceId}/complete`, data);
  },

  /**
   * Reporter une occurrence
   */
  async snooze(
    occurrenceId: string,
    snoozed_until: string
  ): Promise<TaskOccurrence> {
    const response = await apiClient.put<TaskOccurrence>(
      `/occurrences/${occurrenceId}/snooze`,
      { snoozed_until }
    );
    return response.data;
  },

  /**
   * Ignorer une occurrence
   */
  async skip(
    occurrenceId: string,
    reason?: string
  ): Promise<TaskOccurrence> {
    const response = await apiClient.put<TaskOccurrence>(
      `/occurrences/${occurrenceId}/skip`,
      { reason }
    );
    return response.data;
  },

  /**
   * Assigner une occurrence à un membre
   */
  async assign(
    occurrenceId: string,
    assigned_to: string
  ): Promise<TaskOccurrence> {
    const response = await apiClient.put<TaskOccurrence>(
      `/occurrences/${occurrenceId}/assign`,
      { assigned_to }
    );
    return response.data;
  },

  /**
   * Remettre une occurrence effectuée à refaire aujourd'hui
   */
  async reopen(occurrenceId: string): Promise<TaskOccurrence> {
    const response = await apiClient.put<TaskOccurrence>(
      `/occurrences/${occurrenceId}/reopen`
    );
    return response.data;
  },

  /**
   * Supprimer une occurrence (généralement après complétion si on veut la retirer de la vue)
   */
  async delete(occurrenceId: string): Promise<void> {
    await apiClient.delete(`/occurrences/${occurrenceId}`);
  },

  /**
   * Générer les occurrences pour un ménage
   */
  async generateForHousehold(
    householdId: string,
    days_ahead: number = 30
  ): Promise<{ message: string; count: number }> {
    const response = await apiClient.post(
      `/households/${householdId}/occurrences/generate`,
      {},
      { params: { days_ahead } }
    );
    return response.data;
  },

  /**
   * Obtenir les statistiques d'un ménage
   */
  async getStats(
    householdId: string,
    start_date: string,
    end_date: string,
    assigned_to?: string
  ): Promise<TaskOccurrenceStats> {
    const response = await apiClient.get<TaskOccurrenceStats>(
      `/households/${householdId}/occurrences/stats`,
      {
        params: {
          start_date,
          end_date,
          assigned_to
        }
      }
    );
    return response.data;
  }
};
