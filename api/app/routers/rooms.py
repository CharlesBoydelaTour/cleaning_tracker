from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.room import RoomCreate, Room
from app.core.database import (
    get_rooms,
    get_room,
    create_room,
)
import asyncpg
from app.routers.households import get_db_pool, check_household_access
from typing import List
from uuid import UUID

router = APIRouter()


@router.get("/{household_id}/rooms", response_model=List[Room])
async def list_rooms(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère la liste des pièces d'un ménage spécifique.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce ménage",
                )

        rooms = await get_rooms(db_pool, household_id)
        return rooms
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des pièces: {str(e)}",
        )


@router.get("/{household_id}/rooms/{room_id}", response_model=Room)
async def get_room_details(
    household_id: UUID,
    room_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère les détails d'une pièce spécifique.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce ménage",
                )

        room = await get_room(db_pool, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pièce non trouvée (ID: {room_id})",
            )

        # Vérifier que la pièce appartient bien au ménage spécifié
        if room["household_id"] != household_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pièce non trouvée dans ce ménage (ID: {room_id})",
            )

        return room
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de la pièce: {str(e)}",
        )


@router.post(
    "/{household_id}/rooms", response_model=Room, status_code=status.HTTP_201_CREATED
)
async def add_room(
    household_id: UUID,
    room: RoomCreate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Ajoute une nouvelle pièce à un ménage.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce ménage",
                )

        new_room = await create_room(db_pool, room.name, household_id, room.icon)
        return new_room
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la pièce: {str(e)}",
        )
