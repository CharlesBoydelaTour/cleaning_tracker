"""
Service de gestion des notifications pour l'application Cleaning Tracker
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.config import settings
from app.core.database import init_db_pool
from app.core.logging import get_logger, with_context
from app.core.exceptions import InvalidInput

logger = get_logger(__name__)


class NotificationService:
    """Service pour envoyer des notifications push et email"""
    
    def __init__(self):
        self.expo_base_url = "https://exp.host/--/api/v2/push/send"
        self.smtp_host = getattr(settings, "smtp_host", "smtp.gmail.com")
        self.smtp_port = getattr(settings, "smtp_port", 587)
        self.smtp_user = getattr(settings, "smtp_user", None)
        self.smtp_password = getattr(settings, "smtp_password", None)
        self.sender_email = getattr(settings, "sender_email", "noreply@cleaningtracker.com")
        self.sender_name = getattr(settings, "sender_name", "Cleaning Tracker")
    
    async def send_push_notification(
        self, 
        expo_token: str, 
        title: str, 
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envoyer une notification push via Expo
        
        Args:
            expo_token: Token Expo du destinataire
            title: Titre de la notification
            body: Corps de la notification
            data: Données supplémentaires
            
        Returns:
            True si envoyé avec succès
        """
        if not expo_token or not expo_token.startswith("ExponentPushToken"):
            logger.warning(
                "Token Expo invalide",
                extra=with_context(expo_token=expo_token)
            )
            return False
        
        payload = {
            "to": expo_token,
            "title": title,
            "body": body,
            "sound": "default",
            "badge": 1,
            "channelId": "task-reminders"
        }
        
        if data:
            payload["data"] = data
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.expo_base_url,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Accept-encoding": "gzip, deflate",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("data", {}).get("status") == "ok":
                        logger.info(
                            "Notification push envoyée",
                            extra=with_context(
                                expo_token=expo_token[:20] + "...",
                                title=title
                            )
                        )
                        return True
                    else:
                        logger.error(
                            "Erreur Expo",
                            extra=with_context(
                                expo_token=expo_token[:20] + "...",
                                error=result.get("data", {}).get("message")
                            )
                        )
                        return False
                else:
                    logger.error(
                        "Erreur HTTP Expo",
                        extra=with_context(
                            status_code=response.status_code,
                            response=response.text
                        )
                    )
                    return False
                    
        except httpx.TimeoutException:
            logger.error(
                "Timeout lors de l'envoi de la notification",
                extra=with_context(expo_token=expo_token[:20] + "...")
            )
            return False
        except Exception as e:
            logger.error(
                "Erreur lors de l'envoi de la notification push",
                extra=with_context(
                    expo_token=expo_token[:20] + "...",
                    error=str(e)
                ),
                exc_info=True
            )
            return False
    
    async def send_email_reminder(
        self, 
        email: str, 
        task: Dict[str, Any],
        reminder_type: str = "due_soon"
    ) -> bool:
        """
        Envoyer un rappel par email pour une tâche
        
        Args:
            email: Adresse email du destinataire
            task: Dictionnaire contenant les infos de la tâche
            reminder_type: Type de rappel (due_soon, overdue, daily_summary)
            
        Returns:
            True si envoyé avec succès
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning(
                "Configuration SMTP manquante",
                extra=with_context(email=email)
            )
            return False
        
        try:
            # Créer le message
            message = MIMEMultipart("alternative")
            message["Subject"] = self._get_email_subject(task, reminder_type)
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = email
            
            # Corps du message
            html_body = self._create_email_body(task, reminder_type)
            text_body = self._create_text_body(task, reminder_type)
            
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Envoyer l'email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True
            )
            
            logger.info(
                "Email de rappel envoyé",
                extra=with_context(
                    email=email,
                    task_id=task.get("id"),
                    reminder_type=reminder_type
                )
            )
            return True
            
        except Exception as e:
            logger.error(
                "Erreur lors de l'envoi de l'email",
                extra=with_context(
                    email=email,
                    error=str(e)
                ),
                exc_info=True
            )
            return False
    
    async def schedule_task_reminders(
        self, 
        occurrence_id: UUID,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Planifier les rappels pour une occurrence de tâche
        
        Args:
            occurrence_id: ID de l'occurrence
            user_preferences: Préférences de notification de l'utilisateur
            
        Returns:
            Liste des rappels planifiés
        """
        pool = await init_db_pool()
        scheduled_reminders = []
        
        try:
            async with pool.acquire() as conn:
                # Récupérer l'occurrence et les infos associées
                occurrence = await conn.fetchrow(
                    """
                    SELECT 
                        o.*, 
                        td.title, 
                        td.description,
                        u.email,
                        u.id as user_id
                    FROM task_occurrences o
                    JOIN task_definitions td ON o.task_id = td.id
                    LEFT JOIN auth.users u ON o.assigned_to = u.id
                    WHERE o.id = $1
                    """,
                    occurrence_id
                )
                
                if not occurrence:
                    raise InvalidInput(
                        field="occurrence_id",
                        value=str(occurrence_id),
                        reason="Occurrence non trouvée"
                    )
                
                # Si pas d'utilisateur assigné, ne pas planifier de rappels
                if not occurrence["assigned_to"]:
                    logger.info(
                        "Pas de rappels - occurrence non assignée",
                        extra=with_context(occurrence_id=str(occurrence_id))
                    )
                    return []
                
                # Récupérer les préférences si non fournies
                if not user_preferences:
                    user_preferences = await self._get_user_preferences(
                        conn, 
                        occurrence["user_id"]
                    )
                
                # Calculer les moments de rappel
                due_at = occurrence["due_at"]
                reminder_times = self._calculate_reminder_times(
                    due_at, 
                    user_preferences
                )
                
                # Créer les entrées de notification
                for reminder_time, reminder_type in reminder_times:
                    # Ne pas créer de rappels dans le passé
                    if reminder_time > datetime.now(timezone.utc):
                        notification_id = await conn.fetchval(
                            """
                            INSERT INTO notifications 
                                (occurrence_id, member_id, channel, created_at)
                            VALUES ($1, $2, $3, NOW())
                            RETURNING id
                            """,
                            occurrence_id,
                            occurrence["user_id"],
                            user_preferences.get("preferred_channel", "push")
                        )
                        
                        scheduled_reminders.append({
                            "notification_id": notification_id,
                            "scheduled_for": reminder_time,
                            "type": reminder_type,
                            "channel": user_preferences.get("preferred_channel", "push")
                        })
                
                logger.info(
                    "Rappels planifiés",
                    extra=with_context(
                        occurrence_id=str(occurrence_id),
                        count=len(scheduled_reminders)
                    )
                )
                
        finally:
            await pool.close()
        
        return scheduled_reminders
    
    def _get_email_subject(self, task: Dict[str, Any], reminder_type: str) -> str:
        """Générer le sujet de l'email selon le type de rappel"""
        task_title = task.get("title", "Tâche")
        
        subjects = {
            "due_soon": f"⏰ Rappel : {task_title} à faire bientôt",
            "overdue": f"⚠️ En retard : {task_title}",
            "daily_summary": "📋 Vos tâches du jour",
            "assigned": f"✅ Nouvelle tâche assignée : {task_title}"
        }
        
        return subjects.get(reminder_type, f"Rappel : {task_title}")
    
    def _create_email_body(self, task: Dict[str, Any], reminder_type: str) -> str:
        """Créer le corps HTML de l'email"""
        task_title = task.get("title", "Tâche")
        task_desc = task.get("description", "")
        due_at = task.get("due_at")
        
        if due_at:
            due_str = due_at.strftime("%d/%m/%Y à %H:%M")
        else:
            due_str = "Date non définie"
        
        html_template = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4A90E2;">{self._get_email_subject(task, reminder_type)}</h2>
                
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0;">{task_title}</h3>
                    {f'<p style="color: #666; margin: 10px 0;">{task_desc}</p>' if task_desc else ''}
                    <p style="margin: 10px 0;">
                        <strong>Échéance :</strong> {due_str}
                    </p>
                </div>
                
                <div style="margin-top: 30px;">
                    <a href="{settings.app_url}/tasks/{task.get('id', '')}" 
                       style="background: #4A90E2; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        Voir la tâche
                    </a>
                </div>
                
                <hr style="margin: 40px 0; border: none; border-top: 1px solid #eee;">
                
                <p style="color: #999; font-size: 12px;">
                    Vous recevez cet email car vous êtes assigné à cette tâche. 
                    <a href="{settings.app_url}/settings/notifications" style="color: #4A90E2;">
                        Gérer vos préférences
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _create_text_body(self, task: Dict[str, Any], reminder_type: str) -> str:
        """Créer le corps texte de l'email"""
        task_title = task.get("title", "Tâche")
        task_desc = task.get("description", "")
        due_at = task.get("due_at")
        
        if due_at:
            due_str = due_at.strftime("%d/%m/%Y à %H:%M")
        else:
            due_str = "Date non définie"
        
        text_parts = [
            self._get_email_subject(task, reminder_type),
            "",
            f"Tâche : {task_title}",
        ]
        
        if task_desc:
            text_parts.append(f"Description : {task_desc}")
        
        text_parts.extend([
            f"Échéance : {due_str}",
            "",
            f"Voir la tâche : {settings.app_url}/tasks/{task.get('id', '')}",
            "",
            "---",
            "Vous recevez cet email car vous êtes assigné à cette tâche.",
            f"Gérer vos préférences : {settings.app_url}/settings/notifications"
        ])
        
        return "\n".join(text_parts)
    
    def _calculate_reminder_times(
        self, 
        due_at: datetime, 
        preferences: Dict[str, Any]
    ) -> List[tuple[datetime, str]]:
        """
        Calculer les moments où envoyer des rappels
        
        Returns:
            Liste de tuples (datetime, type_de_rappel)
        """
        reminders = []
        
        # Rappel la veille
        if preferences.get("reminder_day_before", True):
            reminder_time = due_at - timedelta(days=1)
            reminders.append((reminder_time, "day_before"))
        
        # Rappel le matin même
        if preferences.get("reminder_same_day", True):
            # 9h du matin le jour de l'échéance
            reminder_date = due_at.date()
            reminder_time = datetime.combine(
                reminder_date, 
                datetime.min.time().replace(hour=9)
            ).replace(tzinfo=timezone.utc)
            
            if reminder_time < due_at:
                reminders.append((reminder_time, "same_day"))
        
        # Rappel 2h avant
        if preferences.get("reminder_2h_before", True):
            reminder_time = due_at - timedelta(hours=2)
            if reminder_time > datetime.now(timezone.utc):
                reminders.append((reminder_time, "2h_before"))
        
        return reminders
    
    async def _get_user_preferences(
        self, 
        conn, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Récupérer les préférences de notification d'un utilisateur"""
        # Pour l'instant, retourner des préférences par défaut
        # TODO: Implémenter la table user_notification_preferences
        return {
            "preferred_channel": "push",
            "reminder_day_before": True,
            "reminder_same_day": True,
            "reminder_2h_before": True,
            "email_daily_summary": False,
            "push_enabled": True,
            "email_enabled": True
        }


# Instance singleton du service
notification_service = NotificationService()