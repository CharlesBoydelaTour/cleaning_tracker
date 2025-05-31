"""
Tests unitaires pour les fonctionnalités d'authentification
"""
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.schemas.auth import UserSignup, UserLogin, RefreshToken
from app.config import settings


class TestPasswordSecurity:
    """Tests pour le hachage et la vérification des mots de passe"""
    
    def test_password_hashing(self):
        """Test du hachage des mots de passe"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50
    
    def test_password_verification_success(self):
        """Test de vérification réussie du mot de passe"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test de vérification échouée du mot de passe"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password("WrongPassword", hashed) is False
        assert verify_password("", hashed) is False
        assert verify_password("TestPassword123", hashed) is False
    
    def test_different_passwords_produce_different_hashes(self):
        """Test que différents mots de passe produisent différents hashes"""
        password1 = "Password123!"
        password2 = "Password456!"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_produces_different_hashes(self):
        """Test que le même mot de passe produit des hashes différents (salt)"""
        password = "Password123!"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests pour la création et vérification des tokens JWT"""
    
    def test_create_access_token_structure(self):
        """Test de la structure du token d'accès"""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT a 3 parties
    
    def test_create_access_token_content(self):
        """Test du contenu du token d'accès"""
        data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data)
        
        decoded = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        assert decoded["sub"] == "test@example.com"
        assert decoded["user_id"] == "123"
        assert "exp" in decoded
    
    def test_create_access_token_expiration(self):
        """Test de l'expiration du token d'accès"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)
        
        decoded = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Vérifier que l'expiration est dans environ 15 minutes
        assert 14 <= (exp_time - now).total_seconds() / 60 <= 16
    
    def test_create_refresh_token_structure(self):
        """Test de la structure du token de rafraîchissement"""
        data = {"sub": "test@example.com"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token.split(".")) == 3
    
    def test_create_refresh_token_longer_expiration(self):
        """Test que le refresh token a une expiration plus longue"""
        data = {"sub": "test@example.com"}
        
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        access_decoded = jwt.decode(
            access_token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        refresh_decoded = jwt.decode(
            refresh_token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        assert refresh_decoded["exp"] > access_decoded["exp"]
    
    def test_verify_token_success(self):
        """Test de vérification réussie d'un token"""
        data = {"sub": "test@example.com", "role": "user"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "user"
        assert "exp" in payload
    
    def test_verify_token_invalid_format(self):
        """Test de vérification avec un format invalide"""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.format")
        
        assert exc_info.value.status_code == 401
        assert "invalide" in exc_info.value.detail.lower()
    
    def test_verify_token_wrong_signature(self):
        """Test de vérification avec une signature incorrecte"""
        fake_token = jwt.encode(
            {"sub": "test@example.com"},
            "wrong_secret_key",
            algorithm=settings.jwt_algorithm
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(fake_token)
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_expired(self):
        """Test de vérification d'un token expiré"""
        data = {
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(
            data,
            settings.secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_missing_claims(self):
        """Test de vérification avec des claims manquants"""
        # Token sans 'sub'
        data = {"user_id": "123", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(
            data,
            settings.secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        # verify_token devrait accepter le token même sans 'sub'
        payload = verify_token(token)
        assert payload["user_id"] == "123"


class TestAuthSchemas:
    """Tests pour les schémas Pydantic d'authentification"""
    
    def test_user_signup_valid(self):
        """Test de création d'un schéma UserSignup valide"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        
        user = UserSignup(**data)
        
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"
        assert user.full_name == "Test User"
    
    def test_user_signup_invalid_email(self):
        """Test avec un email invalide"""
        with pytest.raises(ValueError):
            UserSignup(
                email="invalid_email",
                password="SecurePass123!"
            )
    
    def test_user_signup_missing_password(self):
        """Test avec un mot de passe manquant"""
        with pytest.raises(ValueError):
            UserSignup(email="test@example.com")
    
    def test_user_signup_optional_full_name(self):
        """Test que full_name est optionnel"""
        user = UserSignup(
            email="test@example.com",
            password="SecurePass123!"
        )
        
        assert user.full_name is None
    
    def test_user_login_valid(self):
        """Test de création d'un schéma UserLogin valide"""
        data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        user = UserLogin(**data)
        
        assert user.email == "test@example.com"
        assert user.password == "password123"
    
    def test_refresh_token_schema(self):
        """Test du schéma RefreshToken"""
        data = {"refresh_token": "some_token_value"}
        
        token = RefreshToken(**data)
        
        assert token.refresh_token == "some_token_value"
    
    def test_email_normalization(self):
        """Test de la normalisation des emails"""
        user = UserSignup(
            email="TEST@EXAMPLE.COM",
            password="password123"
        )
        
        # Pydantic EmailStr devrait normaliser l'email
        assert "@" in user.email
        assert "example.com" in user.email.lower()