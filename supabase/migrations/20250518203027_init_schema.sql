-- Households & membres
create table public.households (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table public.household_members (
  household_id uuid references households(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  role text not null default 'member' check (role in ('admin','member','guest')),
  joined_at timestamptz not null default now(),
  id uuid primary key default gen_random_uuid()
);

-- Rooms
create table public.rooms (
  id uuid primary key default gen_random_uuid(),
  household_id uuid references households(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now(),
  icon text
);

-- Task definitions
create type public.task_status as enum ('pending','snoozed','done','skipped','overdue');

create table public.task_definitions (
  id uuid primary key default gen_random_uuid(),
  household_id uuid references households(id) on delete cascade,
  is_catalog boolean not null default false,
  room_id uuid references rooms(id),
  title text not null,
  description text,
  recurrence_rule text not null,
  estimated_minutes int,
  created_by uuid references auth.users(id)
);

-- Task occurrences & complétions
create table public.task_occurrences (
  id uuid primary key default gen_random_uuid(),
  task_id uuid references task_definitions(id) on delete cascade,
  scheduled_date date not null,
  due_at timestamptz not null,
  status task_status not null default 'pending',
  assigned_to uuid references auth.users(id),
  snoozed_until timestamptz,
  unique (task_id, scheduled_date)
);

create table public.task_completions (
  occurrence_id uuid primary key references task_occurrences(id) on delete cascade,
  completed_by uuid references auth.users(id),
  completed_at timestamptz not null default now(),
  duration_minutes int,
  comment text,
  photo_url text
);

-- Notifications
create type public.notif_channel as enum ('push','email');

create table public.notifications (
  id bigint generated always as identity primary key,
  occurrence_id uuid references task_occurrences(id) on delete cascade,
  member_id uuid references auth.users(id),
  channel notif_channel not null,
  sent_at timestamptz,
  delivered boolean default false
);

alter table task_definitions enable row level security;
alter table rooms            enable row level security;
alter table task_occurrences enable row level security;

create policy "Household access"
on task_definitions
using (
  (household_id is null)  -- catalogue global
  or (household_id in (select household_id
                       from household_members
                       where user_id = auth.uid()))
);
