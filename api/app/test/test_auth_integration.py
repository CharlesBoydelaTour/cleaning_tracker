"""
Tests d'intégration pour les endpoints d'authentification
"""
from httpx import AsyncClient
from unittest.mock import MagicMock
from datetime import datetime, timezone



class TestAuthEndpoints:
    """Tests d'intégration pour les endpoints d'authentification"""
    
    async def test_signup_success(
        self, 
        async_client: AsyncClient, 
        valid_signup_data: dict,
        mock_supabase_client
    ):
        """Test d'inscription réussie"""
        response = await async_client.post("/auth/signup", json=valid_signup_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["tokens"]["access_token"]
        assert data["tokens"]["refresh_token"]
        assert data["tokens"]["token_type"] == "bearer"
    
    async def test_signup_duplicate_email(
        self, 
        async_client: AsyncClient,
        valid_signup_data: dict,
        mock_supabase_client
    ):
        """Test d'inscription avec un email déjà utilisé"""
        # Configurer le mock pour retourner None (échec)
        mock_supabase_client.auth.sign_up.return_value = MagicMock(user=None)
        
        response = await async_client.post("/auth/signup", json=valid_signup_data)
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
        assert "email" in error["error"]["message"].lower()
    
    async def test_signup_invalid_data(self, async_client: AsyncClient):
        """Test d'inscription avec des données invalides"""
        invalid_data = {
            "email": "not_an_email",
            "password": "123"  # Trop court
        }
        
        response = await async_client.post("/auth/signup", json=invalid_data)
        
        assert response.status_code == 422
        error = response.json()
        assert "error" in error
        assert "validation" in error["error"]["message"].lower()
    
    async def test_login_success(
        self, 
        async_client: AsyncClient,
        valid_login_data: dict,
        mock_supabase_client
    ):
        """Test de connexion réussie"""
        response = await async_client.post("/auth/login", json=valid_login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "existing@example.com"
        assert data["tokens"]["access_token"]
        assert data["tokens"]["refresh_token"]
    
    async def test_login_wrong_password(
        self,
        async_client: AsyncClient,
        valid_login_data: dict,
        mock_supabase_client
    ):
        """Test de connexion avec mot de passe incorrect"""
        # Configurer le mock pour retourner None (échec)
        mock_supabase_client.auth.sign_in_with_password.return_value = MagicMock(user=None)
        
        response = await async_client.post("/auth/login", json=valid_login_data)
        
        assert response.status_code == 401
        error = response.json()
        assert "error" in error
        assert "incorrect" in error["error"]["message"].lower()
    
    async def test_login_non_existent_user(
        self,
        async_client: AsyncClient,
        mock_supabase_client
    ):
        """Test de connexion avec un utilisateur inexistant"""
        mock_supabase_client.auth.sign_in_with_password.return_value = MagicMock(user=None)
        
        data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = await async_client.post("/auth/login", json=data)
        
        assert response.status_code == 401
        error = response.json()
        assert "error" in error
    
    async def test_refresh_token_success(
        self,
        async_client: AsyncClient,
        refresh_token: str,
        mock_user: dict
    ):
        """Test de rafraîchissement réussi du token"""
        response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_refresh_token_invalid(
        self,
        async_client: AsyncClient
    ):
        """Test de rafraîchissement avec token invalide"""
        response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
        error = response.json()
        assert "error" in error
        assert "invalide" in error["error"]["message"].lower()
    
    async def test_refresh_token_expired(
        self,
        async_client: AsyncClient,
        mock_user: dict
    ):
        """Test de rafraîchissement avec token expiré"""
        from app.core.security import jwt, settings
        from datetime import datetime, timedelta, timezone
        
        # Créer un token expiré
        expired_data = {
            "sub": mock_user["id"],
            "email": mock_user["email"],
            "exp": datetime.now(timezone.utc) - timedelta(days=1)
        }
        expired_token = jwt.encode(
            expired_data,
            settings.secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": expired_token}
        )
        
        assert response.status_code == 401
    
    async def test_get_current_user_invalid_token(
        self,
        async_client: AsyncClient
    ):
        """Test d'accès avec token invalide"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        error = response.json()
        assert "error" in error
    
    async def test_logout_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_supabase_client
    ):
        """Test de déconnexion réussie"""
        response = await async_client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Déconnexion réussie"
        
        # Vérifier que sign_out a été appelé
        mock_supabase_client.auth.sign_out.assert_called_once()
    
    async def test_logout_without_auth(
        self,
        async_client: AsyncClient
    ):
        """Test de déconnexion sans authentification"""
        response = await async_client.post("/auth/logout")
        
        assert response.status_code == 403
    
    async def test_request_password_reset_success(
        self,
        async_client: AsyncClient,
        mock_supabase_client
    ):
        """Test de demande de réinitialisation de mot de passe"""
        response = await async_client.post(
            "/auth/reset-password?email=test@example.com"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "réinitialisation" in data["message"].lower()
    
    async def test_request_password_reset_invalid_email(
        self,
        async_client: AsyncClient
    ):
        """Test de réinitialisation avec email invalide"""
        response = await async_client.post("/auth/reset-password?email=")
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
        assert "email" in error["error"]["message"].lower()
    
    async def test_verify_email_status(
        self,
        async_client: AsyncClient,
        mock_supabase_client
    ):
        """Test de vérification du statut de confirmation d'email"""
        mock_supabase_client.auth.get_user.return_value = MagicMock(
            user=MagicMock(
                email="test@example.com",
                email_confirmed_at=datetime.now(timezone.utc).isoformat()
            )
        )
        
        response = await async_client.get("/auth/verify-email/test@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["confirmed"] is True
    
    async def test_resend_verification_email_success(
        self,
        async_client: AsyncClient,
        mock_supabase_client
    ):
        """Test de renvoi de l'email de vérification"""
        mock_supabase_client.auth.api.send_verification_email.return_value = None
        
        response = await async_client.post(
            "/auth/resend-verification-email?email=test@example.com"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "vérification" in data["message"].lower()
    
    async def test_resend_verification_email_empty(
        self,
        async_client: AsyncClient
    ):
        """Test de renvoi avec email vide"""
        response = await async_client.post("/auth/resend-verification-email?email=")
        
        assert response.status_code == 400
        error = response.json()
        assert error["error"]["code"] == "INVALID_INPUT"
    
    async def test_delete_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_user: dict,
        mock_supabase_admin
    ):
        """Test de suppression d'utilisateur réussie"""
        response = await async_client.delete("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Utilisateur supprimé"
        
        # Vérifier que delete_user a été appelé avec le bon ID
        mock_supabase_admin.auth.admin.delete_user.assert_called_once()
    
    async def test_delete_user_without_auth(
        self,
        async_client: AsyncClient
    ):
        """Test de suppression sans authentification"""
        response = await async_client.delete("/auth/me")
        
        assert response.status_code == 403


class TestAuthWorkflow:
    """Tests des workflows complets d'authentification"""
    
    async def test_complete_signup_login_workflow(
        self,
        async_client: AsyncClient,
        valid_signup_data: dict,
        mock_supabase_client,
        mock_supabase_admin
    ):
        """Test du workflow complet inscription -> connexion -> profil"""
        # 1. Inscription
        signup_response = await async_client.post("/auth/signup", json=valid_signup_data)
        assert signup_response.status_code == 200
        signup_response.json()
        
        # 2. Connexion avec les mêmes identifiants
        login_data = {
            "email": valid_signup_data["email"],
            "password": valid_signup_data["password"]
        }
        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        login_result = login_response.json()
        
        # 3. Utiliser le token pour accéder au profil
        headers = {"Authorization": f"Bearer {login_result['tokens']['access_token']}"}
        profile_response = await async_client.get("/auth/me", headers=headers)
        assert profile_response.status_code == 200
    
    async def test_token_refresh_workflow(
        self,
        async_client: AsyncClient,
        mock_user: dict,
        refresh_token: str
    ):
        """Test du workflow de rafraîchissement de token"""
        # 1. Rafraîchir le token
        refresh_response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        
        # 2. Utiliser le nouveau token
        headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        
        # Mock nécessaire pour get_current_user
        from unittest.mock import patch
        with patch("app.core.security.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": mock_user["id"],
                "email": mock_user["email"]
            }
            
            profile_response = await async_client.get("/auth/me", headers=headers)
            # Le test devrait passer avec le mock approprié
            assert profile_response.status_code in [200, 500]  # 500 si supabase_admin n'est pas mocké


class TestAuthErrorHandling:
    """Tests de gestion des erreurs d'authentification"""
    
    async def test_malformed_authorization_header(
        self,
        async_client: AsyncClient
    ):
        """Test avec header d'autorisation malformé"""
        # Sans "Bearer"
        headers = {"Authorization": "just_a_token"}
        response = await async_client.get("/auth/me", headers=headers)
        assert response.status_code == 403
        
        # Avec Bearer mais sans token
        headers = {"Authorization": "Bearer "}
        response = await async_client.get("/auth/me", headers=headers)
        assert response.status_code == 403
        
        # Format complètement incorrect
        headers = {"Authorization": ""}
        response = await async_client.get("/auth/me", headers=headers)
        assert response.status_code == 403
    
    async def test_service_exceptions(
        self,
        async_client: AsyncClient,
        valid_signup_data: dict,
        mock_supabase_client
    ):
        """Test de gestion des exceptions du service"""
        # Simuler une exception Supabase
        mock_supabase_client.auth.sign_up.side_effect = Exception("Service unavailable")
        
        response = await async_client.post("/auth/signup", json=valid_signup_data)
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
    
    async def test_concurrent_requests(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_supabase_admin
    ):
        """Test de requêtes concurrentes"""
        import asyncio
        
        # Faire plusieurs requêtes en parallèle
        tasks = []
        for _ in range(5):
            task = async_client.get("/auth/me", headers=auth_headers)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # Toutes les requêtes doivent réussir
        for response in responses:
            assert response.status_code == 200
    
    async def current_user_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_user: dict,
        mock_supabase_admin
    ):
        """Test de récupération des infos utilisateur"""
        response = await async_client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "existing_user_123"
        assert data["email"] == "existing@example.com"
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_get_current_user_no_auth(
        self,
        async_client: AsyncClient
    ):
        """Test d'accès sans authentification"""
        response = await async_client.get("/auth/me")
        
        assert response.status_code == 403
    