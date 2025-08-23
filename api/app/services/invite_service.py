import asyncpg
from asyncpg import exceptions as pgex
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from app.config import settings
from app.core.supabase_client import supabase_admin, supabase


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


async def create_invite(
    pool: asyncpg.Pool,
    household_id: UUID,
    email: str,
    role: str,
    invited_by: UUID,
    expires_in_days: int = 7,
) -> tuple[Dict[str, Any], bool]:
    """Crée une invitation si aucune en attente n'existe déjà.

    Retourne (invite_dict, created_bool). Si une invitation 'pending' existe déjà
    pour (household_id,email), elle est retournée avec created=False.
    """
    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    async with pool.acquire() as conn:
        try:
            invite_id = await conn.fetchval(
                """
                INSERT INTO household_invites (household_id, email, role, invited_by, token, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                household_id,
                email,
                role,
                invited_by,
                token,
                expires_at,
            )
            row = await conn.fetchrow(
                """
                SELECT * FROM household_invites WHERE id = $1
                """,
                invite_id,
            )
            return dict(row), True
        except pgex.UniqueViolationError:
            # Une invitation pending existe déjà pour ce couple (household_id,email)
            row = await conn.fetchrow(
                """
                SELECT * FROM household_invites
                WHERE household_id = $1 AND email = $2 AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                household_id,
                email,
            )
            if row:
                return dict(row), False
            raise


async def mark_invite_status(
    pool: asyncpg.Pool, token: str, status: str
) -> Optional[Dict[str, Any]]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE household_invites
            SET status = $1::public.invite_status,
                accepted_at = CASE WHEN $1::public.invite_status = 'accepted'::public.invite_status THEN NOW() ELSE accepted_at END
            WHERE token = $2
            RETURNING *
            """,
            status,
            token,
        )
        return dict(row) if row else None


async def get_invite_by_token(pool: asyncpg.Pool, token: str) -> Optional[Dict[str, Any]]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM household_invites WHERE token = $1
            """,
            token,
        )
        return dict(row) if row else None


# Plus d'envoi SMTP: on s'appuie sur Supabase pour envoyer les emails


async def dispatch_invite(
    pool: asyncpg.Pool,
    invite: Dict[str, Any],
) -> Optional[str]:
    """Envoi d'email selon existence du compte Supabase.

    - Si l'utilisateur existe, on peut générer un magic link avec redirect vers /accept-invite
    - Sinon, on utilise inviteUserByEmail avec redirect vers /accept-invite
    """
    if supabase_admin is None:
        # Pas d'admin: tenter un envoi d'OTP/magic link via client public (si l'email existe déjà), sinon fallback redirect URL
        redirect_to = f"{settings.app_url}/accept-invite?token={invite['token']}&hid={invite['household_id']}"
        try:
            supabase.auth.sign_in_with_otp({
                "email": invite["email"],
                "options": {"email_redirect_to": redirect_to},
            })
            return redirect_to
        except Exception as _:
            # Fallback: aucun envoi possible sans admin si l'utilisateur n'existe pas
            return redirect_to

    # Vérifier si le compte existe
    try:
        # list_users ne filtre pas toujours par email selon SDK; on peut paginer ou filtrer côté client
        user_resp = supabase_admin.auth.admin.list_users()
        user_exists = any(getattr(u, "email", None) == invite["email"] for u in user_resp.users)
    except Exception:
        user_exists = False

    redirect_to = f"{settings.app_url}/accept-invite?token={invite['token']}&hid={invite['household_id']}"

    try:
        if user_exists:
            # Utiliser Supabase pour ENVOYER le magic link (et non juste le générer)
            supabase.auth.sign_in_with_otp({
                "email": invite["email"],
                "options": {"email_redirect_to": redirect_to},
            })
            return redirect_to
        else:
            # Certaines versions du SDK attendent redirect_to (sans data)
            supabase_admin.auth.admin.invite_user_by_email(
                invite["email"],
                redirect_to=redirect_to,
            )
            return None
    except Exception as e:
        print(f"[invite] Erreur envoi: {e}")
        return None
