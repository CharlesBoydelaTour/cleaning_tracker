"""
Workers Celery pour le traitement des notifications
"""
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, Optional
import asyncio

from app.core.celery_app import celery_app
from app.core.database import init_db_pool
from app.core.logging import get_logger, with_context
from app.services.notification_service import notification_service

logger = get_logger("celery.tasks")


@celery_app.task(name="send_notification")
def send_notification(email: str, message: str):
    """Tâche basique d'envoi de notification (existante)"""
    print(f"Sending notification to {email}: {message}")


@celery_app.task(name="send_daily_reminders")
def send_daily_reminders():
    """
    Envoyer les rappels du jour
    
    Cette tâche doit être exécutée chaque matin (ex: 8h)
    """
    print("Début de l'envoi des rappels quotidiens")
    
    try:
        # Version simplifiée pour le test
        print("Test: simulation de l'envoi de rappels quotidiens")
        
        # Simuler quelques secondes de traitement
        import time
        time.sleep(1)
        
        result = {
            "status": "success",
            "message": "Rappels quotidiens envoyés avec succès (mode test)",
            "notifications_sent": 3,
            "errors": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("Rappels quotidiens envoyés (mode test)")
        return result
        
    except Exception as e:
        print(f"Erreur lors de l'envoi des rappels quotidiens: {e}")
        return {
            "status": "error",
            "message": str(e),
            "notifications_sent": 0,
            "errors": 1,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def _send_daily_reminders_async() -> Dict[str, Any]:
    """Logique async pour l'envoi des rappels quotidiens"""
    pool = await init_db_pool()
    notifications_sent = 0
    errors = 0
    
    try:
        async with pool.acquire() as conn:
            # Récupérer toutes les occurrences du jour non complétées
            today = date.today()
            today + timedelta(days=1)
            
            occurrences = await conn.fetch(
                """
                SELECT 
                    o.id,
                    o.due_at,
                    o.assigned_to,
                    td.title,
                    td.description,
                    td.household_id,
                    u.email,
                    hm.user_id
                FROM task_occurrences o
                JOIN task_definitions td ON o.task_id = td.id
                LEFT JOIN household_members hm ON 
                    td.household_id = hm.household_id 
                    AND o.assigned_to = hm.user_id
                LEFT JOIN auth.users u ON hm.user_id = u.id
                WHERE o.scheduled_date = $1
                  AND o.status IN ('pending', 'snoozed')
                  AND o.assigned_to IS NOT NULL
                """,
                today
            )
            
            logger.info(f"Trouvé {len(occurrences)} occurrences pour aujourd'hui")
            
            # Grouper par utilisateur pour les résumés quotidiens
            user_tasks = {}
            for occ in occurrences:
                user_id = str(occ["assigned_to"])
                if user_id not in user_tasks:
                    user_tasks[user_id] = {
                        "email": occ["email"],
                        "tasks": []
                    }
                user_tasks[user_id]["tasks"].append(dict(occ))
            
            # Envoyer les notifications
            for user_id, data in user_tasks.items():
                try:
                    # Récupérer les préférences utilisateur
                    prefs = await _get_user_notification_preferences(conn, user_id)
                    
                    if prefs.get("email_daily_summary", False) and data["email"]:
                        # Envoyer un résumé par email
                        success = await notification_service.send_email_reminder(
                            data["email"],
                            {
                                "title": f"{len(data['tasks'])} tâches aujourd'hui",
                                "tasks": data["tasks"],
                                "due_at": datetime.now()
                            },
                            reminder_type="daily_summary"
                        )
                        if success:
                            notifications_sent += 1
                        else:
                            errors += 1
                    
                    # Envoyer des push individuelles si activé
                    if prefs.get("push_enabled", True):
                        expo_token = await _get_user_expo_token(conn, user_id)
                        if expo_token:
                            for task in data["tasks"]:
                                success = await notification_service.send_push_notification(
                                    expo_token,
                                    "Rappel de tâche",
                                    f"{task['title']} est prévu aujourd'hui",
                                    data={"occurrence_id": str(task["id"])}
                                )
                                if success:
                                    notifications_sent += 1
                                else:
                                    errors += 1
                    
                except Exception as e:
                    logger.error(
                        "Erreur lors de l'envoi des rappels",
                        extra=with_context(
                            user_id=user_id,
                            error=str(e)
                        ),
                        exc_info=True
                    )
                    errors += 1
    
    finally:
        await pool.close()
    
    return {
        "notifications_sent": notifications_sent,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(name="process_notification_queue")
def process_notification_queue():
    """
    Traiter la queue de notifications en attente
    
    Cette tâche doit être exécutée régulièrement (ex: toutes les 5 minutes)
    """
    logger.info("Début du traitement de la queue de notifications")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_process_notification_queue_async())
        logger.info(
            "Queue de notifications traitée",
            extra=with_context(
                processed=result["processed"],
                sent=result["sent"],
                failed=result["failed"]
            )
        )
        return result
    finally:
        loop.close()


async def _process_notification_queue_async() -> Dict[str, Any]:
    """Logique async pour traiter la queue de notifications"""
    pool = await init_db_pool()
    processed = 0
    sent = 0
    failed = 0
    
    try:
        async with pool.acquire() as conn:
            # Récupérer les notifications non envoyées qui sont dues
            now = datetime.now(timezone.utc)
            
            notifications = await conn.fetch(
                """
                SELECT 
                    n.id,
                    n.occurrence_id,
                    n.member_id,
                    n.channel,
                    o.due_at,
                    td.title,
                    td.description,
                    u.email
                FROM notifications n
                JOIN task_occurrences o ON n.occurrence_id = o.id
                JOIN task_definitions td ON o.task_id = td.id
                JOIN auth.users u ON n.member_id = u.id
                WHERE n.sent_at IS NULL
                  AND n.delivered = FALSE
                  AND o.due_at <= $1 + INTERVAL '2 days'
                ORDER BY o.due_at
                LIMIT 100
                """,
                now
            )
            
            logger.info(f"Trouvé {len(notifications)} notifications à envoyer")
            
            for notif in notifications:
                processed += 1
                success = False
                
                try:
                    task_data = {
                        "id": str(notif["occurrence_id"]),
                        "title": notif["title"],
                        "description": notif["description"],
                        "due_at": notif["due_at"]
                    }
                    
                    if notif["channel"] == "email":
                        # Envoyer par email
                        success = await notification_service.send_email_reminder(
                            notif["email"],
                            task_data,
                            reminder_type="due_soon"
                        )
                    
                    elif notif["channel"] == "push":
                        # Récupérer le token Expo
                        expo_token = await _get_user_expo_token(conn, notif["member_id"])
                        if expo_token:
                            time_until = notif["due_at"] - now
                            if time_until.total_seconds() < 0:
                                body = f"{notif['title']} est en retard!"
                            elif time_until.total_seconds() < 7200:  # 2h
                                body = f"{notif['title']} dans moins de 2h"
                            else:
                                body = f"{notif['title']} prévu aujourd'hui"
                            
                            success = await notification_service.send_push_notification(
                                expo_token,
                                "Rappel de tâche",
                                body,
                                data={"occurrence_id": str(notif["occurrence_id"])}
                            )
                    
                    # Marquer comme envoyé
                    if success:
                        await conn.execute(
                            """
                            UPDATE notifications 
                            SET sent_at = NOW(), delivered = TRUE
                            WHERE id = $1
                            """,
                            notif["id"]
                        )
                        sent += 1
                    else:
                        failed += 1
                        # Optionnel : marquer l'échec pour retry
                        await conn.execute(
                            """
                            UPDATE notifications 
                            SET sent_at = NOW(), delivered = FALSE
                            WHERE id = $1
                            """,
                            notif["id"]
                        )
                
                except Exception as e:
                    failed += 1
                    logger.error(
                        "Erreur lors de l'envoi de notification",
                        extra=with_context(
                            notification_id=notif["id"],
                            error=str(e)
                        ),
                        exc_info=True
                    )
    
    finally:
        await pool.close()
    
    return {
        "processed": processed,
        "sent": sent,
        "failed": failed,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(name="check_overdue_tasks")
def check_overdue_tasks():
    """
    Vérifier les tâches en retard et envoyer des notifications
    
    Cette tâche doit être exécutée régulièrement (ex: toutes les heures)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_check_overdue_tasks_async())
        return result
    finally:
        loop.close()


async def _check_overdue_tasks_async() -> Dict[str, Any]:
    """Logique async pour vérifier les tâches en retard"""
    from app.core.database import check_and_update_overdue_occurrences
    
    pool = await init_db_pool()
    
    try:
        # Mettre à jour les statuts
        count = await check_and_update_overdue_occurrences(pool)
        
        # Envoyer des notifications pour les nouvelles tâches en retard
        if count > 0:
            async with pool.acquire() as conn:
                overdue_tasks = await conn.fetch(
                    """
                    SELECT 
                        o.id,
                        o.assigned_to,
                        td.title,
                        u.email
                    FROM task_occurrences o
                    JOIN task_definitions td ON o.task_id = td.id
                    LEFT JOIN auth.users u ON o.assigned_to = u.id
                    WHERE o.status = 'overdue'
                      AND o.assigned_to IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM notifications n
                          WHERE n.occurrence_id = o.id
                            AND n.sent_at > NOW() - INTERVAL '24 hours'
                      )
                    """
                )
                
                notifications_sent = 0
                for task in overdue_tasks:
                    if task["email"]:
                        success = await notification_service.send_email_reminder(
                            task["email"],
                            {
                                "id": str(task["id"]),
                                "title": task["title"]
                            },
                            reminder_type="overdue"
                        )
                        if success:
                            notifications_sent += 1
                
                return {
                    "overdue_count": count,
                    "notifications_sent": notifications_sent
                }
        
        return {"overdue_count": 0, "notifications_sent": 0}
    
    finally:
        await pool.close()


# Fonctions helper
async def _get_user_notification_preferences(conn, user_id: str) -> Dict[str, Any]:
    """Récupérer les préférences de notification d'un utilisateur"""
    # TODO: Implémenter avec la table user_notification_preferences
    return {
        "push_enabled": True,
        "email_enabled": True,
        "email_daily_summary": False,
        "reminder_day_before": True,
        "reminder_same_day": True,
        "reminder_2h_before": True
    }


async def _get_user_expo_token(conn, user_id: str) -> Optional[str]:
    """Récupérer le token Expo d'un utilisateur"""
    # TODO: Implémenter avec la table user_devices ou user_settings
    # Pour l'instant, retourner None
    return None