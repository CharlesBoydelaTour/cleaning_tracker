import asyncpg
from app.config import settings
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import date


async def init_db_pool():

    # Assurons-nous que l'URL est au format attendu par asyncpg
    # Remplacer postgresql+asyncpg:// par postgresql:// si nécessaire
    database_url = settings.database_url
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    print(f"Connexion à la base de données avec l'URL: {database_url}")
    return await asyncpg.create_pool(dsn=database_url)


async def create_household(
    pool: asyncpg.Pool, name: str, created_by_user_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Créer un nouveau ménage dans la base de données.

    Args:
        pool: Pool de connexions à la base de données
        name: Nom du ménage
        created_by_user_id: ID de l'utilisateur qui crée le ménage (optionnel)

    Returns:
        Un dictionnaire contenant les données du ménage créé
    """
    async with pool.acquire() as conn:
        # Insérer le ménage dans la table households
        household_id = await conn.fetchval(
            """
            INSERT INTO households (name, created_at) 
            VALUES ($1, NOW()) 
            RETURNING id
            """,
            name,
        )

        # Si l'ID de l'utilisateur est fourni, vérifier qu'il existe et l'ajouter comme membre du ménage
        if created_by_user_id:
            # Vérifier que l'utilisateur existe
            user_exists = await conn.fetchval(
                "SELECT 1 FROM users WHERE id = $1",
                created_by_user_id
            )
            
            if user_exists:
                await conn.execute(
                    """
                    INSERT INTO household_members (household_id, user_id, role) 
                    VALUES ($1, $2, 'admin')
                    """,
                    household_id,
                    created_by_user_id,
                )

        # Récupérer les données complètes du ménage
        household_data = await conn.fetchrow(
            """
            SELECT id, name, created_at
            FROM households 
            WHERE id = $1
            """,
            household_id,
        )

        # Convertir le record en dictionnaire
        return dict(household_data)


async def get_households(
    pool: asyncpg.Pool, user_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Récupérer la liste des ménages, filtré par user_id si fourni.

    Args:
        pool: Pool de connexions à la base de données
        user_id: ID de l'utilisateur pour filtrer ses ménages (optionnel)

    Returns:
        Une liste de dictionnaires contenant les données des ménages
    """
    async with pool.acquire() as conn:
        if user_id:
            # Récupérer les ménages de l'utilisateur
            households = await conn.fetch(
                """
                SELECT h.id, h.name, h.created_at
                FROM households h
                JOIN household_members hm ON h.id = hm.household_id
                WHERE hm.user_id = $1
                ORDER BY h.name
                """,
                user_id,
            )
        else:
            # Récupérer tous les ménages
            households = await conn.fetch(
                """
                SELECT id, name, created_at
                FROM households
                ORDER BY name
                """
            )

        # Convertir les records en dictionnaires
        return [dict(household) for household in households]


async def get_household_members(
    pool: asyncpg.Pool, household_id: UUID
) -> List[Dict[str, Any]]:
    """
    Récupérer la liste des membres d'un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage

    Returns:
        Une liste de dictionnaires contenant les données des membres
    """
    async with pool.acquire() as conn:
        members = await conn.fetch(
            """
            SELECT id, household_id, user_id, role
            FROM household_members
            WHERE household_id = $1
            ORDER BY role
            """,
            household_id,
        )

        return [dict(member) for member in members]


async def get_household_member(
    pool: asyncpg.Pool, household_id: UUID, member_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Récupérer les détails d'un membre spécifique d'un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage
        member_id: ID du membre

    Returns:
        Un dictionnaire contenant les données du membre ou None si non trouvé
    """
    async with pool.acquire() as conn:
        member = await conn.fetchrow(
            """
            SELECT id, household_id, user_id, role
            FROM household_members
            WHERE household_id = $1 AND id = $2
            """,
            household_id,
            member_id,
        )

        return dict(member) if member else None


async def create_household_member(
    pool: asyncpg.Pool, household_id: UUID, user_id: UUID, role: str = "member"
) -> Dict[str, Any]:
    """
    Ajouter un membre à un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage
        user_id: ID de l'utilisateur à ajouter
        role: Rôle du membre (admin, member, guest)

    Returns:
        Un dictionnaire contenant les données du membre créé
    """
    async with pool.acquire() as conn:
        # Vérifier si le membre existe déjà
        existing_member = await conn.fetchval(
            """
            SELECT id
            FROM household_members
            WHERE household_id = $1 AND user_id = $2
            """,
            household_id,
            user_id,
        )

        if existing_member:
            raise ValueError("Cet utilisateur est déjà membre de ce ménage")

        # Ajouter le membre au ménage
        member_id = await conn.fetchval(
            """
            INSERT INTO household_members (household_id, user_id, role)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            household_id,
            user_id,
            role,
        )

        # Récupérer les données complètes du membre
        member_data = await conn.fetchrow(
            """
            SELECT id, household_id, user_id, role
            FROM household_members
            WHERE id = $1
            """,
            member_id,
        )

        return dict(member_data)


async def update_household_member(
    pool: asyncpg.Pool, household_id: UUID, member_id: UUID, role: str
) -> Dict[str, Any]:
    """
    Mettre à jour le rôle d'un membre d'un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage
        member_id: ID du membre
        role: Nouveau rôle du membre (admin, member, guest)

    Returns:
        Un dictionnaire contenant les données du membre mis à jour
    """
    async with pool.acquire() as conn:
        # Vérifier que le membre existe dans ce ménage
        existing_member = await conn.fetchval(
            """
            SELECT id
            FROM household_members
            WHERE household_id = $1 AND id = $2
            """,
            household_id,
            member_id,
        )

        if not existing_member:
            raise ValueError("Ce membre n'existe pas dans ce ménage")

        # Mettre à jour le rôle du membre
        await conn.execute(
            """
            UPDATE household_members
            SET role = $1
            WHERE household_id = $2 AND id = $3
            """,
            role,
            household_id,
            member_id,
        )

        # Récupérer les données complètes du membre mis à jour
        member_data = await conn.fetchrow(
            """
            SELECT id, household_id, user_id, role
            FROM household_members
            WHERE id = $1
            """,
            member_id,
        )

        return dict(member_data)


async def delete_household_member(
    pool: asyncpg.Pool, household_id: UUID, member_id: UUID
) -> bool:
    """
    Supprimer un membre d'un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage
        member_id: ID du membre

    Returns:
        True si le membre a été supprimé, False sinon
    """
    async with pool.acquire() as conn:
        # Vérifier que le membre existe dans ce ménage avant suppression
        existing_member = await conn.fetchval(
            """
            SELECT id
            FROM household_members
            WHERE household_id = $1 AND id = $2
            """,
            household_id,
            member_id,
        )

        if not existing_member:
            return False

        # Supprimer le membre
        rows_deleted = await conn.execute(
            """
            DELETE FROM household_members
            WHERE household_id = $1 AND id = $2
            """,
            household_id,
            member_id,
        )

        # Vérifier qu'une ligne a été supprimée
        return "DELETE 1" in rows_deleted


async def get_rooms(pool: asyncpg.Pool, household_id: UUID) -> List[Dict[str, Any]]:
    """
    Récupérer la liste des pièces d'un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage

    Returns:
        Une liste de dictionnaires contenant les données des pièces
    """
    async with pool.acquire() as conn:
        rooms = await conn.fetch(
            """
            SELECT id, name, household_id, icon, created_at
            FROM rooms
            WHERE household_id = $1
            ORDER BY name
            """,
            household_id,
        )

        return [dict(room) for room in rooms]


async def get_room(pool: asyncpg.Pool, room_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Récupérer les détails d'une pièce spécifique.

    Args:
        pool: Pool de connexions à la base de données
        room_id: ID de la pièce

    Returns:
        Un dictionnaire contenant les données de la pièce ou None si non trouvée
    """
    async with pool.acquire() as conn:
        room = await conn.fetchrow(
            """
            SELECT id, name, household_id, icon, created_at
            FROM rooms
            WHERE id = $1
            """,
            room_id,
        )

        return dict(room) if room else None


async def create_room(
    pool: asyncpg.Pool, name: str, household_id: UUID, icon: Optional[str] = None
) -> Dict[str, Any]:
    """
    Créer une nouvelle pièce dans un ménage.

    Args:
        pool: Pool de connexions à la base de données
        name: Nom de la pièce
        household_id: ID du ménage
        icon: Icône de la pièce (optionnel)

    Returns:
        Un dictionnaire contenant les données de la pièce créée
    """
    async with pool.acquire() as conn:
        room_id = await conn.fetchval(
            """
            INSERT INTO rooms (name, household_id, icon, created_at)
            VALUES ($1, $2, $3, NOW())
            RETURNING id
            """,
            name,
            household_id,
            icon,
        )

        room_data = await conn.fetchrow(
            """
            SELECT id, name, household_id, icon, created_at
            FROM rooms
            WHERE id = $1
            """,
            room_id,
        )

        return dict(room_data)


async def get_tasks(pool: asyncpg.Pool, household_id: UUID) -> List[Dict[str, Any]]:
    """
    Récupérer la liste des tâches d'un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage

    Returns:
        Une liste de dictionnaires contenant les données des tâches
    """
    async with pool.acquire() as conn:
        tasks = await conn.fetch(
            """
            SELECT id, title, description, household_id, due_date, completed
            FROM tasks
            WHERE household_id = $1
            ORDER BY due_date
            """,
            household_id,
        )

        # Convertir les datetime en date si nécessaire
        result = []
        for task in tasks:
            task_dict = dict(task)
            if task_dict["due_date"] and hasattr(task_dict["due_date"], "date"):
                task_dict["due_date"] = task_dict["due_date"].date()
            result.append(task_dict)
        
        return result


async def get_task(pool: asyncpg.Pool, task_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Récupérer les détails d'une tâche spécifique.

    Args:
        pool: Pool de connexions à la base de données
        task_id: ID de la tâche

    Returns:
        Un dictionnaire contenant les données de la tâche ou None si non trouvée
    """
    async with pool.acquire() as conn:
        task = await conn.fetchrow(
            """
            SELECT id, title, description, household_id, due_date, completed
            FROM tasks
            WHERE id = $1
            """,
            task_id,
        )

        if not task:
            return None
            
        # Convertir due_date de datetime à date si nécessaire
        result = dict(task)
        if result["due_date"] and hasattr(result["due_date"], "date"):
            result["due_date"] = result["due_date"].date()
        
        return result


async def create_task(
    pool: asyncpg.Pool,
    title: str,
    household_id: UUID,
    description: Optional[str] = None,
    due_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Créer une nouvelle tâche dans un ménage.

    Args:
        pool: Pool de connexions à la base de données
        title: Titre de la tâche
        household_id: ID du ménage
        description: Description de la tâche (optionnel)
        due_date: Date d'échéance de la tâche (optionnel)

    Returns:
        Un dictionnaire contenant les données de la tâche créée
    """
    async with pool.acquire() as conn:
        task_id = await conn.fetchval(
            """
            INSERT INTO tasks (title, description, household_id, due_date, completed)
            VALUES ($1, $2, $3, $4, false)
            RETURNING id
            """,
            title,
            description,
            household_id,
            due_date,
        )

        task_data = await conn.fetchrow(
            """
            SELECT id, title, description, household_id, due_date, completed
            FROM tasks
            WHERE id = $1
            """,
            task_id,
        )

        # Convertir due_date de datetime à date si nécessaire
        result = dict(task_data)
        if result["due_date"] and hasattr(result["due_date"], "date"):
            result["due_date"] = result["due_date"].date()
        
        return result
