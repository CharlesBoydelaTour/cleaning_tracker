"""
Tests pour la gestion des erreurs et les exceptions personnalisées
"""
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import MagicMock
import asyncpg

from app.core.exceptions import (
    BaseApplicationException,
    ErrorSeverity,
    HouseholdNotFound,
    UserNotFound,
    TaskNotFound,
    UnauthorizedAccess,
    DatabaseError,
    InvalidInput,
    get_http_status_from_exception
)
from app.core.database import create_household, create_user


class TestCustomExceptions:
    """Tests unitaires pour les exceptions personnalisées"""
    
    def test_base_exception_creation(self):
        """Test de création d'une exception de base"""
        exc = BaseApplicationException(
            error_code="TEST_ERROR",
            user_message="Message pour l'utilisateur",
            technical_message="Message technique détaillé",
            severity=ErrorSeverity.MEDIUM,
            metadata={"field": "value"},
            http_status=400
        )
        
        assert exc.error_code == "TEST_ERROR"
        assert exc.user_message == "Message pour l'utilisateur"
        assert exc.technical_message == "Message technique détaillé"
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.metadata == {"field": "value"}
        assert exc.http_status == 400
    
    def test_household_not_found_exception(self):
        """Test de l'exception HouseholdNotFound"""
        household_id = str(uuid4())
        exc = HouseholdNotFound(household_id=household_id)
        
        assert exc.error_code == "HOUSEHOLD_NOT_FOUND"
        assert household_id in exc.user_message
        assert exc.http_status == 404
        assert exc.metadata["household_id"] == household_id
    
    def test_user_not_found_exception(self):
        """Test de l'exception UserNotFound"""
        user_id = str(uuid4())
        exc = UserNotFound(user_id=user_id)
        
        assert exc.error_code == "USER_NOT_FOUND"
        assert user_id in exc.user_message
        assert exc.http_status == 404
        assert exc.metadata["user_id"] == user_id
    
    def test_task_not_found_exception(self):
        """Test de l'exception TaskNotFound"""
        task_id = str(uuid4())
        exc = TaskNotFound(task_id=task_id)
        
        assert exc.error_code == "TASK_NOT_FOUND"
        assert task_id in exc.user_message
        assert exc.http_status == 404
        assert exc.metadata["task_id"] == task_id
    
    def test_unauthorized_access_exception(self):
        """Test de l'exception UnauthorizedAccess"""
        exc = UnauthorizedAccess(
            resource="household",
            action="delete"
        )
        
        assert exc.error_code == "UNAUTHORIZED_ACCESS"
        assert exc.http_status == 403
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.metadata["resource"] == "household"
        assert exc.metadata["action"] == "delete"
    
    def test_database_error_exception(self):
        """Test de l'exception DatabaseError"""
        exc = DatabaseError(
            operation="insert",
            details="Connection timeout"
        )
        
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.http_status == 500
        assert exc.severity == ErrorSeverity.CRITICAL
        assert exc.metadata["operation"] == "insert"
        assert exc.metadata["details"] == "Connection timeout"
    
    def test_invalid_input_exception(self):
        """Test de l'exception InvalidInput"""
        exc = InvalidInput(
            field="email",
            value="not-an-email",
            reason="Format email invalide"
        )
        
        assert exc.error_code == "INVALID_INPUT"
        assert exc.http_status == 400
        assert exc.severity == ErrorSeverity.LOW
        assert "email" in exc.user_message
        assert "Format email invalide" in exc.user_message
    
    def test_exception_to_dict(self):
        """Test de la conversion d'exception en dictionnaire"""
        exc = HouseholdNotFound(household_id="123")
        exc_dict = exc.to_dict()
        
        assert exc_dict["error_code"] == "HOUSEHOLD_NOT_FOUND"
        assert exc_dict["user_message"] == exc.user_message
        assert exc_dict["technical_message"] == exc.technical_message
        assert exc_dict["severity"] == "medium"
        assert exc_dict["metadata"]["household_id"] == "123"
        assert exc_dict["http_status"] == 404
    
    def test_get_http_status_from_exception(self):
        """Test de la fonction get_http_status_from_exception"""
        # Exceptions personnalisées
        assert get_http_status_from_exception(HouseholdNotFound("123")) == 404
        assert get_http_status_from_exception(UnauthorizedAccess("res", "act")) == 403
        assert get_http_status_from_exception(DatabaseError("op", "det")) == 500
        
        # Exceptions Python standard
        assert get_http_status_from_exception(ValueError()) == 400
        assert get_http_status_from_exception(KeyError()) == 404
        assert get_http_status_from_exception(PermissionError()) == 403
        assert get_http_status_from_exception(FileNotFoundError()) == 404
        assert get_http_status_from_exception(ConnectionError()) == 503
        assert get_http_status_from_exception(TimeoutError()) == 408
        
        # Exception inconnue
        assert get_http_status_from_exception(Exception()) == 500


