import asyncpg
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import date, datetime, timedelta
from dateutil.rrule import rrulestr

from app.config import settings
import socket
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from app.schemas.task import TaskStatus


async def init_db_pool(optional: bool = False, timeout: float = 10.0):
    """Initialise le pool de connexions à la base de données.

    Args:
        optional: si True, en cas d'échec la fonction retourne None au lieu d'élever.
        timeout: délai max (secondes) pour établir le pool.

    Returns:
        asyncpg.Pool ou None si optional et échec.
    """
    # Point de départ: URL principale
    database_url = os.getenv("DATABASE_POOLER_URL") or settings.database_url
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # S'assurer que sslmode=require est présent (bonne pratique pour Supabase)
    try:
        parts = urlsplit(database_url)
        query_pairs = dict(parse_qsl(parts.query, keep_blank_values=True))
        if query_pairs.get("sslmode") is None:
            query_pairs["sslmode"] = "require"
        database_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment))
    except Exception:
        pass

    # Force IPv4 if requested (default True in Docker where IPv6 route may be unavailable)
    prefer_ipv4 = os.getenv("PREFER_IPV4", "1") == "1"
    if prefer_ipv4:
        try:
            parts = urlsplit(database_url)
            host = parts.hostname
            port = parts.port or 5432
            if host and not host.replace('.', '').isdigit():
                # Resolve A record (IPv4)
                infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
                if infos:
                    ipv4_addr = infos[0][4][0]
                    # Rebuild netloc with credentials if any
                    userinfo = ''
                    if parts.username:
                        userinfo += parts.username
                        if parts.password:
                            userinfo += f':{parts.password}'
                        userinfo += '@'
                    netloc = f"{userinfo}{ipv4_addr}:{port}"
                    database_url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
        except Exception as e:
            # Best-effort: keep original URL on any failure
            pass

    # Log minimal sans fuite de secrets
    try:
        parts = urlsplit(database_url)
        logging.info(f"[db] Connecting to {parts.hostname}:{parts.port or 5432} (sslmode=require)")
    except Exception:
        pass

    try:
        # Compatibilité pgbouncer (transaction pooler): pas de prepared statements
        return await asyncio.wait_for(
            asyncpg.create_pool(dsn=database_url, statement_cache_size=0),
            timeout=timeout,
        )
    except Exception as e:
        if optional:
            logging.warning(f"[db] Impossible de créer le pool (mode optionnel activé): {e}")
            return None
        raise

def ensure_pool(pool: Optional[asyncpg.Pool]):
    if pool is None:
        raise RuntimeError("Base de données non initialisée (pool None). Activez DB_OPTIONAL=1 seulement pour les endpoints qui ne requièrent pas le stockage.")


# ============================================================================
# USER CRUD
# ============================================================================

