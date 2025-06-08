#!/bin/bash
# Script helper pour tester l'authentification
# Génère un token JWT et donne les instructions pour l'utiliser

echo "🔧 Génération du token JWT de test..."

# Aller dans le répertoire API et générer le token
cd "$(dirname "$0")/api"

# Générer le token avec uv
TOKEN=$(uv run python ../generate_simple_token.py | grep -E '^eyJ' | head -1)

if [ -z "$TOKEN" ]; then
    echo "❌ Erreur lors de la génération du token"
    exit 1
fi

echo "✅ Token généré avec succès !"
echo ""
echo "📋 Pour tester l'authentification, suivez ces étapes :"
echo ""
echo "1. Ouvrez votre navigateur sur: http://localhost:8080"
echo "2. Ouvrez les outils de développement (F12)"
echo "3. Dans la console, exécutez cette commande :"
echo ""
echo "localStorage.setItem('access_token', '$TOKEN');"
echo ""
echo "4. Rafraîchissez la page (F5)"
echo ""
echo "🧪 Ou testez directement avec curl :"
echo ""
echo "curl -H 'Authorization: Bearer $TOKEN' http://localhost:8000/households/"
echo ""
echo "Token valide pour 30 minutes à partir de maintenant."
