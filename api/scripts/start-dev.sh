#!/bin/bash
# Script de lancement pour le développement local

echo "🚀 Démarrage en mode DÉVELOPPEMENT LOCAL"
export ENVIRONMENT=development

# Lancer l'API avec hot-reload
echo "Démarrage de l'API avec hot-reload..."
supabase start
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
