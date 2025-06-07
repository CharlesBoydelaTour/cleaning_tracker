#!/bin/bash
# Script de lancement pour le développement local

echo "🚀 Démarrage en mode DÉVELOPPEMENT LOCAL"
export ENVIRONMENT=development

# Démarrer Supabase (si pas déjà démarré)
# Cette commande s'assure que les services Supabase sont lancés.
# Si les services sont déjà en cours, elle ne fait généralement rien ou affiche un message.
echo " memastikan layanan Supabase dimulai..." # Ensuring Supabase services are started...
supabase start

# Attendre un court instant pour s'assurer que les services sont stabilisés
# et que `supabase status` peut récupérer les informations correctement.
sleep 2

# Récupérer les informations de Supabase, y compris les clés
echo "Récupération des informations de Supabase..."
SUPABASE_STATUS_OUTPUT=$(supabase status)

if [ -z "$SUPABASE_STATUS_OUTPUT" ]; then
  echo "❌ Erreur: Impossible de récupérer la sortie de 'supabase status'."
  echo "Veuillez vérifier que Supabase CLI est correctement installé et configuré."
  exit 1
fi

# Extraire les clés et l'URL de l'API
# awk '{print $NF}' récupère le dernier champ de la ligne, ce qui correspond à la clé/URL.
SERVICE_KEY=$(echo "$SUPABASE_STATUS_OUTPUT" | grep 'service_role key:' | awk '{print $NF}')
ANON_KEY=$(echo "$SUPABASE_STATUS_OUTPUT" | grep 'anon key:' | awk '{print $NF}')
API_URL=$(echo "$SUPABASE_STATUS_OUTPUT" | grep 'API URL:' | awk '{print $NF}')

# Vérifier et exporter SERVICE_ROLE_KEY
if [ -z "$SERVICE_KEY" ]; then
  echo "❌ Erreur: Impossible de récupérer la SERVICE_ROLE_KEY de Supabase."
  echo "Veuillez vérifier la sortie de 'supabase status' manuellement:"
  echo "$SUPABASE_STATUS_OUTPUT"
  exit 1
else
  echo "🔑 SERVICE_ROLE_KEY récupérée et exportée."
  export SERVICE_ROLE_KEY="$SERVICE_KEY"
fi

# Vérifier et exporter SUPABASE_ANON_KEY (optionnel, mais bonne pratique)
if [ -z "$ANON_KEY" ]; then
  echo "⚠️ Attention: Impossible de récupérer la SUPABASE_ANON_KEY."
else
  echo "🔑 SUPABASE_ANON_KEY récupérée et exportée."
  export SUPABASE_ANON_KEY="$ANON_KEY"
fi

# Vérifier et exporter SUPABASE_URL (optionnel, mais bonne pratique)
if [ -z "$API_URL" ]; then
  echo "⚠️ Attention: Impossible de récupérer l'API URL de Supabase."
else
  echo "🔗 SUPABASE_URL récupérée et exportée: $API_URL"
  export SUPABASE_URL="$API_URL"
fi

# Lancer l'API avec hot-reload
echo "Démarrage de l'API FastAPI avec hot-reload..."
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000