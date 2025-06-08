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

  const snoozeTask = async (occurrenceId: string, snoozedUntil: string) => {
    try {
      const updatedTask = await taskOccurrencesService.snooze(occurrenceId, snoozedUntil);
      
      // Mettre à jour l'état local
      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.id === occurrenceId
            ? { ...task, status: updatedTask.status, snoozed_until: updatedTask.snoozed_until }
            : task
        )
      );

      toast({
        title: 'Tâche reportée',
        description: 'La tâche a été reportée avec succès',
      });
    } catch (err) {
      toast({
        title: 'Erreur',
        description: 'Impossible de reporter la tâche',
        variant: 'destructive',
      });
    }
  };

  const skipTask = async (occurrenceId: string, reason?: string) => {
    try {
      const updatedTask = await taskOccurrencesService.skip(occurrenceId, reason);
      
      // Mettre à jour l'état local
      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.id === occurrenceId
            ? { ...task, status: updatedTask.status }
            : task
        )
      );

      toast({
        title: 'Tâche ignorée',
        description: 'La tâche a été ignorée',
      });
    } catch (err) {
      toast({
        title: 'Erreur',
        description: 'Impossible d\'ignorer la tâche',
        variant: 'destructive',
      });
    }
  };

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
