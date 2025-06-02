# 📊 Schéma de base de données - Cleaning Tracker

## Vue d'ensemble

La base de données utilise PostgreSQL 16 avec les fonctionnalités suivantes :
- **Row Level Security (RLS)** pour l'isolation multi-tenant
- **UUID** pour tous les identifiants
- **Types ENUM** pour les valeurs contraintes
- **Triggers** pour les mises à jour automatiques
- **Indexes** optimisés pour les requêtes fréquentes

## 🗂️ Schéma des tables

### `users` - Utilisateurs (géré par Supabase Auth)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    email_confirmed_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE
);

-- Index pour les recherches par email
CREATE INDEX idx_users_email ON users(email);
```

**Notes :**
- Table gérée par Supabase Auth en production
- `email_confirmed_at` NULL = email non vérifié
- `is_superuser` pour admin système (future feature)

### `households` - Foyers/Ménages

```sql
CREATE TABLE households (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour tri par nom
CREATE INDEX idx_households_name ON households(name);
```

**Contraintes métier :**
- Un foyer doit avoir au moins un membre admin
- Suppression cascade vers toutes les données liées

### `household_members` - Appartenance aux foyers

```sql
CREATE TABLE household_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member' 
        CHECK (role IN ('admin', 'member', 'guest')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(household_id, user_id)  -- Un user ne peut être membre qu'une fois
);

-- Index composé pour les requêtes fréquentes
CREATE INDEX idx_household_members_composite 
    ON household_members(household_id, user_id);
CREATE INDEX idx_household_members_user 
    ON household_members(user_id);
```

**Rôles :**
- `admin` : Tous droits sur le foyer
- `member` : Créer/modifier tâches, voir tout
- `guest` : Lecture seule + compléter assignées

### `rooms` - Pièces de la maison

```sql
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    icon VARCHAR(10),  -- Emoji
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(household_id, name)  -- Pas de doublons dans un foyer
);

-- Index pour lister les pièces d'un foyer
CREATE INDEX idx_rooms_household ON rooms(household_id);
```

**Exemples d'icônes :**
- 🛋️ Salon
- 🍳 Cuisine
- 🛏️ Chambre
- 🚿 Salle de bain

### `task_definitions` - Définitions/Templates de tâches

```sql
CREATE TYPE task_status AS ENUM (
    'pending',   -- À faire
    'snoozed',   -- Reportée
    'done',      -- Complétée
    'skipped',   -- Ignorée
    'overdue'    -- En retard
);

CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    household_id UUID REFERENCES households(id) ON DELETE CASCADE,
    is_catalog BOOLEAN NOT NULL DEFAULT FALSE,
    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    recurrence_rule TEXT NOT NULL,  -- Format RRULE
    estimated_minutes INTEGER CHECK (estimated_minutes > 0),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour filtrage
CREATE INDEX idx_task_definitions_household 
    ON task_definitions(household_id) WHERE NOT is_catalog;
CREATE INDEX idx_task_definitions_catalog 
    ON task_definitions(is_catalog) WHERE is_catalog;
CREATE INDEX idx_task_definitions_room 
    ON task_definitions(room_id);
```

**Contraintes :**
- Si `is_catalog = true`, alors `household_id` doit être NULL
- `recurrence_rule` doit être une RRULE valide

### `task_occurrences` - Instances de tâches

```sql
CREATE TABLE task_occurrences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES task_definitions(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    status task_status NOT NULL DEFAULT 'pending',
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    snoozed_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(task_id, scheduled_date)  -- Une occurrence par jour par tâche
);

-- Index pour requêtes calendrier
CREATE INDEX idx_task_occurrences_date 
    ON task_occurrences(scheduled_date);
CREATE INDEX idx_task_occurrences_status 
    ON task_occurrences(status) WHERE status != 'done';
