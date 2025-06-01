"""
Endpoints pour gérer les préférences de notifications
"""
from fastapi import APIRouter, Depends, status
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.core.exceptions import UnauthorizedAccess, UserNotFound, DatabaseError
from app.core.logging import get_logger, with_context
from app.routers.households import get_db_pool
import asyncpg

router = APIRouter(prefix="/users", tags=["user-preferences"])
logger = get_logger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class NotificationPreferences(BaseModel):
    """Schéma pour les préférences de notifications"""
    push_enabled: bool = Field(True, description="Activer les notifications push")
    email_enabled: bool = Field(True, description="Activer les notifications email")
    preferred_channel: str = Field("push", pattern="^(push|email)$", description="Canal préféré")
    
    # Moments de rappel
    reminder_day_before: bool = Field(True, description="Rappel la veille")
    reminder_same_day: bool = Field(True, description="Rappel le jour même")
    reminder_2h_before: bool = Field(True, description="Rappel 2h avant")
    
    # Options email
    email_daily_summary: bool = Field(False, description="Recevoir un résumé quotidien")
    email_weekly_report: bool = Field(False, description="Recevoir un rapport hebdomadaire")
    
    # Heures de notification
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23, description="Début des heures silencieuses")
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23, description="Fin des heures silencieuses")
    
    # Token push
    expo_push_token: Optional[str] = Field(None, description="Token Expo pour les notifications push")

    class Config:
        schema_extra = {
            "example": {
                "push_enabled": True,
                "email_enabled": True,
                "preferred_channel": "push",
                "reminder_day_before": True,
                "reminder_same_day": True,
                "reminder_2h_before": True,
                "email_daily_summary": False,
                "email_weekly_report": False,
                "quiet_hours_start": 22,
                "quiet_hours_end": 8,
                "expo_push_token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
            }
        }


class NotificationPreferencesUpdate(BaseModel):
    """Schéma pour la mise à jour partielle des préférences"""
    push_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    preferred_channel: Optional[str] = Field(None, pattern="^(push|email)$")
    reminder_day_before: Optional[bool] = None
    reminder_same_day: Optional[bool] = None
    reminder_2h_before: Optional[bool] = None
    email_daily_summary: Optional[bool] = None
    email_weekly_report: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)
    expo_push_token: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/{user_id}/notification-preferences", response_model=NotificationPreferences)
