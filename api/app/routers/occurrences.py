from fastapi import APIRouter, Depends, status
from app.schemas.task import Occurrence
from app.core.exceptions import (
    DatabaseError,
    UnauthorizedAccess,
    OccurrenceNotFound,
    TaskNotFound,
)
from app.routers.households import get_db_pool, check_household_access
import asyncpg
from uuid import UUID
from typing import List

router = APIRouter()


@router.get("/{household_id}/occurrences", response_model=List[Occurrence])
async def list_occurrences(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère la liste des occurrences d'un ménage spécifique.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise UnauthorizedAccess(
                    resource="ménage",
                    resource_id=str(household_id),
                    user_id=str(user_id),
                )

        # TODO: récupérer les occurrences depuis la base de données
        # Pour l'instant, retournons une liste vide
        return []
    except (UnauthorizedAccess,):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération des occurrences",
            details=str(e),
        )


@router.get("/{household_id}/occurrences/{occurrence_id}", response_model=Occurrence)
async def get_occurrence_details(
    household_id: UUID,
    occurrence_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère les détails d'une occurrence spécifique.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise UnauthorizedAccess(
                    resource="ménage",
                    resource_id=str(household_id),
                    user_id=str(user_id),
                )

        # TODO: récupérer l'occurrence depuis la base de données
        # Pour l'instant, lever une exception NotFound
        raise OccurrenceNotFound(occurrence_id=str(occurrence_id))

    except (UnauthorizedAccess, OccurrenceNotFound):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération de l'occurrence",
            details=str(e),
        )
