# Guide des fonctionnalités - Cleaning Tracker

## 📅 Système de récurrence des tâches

### Comprendre les règles RRULE

Le système utilise le standard iCalendar (RFC 5545) pour définir les récurrences. C'est le même format utilisé par Google Calendar, Outlook, etc.

#### Structure d'une règle RRULE

```
FREQ=<frequency>;[INTERVAL=n];[BYDAY=day1,day2];[UNTIL=date];[COUNT=n]
```

- **FREQ** : Fréquence de base (DAILY, WEEKLY, MONTHLY, YEARLY)
- **INTERVAL** : Répéter tous les N intervalles
- **BYDAY** : Jours spécifiques (MO,TU,WE,TH,FR,SA,SU)
- **BYMONTHDAY** : Jour du mois (1-31, ou -1 pour dernier)
- **UNTIL** : Date de fin (format YYYYMMDD)
- **COUNT** : Nombre total d'occurrences

#### Exemples pratiques

**Tâches quotidiennes :**
```python
# Tous les jours
"FREQ=DAILY"

# Un jour sur deux
"FREQ=DAILY;INTERVAL=2"

# Jours ouvrables uniquement
"FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR"

# Weekends uniquement
"FREQ=WEEKLY;BYDAY=SA,SU"
```

**Tâches hebdomadaires :**
```python
# Toutes les semaines (jour actuel)
"FREQ=WEEKLY"

# Tous les lundis
"FREQ=WEEKLY;BYDAY=MO"

# Lundi et vendredi
"FREQ=WEEKLY;BYDAY=MO,FR"

# Toutes les 2 semaines le mercredi
"FREQ=WEEKLY;INTERVAL=2;BYDAY=WE"
```

**Tâches mensuelles :**
```python
# Tous les mois (même date)
"FREQ=MONTHLY"

# Le 15 de chaque mois
"FREQ=MONTHLY;BYMONTHDAY=15"

# Dernier jour du mois
"FREQ=MONTHLY;BYMONTHDAY=-1"

# Tous les 3 mois (trimestriel)
"FREQ=MONTHLY;INTERVAL=3"

# Premier lundi du mois
"FREQ=MONTHLY;BYDAY=1MO"
```

### Utilisation dans l'API

#### 1. Créer une tâche récurrente

```bash
POST /households/{household_id}/task-definitions/
{
  "title": "Passer l'aspirateur salon",
  "recurrence_rule": "FREQ=WEEKLY;BYDAY=SA",
  "estimated_minutes": 20,
  "room_id": "{salon_room_id}"
}
```

#### 2. Templates prédéfinis

Le service offre des règles prédéfinies :

```python
from app.services.recurrence import RecurrenceService

# Obtenir une règle prédéfinie
rule = RecurrenceService.get_preset_rule("weekly_monday")
# → "FREQ=WEEKLY;BYDAY=MO"

# Templates disponibles :
- "daily"           → "FREQ=DAILY"
- "weekdays"        → "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR"
- "weekly"          → "FREQ=WEEKLY"
- "biweekly"        → "FREQ=WEEKLY;INTERVAL=2"
- "monthly"         → "FREQ=MONTHLY"
- "weekly_monday"   → "FREQ=WEEKLY;BYDAY=MO"
- "first_of_month"  → "FREQ=MONTHLY;BYMONTHDAY=1"
- "seasonal"        → "FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=1"
```

#### 3. Génération des occurrences

Le système génère automatiquement les occurrences 30 jours à l'avance :

```python
# Job Celery quotidien à 2h00
async def generate_occurrences_job():
    for household in get_all_households():
        for task_def in household.task_definitions:
            occurrences = recurrence_service.generate_occurrences_between(
                task_def.recurrence_rule,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30)
            )
            # Créer les task_occurrences en DB
```

### Gestion des cas spéciaux

#### Jours fériés

```python
# Le service peut exclure les jours fériés
occurrences = recurrence_service.calculate_next_occurrences(
    "FREQ=DAILY",
    exclude_holidays=True,  # Exclut les jours fériés français
    exclude_weekends=True
)
```

#### Limites et contraintes

- Maximum 366 occurrences par an
- Pas de récurrence horaire (minimum quotidien)
- Génération limitée à 90 jours dans le futur

