# Cleaning Tracker

**Une application collaborative de gestion des tâches ménagères avec rappels automatiques**

## 📋 Vue d'ensemble

Cleaning Tracker est une application multi-plateforme (iOS, Android, Web) qui permet aux membres d'un foyer de planifier, suivre et accomplir leurs tâches ménagères de manière collaborative. L'application génère automatiquement un calendrier de tâches récurrentes et envoie des rappels personnalisés.

### 🎯 Problème résolu

- **Oublis fréquents** : Les tâches ménagères sont souvent oubliées ou reportées
- **Répartition inégale** : Difficile de suivre qui fait quoi dans le foyer
- **Manque de visibilité** : Pas de vue d'ensemble sur les tâches à venir
- **Communication** : Besoin de rappeler constamment aux autres leurs tâches

### 💡 Solution

Une application qui :
- Génère automatiquement un calendrier de tâches basé sur des règles de récurrence
- Envoie des rappels push et email personnalisés
- Permet de suivre qui fait quoi et quand
- Offre des statistiques sur la répartition des tâches

## 🏗️ Architecture technique

```mermaid
graph TB
    subgraph "Frontend"
        Mobile[React Native/Expo]
        Web[Web PWA]
    end
    
    subgraph "Backend"
        API[FastAPI Python]
        Worker[Celery Workers]
        Scheduler[Celery Beat]
    end
    
    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Storage[Supabase Storage]
    end
    
    subgraph "Services externes"
        Push[Expo Push]
        Email[SMTP]
    end
    
    Mobile --> API
    Web --> API
    API --> DB
    API --> Redis
    Worker --> DB
    Worker --> Push
    Worker --> Email
    Scheduler --> Worker
```

### Stack technique

| Composant | Technologie | Justification |
|-----------|------------|---------------|
| **Frontend mobile** | React Native 0.78 + Expo SDK 53 | Cross-platform, OTA updates, écosystème riche |
| **Backend API** | FastAPI (Python 3.12) | Performance async, validation Pydantic, docs auto |
| **Base de données** | PostgreSQL 16 + RLS | Sécurité multi-tenant, robustesse |
| **Jobs asynchrones** | Celery 6 + Redis | Scalabilité, fiabilité des tâches de fond |
| **BaaS** | Supabase | Auth intégrée, storage, realtime (futur) |
| **Notifications** | Expo Push + SMTP | Unification iOS/Android, emails transactionnels |

## 🚀 Fonctionnalités principales

### 1. Gestion des ménages (Households)
- **Création de foyer** : Chaque utilisateur peut créer un ou plusieurs foyers
- **Invitation de membres** : Ajout par email avec différents rôles (admin, membre, invité)
- **Multi-foyers** : Un utilisateur peut appartenir à plusieurs foyers

