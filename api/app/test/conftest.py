"""
Fixtures partagées pour tous les tests de l'API Cleaning Tracker
"""
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
import asyncpg
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import init_db_pool
from app.core.security import create_access_token, create_refresh_token
from app.config import settings


# ============================================================================
# CONFIGURATION PYTEST
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ============================================================================
# FIXTURES DE BASE
# ============================================================================

@pytest.fixture(scope="session")
async def db_pool(event_loop) -> AsyncGenerator[asyncpg.Pool, None]:
    """Pool de connexions à la base de données pour les tests avec nettoyage et recréation des tables."""
    pool = await init_db_pool()
    
    async with pool.acquire() as conn:
        # Supprimer les tables existantes dans le bon ordre pour éviter les problèmes de FK
        await conn.execute("DROP TABLE IF EXISTS tasks CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS rooms CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS household_members CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS households CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS users CASCADE;")

        # Recréer les tables
        await conn.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            full_name VARCHAR(255),
            hashed_password VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            email_confirmed_at TIMESTAMPTZ,
            is_active BOOLEAN DEFAULT TRUE,
            is_superuser BOOLEAN DEFAULT FALSE
        );
        """)
        await conn.execute("""
        CREATE TABLE households (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)
        await conn.execute("""
        CREATE TABLE household_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            household_id UUID REFERENCES households(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL DEFAULT 'member', 
            joined_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (household_id, user_id)
        );
        """)
        
        # Table des pièces
        await conn.execute("""
        CREATE TABLE rooms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
            icon VARCHAR(10),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)
        
        # Table des tâches
        await conn.execute("""
        CREATE TABLE tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
            room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
            assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
            due_date TIMESTAMPTZ,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

    yield pool
    
    # Le nettoyage après la session est maintenant moins critique si on nettoie au début
    # Mais peut être conservé pour s'assurer que la BD de test est propre après tout.
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS tasks CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS rooms CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS household_members CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS households CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS users CASCADE;")

    await pool.close()


@pytest.fixture
def client() -> TestClient:
    """Client de test synchrone FastAPI"""
    return TestClient(app)


@pytest.fixture
async def async_client(db_pool: asyncpg.Pool) -> AsyncGenerator[AsyncClient, None]:
    """Client de test asynchrone pour les tests d'intégration"""
    app.state.db_pool = db_pool  # Assigner le pool de DB à l'instance de l'app pour les tests
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ============================================================================
# FIXTURES UTILISATEURS
# ============================================================================

@pytest.fixture
def mock_user() -> Dict[str, Any]:
    """Utilisateur de test standard avec email unique."""
    user_uuid = uuid4()
    return {
        "id": str(user_uuid),
        "email": f"testuser_{user_uuid}@example.com", # Ensure unique email
        "full_name": "Test User",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "email_confirmed_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def mock_admin_user() -> Dict[str, Any]:
    """Utilisateur admin de test avec email unique."""
    admin_uuid = uuid4()
    return {
        "id": str(admin_uuid),
        "email": f"admin_{admin_uuid}@example.com", # Ensure unique email
        "full_name": "Admin User",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "email_confirmed_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def valid_signup_data() -> Dict[str, str]:
    """Données valides pour l'inscription"""
    return {
        "email": f"newuser_{uuid4().hex[:8]}@example.com",
        "password": "SecurePassword123!",
        "full_name": "New User"
    }


@pytest.fixture
def valid_login_data() -> Dict[str, str]:
    """Données valides pour la connexion"""
    return {
        "email": "existing@example.com",
        "password": "ExistingPassword123!"
    }


# ============================================================================
# FIXTURES AUTHENTIFICATION
# ============================================================================

@pytest.fixture
def auth_headers(mock_user: Dict[str, Any]) -> Dict[str, str]:
    """Headers d'authentification avec token valide"""
    token = create_access_token(
        data={"sub": mock_user["id"], "email": mock_user["email"]}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(mock_admin_user: Dict[str, Any]) -> Dict[str, str]:
    """Headers d'authentification admin avec token valide"""
    token = create_access_token(
        data={"sub": mock_admin_user["id"], "email": mock_admin_user["email"]}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_auth_headers(mock_user: Dict[str, Any]) -> Dict[str, str]:
    """Headers avec token expiré"""
    from datetime import timedelta
    token = create_access_token(
        data={"sub": mock_user["id"], "email": mock_user["email"]},
        expires_delta=timedelta(minutes=-1)  # Token déjà expiré
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def refresh_token(mock_user: Dict[str, Any]) -> str:
    """Token de rafraîchissement valide"""
    return create_refresh_token(
        data={"sub": mock_user["id"], "email": mock_user["email"]}
    )


# ============================================================================
# FIXTURES MÉNAGES
# ============================================================================

@pytest.fixture
def mock_household() -> Dict[str, Any]:
    """Ménage de test"""
    return {
        "id": uuid4(),  # Changed to return actual UUID object
        "name": "Test Household",
        "created_at": datetime.now(timezone.utc)  # Changed to return actual datetime object
    }


@pytest.fixture
def household_create_data() -> Dict[str, str]:
    """Données pour créer un ménage"""
    return {
        "name": f"Test Household {uuid4().hex[:8]}"
    }


# ============================================================================
# FIXTURES MEMBRES
# ============================================================================

@pytest.fixture
def mock_member(mock_user: Dict[str, Any], mock_household: Dict[str, Any]) -> Dict[str, Any]:
    """Membre de ménage de test"""
    return {
        "id": str(uuid4()),
        "household_id": mock_household["id"],
        "user_id": mock_user["id"],
        "role": "member",
        "joined_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def member_create_data(mock_user: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour ajouter un membre"""
    return {
        "user_id": mock_user["id"],
        "role": "member"
    }


# ============================================================================
# FIXTURES PIÈCES
# ============================================================================

@pytest.fixture
def mock_room(mock_household: Dict[str, Any]) -> Dict[str, Any]:
    """Pièce de test"""
    return {
        "id": str(uuid4()),
        "household_id": mock_household["id"],
        "name": "Living Room",
        "icon": "🛋️",
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def room_create_data() -> Dict[str, str]:
    """Données pour créer une pièce"""
    return {
        "name": "Kitchen",
        "icon": "🍳"
    }


# ============================================================================
# FIXTURES TÂCHES
# ============================================================================

@pytest.fixture
def mock_task(mock_household: Dict[str, Any], mock_room: Dict[str, Any]) -> Dict[str, Any]:
    """Tâche de test"""
    return {
        "id": str(uuid4()),
        "household_id": mock_household["id"],
        "room_id": mock_room["id"],
        "title": "Clean the floor",
        "description": "Vacuum and mop the floor",
        "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO,FR",
        "estimated_minutes": 30,
        "is_catalog": False,
        "created_by": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def task_create_data(mock_household: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour créer une tâche"""
    return {
        "household_id": mock_household["id"],
        "title": "Wash dishes",
        "description": "Clean all dishes in the sink"
    }


# ============================================================================
# FIXTURES OCCURRENCES
# ============================================================================

@pytest.fixture
def mock_occurrence(mock_task: Dict[str, Any]) -> Dict[str, Any]:
    """Occurrence de tâche de test"""
    from datetime import date
    return {
        "id": str(uuid4()),
        "task_id": mock_task["id"],
        "scheduled_date": date.today().isoformat(),
        "due_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "assigned_to": None,
        "snoozed_until": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# FIXTURES MOCKS SUPABASE
# ============================================================================

@pytest.fixture
def mock_supabase_client(mocker):
    """Mock du client Supabase avec réponses par défaut"""
    from unittest.mock import MagicMock
    from uuid import uuid4

    mock = MagicMock()

    # Configuration des réponses auth
    mock.auth.sign_up.return_value = MagicMock(
        user=MagicMock(
            id=str(uuid4()),
            email="newuser@example.com",
            email_confirmed_at=None,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            user_metadata={"full_name": "New User"}
        ),
        session=MagicMock(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token"
        )
    )

    mock.auth.sign_in_with_password.return_value = MagicMock(
        user=MagicMock(
            id=str(uuid4()),
            email="existing@example.com",
            email_confirmed_at=datetime.now(timezone.utc).isoformat(),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            user_metadata={"full_name": "Existing User"}
        ),
        session=MagicMock(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token"
        )
    )

    # Patch du client Supabase
    mocker.patch("app.core.supabase_client.supabase", mock)
    mocker.patch("app.services.auth_service.supabase", mock)

    return mock


@pytest.fixture
def mock_supabase_admin(mocker):
    """Mock du client Supabase admin"""
    from unittest.mock import MagicMock
    from uuid import uuid4

    mock = MagicMock()

    # Configuration des réponses admin
    mock.auth.admin.get_user_by_id.return_value = MagicMock(
        user=MagicMock(
            id=str(uuid4()),
            email="existing@example.com",
            email_confirmed_at=datetime.now(timezone.utc).isoformat(),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            user_metadata={"full_name": "Existing User"}
        )
    )

    mock.auth.admin.delete_user.return_value = MagicMock(error=None)

    # Patch du client admin
    mocker.patch("app.core.supabase_client.supabase_admin", mock)
    mocker.patch("app.services.auth_service.supabase_admin", mock)

    return mock


# ============================================================================
# FIXTURES HELPERS
# ============================================================================

@pytest.fixture
async def clean_database(db_pool: asyncpg.Pool):
    """Nettoie la base de données avant/après les tests"""
    # Cette fixture peut être utilisée pour nettoyer les données de test
    # Elle est particulièrement utile pour les tests d'intégration
    yield

    # Nettoyage après le test
    async with db_pool.acquire() as conn:
        # Supprimer les données de test dans l'ordre inverse des dépendances
        await conn.execute("DELETE FROM task_completions WHERE TRUE")
        await conn.execute("DELETE FROM notifications WHERE TRUE")
        await conn.execute("DELETE FROM task_occurrences WHERE TRUE")
        await conn.execute("DELETE FROM task_definitions WHERE TRUE")
        await conn.execute("DELETE FROM rooms WHERE TRUE")
        await conn.execute("DELETE FROM household_members WHERE TRUE")
        await conn.execute("DELETE FROM households WHERE TRUE")


@pytest.fixture
def anyio_backend():
    """Backend pour les tests async avec anyio"""
    return "asyncio"
