from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.member import HouseholdMemberCreate, HouseholdMember, HouseholdMemberUpdate, HouseholdMemberInvite
from app.services.member_service import invite_member_to_household # Assurez-vous d\'avoir cette fonction de service
from app.core.database import (
    get_household_members,
    get_household_member,
    create_household_member,
    update_household_member,
    delete_household_member,
)
import asyncpg
from app.routers.households import get_db_pool, check_household_access, check_member_permissions
from app.core.security import get_current_user
from typing import List
from uuid import UUID

router = APIRouter()


@router.get("/{household_id}/members", response_model=List[HouseholdMember])
async def list_household_members(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère la liste des membres d'un ménage spécifique.
    """
    try:
        user_id = current_user["id"]
        
        # Vérifier que l'utilisateur a accès à ce ménage
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
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère les détails d'un membre spécifique d'un ménage.
    """
    try:
        user_id = current_user["id"]
        
        # Vérifier que l'utilisateur a accès à ce ménage
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
            
            # Vérifier que l'utilisateur a les permissions pour ajouter des membres
            has_permission = await check_member_permissions(
                db_pool, household_id, requesting_user_id, "add_members"
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas les permissions nécessaires pour ajouter un membre à ce ménage.",
                )

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
    except Exception:
        # Pour les erreurs inattendues, loguer l'erreur côté serveur
        import traceback  # Ajoutez cette ligne

        print("--- TRACE D'ERREUR ORIGINELLE ---")  # Optionnel, pour mieux la repérer
        traceback.print_exc()  # Ajoutez cette ligne pour imprimer la stack trace complète
        # Vous pouvez toujours garder le logging si vous avez une configuration de logging plus avancée
        # import logging
        # logging.exception(f\"Erreur inattendue lors de l\'ajout du membre {member_data.user_id} au ménage {household_id}: {e}\")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue lors de l'ajout du membre.",
        )


@router.post("/{household_id}/members/invite", response_model=HouseholdMember, status_code=status.HTTP_201_CREATED)
async def invite_household_member(
    household_id: UUID,
    invite_data: HouseholdMemberInvite,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    """
    Invite un nouvel utilisateur à rejoindre un ménage par email.
    L'utilisateur effectuant la requête doit avoir les permissions de gérer les membres.
    """
    try:
        requesting_user_id = current_user["id"]

        # Vérifier que l'utilisateur a accès à ce ménage
        has_access = await check_household_access(db_pool, household_id, requesting_user_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce ménage pour inviter des membres.",
            )

        # Vérifier que l'utilisateur a les permissions pour gérer les membres (ou une permission spécifique "invite_members")
        # Pour l'instant, nous utilisons "manage_members"
        has_permission = await check_member_permissions(
            db_pool, household_id, requesting_user_id, "manage_members" 
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les permissions nécessaires pour inviter des membres dans ce ménage.",
            )

        # Appeler le service pour gérer l'invitation
        # Cette fonction devra être implémentée dans app.services.member_service
        # Elle devrait gérer la création de l'utilisateur s'il n'existe pas,
        # l'ajout à household_members, et potentiellement l'envoi d'un email d'invitation.
        invited_member = await invite_member_to_household(
            db_pool,
            household_id,
            invite_data.email,
            invite_data.role,
            requesting_user_id  # L'ID de l'utilisateur qui invite
        )
        
        if not invited_member: # Cas où le service ne retourne rien (erreur gérée en interne ou utilisateur déjà membre)
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Ou un autre code approprié
                detail="Impossible d'inviter l'utilisateur. Il est peut-être déjà membre ou une erreur est survenue."
            )

        return invited_member
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue lors de l'invitation du membre: {str(e)}",
        )


@router.put("/{household_id}/members/{member_id}", response_model=HouseholdMember)
async def update_household_member_endpoint(
    household_id: UUID,
    member_id: UUID,
    requesting_user_id: UUID,  # ID de l'utilisateur effectuant la requête
    member_update: HouseholdMemberUpdate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Met à jour un membre d'un ménage (généralement son rôle).
    L'utilisateur doit avoir les permissions nécessaires pour gérer les membres.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        has_access = await check_household_access(db_pool, household_id, requesting_user_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce ménage",
            )

        # Vérifier que l'utilisateur a les permissions pour gérer les membres
        has_permission = await check_member_permissions(
            db_pool, household_id, requesting_user_id, "manage_members"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les permissions nécessaires pour modifier un membre de ce ménage.",
            )

        # Vérifier que le membre existe dans ce ménage
        existing_member = await get_household_member(db_pool, household_id, member_id)
        if not existing_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Membre non trouvé (ID: {member_id})",
            )

        # Mettre à jour le membre (actuellement seul le rôle peut être mis à jour)
        if member_update.role is not None:
            updated_member = await update_household_member(
                db_pool, household_id, member_id, member_update.role
            )
            return updated_member
        else:
            # Si aucune modification n'est demandée, retourner le membre existant
            return existing_member

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du membre: {str(e)}",
        )


@router.delete("/{household_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_household_member_endpoint(
    household_id: UUID,
    member_id: UUID,
    requesting_user_id: UUID,  # ID de l'utilisateur effectuant la requête
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Supprime un membre d'un ménage.
    L'utilisateur doit avoir les permissions nécessaires pour supprimer des membres.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        has_access = await check_household_access(db_pool, household_id, requesting_user_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce ménage",
            )

        # Vérifier que l'utilisateur a les permissions pour supprimer des membres
        has_permission = await check_member_permissions(
            db_pool, household_id, requesting_user_id, "delete_members"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les permissions nécessaires pour supprimer un membre de ce ménage.",
            )

        # Vérifier que le membre existe dans ce ménage
        existing_member = await get_household_member(db_pool, household_id, member_id)
        if not existing_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Membre non trouvé (ID: {member_id})",
            )

        # Supprimer le membre
        success = await delete_household_member(db_pool, household_id, member_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Membre non trouvé (ID: {member_id})",
            )

        # HTTP 204 No Content - pas de corps de réponse

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du membre: {str(e)}",
        )