async def create_user(
    pool: asyncpg.Pool,
    email: str,
    hashed_password: Optional[str] = None,  # Modifié pour être optionnel
    full_name: Optional[str] = None
) -> Dict[str, Any]:
    """Créer un nouvel utilisateur. hashed_password peut être None pour les utilisateurs invités."""
    ensure_pool(pool)
    async with pool.acquire() as conn:
        # Utiliser la partie locale de l'email comme full_name si non fourni
        effective_full_name = full_name if full_name else email.split('@')[0]
        
        # La colonne id dans public.users est synchronisée depuis auth.users.id
        # Si nous créons un utilisateur directement ici, il n'aura pas d'entrée auth.users
        # Cela pourrait être problématique. Idéalement, l'invitation créerait l'utilisateur via Supabase Auth.
        # Pour cette implémentation, nous allons insérer dans public.users,
        # mais il faut être conscient de cette potentielle désynchronisation ou de la nécessité
        # d'un processus d'invitation plus robuste via Supabase.

        # Supposons que la table users (public.users) a une colonne pour le mot de passe haché
        # et qu'elle est nullable. Le nom de la colonne peut varier (ex: hashed_password, encrypted_password)
        # Je vais utiliser hashed_password comme dans la signature.
        # La colonne id doit être gérée correctement, gen_random_uuid() est utilisé ici.
        
        user_id = await conn.fetchval(
            """
            INSERT INTO public.users (email, full_name, hashed_password, created_at, updated_at, is_active)
            VALUES ($1, $2, $3, NOW(), NOW(), TRUE)
            ON CONFLICT (email) DO NOTHING  -- Pour éviter les erreurs si l'email existe déjà, bien que get_user_by_email devrait le gérer
            RETURNING id
            """,
            email,
            effective_full_name,
            hashed_password  # Peut être NULL
        )

        if not user_id: # Si ON CONFLICT DO NOTHING a été déclenché et rien n'a été inséré
            existing_user = await conn.fetchrow("SELECT id FROM public.users WHERE email = $1", email)
            if existing_user:
                user_id = existing_user['id']
            else:
                # Cela ne devrait pas arriver si l'email existe et que ON CONFLICT est bien géré
                raise Exception(f"Impossible de créer ou de récupérer l'utilisateur avec l'email {email}")


        user_data = await conn.fetchrow(
            """
            SELECT id, email, full_name, created_at, updated_at, email_confirmed_at, is_active
            FROM public.users
            WHERE id = $1
            """,
            user_id
        )
        # Note: hashed_password n'est pas retourné pour des raisons de sécurité.
        return dict(user_data) if user_data else None


async def get_user_by_email(pool: asyncpg.Pool, email: str) -> Optional[Dict[str, Any]]:
    """Récupérer un utilisateur par son adresse e-mail."""
    ensure_pool(pool)
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            """
            SELECT id, email, full_name, created_at, updated_at, email_confirmed_at, is_active
            FROM public.users 
            WHERE email = $1
            """,
            email,
        )
        return dict(user_data) if user_data else None


# ============================================================================
# TASK DEFINITIONS CRUD
# ============================================================================

