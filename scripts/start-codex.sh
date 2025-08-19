#!/usr/bin/env bash
set -euo pipefail

echo "[codex] Chargement des variables (.env.remote si présent)"
if [ -f "api/.env.remote" ]; then
  set -a
  source api/.env.remote
  set +a
fi

echo "[codex] Vérification variables critiques (hors DB si mode local)"
missing=()
core_vars=(SUPABASE_URL SUPABASE_ANON_KEY SECRET_KEY)
for v in "${core_vars[@]}"; do
  [ -n "${!v-}" ] || missing+=("$v")
done
if [ "${USE_LOCAL_DB:-0}" = "0" ]; then
  # En mode distant on exige DATABASE_URL
  [ -n "${DATABASE_URL-}" ] || missing+=(DATABASE_URL)
fi
if [ ${#missing[@]} -gt 0 ]; then
  echo "ERREUR: variables manquantes: ${missing[*]}" >&2
  exit 1
fi

if [ "${USE_LOCAL_DB:-0}" = "1" ]; then
  echo "[codex] Mode base locale forcé (USE_LOCAL_DB=1)"
elif [ "${FORCE_REMOTE:-0}" = "1" ]; then
  echo "[codex] FORCE_REMOTE=1 -> on tente la base distante sans fallback"
else
  echo "[codex] Test reachabilité hôte Postgres distant"
  host=$(echo "${DATABASE_URL}" | sed -E 's#.*://[^@]*@([^/:]+).*#\1#') || host=""
  if [ -n "$host" ]; then
    if ! (getent hosts "$host" >/dev/null 2>&1 || nslookup "$host" >/dev/null 2>&1); then
      echo "[codex] DNS vers $host impossible -> fallback local" >&2
      USE_LOCAL_DB=1
    else
      # Tentative socket TCP rapide (si nc présent)
      if command -v nc >/dev/null 2>&1; then
        port=$(echo "$DATABASE_URL" | sed -E 's#.*://[^@]*@[^/:]+:([0-9]+).*#\1#')
        port=${port:-5432}
        if ! nc -z -w2 "$host" "$port" >/dev/null 2>&1; then
          if [ "${FORCE_REMOTE:-0}" = "1" ]; then
            echo "[codex] Port $port injoignable mais FORCE_REMOTE=1 -> pas de fallback" >&2
          else
            echo "[codex] Port $port injoignable sur $host -> fallback local" >&2
            USE_LOCAL_DB=1
          fi
        fi
      fi
  fi
  fi
fi

if [ "${USE_LOCAL_DB:-0}" = "1" ]; then
  echo "[codex] Installation Postgres local"
  apt-get update -y >/dev/null 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib >/dev/null 2>&1 || true
  service postgresql start || true
  export DATABASE_URL="postgresql://postgres@localhost:5432/postgres"
  # Création extension utile
  sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" >/dev/null 2>&1 || true
  echo "[codex] DATABASE_URL basculé sur $DATABASE_URL"
  if [ "${SKIP_AUTH_STUB:-0}" = "1" ]; then
    echo "[codex] SKIP_AUTH_STUB=1 -> tentative sans stub auth"
    if [ "${APPLY_LOCAL_MIGRATIONS:-1}" = "1" ] && [ -d "supabase/migrations" ]; then
      if grep -Eqi '\bauth\.' supabase/migrations/*.sql 2>/dev/null; then
        if [ "${FORCE_FAIL_ON_AUTH:-0}" = "1" ]; then
          echo "[codex][ERREUR] Migrations référencent auth.* mais SKIP_AUTH_STUB=1 et FORCE_FAIL_ON_AUTH=1" >&2
          echo "         -> Désactive FORCE_FAIL_ON_AUTH ou retire SKIP_AUTH_STUB pour continuer." >&2
          exit 12
        else
          echo "[codex] Migrations nécessitent auth.* -> création d'un stub minimal malgré SKIP_AUTH_STUB=1"
          LOCAL_AUTH_USER_ID="${LOCAL_AUTH_USER_ID:-00000000-0000-0000-0000-000000000000}"
          sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
create schema if not exists auth;
create table if not exists auth.users (
  id uuid primary key,
  email text,
  created_at timestamptz default now()
);
create or replace function auth.uid() returns uuid
language plpgsql as $$
begin
  return coalesce(current_setting('request.jwt.claim.sub', true)::uuid, '${LOCAL_AUTH_USER_ID}'::uuid);
end;
$$;
SQL
          sudo -u postgres psql -c "insert into auth.users (id,email) values ('${LOCAL_AUTH_USER_ID}','local@example.com') on conflict (id) do nothing;" >/dev/null
          echo "[codex] Stub minimal auth créé (override)"
        fi
      fi
    fi
  else
    echo "[codex] Préparation stub Supabase (schéma auth + fonction auth.uid())"
    LOCAL_AUTH_USER_ID="${LOCAL_AUTH_USER_ID:-00000000-0000-0000-0000-000000000000}"
    # Création explicite avec arrêt sur erreur
    sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
create schema if not exists auth;
create table if not exists auth.users (
  id uuid primary key,
  email text,
  raw_app_meta_data jsonb default '{}'::jsonb,
  raw_user_meta_data jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);
create or replace function auth.uid() returns uuid
language plpgsql as $$
begin
  return coalesce(current_setting('request.jwt.claim.sub', true)::uuid, '${LOCAL_AUTH_USER_ID}'::uuid);
end;
$$;
SQL
    # Insertion user fictif
    sudo -u postgres psql -c "insert into auth.users (id,email) values ('${LOCAL_AUTH_USER_ID}','local@example.com') on conflict (id) do nothing;" >/dev/null
    # Vérification existence fonction
    if ! sudo -u postgres psql -tAc "select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='auth' and p.proname='uid' and p.pronargs=0" | grep -q 1; then
      echo "[codex][ERREUR] La fonction auth.uid() n'a pas été créée" >&2
      exit 11
    fi
    echo "[codex] Stub auth prêt (user=${LOCAL_AUTH_USER_ID})"
  fi
  if [ "${APPLY_LOCAL_MIGRATIONS:-1}" = "1" ]; then
    echo "[codex] Application des migrations locales"
    if [ -d "supabase/migrations" ]; then
      for f in supabase/migrations/*.sql; do
        [ -f "$f" ] || continue
        echo "[codex][migration] $f"
        sudo -u postgres psql -v ON_ERROR_STOP=1 -f "$f" >/dev/null || { echo "Migration échouée: $f" >&2; exit 3; }
      done
      echo "[codex] Migrations locales appliquées"
    else
      echo "[codex] Dossier supabase/migrations introuvable — skip"
    fi
  else
    echo "[codex] APPLY_LOCAL_MIGRATIONS=0 -> migrations ignorées"
  fi
fi

echo "[codex] Démarrage/installation Redis local (optionnel)"
if ! command -v redis-server >/dev/null 2>&1; then
  apt-get update -y >/dev/null 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get install -y redis-server >/dev/null 2>&1 || true
fi
redis-server --daemonize yes 2>/dev/null || echo "Redis déjà lancé ou indisponible"

echo "[codex] Installation dépendances Python (uv)"
cd api
if [ ! -d .venv ]; then
  pip install --no-cache-dir uv >/dev/null 2>&1 || true
  uv sync --frozen
fi

echo "[codex] Lancement API en arrière-plan (DB=${USE_LOCAL_DB:-0})"
nohup uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 >/tmp/api.log 2>&1 &
API_PID=$!
sleep 2
if ! kill -0 "$API_PID" 2>/dev/null; then
  echo "API ne s'est pas lancée. Voir /tmp/api.log" >&2
  exit 2
fi

echo "[codex] Installation Bun + dépendances front"
cd ../front
if ! command -v bun >/dev/null 2>&1; then
  curl -fsSL https://bun.sh/install | bash >/dev/null 2>&1
  export BUN_INSTALL="$HOME/.bun"
  export PATH="$BUN_INSTALL/bin:$PATH"
fi
bun install --no-progress

if [ "${SKIP_CHECKS:-0}" != "1" ]; then
  echo "[codex] Vérifications pré-lancement front"

  # 1. Vérifier API (retry)
  echo -n "[check] API readiness: "
  api_ok=0
  for i in $(seq 1 15); do
    if curl -fsS http://localhost:8000/ >/dev/null 2>&1; then api_ok=1; break; fi
    sleep 1
  done
  if [ $api_ok -eq 1 ]; then echo "OK"; else echo "ECHEC"; fi

  # 2. Vérifier Redis
  if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping 2>/dev/null | grep -q PONG; then
      echo "[check] Redis: OK"
    else
      echo "[check] Redis: ECHEC" >&2
    fi
  else
    echo "[check] Redis: redis-cli absent"
  fi

  # 3. Vérifier DB (si locale ou si psql disponible)
  if [ "${USE_LOCAL_DB:-0}" = "1" ]; then
    if command -v psql >/dev/null 2>&1; then
      if sudo -u postgres psql -tAc 'select 1' >/dev/null 2>&1; then
        echo "[check] DB locale: OK"
        # Table indicative
        sudo -u postgres psql -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='public' LIMIT 5;" | sed 's/^/[check][tables] /'
      else
        echo "[check] DB locale: ECHEC" >&2
      fi
    else
      echo "[check] DB locale: psql absent"
    fi
  else
    # Pour remote, test résolution + port (best effort)
    host=$(echo "${DATABASE_URL}" | sed -E 's#.*://[^@]*@([^/:]+).*#\1#') || host=""
    if [ -n "$host" ]; then
      if getent hosts "$host" >/dev/null 2>&1; then
        echo "[check] DB distante DNS: OK ($host)"
      else
        echo "[check] DB distante DNS: ECHEC ($host)" >&2
      fi
    fi
  fi

  # 4. Résumé
  echo "[codex] Résumé: MODE_DB=$([ "${USE_LOCAL_DB:-0}" = "1" ] && echo local || echo remote) API=$([ $api_ok -eq 1 ] && echo OK || echo FAIL)"
fi

echo "[codex] Démarrage front (Vite) sur port 8080"
exec bun run dev --host 0.0.0.0 --port 8080
