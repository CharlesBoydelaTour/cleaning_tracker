from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.schemas.household import HouseholdCreate, Household
from app.core.database import get_households, create_household
import asyncpg
from uuid import UUID

router = APIRouter()


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Récupère le pool de connexions à la DB depuis l'état de l'application."""
    return request.app.state.db_pool


@router.get("/", response_model=list[Household])
async def list_households(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère la liste des ménages.

    Si un user_id est fourni, ne récupère que les ménages de cet utilisateur.
    """
    try:
        households = await get_households(db_pool, user_id)
        return households
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des ménages: {str(e)}",
        )


@router.post("/", response_model=Household, status_code=status.HTTP_201_CREATED)
async def create_new_household(
    household: HouseholdCreate,
    requesting_user_id: UUID,  # ID de l'utilisateur créant le ménage (devrait venir de l'authentification)
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Crée un nouveau ménage et ajoute l'utilisateur créateur comme administrateur.
    """
    try:
        # Le user_id est maintenant obligatoire et passé à create_household
        new_household = await create_household(
            db_pool, household.name, requesting_user_id
        )
        return new_household
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du ménage: {str(e)}",
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
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce ménage",
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
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ménage non trouvé (ID: {household_id})",
                )

            return dict(household_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du ménage: {str(e)}",
        )


async def check_household_access(
    pool: asyncpg.Pool, household_id: UUID, user_id: str
) -> bool:
    """
    Vérifie si un utilisateur a accès à un ménage.
    """
    async with pool.acquire() as conn:
        member = await conn.fetchval(
            """
            SELECT id
            FROM household_members
            WHERE household_id = $1 AND user_id = $2
            """,
            household_id,
            user_id,
        )
        return member is not None
