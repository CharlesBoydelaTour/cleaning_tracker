import { useState, useEffect } from 'react';
import { toast } from '@/hooks/use-toast';
import { taskOccurrencesService } from '@/services/task-occurrences.service';
import type { TaskOccurrenceWithDefinition, TaskStatus } from '@/types/task.types';

export interface TaskOccurrenceFilters {
  status?: TaskStatus;
  assigned_to?: string;
  room_id?: string;
}

export function useTaskOccurrences(householdId: string | null) {
  const [tasks, setTasks] = useState<TaskOccurrenceWithDefinition[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async (filters?: TaskOccurrenceFilters) => {
    if (!householdId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await taskOccurrencesService.getByHousehold(householdId, filters);
      setTasks(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(errorMessage);
      toast({
        title: 'Erreur',
        description: 'Impossible de récupérer les tâches',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchTodayTasks = async () => {
    if (!householdId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await taskOccurrencesService.getTodayTasks(householdId);
      setTasks(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch today tasks';
      setError(errorMessage);
      toast({
        title: 'Erreur',
        description: 'Impossible de récupérer les tâches du jour',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (
    occurrenceId: string,
    data: {
      duration_minutes?: number;
      comment?: string;
      photo_url?: string;
    }
  ) => {
    try {
      await taskOccurrencesService.complete(occurrenceId, data);
      
      // Mettre à jour l'état local
      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.id === occurrenceId
            ? { ...task, status: 'done' as TaskStatus }
            : task
        )
      );

      toast({
        title: 'Tâche terminée',
        description: 'La tâche a été marquée comme complétée',
      });
    } catch (err) {
      toast({
        title: 'Erreur',
        description: 'Impossible de marquer la tâche comme complétée',
        variant: 'destructive',
      });
    }
  };

  const reopenTask = async (occurrenceId: string) => {
    try {
      // Appel direct via service (exposé ailleurs). Ici on ne fait pas d'appel réseau pour garder le hook générique,
      // on laisse les pages appeler service.reopen puis mettre à jour via ce setter local
      setTasks(prev => prev.map(t => t.id === occurrenceId ? { ...t, status: 'pending' as TaskStatus, snoozed_until: null } : t));
    } catch (err) {
      // si besoin, on pourrait remonter une erreur
    }
  };

  // Reporter/Ignorer désactivés côté UI par demande produit. On garde les fonctions pour usages futurs.
  const snoozeTask = async (_occurrenceId: string, _snoozedUntil: string) => { /* noop in UI */ };
  const skipTask = async (_occurrenceId: string, _reason?: string) => { /* noop in UI */ };

  useEffect(() => {
    if (householdId) {
      fetchTodayTasks();
    }
  }, [householdId]);

  return {
    tasks,
    loading,
    error,
    fetchTasks,
    fetchTodayTasks,
    completeTask,
  reopenTask,
    snoozeTask,
    skipTask,
    refetch: fetchTasks,
  };
}

export function useTodayTasks(householdId: string | null) {
  const { tasks, loading, error, fetchTodayTasks, completeTask, snoozeTask, skipTask } = useTaskOccurrences(householdId);

  // Calculer les statistiques du jour
  const todayStats = {
    total: tasks.length,
    completed: tasks.filter(task => task.status === 'done').length,
    overdue: tasks.filter(task => task.status === 'overdue').length,
    todo: tasks.filter(task => task.status === 'pending' || task.status === 'snoozed').length,
    completionRate: tasks.length > 0 ? Math.round((tasks.filter(task => task.status === 'done').length / tasks.length) * 100) : 0,
  };

  // Séparer les tâches par statut
  const tasksByStatus = {
    completed: tasks.filter(task => task.status === 'done'),
    overdue: tasks.filter(task => task.status === 'overdue'),
    todo: tasks.filter(task => task.status === 'pending' || task.status === 'snoozed'),
  };

  return {
    tasks,
    loading,
    error,
    todayStats,
    tasksByStatus,
    completeTask,
    snoozeTask,
    skipTask,
    refetch: fetchTodayTasks,
  };
}
