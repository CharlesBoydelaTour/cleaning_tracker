#!/usr/bin/env python3
"""
Script de test pour valider la configuration des environnements
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer l'app
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_environment(env_name: str):
    """Teste la configuration pour un environnement donné"""
    print(f"\n🧪 Test de l'environnement: {env_name}")
    print("=" * 50)
    
    # Définir la variable d'environnement
    os.environ["ENVIRONMENT"] = env_name
    
    try:
        # Recharger les modules pour prendre en compte la nouvelle variable
        import importlib
        if 'app.config' in sys.modules:
            del sys.modules['app.config']
        
        from app.config import settings, get_env_file
        
        print(f"✅ Fichier .env utilisé: {get_env_file()}")
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Log Level: {settings.log_level}")
        print(f"✅ Log Format: {settings.log_format}")
        print(f"✅ Database URL: {settings.database_url}")
        print(f"✅ Supabase URL: {settings.supabase_url}")
        print(f"✅ Redis URL: {settings.redis_url}")
        print(f"✅ App URL: {settings.app_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de {env_name}: {e}")
        return False

def main():
    """Fonction principale"""
    print("🌍 Test de la configuration multi-environnements")
    print("=" * 60)
    
    environments = ["development", "staging", "production"]
    results = {}
    
    for env in environments:
        results[env] = check_environment(env)
    
    # Résumé
    print("\n📊 RÉSUMÉ DES TESTS")
    print("=" * 30)
    
    all_passed = True
    for env, passed in results.items():
        status = "✅ PASSÉ" if passed else "❌ ÉCHEC"
        print(f"{env:12} : {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Tous les tests sont passés avec succès !")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez vos fichiers .env")
        return 1

if __name__ == "__main__":
    sys.exit(main())
