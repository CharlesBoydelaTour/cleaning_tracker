"""
Tests unitaires et d'intégration pour les fonctionnalités de ménages
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
import uuid  # Import the uuid module itself for conversions
import asyncpg

from app.schemas.household import HouseholdCreate, Household
from app.core.database import create_household, get_households


class TestHouseholdSchemas:
    """Tests unitaires pour les schémas de ménages"""
    
    def test_household_create_valid(self):
        """Test de création d'un schéma HouseholdCreate valide"""
        data = {"name": "Ma Maison"}
        household = HouseholdCreate(**data)
        
        assert household.name == "Ma Maison"
    
    def test_household_create_empty_name(self):
        """Test avec un nom vide"""
        with pytest.raises(ValueError):
            HouseholdCreate(name="")
    
    def test_household_schema_conversion(self, mock_household):
        """Test de conversion du schéma Household"""
        household = Household(**mock_household)
        
        assert household.id == mock_household["id"]  # Compare UUID directly
        assert household.name == mock_household["name"]
        assert household.created_at == mock_household["created_at"] # Compare datetime directly


class TestHouseholdDatabase:
    """Tests unitaires pour les opérations de base de données"""
    
    @pytest.mark.asyncio
    async def test_create_household_without_user(self, db_pool: asyncpg.Pool):
        """Test de création de ménage sans utilisateur"""
        household = await create_household(db_pool, "Test House")
        
        assert household["id"]
        assert household["name"] == "Test House"
        assert household["created_at"]
    
    @pytest.mark.asyncio
    async def test_create_household_with_user(self, db_pool: asyncpg.Pool, mock_user: dict): # Added mock_user
        """Test de création de ménage avec utilisateur admin"""
        user_id = uuid4() # This will be the ID of the new user we create
        email = f"user_{user_id}@example.com"
        full_name = "Test User for Household Creation"
        
        # Create a dummy user in the database
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO NOTHING;
                """,
                user_id, email, full_name, "hashed_password"
            )
        
        household = await create_household(db_pool, "Test House", user_id)
        
        assert household["id"]
        assert household["name"] == "Test House"
        
        # Vérifier que l'utilisateur a été ajouté comme admin
        async with db_pool.acquire() as conn:
            member = await conn.fetchrow(
                """
                SELECT role FROM household_members 
                WHERE household_id = $1 AND user_id = $2
                """,
                household["id"],
                user_id
            )
            assert member
            assert member["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_get_households_all(self, db_pool: asyncpg.Pool):
        """Test de récupération de tous les ménages"""
        # Créer quelques ménages
        await create_household(db_pool, "House 1")
        await create_household(db_pool, "House 2")
        
        households = await get_households(db_pool)
        
        assert len(households) >= 2
        assert all("id" in h for h in households)
        assert all("name" in h for h in households)
    
    @pytest.mark.asyncio
    async def test_get_households_by_user(self, db_pool: asyncpg.Pool):
        """Test de récupération des ménages d'un utilisateur"""
        user_id = uuid4()
        other_user_id = uuid4()

        # Create dummy users in the database
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW()), ($5, $6, $7, $8, NOW())
                ON CONFLICT (id) DO NOTHING;
                """,
                user_id, f"user_{user_id}@example.com", "Test User 1", "hashed_password",
                other_user_id, f"user_{other_user_id}@example.com", "Test User 2", "hashed_password"
            )
        
        # Créer des ménages pour différents utilisateurs
        h1 = await create_household(db_pool, "User House 1", user_id)
        h2 = await create_household(db_pool, "User House 2", user_id)
        h3 = await create_household(db_pool, "Other User House", other_user_id)
        
        # Récupérer seulement les ménages de l'utilisateur
        user_households = await get_households(db_pool, user_id)
        
        household_ids = [h["id"] for h in user_households]
        assert h1["id"] in household_ids
        assert h2["id"] in household_ids
        assert h3["id"] not in household_ids


class TestHouseholdEndpoints:
    """Tests d'intégration pour les endpoints de ménages"""
    
    @pytest.mark.asyncio
    async def test_create_household_endpoint(
        self,
        async_client: AsyncClient,
        household_create_data: dict,
        auth_headers: dict, 
        mock_user: dict,
        db_pool: asyncpg.Pool 
    ):
        """Test de création de ménage via l'API"""
        requesting_user_id = uuid.UUID(mock_user['id']) # Corrected: uuid.UUID()
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO NOTHING; 
                """,
                requesting_user_id, mock_user['email'], mock_user['full_name'], "hashed_password"
            )

        response = await async_client.post(
            f"/households/?requesting_user_id={requesting_user_id}", 
            json=household_create_data,
            headers=auth_headers 
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["name"] == household_create_data["name"]
        assert "created_at" in data
    
    async def test_list_households_endpoint(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test de récupération de la liste des ménages"""
        response = await async_client.get("/households/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    async def test_get_household_details(
        self,
        async_client: AsyncClient,
        auth_headers: dict, 
        mock_user: dict,    
        db_pool: asyncpg.Pool
    ):
        """Test de récupération des détails d'un ménage"""
        owner_user_id = uuid.UUID(mock_user['id']) # Corrected: uuid.UUID()
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO NOTHING; 
                """,
                owner_user_id, mock_user['email'], mock_user['full_name'], "hashed_password"
            )
        
        household = await create_household(db_pool, "Test House Details", owner_user_id)
        
        response = await async_client.get(
            f"/households/{household['id']}", 
            headers=auth_headers 
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(household["id"])
        assert data["name"] == household["name"]
    
    async def test_get_household_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test de récupération d'un ménage inexistant"""
        fake_id = uuid4()
        response = await async_client.get(f"/households/{fake_id}")
        
        assert response.status_code == 404
        error = response.json()
        assert "error" in error
        assert "n'existe pas" in error["error"]["message"]
    
    async def test_get_household_unauthorized(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test d'accès non autorisé à un ménage"""
        # Créer un ménage sans y ajouter l'utilisateur
        household = await create_household(db_pool, "Private House")
        
        # Essayer d'y accéder avec un utilisateur non membre
        response = await async_client.get(
            f"/households/{household['id']}?user_id={uuid4()}"
        )
        
        assert response.status_code == 403
        error = response.json()
        assert error["error"]["code"] == "UNAUTHORIZED_ACCESS"
    
    async def test_create_household_validation_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_user: dict
    ):
        """Test de création avec données invalides"""
        invalid_data = {"name": 123}  # name devrait être une string
        
        response = await async_client.post(
            f"/households/?requesting_user_id={mock_user['id']}",
            json=invalid_data
        )
        
        assert response.status_code == 422
    
    async def test_household_member_auto_add(
        self,
        async_client: AsyncClient,
        household_create_data: dict,
        auth_headers: dict, 
        mock_user: dict,    
        db_pool: asyncpg.Pool
    ):
        """Test que le créateur est automatiquement ajouté comme admin"""
        requesting_user_id = uuid.UUID(mock_user['id']) # Corrected: uuid.UUID()
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO NOTHING;
                """,
                requesting_user_id, mock_user['email'], mock_user['full_name'], "hashed_password"
            )
            
        response = await async_client.post(
            f"/households/?requesting_user_id={requesting_user_id}",
            json=household_create_data,
            headers=auth_headers 
        )
        
        assert response.status_code == 201
        household = response.json()
        
        # Vérifier dans la base que l'utilisateur est bien admin
        async with db_pool.acquire() as conn:
            member = await conn.fetchrow(
                """
                SELECT role FROM household_members 
                WHERE household_id = $1 AND user_id = $2
                """,
                household["id"],
                requesting_user_id
            )
            assert member
            assert member["role"] == "admin"


class TestHouseholdAccessControl:
    """Tests pour le contrôle d'accès aux ménages"""
    
    @pytest.mark.asyncio
    async def test_check_household_access_member(self, db_pool: asyncpg.Pool, mock_user: dict): 
        """Test de vérification d'accès pour un membre"""
        from app.routers.households import check_household_access
        
        user_id = uuid.UUID(mock_user['id']) # Corrected: uuid.UUID()
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO NOTHING;
                """,
                user_id, mock_user['email'], mock_user['full_name'], "hashed_password"
            )

        household = await create_household(db_pool, "Test House", user_id)
        
        has_access = await check_household_access(
            db_pool, 
            household["id"], 
            str(user_id) 
        )
        assert has_access is True
    
    @pytest.mark.asyncio
    async def test_check_household_access_non_member(self, db_pool: asyncpg.Pool, mock_user: dict): 
        """Test de vérification d'accès pour un non-membre"""
        from app.routers.households import check_household_access
        
        owner_user_id = uuid4() # This is fine, creates a new random UUID
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO NOTHING;
                """,
                owner_user_id, f"owner_{owner_user_id}@example.com", "Owner User", "hashed_password"
            )
        household = await create_household(db_pool, "Test House", owner_user_id)
        
        non_member_id = uuid.UUID(mock_user['id']) # Corrected: uuid.UUID()
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, email_confirmed_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (id) DO NOTHING;
                """,
                non_member_id, mock_user['email'], mock_user['full_name'], "hashed_password"
            )

        has_access = await check_household_access(
            db_pool,
            household["id"],
            str(non_member_id) 
        )
        assert has_access is False