import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext

from app.main import app
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.schemas.auth import UserSignup, UserLogin
from app.config import settings


# Configuration du client de test
client = TestClient(app)

# Context pour les tests de password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# FIXTURES PYTEST
# ============================================================================


@pytest.fixture
def mock_user():
    """Utilisateur mock réutilisable"""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "created_at": "2025-05-30T10:00:00Z",
        "updated_at": "2025-05-30T10:00:00Z",
    }


@pytest.fixture
def valid_user_data():
    """Données utilisateur valides pour signup/login"""
    return {"email": "newuser@example.com", "password": "SecurePassword123!"}


@pytest.fixture
def mock_supabase():
    """Mock Supabase réutilisable"""
    mock = MagicMock()

    # Configuration des réponses par défaut
    mock.auth.sign_up.return_value = Mock(
        user=Mock(id="new_user_123", email="newuser@example.com"),
        session=Mock(
            access_token="mock_access_token", refresh_token="mock_refresh_token"
        ),
    )

    mock.auth.sign_in_with_password.return_value = Mock(
        user=Mock(id="existing_user_123", email="test@example.com"),
        session=Mock(
            access_token="mock_access_token", refresh_token="mock_refresh_token"
        ),
    )

    mock.auth.refresh_session.return_value = Mock(
        user=Mock(id="existing_user_123"),
        session=Mock(
            access_token="new_access_token", refresh_token="new_refresh_token"
        ),
    )

    return mock


@pytest.fixture
def auth_headers(mock_user):
    """Headers d'authentification avec token valide"""
    token = create_access_token(data={"sub": mock_user["email"]})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. TESTS UNITAIRES DES UTILITAIRES DE SÉCURITÉ
# ============================================================================


