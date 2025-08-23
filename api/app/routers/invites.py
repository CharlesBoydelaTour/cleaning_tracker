from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
import asyncpg

from app.routers.households import get_db_pool, check_household_access, check_member_permissions
from app.core.security import get_current_user
from app.schemas.member import HouseholdMemberInvite
from app.services.invite_service import create_invite, dispatch_invite, get_invite_by_token, mark_invite_status
from app.core.database import create_household_member

router = APIRouter()


@router.post("/{household_id}/members/invite", status_code=201)
async def invite_member(
    household_id: UUID,
    payload: HouseholdMemberInvite,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    has_access = await check_household_access(db_pool, household_id, user_id)
    if not has_access:
        raise HTTPException(status_code=403, detail="Accès refusé")
    has_perm = await check_member_permissions(db_pool, household_id, user_id, "manage_members")
    if not has_perm:
        raise HTTPException(status_code=403, detail="Permission insuffisante")

    inv, created = await create_invite(db_pool, household_id, payload.email, payload.role, user_id)
    if created:
        login_link = await dispatch_invite(db_pool, inv)
        return {"status": "created", "login_link": login_link}
    else:
        # Invitation déjà en attente: ne pas renvoyer 500; indiquer l'état pour l'UI
        return {"status": "already_pending"}


# Acceptation: désormais via /invites/{invite_id}/accept (profil utilisateur)