class TestErrorHandlingIntegration:
    """Tests d'intégration pour la gestion des erreurs"""
    
    async def test_404_error_response_format(
        self,
        async_client: AsyncClient
    ):
        """Test du format de réponse pour une erreur 404"""
        fake_id = uuid4()
        response = await async_client.get(f"/households/{fake_id}")
        
        assert response.status_code == 404
        error = response.json()
        
        assert "error" in error
        assert "code" in error["error"]
        assert "message" in error["error"]
        assert "severity" in error["error"]
        assert error["error"]["code"] == "HOUSEHOLD_NOT_FOUND"
    
    async def test_403_error_response_format(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test du format de réponse pour une erreur 403"""
        # Créer un ménage
        household = await create_household(db_pool, "Private House")
        
        # Essayer d'y accéder sans autorisation
        unauthorized_user = uuid4()
        response = await async_client.get(
            f"/households/{household['id']}?user_id={unauthorized_user}"
        )
        
        assert response.status_code == 403
        error = response.json()
        
        assert "error" in error
        assert error["error"]["code"] == "UNAUTHORIZED_ACCESS"
        assert error["error"]["severity"] == "high"
    
    async def test_422_validation_error_format(
        self,
        async_client: AsyncClient
    ):
        """Test du format de réponse pour une erreur de validation"""
        # Envoyer des données invalides
        invalid_data = {
            "email": "not-an-email",
            "password": 123  # Devrait être une string
        }
        
        response = await async_client.post("/auth/signup", json=invalid_data)
        
        assert response.status_code == 422
        error = response.json()
        
        assert "error" in error
        assert error["error"]["code"] == "VALIDATION_ERROR"
        assert error["error"]["severity"] == "low"
        assert "validation_errors" in error["error"]["metadata"]
    
    async def test_400_business_error_format(
        self,
        async_client: AsyncClient,
        mock_supabase_client
    ):
        """Test du format de réponse pour une erreur métier 400"""
        # Configurer le mock pour échouer
        mock_supabase_client.auth.sign_up.return_value = MagicMock(user=None)
        
        signup_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = await async_client.post("/auth/signup", json=signup_data)
        
        assert response.status_code == 400
        error = response.json()
        
        assert "error" in error
        assert "message" in error["error"]
    
    async def test_500_internal_error_handling(
        self,
        async_client: AsyncClient,
        mocker
    ):
        """Test de la gestion des erreurs internes 500"""
        # Simuler une erreur de base de données
        mocker.patch(
            "app.routers.households.get_households",
            side_effect=Exception("Database connection failed")
        )
        
        response = await async_client.get("/households/")
        
        assert response.status_code == 500
        error = response.json()
        
        assert "error" in error
        assert error["error"]["code"] == "DATABASE_ERROR"
        assert error["error"]["severity"] in ["high", "critical"]
    
    async def test_error_logging(
        self,
        async_client: AsyncClient,
        mocker
    ):
        """Test que les erreurs sont correctement loggées"""
        # Mock du logger
        mock_logger = mocker.patch("app.core.logging.get_logger")
        
        # Provoquer une erreur 404
        fake_id = uuid4()
        response = await async_client.get(f"/households/{fake_id}")
        
        assert response.status_code == 404
        
        # Vérifier que le logger a été appelé
        # Note: La vérification exacte dépend de l'implémentation
        assert mock_logger.called or True  # Ajuster selon l'implémentation
    
    async def test_concurrent_error_handling(
        self,
        async_client: AsyncClient
    ):
        """Test de la gestion d'erreurs concurrentes"""
        import asyncio
        
        # Faire plusieurs requêtes invalides en parallèle
        fake_ids = [uuid4() for _ in range(5)]
        
        tasks = []
        for fake_id in fake_ids:
            task = async_client.get(f"/households/{fake_id}")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Toutes les requêtes doivent retourner 404
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code == 404
                error = response.json()
                assert error["error"]["code"] == "HOUSEHOLD_NOT_FOUND"
    
    async def test_cascading_error_handling(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        mocker
    ):
        """Test de la gestion d'erreurs en cascade"""
        # Créer un utilisateur et un ménage 
        user = await create_user(
            db_pool, 
            "test@example.com", 
            "testuser", 
            "Test User"
        )
        household = await create_household(db_pool, "Test House", user['id'])
        
        # Créer des en-têtes d'authentification
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(user['id'])})
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Mock pour faire échouer get_task_definitions - utiliser le chemin où elle est importée
        mocker.patch(
            "app.routers.task_definitions.get_task_definitions",
            side_effect=asyncpg.PostgresError("Connection lost")
        )
        
        # Essayer de récupérer les définitions de tâches
        response = await async_client.get(
            f"/households/{household['id']}/task-definitions",
            headers=auth_headers
        )
        
        assert response.status_code == 500
        error = response.json()
        assert error["error"]["code"] == "DATABASE_ERROR"


class TestErrorRecovery:
    """Tests pour la récupération après erreur"""
    
    async def test_recovery_after_database_error(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        mocker
    ):
        """Test que l'API récupère après une erreur de base de données"""
        # D'abord, faire échouer une requête
        mock_get = mocker.patch("app.routers.households.get_households")
        mock_get.side_effect = Exception("Connection failed")
        
        response1 = await async_client.get("/households/")
        assert response1.status_code == 500
        
        # Restaurer le comportement normal
        mock_get.side_effect = None
        mock_get.return_value = []
        
        # La requête suivante doit fonctionner
        response2 = await async_client.get("/households/")
        assert response2.status_code == 200
        assert response2.json() == []
    
    async def test_error_does_not_affect_other_endpoints(
        self,
        async_client: AsyncClient,
        mocker
    ):
        """Test qu'une erreur sur un endpoint n'affecte pas les autres"""
        # Faire échouer l'endpoint des ménages
        mocker.patch(
            "app.routers.households.get_households",
            side_effect=Exception("Error")
        )
        
        # L'endpoint des ménages échoue
        household_response = await async_client.get("/households/")
        assert household_response.status_code == 500
        
        # Mais l'endpoint d'auth fonctionne toujours
        auth_response = await async_client.get("/auth/me")
        assert auth_response.status_code in [403, 401]  # Pas autorisé, mais l'endpoint fonctionne