class TestSecurityUtils:
    """Tests des fonctions utilitaires de sécurité"""

    def test_password_hashing(self):
        """Test du hachage et de la vérification des mots de passe"""
        password = "TestPassword123!"

        # Test du hachage
        hashed = get_password_hash(password)
        assert hashed != password
        assert hashed.startswith("$2b$")

        # Test de la vérification
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False
        assert verify_password("", hashed) is False

    def test_create_access_token(self):
        """Test de création des tokens d'accès"""
        test_data = {"sub": "test@example.com"}

        # Création du token
        token = create_access_token(data=test_data)
        assert isinstance(token, str)
        assert len(token) > 0

        # Vérification du contenu
        decoded = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert decoded["sub"] == "test@example.com"
        assert "exp" in decoded

    def test_create_refresh_token(self):
        """Test de création des tokens de rafraîchissement"""
        test_data = {"sub": "test@example.com"}

        # Création du token
        token = create_refresh_token(data=test_data)
        assert isinstance(token, str)
        assert len(token) > 0

        # Vérification du contenu
        decoded = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert decoded["sub"] == "test@example.com"
        assert "exp" in decoded

    def test_verify_token_valid(self):
        """Test de vérification d'un token valide"""
        test_data = {"sub": "test@example.com"}
        token = create_access_token(data=test_data)

        # Vérification
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"

    def test_verify_token_invalid(self):
        """Test de vérification d'un token invalide"""
        # Token malformé - doit lever une HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid_token")
        assert exc_info.value.status_code == 401

        # Token vide - doit lever une HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token("")
        assert exc_info.value.status_code == 401

        # Token avec mauvaise signature - doit lever une HTTPException
        fake_token = jwt.encode(
            {"sub": "test@example.com"},
            "wrong_secret",
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(fake_token)
        assert exc_info.value.status_code == 401

    def test_verify_token_expired(self):
        """Test de vérification d'un token expiré"""
        # Création d'un token expiré
        expired_data = {
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),  # Correction ici
        }
        expired_token = jwt.encode(
            expired_data,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

        # Vérification - doit lever une HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        assert exc_info.value.status_code == 401


# ============================================================================
# 2. TESTS DE VALIDATION DES DONNÉES
# ============================================================================


class TestDataValidation:
    """Tests de validation des modèles Pydantic"""

    def test_user_signup_valid_data(self):
        """Test de validation avec données valides pour signup"""
        valid_data = {"email": "test@example.com", "password": "SecurePass123!"}

        user = UserSignup(**valid_data)
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"

    def test_user_signup_invalid_email(self):
        """Test de validation avec email invalide"""
        with pytest.raises(ValueError):
            UserSignup(email="invalid_email", password="SecurePass123!")

    def test_user_signup_missing_password(self):
        """Test de validation avec mot de passe manquant"""
        with pytest.raises(ValueError):
            UserSignup(email="test@example.com")

    def test_user_login_valid_data(self):
        """Test de validation avec données valides pour login"""
        valid_data = {"email": "test@example.com", "password": "password123"}

        user = UserLogin(**valid_data)
        assert user.email == "test@example.com"
        assert user.password == "password123"


# ============================================================================
# 3. TESTS DES ENDPOINTS D'AUTHENTIFICATION
# ============================================================================


class TestAuthEndpoints:
    """Tests des endpoints d'authentification"""

    # Pour l'instant, testons les endpoints sans mocks complexes
    def test_signup_endpoint_structure(self, valid_user_data):
        """Test de base de l'endpoint signup"""
        # Test que l'endpoint existe et accepte les données
        response = client.post("/auth/signup", json=valid_user_data)
        # L'endpoint devrait exister (pas 404)
        assert response.status_code != 404

    def test_login_endpoint_structure(self):
        """Test de base de l'endpoint login"""
        login_data = {"email": "test@example.com", "password": "password123"}
        response = client.post("/auth/login", json=login_data)
        # L'endpoint devrait exister (pas 404)
        assert response.status_code != 404

    def test_refresh_endpoint_structure(self):
        """Test de base de l'endpoint refresh"""
        refresh_data = {"refresh_token": "some_token"}
        response = client.post("/auth/refresh", json=refresh_data)
        # L'endpoint devrait exister (pas 404)
        assert response.status_code != 404

    def test_me_endpoint_structure(self):
        """Test de base de l'endpoint me"""
        response = client.get("/auth/me")
        # L'endpoint devrait exister (pas 404)
        assert response.status_code != 404

    def test_logout_endpoint_structure(self):
        """Test de base de l'endpoint logout"""
        response = client.post("/auth/logout")
        # L'endpoint devrait exister (pas 404)
        assert response.status_code != 404

    # Test avec token valide pour get_current_user
    def test_get_current_user_with_valid_token(self, auth_headers):
        """Test de récupération des infos utilisateur avec token valide"""
        response = client.get("/auth/me", headers=auth_headers)
        # Avec un token valide, on ne devrait pas avoir 404
        assert response.status_code != 404


# ============================================================================
# 4. TESTS D'AUTORISATION
# ============================================================================


class TestAuthorization:
    """Tests des contrôles d'autorisation"""

    def test_protected_endpoint_without_token(self):
        """Test d'accès à un endpoint protégé sans token"""
        response = client.get("/auth/me")
        # FastAPI retourne 403 par défaut pour les endpoints protégés sans auth
        assert response.status_code == 403

    def test_protected_endpoint_with_invalid_token(self):
        """Test d'accès avec token invalide"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_protected_endpoint_with_expired_token(self):
        """Test d'accès avec token expiré"""
        # Création d'un token expiré
        expired_data = {
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            expired_data, settings.secret_key, algorithm=settings.jwt_algorithm
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_protected_endpoint_with_malformed_authorization_header(self):
        """Test avec header d'autorisation malformé"""
        # Sans "Bearer "
        headers = {"Authorization": "invalid_format_token"}
        response = client.get("/auth/me", headers=headers)
        # FastAPI retourne 403 pour un header malformé
        assert response.status_code == 403

        # Avec Bearer mais sans token - FastAPI retourne aussi 403 pour ce cas
        headers = {"Authorization": "Bearer "}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 403  # Correction: 403 au lieu de 401

    def test_protected_endpoint_with_valid_token_format(self, auth_headers):
        """Test d'accès avec un token valide (structure)"""
        response = client.get("/auth/me", headers=auth_headers)
        # Avec un token bien formaté, on ne devrait pas avoir d'erreur d'auth de base
        assert response.status_code != 403  # Pas d'erreur de format
        # Le token est valide au niveau format, donc si erreur ce serait 401 ou 200
        assert response.status_code in [200, 401]


# ============================================================================
# 5. TESTS D'INTÉGRATION SIMPLIFIÉS
# ============================================================================


class TestIntegrationBasic:
    """Tests d'intégration de base sans mocks complexes"""

    def test_auth_workflow_structure(self):
        """Test de la structure du workflow d'authentification"""
        # Test que tous les endpoints existent
        endpoints_to_test = [
            ("POST", "/auth/signup"),
            ("POST", "/auth/login"),
            ("POST", "/auth/refresh"),
            ("GET", "/auth/me"),
            ("POST", "/auth/logout"),
        ]

        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            # Vérifier que l'endpoint existe (pas 404 ou 405)
            assert response.status_code not in [
                404,
                405,
            ], f"{method} {endpoint} endpoint not found"

    def test_data_validation_on_endpoints(self):
        """Test de validation des données sur les endpoints"""
        # Test signup avec données invalides
        response = client.post("/auth/signup", json={"email": "invalid"})
        assert response.status_code in [400, 422]  # Erreur de validation

        # Test login avec données manquantes
        response = client.post("/auth/login", json={})
        assert response.status_code in [400, 422]  # Erreur de validation

        # Test refresh avec données invalides
        response = client.post("/auth/refresh", json={})
        assert response.status_code in [400, 422]  # Erreur de validation