async def create_task_definition(
    pool: asyncpg.Pool,
    title: str,
    recurrence_rule: str,
    household_id: Optional[UUID] = None,
    description: Optional[str] = None,
    estimated_minutes: Optional[int] = None,
    room_id: Optional[UUID] = None,
    is_catalog: bool = False,
    created_by: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Créer une nouvelle définition de tâche.
    
    Args:
        pool: Pool de connexions à la base de données
        title: Titre de la tâche
        recurrence_rule: Règle de récurrence (format RRULE)
        household_id: ID du ménage (None pour les tâches catalogue)
        description: Description de la tâche
        estimated_minutes: Durée estimée en minutes
        room_id: ID de la pièce associée
        is_catalog: Si True, c'est une tâche du catalogue global
        created_by: ID de l'utilisateur créateur
    
    Returns:
        Dict contenant les données de la définition créée
    """
    ensure_pool(pool)
    async with pool.acquire() as conn:
        task_def_id = await conn.fetchval(
            """
            INSERT INTO task_definitions 
                (title, description, recurrence_rule, estimated_minutes, 
                 room_id, household_id, is_catalog, created_by, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            RETURNING id
            """,
            title, description, recurrence_rule, estimated_minutes,
            room_id, household_id, is_catalog, created_by
        )
        
        # Récupérer la définition complète
        task_def = await conn.fetchrow(
            """
            SELECT id, title, description, recurrence_rule, estimated_minutes,
                   room_id, household_id, is_catalog, created_by, created_at
            FROM task_definitions
            WHERE id = $1
            """,
            task_def_id
        )
        
        return dict(task_def)


async def get_task_definitions(
    pool: asyncpg.Pool,
    household_id: Optional[UUID] = None,
    is_catalog: Optional[bool] = None,
    room_id: Optional[UUID] = None,
    created_by: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Récupérer les définitions de tâches selon les filtres.
    
    Args:
        pool: Pool de connexions
        household_id: Filtrer par ménage
        is_catalog: Filtrer par type (catalogue ou non)
        room_id: Filtrer par pièce
        created_by: Filtrer par créateur
    
    Returns:
        Liste des définitions de tâches
    """
    ensure_pool(pool)
    async with pool.acquire() as conn:
        # Construire la requête dynamiquement
        query = """
            SELECT td.*, r.name as room_name
            FROM task_definitions td
            LEFT JOIN rooms r ON td.room_id = r.id
            WHERE 1=1
        """
        params = []
        param_count = 0
        
        if household_id is not None:
            param_count += 1
            query += f" AND td.household_id = ${param_count}"
            params.append(household_id)
        
        if is_catalog is not None:
            param_count += 1
            query += f" AND td.is_catalog = ${param_count}"
            params.append(is_catalog)
        
        if room_id is not None:
            param_count += 1
            query += f" AND td.room_id = ${param_count}"
            params.append(room_id)
        
        if created_by is not None:
            param_count += 1
            query += f" AND td.created_by = ${param_count}"
            params.append(created_by)
        
        query += " ORDER BY td.title"
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]


async def get_task_definition(
    pool: asyncpg.Pool,
    task_def_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Récupérer une définition de tâche spécifique.
    
    Args:
        pool: Pool de connexions
        task_def_id: ID de la définition
    
    Returns:
        Dict avec les données ou None si non trouvée
    """
    ensure_pool(pool)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT td.*, r.name as room_name
            FROM task_definitions td
            LEFT JOIN rooms r ON td.room_id = r.id
            WHERE td.id = $1
            """,
            task_def_id
        )
        
        return dict(row) if row else None


async def update_task_definition(
    pool: asyncpg.Pool,
    task_def_id: UUID,
    **kwargs
) -> Dict[str, Any]:
    """
    Mettre à jour une définition de tâche.
    
    Args:
        pool: Pool de connexions
        task_def_id: ID de la définition
        **kwargs: Champs à mettre à jour
    
    Returns:
        Dict avec les données mises à jour
    """
    ensure_pool(pool)
    async with pool.acquire() as conn:
        # Construire la requête UPDATE dynamiquement
        update_fields = []
        params = [task_def_id]
        param_count = 1
        
        allowed_fields = ['title', 'description', 'recurrence_rule', 
                         'estimated_minutes', 'room_id']
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                param_count += 1
                update_fields.append(f"{field} = ${param_count}")
                params.append(value)
        
        if not update_fields:
            # Rien à mettre à jour
            return await get_task_definition(pool, task_def_id)
        
        query = f"""
            UPDATE task_definitions
            SET {', '.join(update_fields)}
            WHERE id = $1
            RETURNING *
        """
        
        row = await conn.fetchrow(query, *params)
        return dict(row) if row else None


async def delete_task_definition(
    pool: asyncpg.Pool,
    task_def_id: UUID
) -> bool:
    """
    Supprimer une définition de tâche.
    Note: Les occurrences liées seront supprimées en cascade.
    
    Args:
        pool: Pool de connexions
        task_def_id: ID de la définition
    
    Returns:
        True si supprimée, False sinon
    """
    ensure_pool(pool)
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM task_definitions WHERE id = $1",
            task_def_id
        )
        return "DELETE 1" in result


# ============================================================================
# TASK OCCURRENCES CRUD
# ============================================================================

