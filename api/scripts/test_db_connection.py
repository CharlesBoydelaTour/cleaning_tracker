#!/usr/bin/env python

import asyncio
import sys
import os
import pytest

# Ajoutez le répertoire parent au chemin pour que Python puisse trouver le package app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db_pool


async def check_database_connection():
    """Teste la connexion à la base de données PostgreSQL."""
    print("Initialisation du pool de connexions à la base de données...")
    pool = None
    try:
        pool = await init_db_pool()
        print("✅ Pool de connexions initialisé avec succès.")

        print("Test de la connexion en exécutant une requête SQL simple...")
        async with pool.acquire() as conn:
            # Une simple requête pour vérifier que la connexion fonctionne
            result = await conn.fetchval("SELECT 1")
            print(f"✅ La requête a retourné: {result}")

            # Récupérer la version de PostgreSQL
            pg_version = await conn.fetchval("SHOW server_version")
            print(f"✅ Version PostgreSQL: {pg_version}")

            # Liste des tables dans le schéma public
            tables = await conn.fetch(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            if tables:
                print("✅ Tables dans le schéma public:")
                for table in tables:
                    print(f"   - {table['table_name']}")
            else:
                print("ℹ️ Aucune table trouvée dans le schéma public.")

        return True
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à la base de données: {e}")
        return False
    finally:
        if pool:
            try:
                await pool.close()
                print("✅ Pool de connexions fermé.")
                # Petite pause pour permettre la fermeture complète
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Erreur lors de la fermeture du pool: {e}")