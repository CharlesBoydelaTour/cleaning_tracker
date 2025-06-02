#!/bin/bash
# Script de lancement pour la production

echo "🌍 Démarrage en mode PRODUCTION"
export ENVIRONMENT=production

# Vérifier que le fichier .env.prod existe
if [ ! -f ".env.prod" ]; then
    echo "❌ Erreur: Le fichier .env.prod est requis pour la production"
    exit 1
fi

# Lancer avec docker-compose production
echo "Démarrage des conteneurs de production..."
docker-compose -f docker-compose.yml --env-file .env.prod up -d

echo "✅ Application démarrée en mode production"
echo "🔍 Vérifiez les logs: docker-compose logs -f"