CREATE INDEX idx_task_occurrences_assigned 
    ON task_occurrences(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_task_occurrences_overdue 
    ON task_occurrences(due_at) WHERE status = 'pending';
```

**Logique métier :**
- `status = 'overdue'` si `due_at < NOW()` et `status = 'pending'`
- `snoozed_until` NOT NULL seulement si `status = 'snoozed'`

### `task_completions` - Historique des complétions

```sql
CREATE TABLE task_completions (
    occurrence_id UUID PRIMARY KEY REFERENCES task_occurrences(id) ON DELETE CASCADE,
    completed_by UUID REFERENCES users(id),
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_minutes INTEGER CHECK (duration_minutes > 0),
    comment TEXT,
    photo_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour statistiques
CREATE INDEX idx_task_completions_user 
    ON task_completions(completed_by);
CREATE INDEX idx_task_completions_date 
    ON task_completions(completed_at);
```

**Notes :**
- Une seule complétion par occurrence (PK)
- `photo_url` pointe vers Supabase Storage

### `notifications` - File d'attente des notifications

```sql
CREATE TYPE notif_channel AS ENUM ('push', 'email');

CREATE TABLE notifications (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurrence_id UUID REFERENCES task_occurrences(id) ON DELETE CASCADE,
    member_id UUID REFERENCES users(id),
    channel notif_channel NOT NULL,
    scheduled_for TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    delivered BOOLEAN DEFAULT FALSE,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour le worker
CREATE INDEX idx_notifications_scheduled 
    ON notifications(scheduled_for) 
    WHERE sent_at IS NULL AND delivered = FALSE;
CREATE INDEX idx_notifications_pending 
    ON notifications(created_at) 
    WHERE sent_at IS NULL AND retry_count < 3;
```

### `user_notification_preferences` - Préférences utilisateur

```sql
CREATE TABLE user_notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Activation des canaux
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    preferred_channel notif_channel NOT NULL DEFAULT 'push',
    
    -- Moments de rappel
    reminder_day_before BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_same_day BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_2h_before BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Options email
    email_daily_summary BOOLEAN NOT NULL DEFAULT FALSE,
    email_weekly_report BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Heures silencieuses
    quiet_hours_start INTEGER CHECK (quiet_hours_start BETWEEN 0 AND 23),
    quiet_hours_end INTEGER CHECK (quiet_hours_end BETWEEN 0 AND 23),
    
    -- Token push
    expo_push_token TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger pour updated_at
CREATE TRIGGER update_user_notification_preferences_updated_at
    BEFORE UPDATE ON user_notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

## 🔒 Row Level Security (RLS)

### Politique générale

```sql
-- Activer RLS sur toutes les tables métier
ALTER TABLE households ENABLE ROW LEVEL SECURITY;
ALTER TABLE household_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_occurrences ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_completions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_notification_preferences ENABLE ROW LEVEL SECURITY;
```

### Exemples de policies

#### Households - Membres uniquement

```sql
CREATE POLICY "Members can view their households"
    ON households FOR SELECT
    USING (
        id IN (
            SELECT household_id 
            FROM household_members 
            WHERE user_id = auth.uid()
        )
    );
```

#### Task definitions - Catalogue public + foyer

```sql
CREATE POLICY "Catalog tasks are public, household tasks need membership"
    ON task_definitions FOR SELECT
    USING (
        is_catalog = TRUE
        OR 
        household_id IN (
            SELECT household_id 
            FROM household_members 
            WHERE user_id = auth.uid()
        )
    );
```

#### Préférences - Utilisateur uniquement

```sql
CREATE POLICY "Users manage own preferences"
    ON user_notification_preferences FOR ALL
    USING (user_id = auth.uid());
```

## 📊 Vues utiles

### `notification_queue` - File enrichie

```sql
CREATE VIEW notification_queue AS
SELECT 
    n.*,
    o.due_at,
    o.status as occurrence_status,
    td.title as task_title,
    td.description as task_description,
    r.name as room_name,
    h.name as household_name,
    u.email as user_email,
    unp.push_enabled,
    unp.email_enabled,
    unp.expo_push_token
FROM notifications n
JOIN task_occurrences o ON n.occurrence_id = o.id
JOIN task_definitions td ON o.task_id = td.id
LEFT JOIN rooms r ON td.room_id = r.id
LEFT JOIN households h ON td.household_id = h.id
JOIN users u ON n.member_id = u.id
LEFT JOIN user_notification_preferences unp ON n.member_id = unp.user_id
WHERE n.sent_at IS NULL 
  AND n.delivered = FALSE
  AND n.retry_count < 3;
```

### `household_statistics` - Stats par foyer

```sql
CREATE VIEW household_statistics AS
SELECT 
    h.id as household_id,
    h.name as household_name,
    COUNT(DISTINCT hm.user_id) as member_count,
    COUNT(DISTINCT td.id) as task_count,
    COUNT(DISTINCT r.id) as room_count,
    COUNT(DISTINCT CASE WHEN o.status = 'done' THEN o.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN o.status = 'pending' THEN o.id END) as pending_tasks,
    COUNT(DISTINCT CASE WHEN o.status = 'overdue' THEN o.id END) as overdue_tasks
FROM households h
LEFT JOIN household_members hm ON h.id = hm.household_id
LEFT JOIN task_definitions td ON h.id = td.household_id
LEFT JOIN rooms r ON h.id = r.household_id
LEFT JOIN task_occurrences o ON td.id = o.task_id
GROUP BY h.id, h.name;
```

## 🚀 Optimisations

### Index stratégiques

```sql
-- Requête calendrier (très fréquente)
CREATE INDEX idx_calendar_view ON task_occurrences(household_id, scheduled_date, status)
INCLUDE (task_id, assigned_to, due_at);

-- Dashboard stats
CREATE INDEX idx_stats_completions 
ON task_completions(completed_by, completed_at) 
INCLUDE (duration_minutes);
```

### Partitionnement (futur)

Pour les grandes installations :

```sql
-- Partitionner les occurrences par mois
CREATE TABLE task_occurrences_2024_01 
    PARTITION OF task_occurrences 
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Vacuum et maintenance

```sql
-- Configuration recommandée
ALTER TABLE task_occurrences SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE notifications SET (autovacuum_vacuum_scale_factor = 0.05);

-- Analyser régulièrement
ANALYZE task_occurrences, task_completions, notifications;
```

## 🔧 Fonctions utilitaires

### Générer les occurrences

```sql
CREATE OR REPLACE FUNCTION generate_task_occurrences(
    p_task_id UUID,
    p_start_date DATE,
    p_end_date DATE
) RETURNS SETOF task_occurrences AS $$
DECLARE
    v_rule TEXT;
    v_date DATE;
BEGIN
    -- Récupérer la règle
    SELECT recurrence_rule INTO v_rule
    FROM task_definitions
    WHERE id = p_task_id;
    
    -- Utiliser l'extension pg_rrule (à installer)
    -- ou appeler le service Python
    
    -- Pour l'instant, exemple simple quotidien
    v_date := p_start_date;
    WHILE v_date <= p_end_date LOOP
        INSERT INTO task_occurrences (task_id, scheduled_date, due_at)
        VALUES (p_task_id, v_date, v_date + TIME '23:59:59')
        ON CONFLICT (task_id, scheduled_date) DO NOTHING
        RETURNING * INTO task_occurrences;
        
        v_date := v_date + INTERVAL '1 day';
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

### Statistiques utilisateur

```sql
CREATE OR REPLACE FUNCTION get_user_stats(
    p_user_id UUID,
    p_start_date DATE,
    p_end_date DATE
) RETURNS TABLE (
    total_assigned INT,
    total_completed INT,
    total_duration_minutes INT,
    completion_rate NUMERIC,
    avg_delay_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT o.id)::INT as total_assigned,
        COUNT(DISTINCT c.occurrence_id)::INT as total_completed,
        COALESCE(SUM(c.duration_minutes), 0)::INT as total_duration_minutes,
        CASE 
            WHEN COUNT(o.id) > 0 
            THEN ROUND(COUNT(c.occurrence_id)::NUMERIC / COUNT(o.id) * 100, 2)
            ELSE 0
        END as completion_rate,
        ROUND(AVG(
            EXTRACT(EPOCH FROM (c.completed_at - o.due_at)) / 3600
        )::NUMERIC, 2) as avg_delay_hours
    FROM task_occurrences o
    LEFT JOIN task_completions c ON o.id = c.occurrence_id
    WHERE o.assigned_to = p_user_id
      AND o.scheduled_date BETWEEN p_start_date AND p_end_date;
END;
$$ LANGUAGE plpgsql;
```

## 🔄 Migrations

### Ordre de création

1. Types ENUM
2. Tables indépendantes (users, households)
3. Tables avec FK simples (household_members, rooms)
4. Tables complexes (task_definitions, task_occurrences)
5. Tables de jointure (task_completions, notifications)
6. Vues
7. Index
8. RLS policies

### Rollback safe

Toutes les migrations doivent être réversibles :

```sql
-- UP
CREATE TABLE IF NOT EXISTS ...
CREATE INDEX IF NOT EXISTS ...

-- DOWN  
DROP TABLE IF EXISTS ... CASCADE;
DROP INDEX IF EXISTS ...;
```

## 📈 Métriques de performance

### Requêtes critiques à optimiser

1. **Calendrier mensuel** (~50ms cible)
   ```sql
   SELECT * FROM task_occurrences 
   WHERE household_id = ? 
   AND scheduled_date BETWEEN ? AND ?
   ```

2. **Dashboard stats** (~100ms cible)
   ```sql
   SELECT status, COUNT(*) FROM task_occurrences
   WHERE household_id = ?
   GROUP BY status
   ```

3. **Notifications dues** (~20ms cible)
   ```sql
   SELECT * FROM notification_queue
   WHERE scheduled_for <= NOW()
   LIMIT 100
   ```

### Monitoring

Requêtes à surveiller :

```sql
-- Requêtes lentes
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC;

-- Tables volumineuses
SELECT relname, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Index inutilisés
SELECT indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```