async def get_user_notification_preferences(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Récupérer les préférences de notifications d'un utilisateur
    
    L'utilisateur ne peut récupérer que ses propres préférences.
    """
    try:
        # Vérifier que l'utilisateur accède à ses propres préférences
        if str(user_id) != current_user["id"]:
            raise UnauthorizedAccess(
                resource="notification_preferences",
                action="read"
            )
        
        async with db_pool.acquire() as conn:
            # Récupérer les préférences
            prefs = await conn.fetchrow(
                """
                SELECT 
                    push_enabled,
                    email_enabled,
                    preferred_channel,
                    reminder_day_before,
                    reminder_same_day,
                    reminder_2h_before,
                    email_daily_summary,
                    email_weekly_report,
                    quiet_hours_start,
                    quiet_hours_end,
                    expo_push_token
                FROM user_notification_preferences
                WHERE user_id = $1
                """,
                user_id
            )
            
            if prefs:
                return NotificationPreferences(**dict(prefs))
            else:
                # Retourner les préférences par défaut si non trouvées
                logger.info(
                    "Préférences non trouvées, retour des valeurs par défaut",
                    extra=with_context(user_id=str(user_id))
                )
                return NotificationPreferences()
    
    except UnauthorizedAccess:
        raise
    except Exception as e:
        logger.error(
            "Erreur lors de la récupération des préférences",
            extra=with_context(user_id=str(user_id), error=str(e)),
            exc_info=True
        )
        raise DatabaseError(
            operation="récupération des préférences",
            details=str(e)
        )


@router.post("/{user_id}/notification-preferences", response_model=NotificationPreferences)
async def create_user_notification_preferences(
    user_id: UUID,
    preferences: NotificationPreferences,
    current_user: dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Créer les préférences de notifications pour un utilisateur
    
    L'utilisateur ne peut créer que ses propres préférences.
    """
    try:
        # Vérifier que l'utilisateur crée ses propres préférences
        if str(user_id) != current_user["id"]:
            raise UnauthorizedAccess(
                resource="notification_preferences",
                action="create"
            )
        
        async with db_pool.acquire() as conn:
            # Vérifier que l'utilisateur existe
            user_exists = await conn.fetchval(
                "SELECT 1 FROM auth.users WHERE id = $1",
                user_id
            )
            
            if not user_exists:
                raise UserNotFound(user_id=str(user_id))
            
            # Insérer les préférences
            await conn.execute(
                """
                INSERT INTO user_notification_preferences (
                    user_id,
                    push_enabled,
                    email_enabled,
                    preferred_channel,
                    reminder_day_before,
                    reminder_same_day,
                    reminder_2h_before,
                    email_daily_summary,
                    email_weekly_report,
                    quiet_hours_start,
                    quiet_hours_end,
                    expo_push_token,
                    created_at,
                    updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET
                    push_enabled = EXCLUDED.push_enabled,
                    email_enabled = EXCLUDED.email_enabled,
                    preferred_channel = EXCLUDED.preferred_channel,
                    reminder_day_before = EXCLUDED.reminder_day_before,
                    reminder_same_day = EXCLUDED.reminder_same_day,
                    reminder_2h_before = EXCLUDED.reminder_2h_before,
                    email_daily_summary = EXCLUDED.email_daily_summary,
                    email_weekly_report = EXCLUDED.email_weekly_report,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    expo_push_token = EXCLUDED.expo_push_token,
                    updated_at = NOW()
                """,
                user_id,
                preferences.push_enabled,
                preferences.email_enabled,
                preferences.preferred_channel,
                preferences.reminder_day_before,
                preferences.reminder_same_day,
                preferences.reminder_2h_before,
                preferences.email_daily_summary,
                preferences.email_weekly_report,
                preferences.quiet_hours_start,
                preferences.quiet_hours_end,
                preferences.expo_push_token
            )
            
            logger.info(
                "Préférences de notifications créées/mises à jour",
                extra=with_context(user_id=str(user_id))
            )
            
            return preferences
    
    except (UnauthorizedAccess, UserNotFound):
        raise
    except Exception as e:
        logger.error(
            "Erreur lors de la création des préférences",
            extra=with_context(user_id=str(user_id), error=str(e)),
            exc_info=True
        )
        raise DatabaseError(
            operation="création des préférences",
            details=str(e)
        )


@router.patch("/{user_id}/notification-preferences", response_model=NotificationPreferences)
async def update_user_notification_preferences(
    user_id: UUID,
    preferences_update: NotificationPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Mettre à jour partiellement les préférences de notifications
    
    Seuls les champs fournis seront mis à jour.
    """
    try:
        # Vérifier que l'utilisateur met à jour ses propres préférences
        if str(user_id) != current_user["id"]:
            raise UnauthorizedAccess(
                resource="notification_preferences",
                action="update"
            )
        
        async with db_pool.acquire() as conn:
            # Récupérer les préférences actuelles
            current_prefs = await conn.fetchrow(
                """
                SELECT * FROM user_notification_preferences
                WHERE user_id = $1
                """,
                user_id
            )
            
            if not current_prefs:
                # Créer avec les valeurs par défaut si n'existe pas
                current_prefs = NotificationPreferences()
            else:
                current_prefs = NotificationPreferences(**dict(current_prefs))
            
            # Appliquer les mises à jour
            update_data = preferences_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(current_prefs, field, value)
            
            # Sauvegarder
            await conn.execute(
                """
                INSERT INTO user_notification_preferences (
                    user_id,
                    push_enabled,
                    email_enabled,
                    preferred_channel,
                    reminder_day_before,
                    reminder_same_day,
                    reminder_2h_before,
                    email_daily_summary,
                    email_weekly_report,
                    quiet_hours_start,
                    quiet_hours_end,
                    expo_push_token,
                    created_at,
                    updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET
                    push_enabled = EXCLUDED.push_enabled,
                    email_enabled = EXCLUDED.email_enabled,
                    preferred_channel = EXCLUDED.preferred_channel,
                    reminder_day_before = EXCLUDED.reminder_day_before,
                    reminder_same_day = EXCLUDED.reminder_same_day,
                    reminder_2h_before = EXCLUDED.reminder_2h_before,
                    email_daily_summary = EXCLUDED.email_daily_summary,
                    email_weekly_report = EXCLUDED.email_weekly_report,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    expo_push_token = EXCLUDED.expo_push_token,
                    updated_at = NOW()
                """,
                user_id,
                current_prefs.push_enabled,
                current_prefs.email_enabled,
                current_prefs.preferred_channel,
                current_prefs.reminder_day_before,
                current_prefs.reminder_same_day,
                current_prefs.reminder_2h_before,
                current_prefs.email_daily_summary,
                current_prefs.email_weekly_report,
                current_prefs.quiet_hours_start,
                current_prefs.quiet_hours_end,
                current_prefs.expo_push_token
            )
            
            logger.info(
                "Préférences de notifications mises à jour",
                extra=with_context(
                    user_id=str(user_id),
                    updated_fields=list(update_data.keys())
                )
            )
            
            return current_prefs
    
    except (UnauthorizedAccess, UserNotFound):
        raise
    except Exception as e:
        logger.error(
            "Erreur lors de la mise à jour des préférences",
            extra=with_context(user_id=str(user_id), error=str(e)),
            exc_info=True
        )
        raise DatabaseError(
            operation="mise à jour des préférences",
            details=str(e)
        )


@router.delete("/{user_id}/notification-preferences", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_notification_preferences(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Supprimer les préférences de notifications (retour aux valeurs par défaut)
    """
    try:
        # Vérifier que l'utilisateur supprime ses propres préférences
        if str(user_id) != current_user["id"]:
            raise UnauthorizedAccess(
                resource="notification_preferences",
                action="delete"
            )
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM user_notification_preferences
                WHERE user_id = $1
                """,
                user_id
            )
            
            logger.info(
                "Préférences de notifications supprimées",
                extra=with_context(user_id=str(user_id))
            )
    
    except UnauthorizedAccess:
        raise
    except Exception as e:
        logger.error(
            "Erreur lors de la suppression des préférences",
            extra=with_context(user_id=str(user_id), error=str(e)),
            exc_info=True
        )
        raise DatabaseError(
            operation="suppression des préférences",
            details=str(e)
        )