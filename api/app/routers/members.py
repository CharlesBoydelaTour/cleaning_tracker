from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.member import HouseholdMemberCreate, HouseholdMember
from app.core.database import (
    get_household_members,
    get_household_member,
    create_household_member,
)
import asyncpg
from app.routers.households import get_db_pool, check_household_access
from typing import List
from uuid import UUID

router = APIRouter()


@router.get("/{household_id}/members", response_model=List[HouseholdMember])
async def list_household_members(
    household_id: UUID,
    user_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Récupère la liste des membres d'un ménage spécifique.
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

        members = await get_household_members(db_pool, household_id)
        return members
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des membres: {str(e)}",
        )


@router.get("/{household_id}/members/{member_id}", response_model=HouseholdMember)
async def get_household_member_details(
    household_id: UUID,
    member_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère les détails d'un membre spécifique d'un ménage.
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

        member = await get_household_member(db_pool, household_id, member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Membre non trouvé (ID: {member_id})",
            )

        return member
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du membre: {str(e)}",
        )


@router.post(
    "/{household_id}/members",
    response_model=HouseholdMember,
    status_code=status.HTTP_201_CREATED,
)
async def add_household_member(
    household_id: UUID,  # ID du ménage depuis le chemin de l'URL
    requesting_user_id: UUID,  # ID de l'utilisateur effectuant la requête (devrait venir de l'authentification)
    member_data: HouseholdMemberCreate,  # Données du membre à ajouter
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Ajoute un nouveau membre à un ménage.
    L'utilisateur spécifié par `requesting_user_id` (paramètre de requête) doit avoir les permissions
    nécessaires, sauf s'il s'ajoute lui-même comme premier administrateur.
    """
    try:
        # Cas spécial : si l'utilisateur (identifié par requesting_user_id)
        # s'ajoute lui-même (member_data.user_id) comme admin (member_data.role == "admin").
        # Cela est typiquement utilisé pour que le créateur du ménage s'ajoute comme premier admin.
        is_self_adding_as_admin = (
            requesting_user_id == member_data.user_id and member_data.role == "admin"
        )

        # Vérifier que l'utilisateur a accès à ce ménage,
        # SAUF s'il s'ajoute lui-même comme premier admin.
        if not is_self_adding_as_admin:
            has_access = await check_household_access(
                db_pool, household_id, requesting_user_id
            )
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas les permissions nécessaires pour ajouter un membre à ce ménage.",
                )
            # TODO: Si 'check_household_access' ne vérifie pas déjà que l'utilisateur est admin,
            # et que seuls les admins peuvent ajouter d'autres membres,
            # ajoutez ici une vérification du rôle de 'requesting_user_id' pour le 'household_id'.

        # Utiliser l'ID du ménage du chemin de l'URL pour la création
        # Le household_id dans member_data est maintenant optionnel et ignoré ici en faveur de celui du chemin.
        new_member = await create_household_member(
            db_pool, household_id, member_data.user_id, member_data.role
        )
        return new_member
    except (
        ValueError
    ) as e:  # Par exemple, si create_household_member lève une erreur pour un rôle invalide, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except (
        HTTPException
    ):  # Re-lever les HTTPException spécifiques (comme celles de la vérification d'accès)
        raise
    except (
        HTTPException
    ):  # Re-lever les HTTPException spécifiques (comme celles de la vérification d'accès)
        raise
    except Exception as e:
        # Pour les erreurs inattendues, loguer l'erreur côté serveur
        import traceback  # Ajoutez cette ligne

        print("--- TRACE D'ERREUR ORIGINELLE ---")  # Optionnel, pour mieux la repérer
        traceback.print_exc()  # Ajoutez cette ligne pour imprimer la stack trace complète
        # Vous pouvez toujours garder le logging si vous avez une configuration de logging plus avancée
        # import logging
        # logging.exception(f"Erreur inattendue lors de l'ajout du membre {member_data.user_id} au ménage {household_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue lors de l'ajout du membre.",
        )
