# test_integration.py
import asyncio
from app.core.database import init_db_pool
from app.services.notification_service import notification_service

async def test_full_flow():
    pool = await init_db_pool()
    
    try:
        async with pool.acquire():
            # 1. Créer une occurrence de test
            
            # 2. Planifier les rappels
            occurrence_id = "OCCURRENCE_ID"  # Remplace par une vraie occurrence
            
            reminders = await notification_service.schedule_task_reminders(
                occurrence_id,
                {
                    "preferred_channel": "email",
                    "email_enabled": True,
                    "reminder_same_day": True
                }
            )
            
            print(f"Rappels planifiés: {len(reminders)}")
            
    finally:
        await pool.close()

asyncio.run(test_full_flow())