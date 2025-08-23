from fastapi import APIRouter, Depends, Request, status, HTTPException
from app.schemas.household import HouseholdCreate, Household
from app.core.database import get_households, create_household
from app.core.exceptions import DatabaseError, UnauthorizedAccess, HouseholdNotFound
from app.core.security import get_current_user
import asyncpg
from uuid import UUID
from app.schemas.auth import UserResponse

router = APIRouter()


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Récupère le pool de connexions à la DB depuis l'état de l'application."""
    return request.app.state.db_pool


@router.get("/", response_model=list[Household])
async def list_households(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère la liste des ménages de l'utilisateur authentifié.
    """
    try:
        user_id = current_user["id"]
        households = await get_households(db_pool, user_id)
        return households
    except Exception as e:
        raise DatabaseError(
            operation="récupération des ménages",
            details=str(e),
        )


@router.post("/", response_model=Household, status_code=status.HTTP_201_CREATED)
async def create_new_household(
    household: HouseholdCreate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    """
    Crée un nouveau ménage et ajoute l'utilisateur créateur comme administrateur.
    """
    try:
        requesting_user_id = current_user["id"]
        # Le user_id est maintenant obligatoire et passé à create_household
        new_household = await create_household(
            db_pool, household.name, requesting_user_id
        )
        return new_household
    except Exception as e:
        raise DatabaseError(
            operation="création du ménage",
            details=str(e),
        )


@router.get("/{household_id}", response_model=Household)
async def get_household(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère les détails d'un ménage spécifique.
    """
    try:
        # Vérifier d'abord si l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise UnauthorizedAccess(
                    resource="ménage",
                    action="read",  # MODIFIED: Added missing 'action' argument
                )

        # Récupérer les détails du ménage
        async with db_pool.acquire() as conn:
            household_data = await conn.fetchrow(
                """
                SELECT id, name, created_at
                FROM households
                WHERE id = $1
                """,
                household_id,
            )

            if not household_data:
                raise HouseholdNotFound(household_id=str(household_id))

            return dict(household_data)
    except (UnauthorizedAccess, HouseholdNotFound):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération du ménage",
            details=str(e),
        )


@router.post("/{household_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_household(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    """
    Permet à l'utilisateur courant de quitter un foyer.
    Si le foyer devient vide, il est supprimé (cascade sur les entités liées).
    """
    user_id = current_user["id"]
    async with db_pool.acquire() as conn:
        tr = conn.transaction()
        await tr.start()
        try:
            # Vérifier que l'utilisateur est bien membre
            member_id = await conn.fetchval(
                """
                SELECT id FROM household_members
                WHERE household_id = $1 AND user_id = $2
                """,
                household_id,
                user_id,
            )
            if not member_id:
                raise HTTPException(status_code=404, detail="Vous n'êtes pas membre de ce foyer")

            # Supprimer son appartenance
            await conn.execute(
                """
                DELETE FROM household_members
                WHERE household_id = $1 AND user_id = $2
                """,
                household_id,
                user_id,
            )

            # Vérifier si le foyer est vide
            remaining = await conn.fetchval(
                """
                SELECT count(*)::int FROM household_members WHERE household_id = $1
                """,
                household_id,
            )
            if remaining == 0:
                await conn.execute(
                    """
                    DELETE FROM households WHERE id = $1
                    """,
                    household_id,
                )

            await tr.commit()
        except Exception:
            await tr.rollback()
            raise
    # 204 No Content
    return


@router.delete("/{household_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_household_endpoint(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    """
    Supprime un foyer et toutes ses données liées (cascade). Réservé aux administrateurs du foyer.
    """
    user_id = current_user["id"]
    # Vérifier le rôle
    role = await get_user_role_in_household(db_pool, household_id, user_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Seul un administrateur peut supprimer ce foyer")

    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM households WHERE id = $1
            """,
            household_id,
        )
        # result est de type 'DELETE X'
        if not result or result.split()[-1] == '0':
            raise HTTPException(status_code=404, detail="Foyer introuvable")
    return


async def check_household_access(
    pool: asyncpg.Pool, household_id: UUID, user_id: str
) -> bool:
    """
    Vérifie si un utilisateur a accès à un ménage.
    """
    # Convertir user_id de string vers UUID si nécessaire
    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    except ValueError:
        return False
        
    async with pool.acquire() as conn:
        member = await conn.fetchval(
            """
            SELECT id
            FROM household_members
            WHERE household_id = $1 AND user_id = $2
            """,
            household_id,
            user_uuid,
        )
        return member is not None


async def get_user_role_in_household(
    pool: asyncpg.Pool, household_id: UUID, user_id: UUID
) -> str:
    """
    Récupère le rôle d'un utilisateur dans un ménage.

    Returns:
        Le rôle de l'utilisateur ('admin', 'member', 'guest') ou None s'il n'est pas membre
    """
    async with pool.acquire() as conn:
        role = await conn.fetchval(
            """
            SELECT role
            FROM household_members
            WHERE household_id = $1 AND user_id = $2
            """,
            household_id,
            user_id,
        )
        return role


async def check_member_permissions(
    pool: asyncpg.Pool, household_id: UUID, user_id: UUID, required_permission: str
) -> bool:
    """
    Vérifie si un utilisateur a les permissions requises dans un ménage.

    Args:
        pool: Pool de connexions à la base de données
        household_id: ID du ménage
        user_id: ID de l'utilisateur
        required_permission: Permission requise ('add_members', 'manage_members', etc.)

    Returns:
        True si l'utilisateur a les permissions, False sinon
    """
    user_role = await get_user_role_in_household(pool, household_id, user_id)

    if not user_role:
        return False

    # Définir les permissions par rôle
    permissions = {
        "admin": ["add_members", "manage_members", "delete_members"],
        "member": [],  # Les membres ordinaires ne peuvent pas ajouter d'autres membres
        "guest": [],  # Les invités ne peuvent rien faire
    }

    return required_permission in permissions.get(user_role, [])
