from fastapi import APIRouter, Depends, status  # Ajout de status
from app.schemas.auth import (
    UserSignup,
    UserLogin,
    AuthResponse,
    Token,
    RefreshToken,
    UserResponse,
)
from fastapi import HTTPException
from app.core.security import get_current_user
from app.services.auth_service import AuthService
from app.core.exceptions import InvalidInput
from app.core.supabase_client import supabase_admin # Assurez-vous que supabase_admin est importé
from fastapi.responses import Response
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: UserSignup):
    """Inscription d'un nouvel utilisateur"""
    return await AuthService.signup_user(user_data)


@router.post("/login", response_model=AuthResponse)
async def login(user_credentials: UserLogin):
    """Connexion d'un utilisateur"""
    return await AuthService.login_user(user_credentials)


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_data: RefreshToken):
    """Renouveler le token d'accès"""
    return await AuthService.refresh_tokens(refresh_data.refresh_token)


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Déconnexion de l'utilisateur"""
    return await AuthService.logout_user()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Obtenir les informations de l'utilisateur courant"""
    return await AuthService.get_user_profile(current_user)


@router.post("/reset-password")
async def request_password_reset(email: str):
    """Demander une réinitialisation de mot de passe"""
    if not email or not email.strip():
        raise InvalidInput(
            field="email",
            value=email,
            reason="L'adresse email est requise",
        )
    return await AuthService.request_password_reset(email)


@router.get("/verify-email/{email}")
async def verify_email_status(email: str):
    """Vérifier le statut de confirmation d'email"""
    is_confirmed = await AuthService.verify_email_confirmation(email)
    return {"email": email, "confirmed": is_confirmed}


@router.post("/resend-verification-email", status_code=status.HTTP_200_OK)
async def resend_verification_email_endpoint(email: str):
    """
    Renvoyer l'e-mail de vérification à l'utilisateur.
    """
    if not email or not email.strip():
        raise InvalidInput(
            field="email",
            reason="L'adresse email est requise",  # Corrigé: message -> reason
            value=email,  # Corrigé: received_value -> value
        )
    return await AuthService.resend_verification_email(email)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Supprimer le compte de l'utilisateur actuellement authentifié.
    """
    user_id_to_delete = current_user.get("id")
    if not user_id_to_delete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Impossible de récupérer l'ID de l'utilisateur."
        )

    # La méthode delete_user lève maintenant des HTTPException directement
    await AuthService.delete_user(user_id_to_delete, supabase_admin)