### 2. Définition des tâches
- **Catalogue prédéfini** : Bibliothèque de tâches courantes (nettoyer cuisine, passer aspirateur...)
- **Tâches personnalisées** : Création de tâches spécifiques au foyer
- **Règles de récurrence** : Support complet du format RRULE
  - Quotidien, hebdomadaire, mensuel, annuel
  - Jours spécifiques (ex: tous les lundis et vendredis)
  - Intervalles (ex: toutes les 2 semaines)
  - Limites (ex: 10 fois ou jusqu'au 31/12/2024)

### 3. Calendrier intelligent
- **Génération automatique** : Création des occurrences selon les règles
- **Vue jour/semaine/mois** : Navigation intuitive
- **Assignation** : Attribution des tâches aux membres
- **États des tâches** :
  - `pending` : À faire
  - `snoozed` : Reportée
  - `done` : Complétée
  - `skipped` : Ignorée
  - `overdue` : En retard

### 4. Système de rappels
- **Multi-canal** : Push notifications et emails
- **Timing personnalisable** :
  - Veille de l'échéance
  - Jour même (matin)
  - 2h avant l'échéance
- **Heures silencieuses** : Pas de notifications la nuit
- **Préférences par utilisateur** : Chacun configure ses rappels

### 5. Suivi et statistiques
- **Historique** : Qui a fait quoi et quand
- **Durée réelle** : Temps passé vs estimé
- **Taux de complétion** : Par personne, par pièce, global
- **Photos de preuve** : Option pour documenter le travail effectué

## 📊 Modèle de données

### Tables principales

#### `households` - Les foyers
```sql
- id: UUID (PK)
- name: string
- created_at: timestamp
```

#### `users` - Les utilisateurs (géré par Supabase Auth)
```sql
- id: UUID (PK) 
- email: string (unique)
- full_name: string
- created_at: timestamp
```

#### `household_members` - Appartenance aux foyers
```sql
- id: UUID (PK)
- household_id: UUID (FK → households)
- user_id: UUID (FK → users)
- role: enum('admin', 'member', 'guest')
- joined_at: timestamp
```

#### `rooms` - Les pièces de la maison
```sql
- id: UUID (PK)
- household_id: UUID (FK → households)
- name: string
- icon: string (emoji)
- created_at: timestamp
```

#### `task_definitions` - Templates de tâches
```sql
- id: UUID (PK)
- household_id: UUID (FK → households, NULL pour catalogue)
- is_catalog: boolean
- room_id: UUID (FK → rooms)
- title: string
- description: text
- recurrence_rule: string (RRULE format)
- estimated_minutes: integer
- created_by: UUID (FK → users)
- created_at: timestamp
```

#### `task_occurrences` - Instances de tâches
```sql
- id: UUID (PK)
- task_id: UUID (FK → task_definitions)
- scheduled_date: date
- due_at: timestamp
- status: enum('pending','snoozed','done','skipped','overdue')
- assigned_to: UUID (FK → users)
- snoozed_until: timestamp
- created_at: timestamp
```

#### `task_completions` - Historique des complétions
```sql
- occurrence_id: UUID (PK, FK → task_occurrences)
- completed_by: UUID (FK → users)
- completed_at: timestamp
- duration_minutes: integer
- comment: text
- photo_url: text
- created_at: timestamp
```

## 🔄 Flux de données typique

1. **Création d'une tâche récurrente**
   ```
   User → API → task_definitions (RRULE: "FREQ=WEEKLY;BYDAY=MO,FR")
   ```

2. **Génération des occurrences** (job automatique quotidien)
   ```
   Celery Beat → generate_occurrences → task_occurrences (30 jours à l'avance)
   ```

3. **Planification des rappels** (lors de la génération)
   ```
   Worker → schedule_notifications → notifications (J-1, Jour J, H-2)
   ```

4. **Envoi des rappels** (job toutes les 5 min)
   ```
   Worker → check notifications due → Expo Push / SMTP
   ```

5. **Complétion d'une tâche**
   ```
   User → API → task_occurrences (status=done) + task_completions
   ```

## 🛠️ Installation et développement

### Prérequis
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (ou compte Supabase)
- Redis (pour Celery)
- uv (gestionnaire de packages Python)
- pnpm (gestionnaire de packages Node)

### Installation rapide

```bash
# 1. Cloner le repo
git clone https://github.com/your-org/cleaning-tracker.git
cd cleaning-tracker

# 2. Frontend (React Native)
pnpm install
cd apps/mobile
pnpm expo start

# 3. Backend (FastAPI)
cd ../../api
uv sync
make dev  # Lance l'API en mode dev

# 4. Workers (optionnel pour les rappels)
make dev-worker  # Dans un autre terminal
```

### Configuration

Créer les fichiers `.env` nécessaires :

```bash
# api/.env.dev
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your_anon_key
SERVICE_ROLE_KEY=your_service_key
SECRET_KEY=your_secret_key_for_jwt
REDIS_URL=redis://localhost:6379/0
```

## 📱 Captures d'écran

[À ajouter : screenshots de l'app mobile montrant le calendrier, les tâches, les stats]

## 🧪 Tests

```bash
# Backend
cd api
make test          # Tous les tests
make test-coverage # Avec couverture

# Frontend  
cd apps/mobile
pnpm test
```

## 📈 Roadmap

### MVP (Sprint 1) ✅
- [x] Auth email/password
- [x] Gestion des foyers
- [x] CRUD tâches avec récurrence
- [x] Calendrier de base
- [x] Rappels push/email

### v1.1 (Sprint 2) 🚧
- [ ] Dashboard statistiques
- [ ] Assignation automatique (round-robin)
- [ ] Templates de planning (ex: "Grand ménage printemps")
- [ ] Export CSV des historiques

### v1.2 (Sprint 3) 📋
- [ ] Mode hors-ligne avec sync
- [ ] Notifications in-app temps réel
- [ ] Gamification (badges, streaks)
- [ ] Intégration calendrier natif (iOS/Android)

### Futur
- [ ] IA pour suggestions de planning optimal
- [ ] Intégrations domotique (démarrer aspirateur robot)
- [ ] Mode colocation avec espaces privés/partagés
- [ ] Application Apple Watch / WearOS