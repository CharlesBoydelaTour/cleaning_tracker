#!/usr/bin/env python

import asyncio
import sys
import os

# Ajoutez le répertoire parent au chemin pour que Python puisse trouver le package app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db_pool


async def describe_table(table_name):
    """Décrit la structure d'une table."""
    print(f"Examen de la structure de la table {table_name}...")
    try:
        pool = await init_db_pool()
        
        async with pool.acquire() as conn:
            columns = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = 'public'
                ORDER BY ordinal_position
                """, 
                table_name
            )
            
            if not columns:
                print(f"❌ La table {table_name} n'existe pas ou n'a pas de colonnes.")
                return
            
            print(f"✅ Structure de la table {table_name}:")
            for col in columns:
                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                print(f"   - {col['column_name']} ({col['data_type']}) {nullable}")
            
            # Vérifier les contraintes (clés primaires, etc.)
            constraints = await conn.fetch(
                """
                SELECT c.conname as constraint_name,
                       c.contype as constraint_type,
                       pg_get_constraintdef(c.oid) as constraint_definition
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE conrelid = (SELECT oid FROM pg_class WHERE relname = $1
                                  AND relnamespace = (SELECT oid FROM pg_namespace
                                                     WHERE nspname = 'public'))
                """,
                table_name
            )
            
            if constraints:
                print(f"\n✅ Contraintes de la table {table_name}:")
                for constraint in constraints:
                    constraint_type = {
                        'p': 'PRIMARY KEY',
                        'f': 'FOREIGN KEY',
                        'u': 'UNIQUE',
                        'c': 'CHECK',
                        't': 'TRIGGER',
                        'x': 'EXCLUSION'
                    }.get(constraint["constraint_type"], "AUTRE")
                    
                    print(f"   - {constraint['constraint_name']} ({constraint_type}): {constraint['constraint_definition']}")
        
        await pool.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'examen de la table: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python db_schema.py <table_name>")
        sys.exit(1)
    
    table_name = sys.argv[1]
    success = asyncio.run(describe_table(table_name))
    
    if not success:
        sys.exit(1)
