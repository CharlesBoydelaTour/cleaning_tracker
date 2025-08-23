from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from uuid import UUID
import asyncpg
from datetime import datetime, timezone

from app.routers.households import get_db_pool
from app.core.security import get_current_user
from app.services.invite_service import get_invite_by_token, mark_invite_status
from app.core.database import create_household_member

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_my_invites(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    email = (current_user.get("email") or "").lower()
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT hi.id, hi.household_id, h.name as household_name, hi.role,
                   hi.status, hi.expires_at, hi.created_at
            FROM household_invites hi
            JOIN households h ON h.id = hi.household_id
            WHERE lower(hi.email) = $1
              AND hi.status = 'pending'
              AND (hi.expires_at IS NULL OR hi.expires_at > now())
            ORDER BY hi.created_at DESC
            """,
            email,
        )
        return [dict(r) for r in rows]


@router.post("/{invite_id}/accept")
async def accept_my_invite(
    invite_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    # Charger l'invite par id
    async with db_pool.acquire() as conn:
        inv = await conn.fetchrow(
            """
            SELECT * FROM household_invites WHERE id = $1
            """,
            invite_id,
        )
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation introuvable")

    if inv["status"] != "pending":
        raise HTTPException(status_code=410, detail="Invitation non valide")
    if inv["email"].lower() != (current_user.get("email") or "").lower():
        raise HTTPException(status_code=403, detail="Cette invitation ne vous est pas destinée")
    expires_at = inv["expires_at"]
    if expires_at and expires_at < datetime.now(timezone.utc):
        await mark_invite_status(db_pool, inv["token"], "expired")
        raise HTTPException(status_code=410, detail="Invitation expirée")

    # Ajouter le membre (idempotent)
    try:
        await create_household_member(
            db_pool,
            household_id=inv["household_id"],
            user_id=current_user["id"],
            role=inv["role"] or "member",
        )
    except ValueError:
        pass

    await mark_invite_status(db_pool, inv["token"], "accepted")
    return {"status": "accepted"}


@router.post("/{invite_id}/decline")
async def decline_my_invite(
    invite_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
):
    async with db_pool.acquire() as conn:
        inv = await conn.fetchrow(
            """
            SELECT * FROM household_invites WHERE id = $1
            """,
            invite_id,
        )
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation introuvable")
    if inv["email"].lower() != (current_user.get("email") or "").lower():
        raise HTTPException(status_code=403, detail="Cette invitation ne vous est pas destinée")

    await mark_invite_status(db_pool, inv["token"], "revoked")
    return {"status": "revoked"}
