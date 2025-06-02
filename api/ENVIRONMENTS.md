# 🌍 Gestion des Environnements - Cleaning Tracker API

Ce guide explique comment utiliser la nouvelle gestion des environnements mise en place pour l'API Cleaning Tracker.

## 📁 Structure des fichiers d'environnement

```
api/
├── .env.dev        # Développement local (Python direct)
├── .env.staging    # Préproduction (Docker + DB locale)
├── .env.prod       # Production (à créer avec vos vraies valeurs)
├── .env.example    # Template pour .env.prod
└── scripts/
    ├── start-dev.sh     # Script de lancement dev
    ├── start-staging.sh # Script de lancement staging
    └── start-prod.sh    # Script de lancement production
```

## 🚀 Démarrage selon l'environnement

### 🛠️ Développement local (recommandé)
```bash
# Option 1: Avec make (recommandé)
make dev

# Option 2: Script direct
./scripts/start-dev.sh

# Option 3: Commande manuelle
export ENVIRONMENT=development
uv run uvicorn app.main:app --reload
```

**Caractéristiques:**
- ✅ Hot reload activé
- ✅ Logs en mode text avec couleurs
- ✅ Base de données Supabase locale (localhost:54321)
- ✅ Redis local (localhost:6379)
- ✅ Niveau de log: DEBUG

### 🐳 Staging (Docker + BD locale)
```bash
# Option 1: Avec make (recommandé)
make staging

# Option 2: Script direct
./scripts/start-staging.sh

# Option 3: Docker-compose direct
docker-compose -f docker-compose.dev.yml --env-file .env.staging up --build
```

**Caractéristiques:**
- ✅ Environnement dockerisé
- ✅ Base de données Supabase locale via host.docker.internal
- ✅ Redis dans un conteneur
- ✅ Logs en JSON
- ✅ Niveau de log: INFO

### 🌍 Production
```bash
# Créer d'abord votre fichier .env.prod avec les vraies valeurs
cp .env.example .env.prod
# Éditer .env.prod avec vos valeurs de production

# Puis lancer
make prod
# ou
./scripts/start-prod.sh
```

**Caractéristiques:**
- 🔒 Variables d'environnement sécurisées
- 📊 Logs en JSON structuré
- ⚠️ Niveau de log: WARNING
- 🚀 Multi-workers (4)

## 📋 Commandes Make disponibles

```bash
make help           # Affiche toutes les commandes disponibles
make install        # Installe les dépendances
make dev           # Lance en mode développement
make staging       # Lance en mode staging (Docker)
make prod          # Lance en mode production
make test          # Lance les tests
make lint          # Vérifie le style du code
make format        # Formate le code
make clean         # Nettoie les fichiers temporaires
make env-check     # Vérifie la configuration d'environnement
```

## 🔧 Configuration des variables d'environnement

### Variables critiques à modifier pour production:

```bash
# Dans .env.prod
DATABASE_URL=postgresql://username:password@your-db-host:5432/production_db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_production_anon_key
SERVICE_ROLE_KEY=your_production_service_role_key
SECRET_KEY=your_production_secret_key_here
REDIS_URL=redis://your-redis-host:6379/0
APP_URL=https://yourdomain.com
```

### Hiérarchie de chargement:

1. **Variables d'environnement système** (priorité maximale)
2. **Fichier .env selon ENVIRONMENT**:
   - `ENVIRONMENT=development` → `.env.dev`
   - `ENVIRONMENT=staging` → `.env.staging`
   - `ENVIRONMENT=production` → `.env.prod`
3. **Valeurs par défaut** dans `app/config.py`


## 🧪 Tests

Les tests utilisent automatiquement l'environnement `development`:

```bash
# Tous les tests
make test

# Tests rapides seulement
make test-fast

# Tests avec coverage
make test-coverage
```

## 🐛 Dépannage

### Vérifier l'environnement actuel:
```bash
make env-check
```

### Voir les logs:
```bash
# Développement local
tail -f logs/app.log

# Docker (staging/prod)
make staging-logs  # ou make prod-logs
```

### Problèmes courants:

1. **Erreur "fichier .env non trouvé"**
   ```bash
   # Vérifiez que le bon fichier existe
   ls -la .env*
   
   # Créez le fichier manquant depuis l'example
   cp .env.example .env.dev
   ```

2. **Connexion base de données échouée**
   ```bash
   # Testez la connexion
   make db-test
   ```

3. **Variables d'environnement non chargées**
   ```bash
   # Vérifiez la variable ENVIRONMENT
   echo $ENVIRONMENT
   
   # Forcez l'environnement
   export ENVIRONMENT=development
   make dev
   ```

## 🔄 Migration depuis l'ancien système

Si vous utilisez encore l'ancien fichier `.env`:

1. **Sauvegardez votre ancien .env:**
   ```bash
   cp .env .env.backup
   ```

2. **Créez les nouveaux fichiers:**
   ```bash
   # Pour le développement
   cp .env .env.dev
   
   # Pour la production (et éditez avec vos vraies valeurs)
   cp .env .env.prod
   ```

3. **Testez la nouvelle configuration:**
   ```bash
   make env-check
   make dev
   ```

## 📚 Ressources supplémentaires

- [Documentation Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/)
- [Docker Compose Environment Files](https://docs.docker.com/compose/environment-variables/)
- [Twelve-Factor App Config](https://12factor.net/config)
