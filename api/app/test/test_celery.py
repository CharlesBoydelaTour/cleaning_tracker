# test_celery.py
from app.core.celery_app import celery_app
from app.worker import tasks  # Import explicite des tâches

def test_celery():
    print("=== Test des tâches Celery ===")
    
    # Afficher les tâches disponibles
    print("\nTâches enregistrées:")
    custom_tasks = [name for name in celery_app.tasks if not name.startswith('celery.')]
    for task_name in sorted(custom_tasks):
        print(f"  ✓ {task_name}")
    
    # Test avec delay() au lieu de send_task()
    print("\n=== Test d'envoi via delay() ===")
    try:
        result = tasks.send_daily_reminders.delay()
        print(f"✓ Tâche envoyée (ID: {result.id})")
        print(f"✓ Statut: {result.status}")
        
        # Essayer d'obtenir le résultat avec un timeout court
        try:
            result_data = result.get(timeout=5)
            print(f"✓ Résultat: {result_data}")
        except Exception as e:
            print(f"⚠️  Timeout ou worker non disponible: {e}")
            print("⚠️  Pour exécuter la tâche, démarrez un worker:")
            print("    celery -A app.core.celery_app worker --loglevel=info")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_celery()