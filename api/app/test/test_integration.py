# test_integration.py
import asyncio
from uuid import uuid4
from app.core.database import init_db_pool, create_household, create_user, create_task_definition
from app.services.notification_service import notification_service

async def test_full_flow():
    pool = await init_db_pool()
    
    try:
        async with pool.acquire() as conn:
            # 1. Créer un utilisateur de test avec un email unique
            unique_id = str(uuid4())
            user = await create_user(
                pool,
                f"test_{unique_id}@example.com",
                "hashed_password",
                "Test User"
            )
            
            # 2. Créer un ménage de test
            household = await create_household(pool, "Test House", user["id"])
            
            # 3. Créer une définition de tâche
            task_def = await create_task_definition(
                pool,
                title="Test Task",
                recurrence_rule="FREQ=DAILY",
                household_id=household["id"],
                created_by=user["id"]
            )
            
            # 4. Créer une occurrence de test
            occurrence_id = await conn.fetchval(
                """
                INSERT INTO task_occurrences (id, task_id, scheduled_date, due_at, status, created_at)
                VALUES (gen_random_uuid(), $1, CURRENT_DATE + INTERVAL '1 day', NOW() + INTERVAL '1 day', 'pending', NOW())
                RETURNING id
                """,
                task_def["id"]
            )
            
            # 5. Planifier les rappels
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

if __name__ == "__main__":
    asyncio.run(test_full_flow())