## 🔔 Système de notifications

### Architecture des rappels

```
User Preferences → Notification Scheduler → Queue → Worker → Push/Email
```

### Préférences utilisateur

Chaque utilisateur configure ses rappels :

```json
POST /users/{user_id}/notification-preferences
{
  "push_enabled": true,
  "email_enabled": true,
  "preferred_channel": "push",
  
  "reminder_day_before": true,     // J-1 à 18h
  "reminder_same_day": true,       // Jour J à 9h
  "reminder_2h_before": true,      // 2h avant
  
  "email_daily_summary": false,    // Résumé quotidien
  "email_weekly_report": false,    // Rapport hebdo
  
  "quiet_hours_start": 22,         // Pas de notif après 22h
  "quiet_hours_end": 8,            // Ni avant 8h
  
  "expo_push_token": "ExponentPushToken[xxx]"
}
```

### Types de rappels

#### 1. Rappels de tâches

Automatiquement créés lors de la génération d'occurrences :

```python
# Pour chaque occurrence générée
await notification_service.schedule_task_reminders(
    occurrence_id,
    user_preferences
)

# Crée jusqu'à 3 notifications :
# - Veille 18h
# - Jour même 9h  
# - 2h avant l'échéance
```

#### 2. Résumés quotidiens

Email envoyé chaque matin avec la liste des tâches du jour :

```
Objet: 📋 Vos 3 tâches du jour

Bonjour John,

Voici vos tâches pour aujourd'hui :

✓ Nettoyer la cuisine (30 min) - 10h00
✓ Passer l'aspirateur salon (20 min) - 15h00  
✓ Sortir les poubelles (5 min) - 19h00

Bonne journée !
```

#### 3. Alertes retard

Notification immédiate quand une tâche devient en retard :

```python
# Job horaire qui vérifie
overdue = await check_and_update_overdue_occurrences()
# → status: pending → overdue si due_at < NOW()
```

### Canaux de notification

#### Push (Expo)

```python
await notification_service.send_push_notification(
    expo_token="ExponentPushToken[xxx]",
    title="Rappel de tâche",
    body="Nettoyer la cuisine dans 2h",
    data={"occurrence_id": "xxx", "action": "view"}
)
```

Configuration côté mobile :
- Demander la permission
- Enregistrer le token Expo
- Gérer les deep links

#### Email (SMTP)

Templates HTML responsives avec :
- Logo et branding
- Boutons d'action
- Lien vers l'app
- Désabonnement

### Gestion de la queue

Les notifications sont traitées par batch toutes les 5 minutes :

```python
# Worker Celery
@celery_app.task
def process_notification_queue():
    # Récupère les notifications dues
    notifications = get_pending_notifications(
        scheduled_for__lte=now()
    )
    
    for batch in chunks(notifications, 100):
        send_batch(batch)
```

## 👥 Gestion des membres et permissions

### Rôles disponibles

| Rôle | Permissions |
|------|-------------|
| **admin** | Tout : membres, tâches, paramètres |
| **member** | Créer/modifier ses tâches, voir tout |
| **guest** | Lecture seule, compléter assignées |

### Matrice des permissions

| Action | Admin | Member | Guest |
|--------|-------|--------|-------|
| Voir le calendrier | ✅ | ✅ | ✅ |
| Créer des tâches | ✅ | ✅ | ❌ |
| Modifier toutes les tâches | ✅ | ❌ | ❌ |
| Modifier ses tâches | ✅ | ✅ | ❌ |
| Assigner des tâches | ✅ | ✅ | ❌ |
| Compléter assignées | ✅ | ✅ | ✅ |
| Ajouter des membres | ✅ | ❌ | ❌ |
| Modifier les rôles | ✅ | ❌ | ❌ |
| Supprimer le foyer | ✅ | ❌ | ❌ |

### Invitation de membres

Workflow d'ajout :

1. **Admin ajoute par email**
   ```json
   POST /households/{id}/members
   {
     "user_id": "{user_uuid}",
     "role": "member"
   }
   ```

2. **Notification envoyée** (à implémenter)
   - Email d'invitation
   - Lien de confirmation
   - Expiration 7 jours

