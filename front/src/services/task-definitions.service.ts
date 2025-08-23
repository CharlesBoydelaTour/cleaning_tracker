import apiClient from '@/lib/api-client';
import type { TaskDefinition } from '@/types/task.types';
import { addDays, formatISO } from 'date-fns';

// Réponse enrichie par l'API (jointure avec rooms)
export interface TaskDefinitionListItem extends TaskDefinition {
  room_name?: string;
}

export const taskDefinitionsService = {
  async getByHousehold(householdId: string): Promise<TaskDefinitionListItem[]> {
    const response = await apiClient.get<TaskDefinitionListItem[]>(
      `/households/${householdId}/task-definitions`
    );
    return response.data;
  },

  /**
   * Récupérer la prochaine occurrence d'une définition de tâche.
   * Retourne la date planifiée (scheduled_date) sous forme de string ISO (YYYY-MM-DD) si trouvée, sinon null.
   */
  async getNextOccurrenceDate(
    householdId: string,
    taskDefId: string,
    options?: { horizonDays?: number }
  ): Promise<string | null> {
    const horizonDays = options?.horizonDays ?? 365;
    const start = new Date();
    const end = addDays(start, horizonDays);
    const params = {
      start_date: formatISO(start, { representation: 'date' }),
      end_date: formatISO(end, { representation: 'date' }),
      max_occurrences: 1,
    } as const;

    const response = await apiClient.post(
      `/households/${householdId}/task-definitions/${taskDefId}/generate-occurrences`,
      {},
      { params }
    );
    const list = response.data as Array<{ scheduled_date?: string }>;
    if (Array.isArray(list) && list.length > 0) {
      return list[0]?.scheduled_date ?? null;
    }
    return null;
  },
};

export default taskDefinitionsService;
