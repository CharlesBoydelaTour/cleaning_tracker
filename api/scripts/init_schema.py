#!/usr/bin/env python
"""
Script pour initialiser le schéma de base de données PostgreSQL
"""

import asyncio
import sys
import os

# Ajoutez le répertoire parent au chemin pour que Python puisse trouver le package app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db_pool


async def create_schema():
    """Crée toutes les tables nécessaires pour l'application."""
    print("Initialisation du pool de connexions à la base de données...")
    try:
        pool = await init_db_pool()
        print("✅ Pool de connexions initialisé avec succès.")

        async with pool.acquire() as conn:
            print("🔧 Création du schéma de base de données...")
            
            # Table des utilisateurs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Table 'users' créée.")

            # Table des ménages
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS households (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Table 'households' créée.")

            # Table des membres de ménage
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS household_members (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(household_id, user_id)
                )
            """)
            print("✅ Table 'household_members' créée.")

            # Table des pièces
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    icon VARCHAR(10),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Table 'rooms' créée.")

            # Table des tâches
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
                    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
                    due_date TIMESTAMP,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Table 'tasks' créée.")

            # Créer des index pour améliorer les performances
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_household_members_household_id ON household_members(household_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_household_members_user_id ON household_members(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_rooms_household_id ON rooms(household_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_household_id ON tasks(household_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_room_id ON tasks(room_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to)")
            print("✅ Index créés.")

        # Fermeture du pool de connexions
        await pool.close()
        print("✅ Pool de connexions fermé.")
        print("🎉 Schéma de base de données créé avec succès!")

        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du schéma: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(create_schema())
    if success:
        print("✅ Initialisation du schéma réussie!")
        sys.exit(0)
    else:
        print("❌ Échec de l'initialisation du schéma.")
        sys.exit(1)
