from typing import Dict, Any
from fastapi import HTTPException, status
from app.core.supabase_client import supabase
from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth import UserSignup, UserLogin, AuthResponse, UserResponse, Token
from app.core.supabase_client import supabase_admin
from app.core.logging import get_logger, with_context
from gotrue.errors import AuthApiError

logger = get_logger(__name__)


class AuthService:
    """Service gérant l'authentification des utilisateurs avec Supabase"""

    @staticmethod
    async def signup_user(user_data: UserSignup) -> AuthResponse:
        """
        Créer un nouveau compte utilisateur

        Args:
            user_data: Données d'inscription

        Returns:
            AuthResponse: Réponse avec utilisateur et tokens

        Raises:
            HTTPException: Si l'inscription échoue
        """

        logger.info(
            "Tentative d'inscription d'un nouvel utilisateur",
            extra=with_context(email=user_data.email),
        )

        try:
            # Créer l'utilisateur avec Supabase Auth
            response = supabase.auth.sign_up(
                {
                    "email": user_data.email,
                    "password": user_data.password,
                    "options": {"data": {"full_name": user_data.full_name}},
                }
            )

            if response.user is None:
                logger.error(
                    "Échec de l'inscription de l'utilisateur",
                    extra=with_context(email=user_data.email),
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Erreur lors de la création du compte. Email peut-être déjà utilisé.",
                )

            user = response.user

            logger.info(
                "Utilisateur créé avec succès dans Supabase Auth",
                extra=with_context(user_id=user.id, email=user.email),
            )

            # Créer nos propres tokens JWT
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email}
            )
            refresh_token = create_refresh_token(
                data={"sub": user.id, "email": user.email}
            )

            return AuthResponse(
                user=UserResponse(
                    id=user.id,
                    email=user.email,
                    full_name=user.user_metadata.get("full_name"),
                    email_confirmed_at=user.email_confirmed_at,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                ),
                tokens=Token(access_token=access_token, refresh_token=refresh_token),
            )

        except Exception as e:
            logger.error(
                "Erreur inattendue lors de l'inscription",
                extra=with_context(email=user_data.email, error_type=type(e).__name__),
                exc_info=True,
            )
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors de l'inscription: {str(e)}",
            )

    @staticmethod
    async def login_user(user_credentials: UserLogin) -> AuthResponse:
        """
        Connecter un utilisateur

        Args:
            user_credentials: Identifiants de connexion

        Returns:
            AuthResponse: Réponse avec utilisateur et tokens

        Raises:
            HTTPException: Si la connexion échoue
        """

        logger.info(
            "Tentative de connexion", extra=with_context(email=user_credentials.email)
        )

        try:
            # Authentifier avec Supabase
            response = supabase.auth.sign_in_with_password(
                {"email": user_credentials.email, "password": user_credentials.password}
            )

            if response.user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou mot de passe incorrect",
                )

            user = response.user
            logger.info(
                "Connexion réussie",
                extra=with_context(user_id=user.id, email=user.email),
            )
            # Créer nos propres tokens JWT
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email}
            )
            refresh_token = create_refresh_token(
                data={"sub": user.id, "email": user.email}
            )

            return AuthResponse(
                user=UserResponse(
                    id=user.id,
                    email=user.email,
                    full_name=user.user_metadata.get("full_name"),
                    email_confirmed_at=user.email_confirmed_at,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                ),
                tokens=Token(access_token=access_token, refresh_token=refresh_token),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.warning(
                "Erreur inattendue lors de la connexion",
                extra=with_context(
                    email=user_credentials.email, error_type=type(e).__name__
                ),
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect",
            )

    @staticmethod
    async def refresh_tokens(refresh_token: str) -> Token:
        """
        Renouveler les tokens d'accès

        Args:
            refresh_token: Token de rafraîchissement

        Returns:
            Token: Nouveaux tokens

        Raises:
            HTTPException: Si le token est invalide
        """
        try:
            from app.core.security import verify_token

            # Vérifier le refresh token
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            email = payload.get("email")
            logger.info(
                "Renouvellement des tokens",
                extra=with_context(user_id=user_id, email=email),
            )
            if user_id is None or email is None:
                logger.error(
                    "Token de rafraîchissement invalide",
                    extra=with_context(refresh_token=refresh_token),
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token de rafraîchissement invalide",
                )

            # Créer un nouveau token d'accès
            access_token = create_access_token(data={"sub": user_id, "email": email})
            logger.info(
                "Nouveau token d'accès créé",
                extra=with_context(user_id=user_id, email=email),
            )
            return Token(access_token=access_token, refresh_token=refresh_token)

        except Exception as e:
            logger.error(
                "Erreur lors du renouvellement des tokens",
                extra=with_context(
                    refresh_token=refresh_token, error_type=type(e).__name__
                ),
                exc_info=True,
            )
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de rafraîchissement invalide",
            )

    @staticmethod
    async def logout_user() -> Dict[str, str]:
        """
        Déconnecter l'utilisateur

        Returns:
            Dict: Message de confirmation
        """
        try:
            # Déconnecter de Supabase
            logger.info("Tentative de déconnexion de l'utilisateur")
            supabase.auth.sign_out()
            return {"message": "Déconnexion réussie"}
        except Exception as e:
            logger.error(
                "Erreur lors de la déconnexion de l'utilisateur",
                extra=with_context(error_type=type(e).__name__),
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors de la déconnexion: {str(e)}",
            )

    @staticmethod
    async def get_user_profile(user: Any) -> UserResponse:
        """
        Obtenir le profil utilisateur

        Args:
            user: Utilisateur courant (dict avec id et email depuis JWT)

        Returns:
            UserResponse: Profil utilisateur complet
        """
        try:
            from app.core.supabase_client import supabase_admin

            logger.info(
                "Récupération du profil utilisateur",
                extra=with_context(
                    user_id=user["id"] if isinstance(user, dict) else user.id
                ),
            )
            # Récupérer les données complètes de l'utilisateur depuis Supabase
            user_id = user["id"] if isinstance(user, dict) else user.id

            # Utiliser l'admin client pour récupérer les données utilisateur
            user_response = supabase_admin.auth.admin.get_user_by_id(user_id)

            if not user_response.user:
                logger.error(
                    "Utilisateur non trouvé",
                    extra=with_context(user_id=user_id),
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé",
                )

            supabase_user = user_response.user

            # Convertir les chaînes de date en objets datetime si nécessaire
            email_confirmed_at = None
            if supabase_user.email_confirmed_at:
                if isinstance(supabase_user.email_confirmed_at, str):
                    from datetime import datetime

                    email_confirmed_at = datetime.fromisoformat(
                        supabase_user.email_confirmed_at.replace("Z", "+00:00")
                    )
                else:
                    email_confirmed_at = supabase_user.email_confirmed_at

            created_at = None
            if supabase_user.created_at:
                if isinstance(supabase_user.created_at, str):
                    from datetime import datetime

                    created_at = datetime.fromisoformat(
                        supabase_user.created_at.replace("Z", "+00:00")
                    )
                else:
                    created_at = supabase_user.created_at

            updated_at = None
            if supabase_user.updated_at:
                if isinstance(supabase_user.updated_at, str):
                    from datetime import datetime

                    updated_at = datetime.fromisoformat(
                        supabase_user.updated_at.replace("Z", "+00:00")
                    )
                else:
                    updated_at = supabase_user.updated_at
            logger.info(
                "Profil utilisateur récupéré avec succès",
                extra=with_context(user_id=supabase_user.id, email=supabase_user.email),
            )
            return UserResponse(
                id=supabase_user.id,
                email=supabase_user.email,
                full_name=(
                    supabase_user.user_metadata.get("full_name")
                    if supabase_user.user_metadata
                    else None
                ),
                email_confirmed_at=email_confirmed_at,
                created_at=created_at,
                updated_at=updated_at,
            )

        except Exception as e:
            logger.error(
                "Erreur lors de la récupération du profil utilisateur",
                extra=with_context(
                    user_id=user["id"] if isinstance(user, dict) else user.id,
                    error_type=type(e).__name__,
                ),
                exc_info=True,
            )
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la récupération du profil: {str(e)}",
            )

    @staticmethod
    async def verify_email_confirmation(email: str) -> bool:
        """
        Vérifier si l'email est confirmé

        Args:
            email: Email à vérifier

        Returns:
            bool: True si confirmé
        """
        try:
            logger.info(
                "Vérification de la confirmation de l'email",
                extra=with_context(email=email),
            )
            # Ici on pourrait ajouter une logique pour vérifier
            # le statut de confirmation email via Supabase
            response = supabase.auth.get_user()
            if response.user and response.user.email == email:
                logger.info(
                    "Email confirmé",
                    extra=with_context(
                        email=email, confirmed=response.user.email_confirmed_at
                    ),
                )
                return response.user.email_confirmed_at is not None
            return False
        except Exception:
            logger.error(
                "Erreur lors de la vérification de la confirmation de l'email",
                extra=with_context(email=email),
                exc_info=True,
            )
            return False

    @staticmethod
    async def request_password_reset(email: str) -> Dict[str, str]:
        """
        Demander une réinitialisation de mot de passe

        Args:
            email: Email pour la réinitialisation

        Returns:
            Dict: Message de confirmation
        """
        try:
            logger.info(
                "Demande de réinitialisation de mot de passe",
                extra=with_context(email=email),
            )
            supabase.auth.reset_password_email(email)
            return {"message": "Email de réinitialisation envoyé"}
        except Exception as e:
            logger.error(
                "Erreur lors de l'envoi de l'email de réinitialisation",
                extra=with_context(email=email, error_type=type(e).__name__),
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors de l'envoi de l'email: {str(e)}",
            )

    @staticmethod
    async def resend_verification_email(email: str) -> Dict[str, str]:
        """
        Renvoyer l'e-mail de vérification à l'utilisateur.

        Args:
            email: L'adresse e-mail de l'utilisateur.

        Returns:
            Dict: Message de confirmation.

        Raises:
            HTTPException: Si l'envoi de l'e-mail échoue.
        """
        logger.info(
            "Tentative de renvoi de l'e-mail de vérification",
            extra=with_context(email=email),
        )
        try:
            # Note: La méthode exacte peut varier légèrement en fonction de la version de gotrue-py
            # ou des configurations spécifiques de Supabase.
            # send_otp est souvent utilisé pour cela avec le type 'signup' ou 'email_change'.
            # Si une URL de redirection spécifique est nécessaire, elle doit être configurée.
            # Par exemple: redirect_to=settings.EMAIL_VERIFICATION_REDIRECT_URL
            # Pour l'instant, on suppose que Supabase gère la redirection par défaut.
            supabase.auth.api.send_verification_email(email=email)  # ou supabase.auth.resend(email=email, type="signup")

            # La réponse de send_verification_email ne contient généralement pas d'erreur explicite
            # mais lève une exception en cas de problème majeur.
            # Il est bon de vérifier si l'utilisateur existe et n'est pas déjà confirmé,
            # mais Supabase devrait gérer ces cas.
            logger.info(
                "E-mail de vérification renvoyé avec succès",
                extra=with_context(email=email),
            )
            return {"message": "E-mail de vérification renvoyé avec succès. Veuillez consulter votre boîte de réception."}
        except Exception as e:
            logger.error(
                "Erreur lors du renvoi de l'e-mail de vérification",
                extra=with_context(email=email, error_type=type(e).__name__),
                exc_info=True,
            )
            # Il est préférable de ne pas révéler si l'email existe ou non pour des raisons de sécurité.
            # Cependant, Supabase peut retourner des erreurs spécifiques que l'on pourrait vouloir gérer.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur lors du renvoi de l'e-mail de vérification: {str(e)}",
            )

    @staticmethod
    async def delete_user(user_id: str, supabase_admin_client) -> bool:
        """
        Supprimer un utilisateur de Supabase Auth.

        Args:
            user_id: L'identifiant UUID de l'utilisateur à supprimer
            supabase_admin_client: Le client admin Supabase

        Returns:
            bool: True si la suppression a réussi

        Raises:
            HTTPException: Si la suppression échoue
        """
        logger.info(
            "Tentative de suppression d'utilisateur",
            extra=with_context(user_id=user_id),
        )

        try:
            # La méthode delete_user du client Supabase admin ne retourne rien (None) en cas de succès
            # et lève une AuthApiError en cas d'échec.
            supabase_admin_client.auth.admin.delete_user(user_id)

            logger.info(
                "Utilisateur supprimé avec succès de Supabase",
                extra=with_context(user_id=user_id),
            )
            return True

        except AuthApiError as e:
            logger.error(
                "Erreur API Supabase lors de la suppression de l'utilisateur",
                extra=with_context(user_id=user_id, error_type=type(e).__name__),
                exc_info=True,
            )
            # Utiliser str(e) au lieu de e.message qui pourrait ne pas exister
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Échec de la suppression de l'utilisateur : {str(e)}",
            )
        except Exception as e:
            logger.error(
                "Erreur inattendue lors de la tentative de suppression de l'utilisateur",
                extra=with_context(user_id=user_id, error_type=type(e).__name__),
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur inattendue lors de la suppression de l'utilisateur : {str(e)}",
            )

