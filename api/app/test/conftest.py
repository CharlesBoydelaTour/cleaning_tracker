"""
Fixtures partagées pour tous les tests de l'API Cleaning Tracker
"""
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime, timezone, date, timedelta
from uuid import uuid4,UUID
import asyncpg
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db_pool
from app.core.security import create_access_token, create_refresh_token
from app.schemas.task import TaskStatus


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
        await conn.execute("DROP TABLE IF EXISTS task_completions CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS notifications CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS task_occurrences CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS task_definitions CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS rooms CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS household_members CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS households CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS users CASCADE;")
        
        # Supprimer les types ENUM s'ils existent
        await conn.execute("DROP TYPE IF EXISTS task_status CASCADE;")
        await conn.execute("DROP TYPE IF EXISTS notif_channel CASCADE;")

        # Créer les types ENUM
        await conn.execute("""
            CREATE TYPE task_status AS ENUM ('pending', 'snoozed', 'done', 'skipped', 'overdue');
            CREATE TYPE notif_channel AS ENUM ('push', 'email');
        """)

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
        
        # Table des définitions de tâches
        await conn.execute("""
        CREATE TABLE task_definitions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            household_id UUID REFERENCES households(id) ON DELETE CASCADE,
            is_catalog BOOLEAN NOT NULL DEFAULT FALSE,
            room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            recurrence_rule TEXT NOT NULL,
            estimated_minutes INTEGER,
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)
        
        # Table des occurrences de tâches
        await conn.execute("""
        CREATE TABLE task_occurrences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id UUID NOT NULL REFERENCES task_definitions(id) ON DELETE CASCADE,
            scheduled_date DATE NOT NULL,
            due_at TIMESTAMPTZ NOT NULL,
            status task_status NOT NULL DEFAULT 'pending',
            assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
            snoozed_until TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(task_id, scheduled_date)
        );
        """)
        
        # Table des complétions de tâches
        await conn.execute("""
        CREATE TABLE task_completions (
            occurrence_id UUID PRIMARY KEY REFERENCES task_occurrences(id) ON DELETE CASCADE,
            completed_by UUID REFERENCES users(id),
            completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            duration_minutes INTEGER,
            comment TEXT,
            photo_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)
        
        # Table des notifications
        await conn.execute("""
        CREATE TABLE notifications (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            occurrence_id UUID REFERENCES task_occurrences(id) ON DELETE CASCADE,
            member_id UUID REFERENCES users(id),
            channel notif_channel NOT NULL,
            sent_at TIMESTAMPTZ,
            delivered BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)

    yield pool
    
    # Nettoyage après les tests
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS notifications CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS task_completions CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS task_occurrences CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS task_definitions CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS rooms CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS household_members CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS households CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS users CASCADE;")
        await conn.execute("DROP TYPE IF EXISTS task_status CASCADE;")
        await conn.execute("DROP TYPE IF EXISTS notif_channel CASCADE;")

    await pool.close()


@pytest.fixture
def client() -> TestClient:
    """Client de test synchrone FastAPI"""
    return TestClient(app)


@pytest.fixture
async def async_client(db_pool: asyncpg.Pool) -> AsyncGenerator[AsyncClient, None]:
    """Client de test asynchrone pour les tests d'intégration"""
    app.state.db_pool = db_pool
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
        "email": f"testuser_{user_uuid}@example.com",
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
        "email": f"admin_{admin_uuid}@example.com",
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
        expires_delta=timedelta(minutes=-1)
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
        "id": uuid4(),
        "name": "Test Household",
        "created_at": datetime.now(timezone.utc)
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
# FIXTURES DÉFINITIONS DE TÂCHES
# ============================================================================

@pytest.fixture
def mock_task_definition(mock_household: Dict[str, Any], mock_room: Dict[str, Any]) -> Dict[str, Any]:
    """Définition de tâche de test"""
    return {
        "id": str(uuid4()),
        "household_id": mock_household["id"],
        "room_id": mock_room["id"],
        "title": "Nettoyer le sol",
        "description": "Passer l'aspirateur et la serpillière",
        "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO,FR",
        "estimated_minutes": 30,
        "is_catalog": False,
        "created_by": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def task_definition_create_data(mock_household: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour créer une définition de tâche"""
    return {
        "household_id": str(mock_household["id"]),
        "title": "Faire la vaisselle",
        "description": "Laver tous les plats dans l'évier",
        "recurrence_rule": "FREQ=DAILY",
        "estimated_minutes": 15,
        "is_catalog": False
    }


@pytest.fixture
def catalog_task_definition() -> Dict[str, Any]:
    """Tâche du catalogue global"""
    return {
        "id": str(uuid4()),
        "household_id": None,
        "title": "Nettoyer les vitres",
        "description": "Nettoyer toutes les vitres de la maison",
        "recurrence_rule": "FREQ=MONTHLY;BYMONTHDAY=1",
        "estimated_minutes": 60,
        "is_catalog": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def recurrence_rules() -> Dict[str, str]:
    """Règles de récurrence de test"""
    return {
        "daily": "FREQ=DAILY",
        "weekdays": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR",
        "weekly": "FREQ=WEEKLY",
        "biweekly": "FREQ=WEEKLY;INTERVAL=2",
        "monthly": "FREQ=MONTHLY",
        "weekly_monday": "FREQ=WEEKLY;BYDAY=MO",
        "twice_weekly": "FREQ=WEEKLY;BYDAY=MO,TH",
        "first_of_month": "FREQ=MONTHLY;BYMONTHDAY=1",
        "last_of_month": "FREQ=MONTHLY;BYMONTHDAY=-1",
        "quarterly": "FREQ=MONTHLY;INTERVAL=3",
        "yearly": "FREQ=YEARLY",
        "limited": "FREQ=DAILY;COUNT=5",
        "until_date": f"FREQ=WEEKLY;UNTIL={date.today() + timedelta(days=30):%Y%m%d}"
    }


# ============================================================================
# FIXTURES OCCURRENCES DE TÂCHES
# ============================================================================

@pytest.fixture
def mock_task_occurrence(mock_task_definition: Dict[str, Any]) -> Dict[str, Any]:
    """Occurrence de tâche de test"""
    return {
        "id": str(uuid4()),
        "task_id": mock_task_definition["id"],
        "scheduled_date": date.today().isoformat(),
        "due_at": datetime.combine(date.today(), datetime.max.time()).isoformat(),
        "status": TaskStatus.PENDING.value,
        "assigned_to": None,
        "snoozed_until": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def task_occurrence_create_data(mock_task_definition: Dict[str, Any]) -> Dict[str, Any]:
    """Données pour créer une occurrence"""
    return {
        "task_id": mock_task_definition["id"],
        "scheduled_date": date.today().isoformat(),
        "due_at": datetime.combine(date.today(), datetime.max.time()).isoformat()
    }


@pytest.fixture
def task_completion_data() -> Dict[str, Any]:
    """Données pour compléter une tâche"""
    return {
        "duration_minutes": 25,
        "comment": "Bien nettoyé, utilisé le nouveau produit",
        "photo_url": "https://example.com/photo.jpg"
    }


@pytest.fixture
def task_snooze_data() -> Dict[str, Any]:
    """Données pour reporter une tâche"""
    return {
        "snoozed_until": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
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
    yield

    # Nettoyage après le test
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM notifications WHERE TRUE")
        await conn.execute("DELETE FROM task_completions WHERE TRUE")
        await conn.execute("DELETE FROM task_occurrences WHERE TRUE")
        await conn.execute("DELETE FROM task_definitions WHERE TRUE")
        await conn.execute("DELETE FROM rooms WHERE TRUE")
        await conn.execute("DELETE FROM household_members WHERE TRUE")
        await conn.execute("DELETE FROM households WHERE TRUE")


@pytest.fixture
def anyio_backend():
    """Backend pour les tests async avec anyio"""
    return "asyncio"


# ============================================================================
# FIXTURES POUR TESTS D'INTÉGRATION
# ============================================================================

@pytest.fixture
async def test_household_with_user(db_pool: asyncpg.Pool, mock_user: Dict[str, Any]):
    """Crée un ménage avec un utilisateur admin pour les tests"""
    from app.core.database import create_household
    
    # Créer l'utilisateur dans la DB
    user_id = UUID(mock_user["id"])
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
            VALUES ($1, $2, $3, $4, NOW())
            """,
            user_id, mock_user["email"], mock_user["full_name"], "hashed_password"
        )
    
    # Créer le ménage
    household = await create_household(db_pool, "Test House", user_id)
    
    return {
        "household": household,
        "user": mock_user,
        "user_id": user_id
    }


@pytest.fixture
async def test_task_definition(db_pool: asyncpg.Pool, test_household_with_user):
    """Crée une définition de tâche pour les tests"""
    from app.core.database import create_task_definition
    
    household = test_household_with_user["household"]
    user_id = test_household_with_user["user_id"]
    
    task_def = await create_task_definition(
        db_pool,
        title="Test Task",
        recurrence_rule="FREQ=WEEKLY;BYDAY=MO,WE,FR",
        household_id=household["id"],
        description="Test task description",
        estimated_minutes=30,
        created_by=user_id
    )
    
    return task_def