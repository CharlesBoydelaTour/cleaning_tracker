# Cleaning Tracker API

API REST pour l'application Cleaning Tracker, construite avec FastAPI et PostgreSQL.

## 📋 Table des matières

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Structure du projet](#structure-du-projet)
5. [Authentification](#authentification)
6. [Endpoints API](#endpoints-api)
7. [Modèles de données](#modèles-de-données)
8. [Système de récurrence](#système-de-récurrence)
9. [Jobs asynchrones](#jobs-asynchrones)
10. [Gestion des erreurs](#gestion-des-erreurs)
11. [Tests](#tests)
12. [Déploiement](#déploiement)

## 🏗️ Architecture

L'API suit une architecture en couches :

```
┌─────────────────┐
│   Routes/API    │  ← FastAPI endpoints
├─────────────────┤
│    Services     │  ← Logique métier
├─────────────────┤
│    Database     │  ← Accès données (asyncpg)
├─────────────────┤
│   PostgreSQL    │  ← Stockage + RLS
└─────────────────┘
```

### Composants clés

- **FastAPI** : Framework web async haute performance
- **Pydantic** : Validation et sérialisation des données
- **Redis** : Broker pour Celery et cache

## 🚀 Installation

### Prérequis

- Python 3.12+
- PostgreSQL 16+ (ou Supabase)
- Redis
- uv (gestionnaire de packages Python)

### Installation locale

```bash
# 1. Cloner et naviguer
cd cleaning-tracker/api

# 2. Installer les dépendances avec uv
uv sync

# 3. Configurer l'environnement
cp .env.example .env.dev
- Invitations (foyers)
  - POST `/households/{household_id}/members/invite2` { email, role }
    - Crée une invitation avec token; envoie un email.
    - Si le compte existe: email avec lien de connexion (magic link) vers `/accept-invite`.
    - Si le compte n'existe pas: email d'invitation Supabase pour créer le compte, redirigé vers `/accept-invite`.
  - POST `/households/{household_id}/invites/{token}/accept`
    - Auth requis. Valide le token et ajoute l'utilisateur au foyer.

# Éditer .env.dev avec vos valeurs

# 4. Lancer les migrations Supabase
supabase db reset

# 5. Démarrer l'API
make dev
# ou directement : uv run uvicorn app.main:app --reload
```

### Installation Docker

```bash
# Développement avec hot-reload
make staging

# Production
make prod
```

## ⚙️ Configuration

### Variables d'environnement

L'API utilise différents fichiers `.env` selon l'environnement :

- `.env.dev` : Développement local
- `.env.staging` : Test avec Docker
- `.env.prod` : Production

Variables principales :

```bash
# Base de données
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SERVICE_ROLE_KEY=xxx  # Pour les opérations admin

# Sécurité
SECRET_KEY=xxx  # Pour JWT, générer avec: openssl rand -hex 32

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-specific-password

# Application
APP_URL=https://yourdomain.com
ENVIRONMENT=development
LOG_LEVEL=INFO
LOG_FORMAT=json  # ou "text" pour dev
```

### Configuration du logging

Le système de logging est configurable via `app/core/logging/` :

```python
# Niveaux : DEBUG, INFO, WARNING, ERROR, CRITICAL
# Formats : json (production), text avec couleurs (dev)
# Destinations : console, fichier rotatif
```

## 📁 Structure du projet

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration Pydantic
│   │
│   ├── core/               # Fonctionnalités transverses
│   │   ├── database.py     # Pool asyncpg et helpers
│   │   ├── security.py     # JWT, hashing passwords
│   │   ├── exceptions.py   # Exceptions personnalisées
│   │   ├── celery_app.py   # Configuration Celery
│   │   └── logging/        # Système de logging
│   │
│   ├── routers/            # Endpoints API
│   │   ├── auth.py         # /auth/*
│   │   ├── households.py   # /households/*
│   │   ├── members.py      # /households/{id}/members/*
│   │   ├── rooms.py        # /households/{id}/rooms/*
│   │   ├── task_definitions.py  # /catalog, /households/{id}/task-definitions/*
│   │   ├── task_occurrences.py  # /occurrences/*, /households/{id}/occurrences/*
│   │   └── notification_preferences.py  # /users/{id}/notification-preferences/*
│   │
│   ├── schemas/            # Modèles Pydantic
│   │   ├── auth.py
│   │   ├── household.py
│   │   ├── member.py
│   │   ├── room.py
│   │   └── task.py
│   │
│   ├── services/           # Logique métier
│   │   ├── auth_service.py
│   │   ├── recurrence.py   # Moteur RRULE
│   │   └── notification_service.py
│   │
│   ├── worker/             # Jobs Celery
│   │   └── tasks.py
│   │
│   └── test/              # Tests
│       ├── conftest.py    # Fixtures pytest
│       └── test_*.py
│
├── scripts/               # Scripts utilitaires
├── supabase/             # Migrations SQL
└── docker/               # Dockerfiles
```

## 🔐 Authentification

### Flux d'authentification

1. **Inscription** : `/auth/signup`
   ```json
   POST {
     "email": "user@example.com",
     "password": "SecurePass123!",
     "full_name": "John Doe"
   }
   ```

2. **Connexion** : `/auth/login`
   ```json
   POST {
     "email": "user@example.com",
     "password": "SecurePass123!"
   }
   
   Response: {
     "user": {...},
     "tokens": {
       "access_token": "eyJ...",
       "refresh_token": "eyJ...",
       "token_type": "bearer"
     }
   }
   ```

3. **Utilisation du token** :
   ```
   Authorization: Bearer eyJ...
   ```

### Sécurité

- Mots de passe hashés avec bcrypt
- Tokens JWT avec expiration configurable
- Refresh tokens pour renouvellement
- Protection CORS configurée

## 📡 Endpoints API

### Documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Endpoints principaux

#### Auth - `/auth/*`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/auth/signup` | Créer un compte |
| POST | `/auth/login` | Se connecter |
| POST | `/auth/refresh` | Renouveler le token |
| POST | `/auth/logout` | Se déconnecter |
| GET | `/auth/me` | Profil utilisateur |
| DELETE | `/auth/me` | Supprimer compte |

#### Households - `/households/*`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/households/` | Liste des foyers |
| POST | `/households/` | Créer un foyer |
| GET | `/households/{id}` | Détails d'un foyer |

#### Members - `/households/{household_id}/members/*`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/members/` | Liste des membres |
| POST | `/members/` | Ajouter un membre |
| PUT | `/members/{id}` | Modifier le rôle |
| DELETE | `/members/{id}` | Retirer un membre |

#### Rooms - `/households/{household_id}/rooms/*`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/rooms/` | Liste des pièces |
| POST | `/rooms/` | Créer une pièce |
| GET | `/rooms/{id}` | Détails d'une pièce |

#### Task Definitions

**Catalogue global** :
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/catalog` | Tâches prédéfinies |

**Tâches du foyer** :
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/households/{id}/task-definitions/` | Liste des tâches |
| POST | `/households/{id}/task-definitions/` | Créer une tâche |
| PUT | `/households/{id}/task-definitions/{task_id}` | Modifier |
| DELETE | `/households/{id}/task-definitions/{task_id}` | Supprimer |
| POST | `/households/{id}/task-definitions/{catalog_id}/copy` | Copier du catalogue |

#### Task Occurrences

**Actions sur les occurrences** :
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/occurrences/{id}` | Détails occurrence |
| PUT | `/occurrences/{id}/complete` | Marquer complétée |
| PUT | `/occurrences/{id}/snooze` | Reporter |
| PUT | `/occurrences/{id}/skip` | Ignorer |
| PUT | `/occurrences/{id}/assign` | Assigner |

**Gestion du foyer** :
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/households/{id}/occurrences/` | Calendrier |
| POST | `/households/{id}/occurrences/generate` | Générer |
| GET | `/households/{id}/occurrences/stats` | Statistiques |

### Exemples d'utilisation

#### Créer une tâche récurrente

```bash
curl -X POST http://localhost:8000/households/{household_id}/task-definitions/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Nettoyer la cuisine",
    "description": "Plan de travail + évier + sol",
    "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO,FR",
    "estimated_minutes": 30,
    "room_id": "{room_id}"
  }'
```

#### Compléter une tâche

```bash
curl -X PUT http://localhost:8000/occurrences/{occurrence_id}/complete \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_minutes": 25,
    "comment": "Utilisé le nouveau produit nettoyant",
    "photo_url": "https://..."
  }'
```

## 🗃️ Modèles de données

### Schemas Pydantic principaux

#### TaskDefinitionCreate
```python
{
  "title": str,                    # Requis
  "description": str | None,
  "recurrence_rule": str,          # Format RRULE
  "estimated_minutes": int | None,
  "room_id": UUID | None,
  "household_id": UUID | None,     # None = catalogue
  "is_catalog": bool = False
}
```

#### TaskOccurrence
```python
{
  "id": UUID,
  "task_id": UUID,
  "scheduled_date": date,
  "due_at": datetime,
  "status": "pending" | "snoozed" | "done" | "skipped" | "overdue",
  "assigned_to": UUID | None,
  "snoozed_until": datetime | None,
  "created_at": datetime
}
```

### Validation des données

Pydantic assure la validation automatique :

- Emails valides
- UUIDs corrects
- Enums respectées
- Dates futures pour les reports
- Cohérence des champs liés

## 🔄 Système de récurrence

### Format RRULE

L'API utilise le standard RFC 5545 (iCalendar) pour les récurrences.

#### Exemples courants

```python
# Quotidien
"FREQ=DAILY"

# Tous les 2 jours
"FREQ=DAILY;INTERVAL=2"

# Jours de semaine uniquement
"FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR"

# Hebdomadaire le lundi
"FREQ=WEEKLY;BYDAY=MO"

# Toutes les 2 semaines, lundi et vendredi
"FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,FR"

# Mensuel le 15
"FREQ=MONTHLY;BYMONTHDAY=15"

# Dernier jour du mois
"FREQ=MONTHLY;BYMONTHDAY=-1"

# Trimestriel (tous les 3 mois)
"FREQ=MONTHLY;INTERVAL=3"

# Annuel le 1er janvier
"FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"

# Avec limite de 10 occurrences
"FREQ=DAILY;COUNT=10"

# Jusqu'au 31/12/2024
"FREQ=WEEKLY;UNTIL=20241231"
```

### Service RecurrenceService

Le service `app.services.recurrence` offre :

- **Validation** : `validate_rrule(rule)` → RecurrenceInfo
- **Génération** : `calculate_next_occurrences(rule, start, count)`
- **Description** : `describe_rrule(rule)` → "Tous les lundis et vendredis"
- **Presets** : `get_preset_rule("weekly_monday")` → "FREQ=WEEKLY;BYDAY=MO"

### Limites de sécurité

- Max 366 occurrences par an
- Génération limitée à 90 jours
- Pas de récurrence plus fréquente que quotidienne

## ⚡ Jobs asynchrones

### Architecture Celery

```
┌──────────┐     ┌─────────┐     ┌────────┐
│   Beat   │────▶│  Redis  │◀────│ Worker │
└──────────┘     └─────────┘     └────────┘
     │                                 │
     └─── Planifie ──┐    ┌── Execute ─┘
                     ▼    ▼
                  ┌─────────┐
                  │   DB    │
                  └─────────┘
```

### Tâches planifiées

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| `send_daily_reminders` | 8h00 quotidien | Résumé du jour |
| `process_notification_queue` | Toutes les 5 min | Envoi des rappels |
| `check_overdue_tasks` | Toutes les heures | Marquer les retards |
| `generate_occurrences` | 2h00 quotidien | Créer occurrences J+30 |

### Lancer les workers

```bash
# Worker
make dev-worker
# ou : celery -A app.core.celery_app worker --loglevel=info

# Beat (planificateur)
celery -A app.core.celery_app beat --loglevel=info

# Monitoring
celery -A app.core.celery_app flower
```

## 🚨 Gestion des erreurs

### Exceptions personnalisées

L'API utilise des exceptions structurées (`app.core.exceptions`) :

```python
# Business
HouseholdNotFound(household_id)      # 404
TaskNotFound(task_id)                 # 404
UnauthorizedAccess(resource, action)  # 403
BusinessRuleViolation(rule, details)  # 409

# Validation
InvalidInput(field, value, reason)    # 400
MissingRequiredField(field)          # 400

# Technique
DatabaseError(operation, details)     # 500
ExternalServiceError(service, error)  # 503
```

### Format de réponse d'erreur

```json
{
  "error": {
    "code": "HOUSEHOLD_NOT_FOUND",
    "message": "Le ménage avec l'ID xxx n'existe pas",
    "severity": "medium",
    "metadata": {
      "household_id": "xxx"
    }
  }
}
```

### Logging structuré

Tous les événements sont loggés avec contexte :

```python
logger.info(
    "Tâche complétée",
    extra=with_context(
        occurrence_id=str(occurrence_id),
        user_id=user_id,
        duration=25
    )
)
```

## 🧪 Tests

### Structure des tests

```
test/
├── conftest.py         # Fixtures partagées
├── test_auth_*.py      # Tests auth
├── test_households.py  # Tests foyers
├── test_tasks_*.py     # Tests tâches
└── test_integration.py # Tests E2E
```

### Lancer les tests

```bash
# Tous les tests
make test

# Tests rapides seulement
make test-fast

# Avec couverture
make test-coverage

# Un fichier spécifique
uv run pytest app/test/test_auth_unit.py -v
```

### Fixtures principales

- `db_pool` : Pool de connexions test
- `async_client` : Client HTTP de test
- `auth_headers` : Headers avec token valide
- `mock_user` : Utilisateur de test
- `test_household_with_user` : Foyer avec admin

### Exemple de test

```python
async def test_create_task(
    async_client: AsyncClient,
    test_household_with_user,
    auth_headers: dict
):
    household = test_household_with_user["household"]
    
    response = await async_client.post(
        f"/households/{household['id']}/task-definitions/",
        json={
            "title": "Test Task",
            "recurrence_rule": "FREQ=DAILY"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["title"] == "Test Task"
```

## 🚢 Déploiement

### Docker

```dockerfile
# Build multi-stage optimisé
FROM python:3.13-slim AS builder
# ... installation des dépendances avec uv

FROM python:3.13-slim
# ... copie du venv et run
```

### Docker Compose

Trois configurations disponibles :

1. **Développement** : `docker-compose.dev.yml`
   - Hot reload
   - Redis Commander
   - Volumes montés

2. **Staging** : `docker-compose.yml --env-file .env.staging`
   - Proche de la prod
   - Logs JSON

3. **Production** : `docker-compose.yml --env-file .env.prod`
   - Multi-workers
   - Healthchecks
   - Restart policies

### Monitoring

- Logs structurés en JSON
- Métriques Prometheus (à venir)
- Healthchecks sur `/health`
- Sentry pour les erreurs (à configurer)

## 📚 Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Pydantic V2 Guide](https://docs.pydantic.dev)
- [RRULE Specification](https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html)
- [PostgreSQL RLS Guide](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing`)
3. Commiter (`git commit -m 'Add amazing feature'`)
4. Pousser (`git push origin feature/amazing`)
5. Ouvrir une Pull Request

### Standards de code

- Formatter : `make format` (ruff)
- Linter : `make lint`
- Type hints obligatoires
- Docstrings pour les fonctions publiques
- Tests pour toute nouvelle feature