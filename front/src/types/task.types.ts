export type TaskStatus = 'pending' | 'snoozed' | 'done' | 'skipped' | 'overdue';

export interface TaskDefinition {
  id: string;
  household_id?: string;
  title: string;
  description?: string;
  recurrence_rule: string;
  estimated_minutes?: number;
  room_id?: string;
  is_catalog: boolean;
  created_by?: string;
  created_at: string;
}

export interface TaskOccurrence {
  id: string;
  task_id: string;
  scheduled_date: string;
  due_at: string;
  status: TaskStatus;
  assigned_to?: string;
  snoozed_until?: string;
  created_at: string;
  // Champs enrichis
  task_title?: string;
  task_description?: string;
  room_name?: string;
  assigned_user_email?: string;
}

export interface TaskCompletion {
  occurrence_id: string;
  completed_by: string;
  completed_at: string;
  duration_minutes?: number;
  comment?: string;
  photo_url?: string;
  created_at: string;
}

export interface TaskDefinitionCreate {
  title: string;
  description?: string;
  recurrence_rule: string;
  estimated_minutes?: number;
  room_id?: string;
  household_id?: string;
  is_catalog?: boolean;
}

export interface TaskOccurrenceComplete {
  duration_minutes?: number;
  comment?: string;
  photo_url?: string;
}