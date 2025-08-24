-- Ajouter le champ priority aux tâches
ALTER TABLE public.task_definitions 
ADD COLUMN priority text DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high'));
