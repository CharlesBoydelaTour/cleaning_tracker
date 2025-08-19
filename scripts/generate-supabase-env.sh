#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="api/.supabase.env"

if ! command -v supabase >/dev/null 2>&1; then
  echo "Supabase CLI non installé (https://supabase.com/docs/reference/cli/install)." >&2
  exit 1
fi

# Démarre supabase si pas lancé
supabase status >/dev/null 2>&1 || supabase start >/dev/null

STATUS=$(supabase status)
SERVICE_KEY=$(echo "$STATUS" | grep 'service_role key:' | awk '{print $NF}')
ANON_KEY=$(echo "$STATUS" | grep 'anon key:' | awk '{print $NF}')
API_URL=$(echo "$STATUS" | grep 'API URL:' | awk '{print $NF}')
DB_PORT=$(echo "$STATUS" | grep 'DB URL:' | sed -E 's/.*:([0-9]{4,5})\/.*/\1/' | tail -1)

if [ -z "${SERVICE_KEY}" ] || [ -z "${ANON_KEY}" ] || [ -z "${API_URL}" ]; then
  echo "Impossible d'extraire toutes les valeurs depuis supabase status:" >&2
  echo "$STATUS" >&2
  exit 1
fi

# Le port DB par défaut CLI est 54322 si non détecté
DB_PORT=${DB_PORT:-54322}

cat >"${OUT_FILE}" <<EOF
# Fichier généré automatiquement - NE PAS COMMIT SI SENSIBLE
SUPABASE_URL=${API_URL}
SUPABASE_ANON_KEY=${ANON_KEY}
SERVICE_ROLE_KEY=${SERVICE_KEY}
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:${DB_PORT}/postgres
EOF

echo "Fichier ${OUT_FILE} généré avec succès."
