-- Ajouter le champ start_date aux définitions de tâches
ALTER TABLE public.task_definitions 
ADD COLUMN start_date date DEFAULT CURRENT_DATE;

-- Ajouter un commentaire
COMMENT ON COLUMN public.task_definitions.start_date IS 'Date de début de la génération des occurrences pour cette tâche';
