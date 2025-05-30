from fastapi import APIRouter, Depends
from app.schemas.auth import (
    UserSignup,
    UserLogin,
    AuthResponse,
    Token,
    RefreshToken,
    UserResponse,
)
from app.core.security import get_current_user
from app.services.auth_service import AuthService
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
    return await AuthService.request_password_reset(email)


@router.get("/verify-email/{email}")
async def verify_email_status(email: str):
    """Vérifier le statut de confirmation d'email"""
    is_confirmed = await AuthService.verify_email_confirmation(email)
    return {"email": email, "confirmed": is_confirmed}


@router.delete("/me", summary="Supprime le compte de l'utilisateur connecté")
async def delete_current_user(current_user=Depends(get_current_user)):
    """
    Supprime l'utilisateur en cours (self-delete).
    """
    # current_user peut être un dict ou un objet selon votre implémentation
    user_id = getattr(current_user, "id", None) or current_user.get("id")
    AuthService.delete_user(user_id)
    return {"message": "Utilisateur supprimé"}