async def create_task_occurrence(
    pool: asyncpg.Pool,
    task_id: UUID,
    scheduled_date: date,
    due_at: datetime,
    assigned_to: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Créer une nouvelle occurrence de tâche.
    
    Args:
        pool: Pool de connexions
        task_id: ID de la définition de tâche
        scheduled_date: Date prévue
        due_at: Date/heure d'échéance
        assigned_to: ID de l'utilisateur assigné
    
    Returns:
        Dict avec les données de l'occurrence créée
    """
    ensure_pool(pool)
    async with pool.acquire() as conn:
        try:
            occurrence_id = await conn.fetchval(
                """
                INSERT INTO task_occurrences 
                    (task_id, scheduled_date, due_at, status, assigned_to, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                RETURNING id
                """,
                task_id, scheduled_date, due_at, TaskStatus.PENDING.value, assigned_to
            )
            
            return await get_task_occurrence(pool, occurrence_id)
            
        except asyncpg.UniqueViolationError:
            # Une occurrence existe déjà pour cette tâche à cette date
            existing = await conn.fetchrow(
                """
                SELECT * FROM task_occurrences
                WHERE task_id = $1 AND scheduled_date = $2
                """,
                task_id, scheduled_date
            )
            return dict(existing) if existing else None


async def get_task_occurrences(
    pool: asyncpg.Pool,
    household_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[TaskStatus] = None,
    assigned_to: Optional[UUID] = None,
    room_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Récupérer les occurrences de tâches selon les filtres.
    
    Args:
        pool: Pool de connexions
        household_id: Filtrer par ménage
        start_date: Date de début
        end_date: Date de fin
        status: Filtrer par statut
        assigned_to: Filtrer par assignation
        room_id: Filtrer par pièce
    
    Returns:
        Liste des occurrences avec les infos de définition
    """
    ensure_pool(pool)
    async with pool.acquire() as conn:
        query = """
            SELECT 
                o.*,
                td.title as task_title,
                td.description as task_description,
                td.estimated_minutes,
                td.room_id,
                r.name as room_name,
                u.email as assigned_user_email
            FROM task_occurrences o
            JOIN task_definitions td ON o.task_id = td.id
            LEFT JOIN rooms r ON td.room_id = r.id
            LEFT JOIN auth.users u ON o.assigned_to = u.id
            WHERE 1=1
        """
        params = []
        param_count = 0
        
        if household_id is not None:
            param_count += 1
            query += f" AND td.household_id = ${param_count}"
            params.append(household_id)
        
        if start_date is not None:
            param_count += 1
            query += f" AND o.scheduled_date >= ${param_count}"
            params.append(start_date)
        
        if end_date is not None:
            param_count += 1
            query += f" AND o.scheduled_date <= ${param_count}"
            params.append(end_date)
        
        if status is not None:
            param_count += 1
            query += f" AND o.status = ${param_count}"
            params.append(status.value if hasattr(status, 'value') else status)
        
        if assigned_to is not None:
            param_count += 1
            query += f" AND o.assigned_to = ${param_count}"
            params.append(assigned_to)
        
        if room_id is not None:
            param_count += 1
            query += f" AND td.room_id = ${param_count}"
            params.append(room_id)
        
        query += " ORDER BY o.due_at"
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]


async def get_task_occurrence(
    pool: asyncpg.Pool,
    occurrence_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Récupérer une occurrence spécifique avec ses détails.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                o.*,
                td.title as task_title,
                td.description as task_description,
                td.estimated_minutes,
                td.room_id,
                td.household_id,
                r.name as room_name,
                u.email as assigned_user_email
            FROM task_occurrences o
            JOIN task_definitions td ON o.task_id = td.id
            LEFT JOIN rooms r ON td.room_id = r.id
            LEFT JOIN auth.users u ON o.assigned_to = u.id
            WHERE o.id = $1
            """,
            occurrence_id
        )
        
        return dict(row) if row else None


async def update_task_occurrence_status(
    pool: asyncpg.Pool,
    occurrence_id: UUID,
    status: TaskStatus,
    **kwargs
) -> Dict[str, Any]:
    """
    Mettre à jour le statut d'une occurrence.
    
    Args:
        pool: Pool de connexions
        occurrence_id: ID de l'occurrence
        status: Nouveau statut
        **kwargs: Champs additionnels (assigned_to, snoozed_until)
    
    Returns:
        Dict avec les données mises à jour
    """
    async with pool.acquire() as conn:
        # Construire la requête UPDATE
        update_fields = ["status = $2"]
        params = [occurrence_id, status.value]
        param_count = 2
        
        if 'assigned_to' in kwargs:
            param_count += 1
            update_fields.append(f"assigned_to = ${param_count}")
            params.append(kwargs['assigned_to'])
        
        if 'snoozed_until' in kwargs and status == TaskStatus.SNOOZED:
            param_count += 1
            update_fields.append(f"snoozed_until = ${param_count}")
            params.append(kwargs['snoozed_until'])
        elif status != TaskStatus.SNOOZED:
            # Effacer snoozed_until si le statut n'est pas SNOOZED
            update_fields.append("snoozed_until = NULL")
        
        query = f"""
            UPDATE task_occurrences
            SET {', '.join(update_fields)}
            WHERE id = $1
            RETURNING *
        """
        
        await conn.execute(query, *params)
        return await get_task_occurrence(pool, occurrence_id)


async def complete_task_occurrence(
    pool: asyncpg.Pool,
    occurrence_id: UUID,
    completed_by: UUID,
    duration_minutes: Optional[int] = None,
    comment: Optional[str] = None,
    photo_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Marquer une occurrence comme complétée et créer l'enregistrement de complétion.
    
    Args:
        pool: Pool de connexions
        occurrence_id: ID de l'occurrence
        completed_by: ID de l'utilisateur qui complète
        duration_minutes: Durée réelle en minutes
        comment: Commentaire optionnel
        photo_url: URL de photo optionnelle
    
    Returns:
        Dict avec les données de complétion
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Mettre à jour le statut de l'occurrence
            await conn.execute(
                """
                UPDATE task_occurrences
                SET status = $1
                WHERE id = $2
                """,
                TaskStatus.DONE.value, occurrence_id
            )
            
            # Créer l'enregistrement de complétion
            completion = await conn.fetchrow(
                """
                INSERT INTO task_completions
                    (occurrence_id, completed_by, completed_at, 
                     duration_minutes, comment, photo_url, created_at)
                VALUES ($1, $2, NOW(), $3, $4, $5, NOW())
                RETURNING *
                """,
                occurrence_id, completed_by, duration_minutes, comment, photo_url
            )
            
            return dict(completion)


# ============================================================================
# GÉNÉRATION D'OCCURRENCES
# ============================================================================

async def generate_occurrences_for_definition(
    pool: asyncpg.Pool,
    task_def_id: UUID,
    start_date: date,
    end_date: date,
    max_occurrences: int = 100
) -> List[Dict[str, Any]]:
    """
    Générer les occurrences pour une définition de tâche sur une période.
    
    Args:
        pool: Pool de connexions
        task_def_id: ID de la définition de tâche
        start_date: Date de début de génération
        end_date: Date de fin de génération
        max_occurrences: Nombre maximum d'occurrences à générer
    
    Returns:
        Liste des occurrences créées
    """
    async with pool.acquire() as conn:
        # Récupérer la définition
        task_def = await conn.fetchrow(
            "SELECT * FROM task_definitions WHERE id = $1",
            task_def_id
        )
        
        if not task_def:
            return []
        
        # Parser la règle de récurrence
        try:
            # Convertir les dates en datetime pour rrule
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            rrule = rrulestr(task_def['recurrence_rule'], dtstart=start_datetime)
        except Exception:
            # Si la règle est invalide, ne pas générer d'occurrences
            return []
        
        created_occurrences = []
        
        # Générer les dates selon la règle
        for occurrence_date in rrule.between(start_datetime, end_datetime, inc=True):
            if len(created_occurrences) >= max_occurrences:
                break
            
            scheduled_date = occurrence_date.date()
            
            # Calculer l'heure d'échéance (par défaut à 23:59)
            due_at = datetime.combine(scheduled_date, datetime.max.time())
            
            # Créer l'occurrence
            occurrence = await create_task_occurrence(
                pool, task_def_id, scheduled_date, due_at
            )
            
            if occurrence:
                created_occurrences.append(occurrence)
        
        return created_occurrences


async def generate_occurrences_for_household(
    pool: asyncpg.Pool,
    household_id: UUID,
    days_ahead: int = 30
) -> List[Dict[str, Any]]:
    """
    Générer les occurrences pour toutes les tâches d'un ménage.
    
    Args:
        pool: Pool de connexions
        household_id: ID du ménage
        days_ahead: Nombre de jours à générer dans le futur
    
    Returns:
        Liste de toutes les occurrences créées
    """
    start_date = date.today()
    end_date = start_date + timedelta(days=days_ahead)
    
    # Récupérer toutes les définitions actives du ménage
    task_defs = await get_task_definitions(pool, household_id=household_id)
    
    all_occurrences = []
    
    for task_def in task_defs:
        occurrences = await generate_occurrences_for_definition(
            pool, task_def['id'], start_date, end_date
        )
        all_occurrences.extend(occurrences)
    
    return all_occurrences


async def check_and_update_overdue_occurrences(
    pool: asyncpg.Pool,
    household_id: Optional[UUID] = None
) -> int:
    """
    Vérifier et mettre à jour les occurrences en retard.
    
    Args:
        pool: Pool de connexions
        household_id: Limiter à un ménage spécifique
    
    Returns:
        Nombre d'occurrences mises à jour
    """
    async with pool.acquire() as conn:
        query = """
            UPDATE task_occurrences o
            SET status = $1
            FROM task_definitions td
            WHERE o.task_id = td.id
              AND o.status = $2
              AND o.due_at < NOW()
        """
        params = [TaskStatus.OVERDUE.value, TaskStatus.PENDING.value]
        
        if household_id:
            query += " AND td.household_id = $3"
            params.append(household_id)
        
        result = await conn.execute(query, *params)
        
        # Extraire le nombre de lignes mises à jour
        count = int(result.split()[-1]) if result else 0
        return count


# ============================================================================
# FONCTIONS EXISTANTES (Households, Members, Rooms)
# ============================================================================

async def create_household(
    pool: asyncpg.Pool, 
    name: str, 
    created_by_user_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Créer un nouveau ménage"""
    async with pool.acquire() as conn:
        async with conn.transaction():
            household_id = await conn.fetchval(
                """
                INSERT INTO households (name, created_at) 
                VALUES ($1, NOW()) 
                RETURNING id
                """,
                name,
            )

            if created_by_user_id:
                # Supabase stocke les utilisateurs dans la table auth.users
                user_exists = await conn.fetchval(
                    "SELECT 1 FROM auth.users WHERE id = $1",
                    created_by_user_id,
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

            household_data = await conn.fetchrow(
                """
                SELECT id, name, created_at
                FROM households 
                WHERE id = $1
                """,
                household_id,
            )

            return dict(household_data)


async def get_households(
    pool: asyncpg.Pool, 
    user_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """Récupérer la liste des ménages"""
    async with pool.acquire() as conn:
        if user_id:
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
            households = await conn.fetch(
                """
                SELECT id, name, created_at
                FROM households
                ORDER BY name
                """
            )

        return [dict(household) for household in households]


async def get_household_members(
    pool: asyncpg.Pool, 
    household_id: UUID
) -> List[Dict[str, Any]]:
    """Récupérer tous les membres d'un ménage avec leurs détails utilisateur."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                hm.id, 
                hm.household_id, 
                hm.user_id, 
                hm.role, 
                hm.joined_at,
        COALESCE(u.raw_user_meta_data->>'full_name', u.email, '') AS user_full_name,
                u.email AS user_email
            FROM household_members hm
            JOIN auth.users u ON hm.user_id = u.id
            WHERE hm.household_id = $1
            """,
            household_id,
        )
        return [dict(row) for row in rows]


async def get_household_member(
    pool: asyncpg.Pool, 
    household_id: UUID, 
    member_id: UUID
) -> Optional[Dict[str, Any]]:
    """Récupérer un membre spécifique d'un ménage avec ses détails utilisateur."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT 
                hm.id, 
                hm.household_id, 
                hm.user_id, 
                hm.role, 
                hm.joined_at,
        COALESCE(u.raw_user_meta_data->>'full_name', u.email, '') AS user_full_name,
                u.email AS user_email
            FROM household_members hm
            JOIN auth.users u ON hm.user_id = u.id
            WHERE hm.household_id = $1 AND hm.id = $2
            """,
            household_id,
            member_id,
        )
        return dict(row) if row else None


async def create_household_member(
    pool: asyncpg.Pool, 
    household_id: UUID, 
    user_id: UUID, 
    role: str = "member"
) -> Dict[str, Any]:
    """Ajouter un membre à un ménage"""
    async with pool.acquire() as conn:
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

        member_id = await conn.fetchval(
            """
            INSERT INTO household_members (household_id, user_id, role, joined_at)
            VALUES ($1, $2, $3, NOW())
            RETURNING id
            """,
            household_id,
            user_id,
            role,
        )

        member_data = await conn.fetchrow(
            """
            SELECT id, household_id, user_id, role, joined_at
            FROM household_members
            WHERE id = $1
            """,
            member_id,
        )

        return dict(member_data)


async def update_household_member(
    pool: asyncpg.Pool, 
    household_id: UUID, 
    member_id: UUID, 
    role: str
) -> Dict[str, Any]:
    """Mettre à jour le rôle d'un membre"""
    async with pool.acquire() as conn:
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

        member_data = await conn.fetchrow(
            """
            SELECT id, household_id, user_id, role, joined_at
            FROM household_members
            WHERE id = $1
            """,
            member_id,
        )

        return dict(member_data)


async def delete_household_member(
    pool: asyncpg.Pool, 
    household_id: UUID, 
    member_id: UUID
) -> bool:
    """Supprimer un membre d'un ménage"""
    async with pool.acquire() as conn:
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

        rows_deleted = await conn.execute(
            """
            DELETE FROM household_members
            WHERE household_id = $1 AND id = $2
            """,
            household_id,
            member_id,
        )

        return "DELETE 1" in rows_deleted


async def get_rooms(
    pool: asyncpg.Pool, 
    household_id: UUID
) -> List[Dict[str, Any]]:
    """Récupérer la liste des pièces d'un ménage"""
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


async def get_room(
    pool: asyncpg.Pool, 
    room_id: UUID
) -> Optional[Dict[str, Any]]:
    """Récupérer une pièce spécifique"""
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
    pool: asyncpg.Pool, 
    name: str, 
    household_id: UUID, 
    icon: Optional[str] = None
) -> Dict[str, Any]:
    """Créer une nouvelle pièce"""
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


async def delete_room(
    pool: asyncpg.Pool,
    household_id: UUID,
    room_id: UUID,
) -> bool:
    """Supprimer une pièce d'un ménage.

    Retourne True si une ligne a été supprimée, False si la pièce n'existe pas
    (ou n'appartient pas au ménage donné).
    Peut lever asyncpg.ForeignKeyViolationError si des enregistrements référencent cette pièce
    (ex: task_definitions.room_id), auquel cas l'API doit retourner 409.
    """
    async with pool.acquire() as conn:
        # Vérifier l'existence et l'appartenance au ménage
        existing = await conn.fetchval(
            """
            SELECT 1 FROM rooms WHERE id = $1 AND household_id = $2
            """,
            room_id,
            household_id,
        )
        if not existing:
            return False

        result = await conn.execute(
            """
            DELETE FROM rooms
            WHERE id = $1 AND household_id = $2
            """,
            room_id,
            household_id,
        )
        return "DELETE 1" in result