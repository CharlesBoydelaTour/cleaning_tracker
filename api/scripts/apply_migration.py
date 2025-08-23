#!/usr/bin/env python
import asyncio
import os
import sys
from typing import List

from dotenv import load_dotenv
import asyncpg

# Rendre importable app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import init_db_pool


def load_env():
    # Charge d'abord api/.env.remote si présent (fall back sur variables déjà dans l'env)
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env.remote'))
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)


def split_sql(sql: str) -> List[str]:
    # Séparation très simple par ';' en fin de ligne. Suffisant pour cette migration.
    stmts: List[str] = []
    buff: List[str] = []
    for line in sql.splitlines():
        buff.append(line)
        if line.rstrip().endswith(';'):
            stmts.append('\n'.join(buff).strip())
            buff = []
    if buff:
        stmts.append('\n'.join(buff).strip())
    return [s for s in stmts if s]


async def apply_sql_file(path: str) -> bool:
    load_env()
    pool = None
    try:
        pool = await init_db_pool(optional=False)
        with open(path, 'r', encoding='utf-8') as f:
            sql = f.read()
        statements = split_sql(sql)
        print(f"Applying migration: {path} ({len(statements)} statements)")
        async with pool.acquire() as conn:
            async with conn.transaction():
                for stmt in statements:
                    try:
                        await conn.execute(stmt)
                    except asyncpg.DuplicateObjectError:
                        # Ex: type/table/index already exists
                        print("- Skipped (already exists)")
                    except Exception as e:
                        # Autoriser les reruns idempotents: ignorer si message 'already exists'
                        if 'already exists' in str(e):
                            print(f"- Skipped (already exists): {str(e).splitlines()[0]}")
                            continue
                        raise
        print("✅ Migration applied successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to apply migration: {e}")
        return False
    finally:
        if pool:
            await pool.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/apply_migration.py <path_to_sql>")
        sys.exit(1)
    sql_path = sys.argv[1]
    if not os.path.isabs(sql_path):
        # Résoudre par rapport au CWD
        sql_path = os.path.abspath(sql_path)
    if not os.path.exists(sql_path):
        print(f"SQL file not found: {sql_path}")
        sys.exit(1)
    ok = asyncio.run(apply_sql_file(sql_path))
    sys.exit(0 if ok else 2)
