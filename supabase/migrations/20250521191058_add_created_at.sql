-- 1. Households : ajout de created_at si absent
ALTER TABLE public.households
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();

-- 2. Household members : ajout de joined_at si absent
ALTER TABLE public.household_members
  ADD COLUMN IF NOT EXISTS joined_at timestamptz NOT NULL DEFAULT now();

-- 3. Rooms : ajout de created_at et icon si absents
ALTER TABLE public.rooms
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS icon text;

-- 4. Task definitions :
--    ajout de created_at et created_by si absents
ALTER TABLE public.task_definitions
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS created_by uuid REFERENCES auth.users(id);

-- 5. Task occurrences :
--    ajout de created_at, status, assigned_to et snoozed_until si absents
ALTER TABLE public.task_occurrences
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS status public.task_status NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS assigned_to uuid REFERENCES auth.users(id),
  ADD COLUMN IF NOT EXISTS snoozed_until timestamptz;

-- 6. Task completions :
--    ajout de completed_by, completed_at, duration_minutes, comment, created_at et photo_url si absents
ALTER TABLE public.task_completions
  ADD COLUMN IF NOT EXISTS completed_by uuid REFERENCES auth.users(id),
  ADD COLUMN IF NOT EXISTS completed_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS duration_minutes int,
  ADD COLUMN IF NOT EXISTS comment text,
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS photo_url text;

-- 7. Notifications :
--    ajout de channel, created_at, sent_at et delivered si absents
--    (la colonne id et occurrence_id existaient déjà)
--    suppose que le type notif_channel a déjà été créé
ALTER TABLE public.notifications
  ADD COLUMN IF NOT EXISTS channel public.notif_channel NOT NULL,
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS sent_at timestamptz,
  ADD COLUMN IF NOT EXISTS delivered boolean DEFAULT false;

-- 8. S’assurer que vos types ENUM sont présents (PostgreSQL < 9.6 n’a pas IF NOT EXISTS)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
    CREATE TYPE public.task_status AS ENUM ('pending','snoozed','done','skipped','overdue');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notif_channel') THEN
    CREATE TYPE public.notif_channel AS ENUM ('push','email');
  END IF;
END
$$;

-- 9. Policies et RLS (idempotent)
ALTER TABLE public.task_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rooms            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_occurrences ENABLE ROW LEVEL SECURITY;

-- La policy “Household access” :
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM pg_policies
     WHERE schemaname = 'public'
       AND tablename  = 'task_definitions'
       AND policyname = 'Household access'
  ) THEN
    CREATE POLICY "Household access"
      ON public.task_definitions
      USING (
        (household_id IS NULL)
        OR (household_id IN (
           SELECT household_id
             FROM public.household_members
            WHERE user_id = auth.uid()
         ))
      );
  END IF;
END
$$;
