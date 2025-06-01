-- Table des préférences de notifications utilisateur
CREATE TABLE IF NOT EXISTS public.user_notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Activation des canaux
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    preferred_channel public.notif_channel NOT NULL DEFAULT 'push',
    
    -- Moments de rappel
    reminder_day_before BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_same_day BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_2h_before BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Options email
    email_daily_summary BOOLEAN NOT NULL DEFAULT FALSE,
    email_weekly_report BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Heures silencieuses (NULL = pas de restriction)
    quiet_hours_start INTEGER CHECK (quiet_hours_start >= 0 AND quiet_hours_start <= 23),
    quiet_hours_end INTEGER CHECK (quiet_hours_end >= 0 AND quiet_hours_end <= 23),
    
    -- Token pour les notifications push
    expo_push_token TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_push_enabled 
    ON public.user_notification_preferences(push_enabled) 
    WHERE push_enabled = TRUE;

CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_email_enabled 
    ON public.user_notification_preferences(email_enabled) 
    WHERE email_enabled = TRUE;

-- Trigger pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_notification_preferences_updated_at
    BEFORE UPDATE ON public.user_notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security)
ALTER TABLE public.user_notification_preferences ENABLE ROW LEVEL SECURITY;

-- Policy: Les utilisateurs peuvent lire/modifier leurs propres préférences
CREATE POLICY "Users can manage own notification preferences" 
    ON public.user_notification_preferences 
    FOR ALL 
    USING (auth.uid() = user_id);

-- Ajouter une colonne scheduled_for dans la table notifications pour gérer le timing
ALTER TABLE public.notifications
    ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error TEXT;

-- Index pour optimiser la récupération des notifications à envoyer
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled 
    ON public.notifications(scheduled_for) 
    WHERE sent_at IS NULL AND delivered = FALSE;

-- Vue pour faciliter la récupération des notifications avec toutes les infos
CREATE OR REPLACE VIEW notification_queue AS
SELECT 
    n.id,
    n.occurrence_id,
    n.member_id,
    n.channel,
    n.scheduled_for,
    n.retry_count,
    o.due_at,
    o.status as occurrence_status,
    td.title as task_title,
    td.description as task_description,
    td.estimated_minutes,
    r.name as room_name,
    h.name as household_name,
    u.email as user_email,
    unp.push_enabled,
    unp.email_enabled,
    unp.expo_push_token,
    unp.quiet_hours_start,
    unp.quiet_hours_end
FROM notifications n
JOIN task_occurrences o ON n.occurrence_id = o.id
JOIN task_definitions td ON o.task_id = td.id
LEFT JOIN rooms r ON td.room_id = r.id
LEFT JOIN households h ON td.household_id = h.id
JOIN auth.users u ON n.member_id = u.id
LEFT JOIN user_notification_preferences unp ON n.member_id = unp.user_id
WHERE n.sent_at IS NULL 
  AND n.delivered = FALSE
  AND n.retry_count < 3;

-- Fonction pour planifier les notifications d'une occurrence
CREATE OR REPLACE FUNCTION schedule_occurrence_notifications(
    p_occurrence_id UUID,
    p_user_id UUID
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_due_at TIMESTAMPTZ;
    v_prefs RECORD;
BEGIN
    -- Récupérer l'échéance
    SELECT due_at INTO v_due_at
    FROM task_occurrences
    WHERE id = p_occurrence_id;
    
    IF v_due_at IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Récupérer les préférences
    SELECT * INTO v_prefs
    FROM user_notification_preferences
    WHERE user_id = p_user_id;
    
    -- Si pas de préférences, utiliser les valeurs par défaut
    IF v_prefs IS NULL THEN
        v_prefs := ROW(
            p_user_id,
            TRUE,  -- push_enabled
            TRUE,  -- email_enabled
            'push'::notif_channel,  -- preferred_channel
            TRUE,  -- reminder_day_before
            TRUE,  -- reminder_same_day
            TRUE,  -- reminder_2h_before
            FALSE, -- email_daily_summary
            FALSE, -- email_weekly_report
            NULL,  -- quiet_hours_start
            NULL,  -- quiet_hours_end
            NULL,  -- expo_push_token
            NOW(), -- created_at
            NOW()  -- updated_at
        );
    END IF;
    
    -- Créer les notifications selon les préférences
    IF v_prefs.reminder_day_before THEN
        INSERT INTO notifications (occurrence_id, member_id, channel, scheduled_for, created_at)
        VALUES (p_occurrence_id, p_user_id, v_prefs.preferred_channel, v_due_at - INTERVAL '1 day', NOW());
        v_count := v_count + 1;
    END IF;
    
    IF v_prefs.reminder_same_day THEN
        -- Rappel à 9h le jour même
        INSERT INTO notifications (occurrence_id, member_id, channel, scheduled_for, created_at)
        VALUES (
            p_occurrence_id, 
            p_user_id, 
            v_prefs.preferred_channel, 
            DATE_TRUNC('day', v_due_at) + INTERVAL '9 hours', 
            NOW()
        );
        v_count := v_count + 1;
    END IF;
    
    IF v_prefs.reminder_2h_before AND v_due_at > NOW() + INTERVAL '2 hours' THEN
        INSERT INTO notifications (occurrence_id, member_id, channel, scheduled_for, created_at)
        VALUES (p_occurrence_id, p_user_id, v_prefs.preferred_channel, v_due_at - INTERVAL '2 hours', NOW());
        v_count := v_count + 1;
    END IF;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Commentaires pour documentation
COMMENT ON TABLE public.user_notification_preferences IS 'Préférences de notifications pour chaque utilisateur';
COMMENT ON COLUMN public.user_notification_preferences.quiet_hours_start IS 'Heure de début (0-23) où les notifications sont suspendues';
COMMENT ON COLUMN public.user_notification_preferences.quiet_hours_end IS 'Heure de fin (0-23) où les notifications reprennent';
COMMENT ON COLUMN public.user_notification_preferences.expo_push_token IS 'Token Expo pour les notifications push mobile';