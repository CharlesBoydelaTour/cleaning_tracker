#!/bin/bash
# Script de lancement pour l'environnement staging (Docker local)

echo "🐳 Démarrage en mode STAGING (Docker)"
export ENVIRONMENT=staging

# Construire et lancer avec docker-compose
echo "Construction et démarrage des conteneurs..."
docker-compose -f docker-compose.yml --env-file .env.staging up --build -d

echo "✅ Application démarrée en mode staging"
echo "📊 API: http://localhost:8000"
echo "📝 Logs: docker-compose logs -f"
