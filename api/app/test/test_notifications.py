from datetime import datetime, timezone
from app.services.notification_service import notification_service

async def test_email():
    # Test d'envoi d'email
    success = await notification_service.send_email_reminder(
        "yourmail@test.com", # Remplacez par une adresse email valide
        {
            "id": "test-123",
            "title": "Nettoyer la cuisine",
            "description": "Faire la vaisselle et nettoyer le plan de travail",
            "due_at": datetime.now(timezone.utc)
        },
        reminder_type="due_soon"
    )
    print(f"Email envoyé: {success}")

# Lancer le test
if __name__ == "__main__":
    pass
    # Uncomment the line below to run the test when executing this script (will send an email)
    #asyncio.run(test_email())
