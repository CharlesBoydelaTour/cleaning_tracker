#!/usr/bin/env bash
set -euo pipefail

echo "[deps] Installation des dépendances (sans lancement API/front)"

# Fonction retry simple (3 tentatives)
retry() {
  local n=0 max=${2:-3} delay=${3:-2}
  shift || true
  until "$@"; do
    n=$((n+1))
    if [ $n -ge $max ]; then
      return 1
    fi
    sleep $delay
  done
}

if [ -f "api/.env.remote" ]; then
  echo "[deps] Chargement api/.env.remote"
  set -a; source api/.env.remote; set +a
fi

SKIP_PY=${SKIP_PY:-0}
SKIP_FRONT=${SKIP_FRONT:-0}

if [ "$SKIP_PY" = "0" ]; then
  echo "[deps] Backend: installation uv + synchro dépendances"
  cd api
  if ! command -v uv >/dev/null 2>&1; then
    echo "[deps][py] Installation uv (retry)"
    retry 3 2 pip install --no-cache-dir uv >/dev/null 2>&1 || echo "[deps][warn] uv non installé (continu)"
  fi
  if command -v uv >/dev/null 2>&1; then
    if [ ! -d .venv ]; then
      retry 3 2 uv sync --frozen || uv sync || echo "[deps][warn] uv sync partielle"
    else
      retry 3 2 uv sync || echo "[deps][warn] uv sync partielle"
    fi
  fi
  cd - >/dev/null
else
  echo "[deps] Backend ignoré (SKIP_PY=1)"
fi

if [ "$SKIP_FRONT" = "0" ]; then
  echo "[deps] Frontend: installation Bun + packages"
  if ! command -v bun >/dev/null 2>&1; then
    echo "[deps][front] Installation bun (retry)"
    if retry 3 3 curl -fsSL https://bun.sh/install | bash >/dev/null 2>&1; then
      export BUN_INSTALL="$HOME/.bun"
      export PATH="$BUN_INSTALL/bin:$PATH"
    else
      echo "[deps][warn] bun non installé (continu)"
    fi
  fi
  if command -v bun >/dev/null 2>&1; then
    cd front
    retry 3 2 bun install --no-progress || bun install --no-progress || echo "[deps][warn] bun install partielle"
    cd - >/dev/null
  fi
else
  echo "[deps] Frontend ignoré (SKIP_FRONT=1)"
fi

echo "[deps] Terminé. Pour lancer ensuite: scripts/start-codex.sh (ou docker-compose)."

if [ "${KEEP_ALIVE:-0}" = "1" ]; then
  echo "[deps] KEEP_ALIVE=1 -> maintien du terminal ouvert (Ctrl+C pour sortir)"
  tail -f /dev/null
fi
