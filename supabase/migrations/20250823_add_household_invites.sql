-- Invitations à des foyers
create type public.invite_status as enum ('pending','accepted','revoked','expired');

create table public.household_invites (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references households(id) on delete cascade,
  email text not null,
  role text not null check (role in ('admin','member','guest')) default 'member',
  invited_by uuid not null references auth.users(id) on delete set null,
  token text not null unique,
  status invite_status not null default 'pending',
  expires_at timestamptz not null default (now() + interval '7 days'),
  accepted_at timestamptz,
  created_at timestamptz not null default now()
);

create index household_invites_household_idx on public.household_invites(household_id);
create index household_invites_email_idx on public.household_invites(email);
create unique index household_invites_unique_pending on public.household_invites(household_id, email) where status = 'pending';

alter table public.household_invites enable row level security;