3. **Acceptation**
   - Création compte si nécessaire
   - Ajout automatique au foyer

## 📊 Statistiques et tableaux de bord

### Métriques disponibles

L'endpoint `/households/{id}/occurrences/stats` retourne :

```json
{
  "total": 150,
  "by_status": {
    "pending": 10,
    "done": 130,
    "skipped": 5,
    "overdue": 5
  },
  "completion_rate": 86.7,
  "by_room": {
    "Cuisine": {"total": 50, "done": 45},
    "Salon": {"total": 30, "done": 28}
  },
  "by_assignee": {
    "john@example.com": {"total": 80, "done": 70},
    "jane@example.com": {"total": 70, "done": 60}
  }
}
```

### Analyses avancées (v1.1)

Futures métriques prévues :

- **Temps moyen** : Réel vs estimé par tâche
- **Charge de travail** : Répartition équitable
- **Tendances** : Évolution du taux de complétion
- **Prédictions** : Risques de surcharge

## 🔄 Gestion des états

### Cycle de vie d'une occurrence

```
                  ┌─────────────┐
                  │   PENDING   │ ← État initial
                  └─────┬───────┘
                        │
          ┌─────────────┼─────────────┬──────────────┐
          ▼             ▼             ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ SNOOZED │   │  DONE   │   │ SKIPPED │   │ OVERDUE │
    └─────┬───┘   └─────────┘   └─────────┘   └─────────┘
          │
          └──────► PENDING (après délai)
```

### Actions possibles

| État actuel | Actions possibles |
|-------------|------------------|
| **pending** | complete, snooze, skip, assign |
| **snoozed** | complete, skip, re-snooze |
| **overdue** | complete, skip |
| **done** | aucune |
| **skipped** | aucune |

### Report intelligent

Le système suggère des dates de report :

```python
# Reporter au prochain créneau logique
next_date = recurrence_service.suggest_skip_until(
    "FREQ=WEEKLY;BYDAY=MO",
    current_date=date(2024, 1, 8),  # Lundi
    skip_count=1
)
# → date(2024, 1, 15)  # Lundi suivant
```

## 🎯 Cas d'usage avancés

### 1. Planning saisonnier

Grand ménage de printemps :

```python
# Tâche trimestrielle en mars
"FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=15"

# Avec sous-tâches
- Nettoyer les vitres
- Laver les rideaux  
- Dégivrer le congélateur
```

### 2. Rotation des assignations

Round-robin automatique (v1.1) :

```python
# Configuration au niveau tâche
{
  "auto_assign": true,
  "assign_strategy": "round_robin",
  "eligible_members": ["user1", "user2", "user3"]
}
```

### 3. Tâches conditionnelles

Basées sur d'autres complétions :

```python
# Si "Courses" complétée → activer "Ranger courses"
{
  "depends_on": "{task_id}",
  "activation_delay": "PT30M"  # 30 minutes après
}
```

### 4. Templates de foyer

Packages prédéfinis :

- **Studio étudiant** : Minimal, hebdo
- **Famille 4 pers** : Complet, quotidien
- **Colocation** : Zones communes seulement

## 🛠️ Intégrations futures

### Calendriers natifs

Export iCal pour sync avec :
- Google Calendar
- Apple Calendar
- Outlook

### Assistants vocaux

- "Alexa, quelles sont mes tâches aujourd'hui ?"
- "OK Google, marque 'aspirateur' comme fait"

### Domotique

- Démarrer Roomba quand "Aspirateur" assigné
- Notification sur TV quand tâche due
- Lumière rouge si tâches en retard

### Gamification

- Points par tâche (durée × difficulté)
- Badges (streak 7 jours, plus rapide)
- Classement familial mensuel

## 📱 Optimisations mobile

### Mode hors-ligne

Cache local SQLite avec sync :

```typescript
// Stocker les occurrences localement
await db.occurrences.bulkPut(occurrences);

// Sync au retour en ligne
await syncManager.push(localChanges);
await syncManager.pull(lastSyncDate);
```

### Performance

- Pagination des listes (20 items)
- Lazy loading des détails
- Images compressées côté client
- WebP avec fallback JPEG

### Batterie

- Pas de polling, que du push
- Sync en WiFi uniquement (option)
- Mode économie : pas d'animations