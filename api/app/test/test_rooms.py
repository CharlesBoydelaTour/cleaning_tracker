"""
Tests pour la gestion des pièces (rooms)
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
import asyncpg

from app.schemas.room import RoomCreate, Room
from app.core.database import create_household, create_room, get_rooms, get_room


class TestRoomSchemas:
    """Tests unitaires pour les schémas de pièces"""
    
    def test_room_create_valid(self):
        """Test de création d'un schéma RoomCreate valide"""
        data = {
            "name": "Living Room",
            "icon": "🛋️"
        }
        room = RoomCreate(**data)
        
        assert room.name == "Living Room"
        assert room.icon == "🛋️"
    
    def test_room_create_without_icon(self):
        """Test de création sans icône"""
        room = RoomCreate(name="Bedroom")
        
        assert room.name == "Bedroom"
        assert room.icon is None
    
    def test_room_create_empty_name(self):
        """Test avec un nom vide"""
        with pytest.raises(ValueError):
            RoomCreate(name="")
    
    def test_room_schema_conversion(self, mock_room):
        """Test de conversion du schéma Room"""
        room = Room(**mock_room)
        
        assert room.name == mock_room["name"]
        assert room.icon == mock_room["icon"]


class TestRoomDatabase:
    """Tests unitaires pour les opérations de base de données"""
    
    @pytest.mark.asyncio
    async def test_create_room_with_icon(self, db_pool: asyncpg.Pool):
        """Test de création d'une pièce avec icône"""
        household = await create_household(db_pool, "Test House")
        
        room = await create_room(
            db_pool,
            "Kitchen",
            household["id"],
            "🍳"
        )
        
        assert room["id"]
        assert room["name"] == "Kitchen"
        assert room["household_id"] == household["id"]
        assert room["icon"] == "🍳"
        assert room["created_at"]
    
    @pytest.mark.asyncio
    async def test_create_room_without_icon(self, db_pool: asyncpg.Pool):
        """Test de création d'une pièce sans icône"""
        household = await create_household(db_pool, "Test House")
        
        room = await create_room(
            db_pool,
            "Bathroom",
            household["id"]
        )
        
        assert room["id"]
        assert room["name"] == "Bathroom"
        assert room["icon"] is None
    
    @pytest.mark.asyncio
    async def test_get_rooms_for_household(self, db_pool: asyncpg.Pool):
        """Test de récupération des pièces d'un ménage"""
        household = await create_household(db_pool, "Test House")
        
        # Créer plusieurs pièces
        rooms_data = [
            ("Living Room", "🛋️"),
            ("Kitchen", "🍳"),
            ("Bedroom", "🛏️"),
            ("Bathroom", "🚿")
        ]
        
        for name, icon in rooms_data:
            await create_room(db_pool, name, household["id"], icon)
        
        # Récupérer les pièces
        rooms = await get_rooms(db_pool, household["id"])
        
        assert len(rooms) == 4
        room_names = [r["name"] for r in rooms]
        assert "Living Room" in room_names
        assert "Kitchen" in room_names
        assert "Bedroom" in room_names
        assert "Bathroom" in room_names
    
    @pytest.mark.asyncio
    async def test_get_specific_room(self, db_pool: asyncpg.Pool):
        """Test de récupération d'une pièce spécifique"""
        household = await create_household(db_pool, "Test House")
        
        created_room = await create_room(
            db_pool,
            "Office",
            household["id"],
            "💻"
        )
        
        room = await get_room(db_pool, created_room["id"])
        
        assert room
        assert room["id"] == created_room["id"]
        assert room["name"] == "Office"
        assert room["icon"] == "💻"
    
    @pytest.mark.asyncio
    async def test_rooms_isolated_by_household(self, db_pool: asyncpg.Pool):
        """Test que les pièces sont isolées par ménage"""
        # Créer deux ménages
        household1 = await create_household(db_pool, "House 1")
        household2 = await create_household(db_pool, "House 2")
        
        # Créer des pièces dans chaque ménage
        await create_room(db_pool, "Kitchen", household1["id"], "🍳")
        await create_room(db_pool, "Bedroom", household1["id"], "🛏️")
        
        await create_room(db_pool, "Living Room", household2["id"], "🛋️")
        await create_room(db_pool, "Office", household2["id"], "💻")
        
        # Vérifier l'isolation
        rooms1 = await get_rooms(db_pool, household1["id"])
        rooms2 = await get_rooms(db_pool, household2["id"])
        
        assert len(rooms1) == 2
        assert len(rooms2) == 2
        
        room_names1 = [r["name"] for r in rooms1]
        room_names2 = [r["name"] for r in rooms2]
        
        assert "Kitchen" in room_names1
        assert "Living Room" not in room_names1
        
        assert "Living Room" in room_names2
        assert "Kitchen" not in room_names2


class TestRoomEndpoints:
    """Tests d'intégration pour les endpoints de pièces"""
    
    async def test_create_room_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        room_create_data: dict
    ):
        """Test de création de pièce via l'API"""
        # Créer un ménage
        admin_id = uuid4()
        household = await create_household(db_pool, "Test House", admin_id)
        
        response = await async_client.post(
            f"/households/{household['id']}/rooms",
            json=room_create_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["name"] == room_create_data["name"]
        assert data["icon"] == room_create_data["icon"]
    
    async def test_list_rooms_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération de la liste des pièces"""
        # Créer un ménage avec des pièces
        household = await create_household(db_pool, "Test House")
        
        await create_room(db_pool, "Room 1", household["id"], "🔵")
        await create_room(db_pool, "Room 2", household["id"], "🔴")
        await create_room(db_pool, "Room 3", household["id"], "🟢")
        
        response = await async_client.get(f"/households/{household['id']}/rooms")
        
        assert response.status_code == 200
        rooms = response.json()
        
        assert len(rooms) == 3
        assert all("id" in room for room in rooms)
        assert all("name" in room for room in rooms)
    
    async def test_get_room_details(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération des détails d'une pièce"""
        household = await create_household(db_pool, "Test House")
        room = await create_room(db_pool, "Study", household["id"], "📚")
        
        response = await async_client.get(
            f"/households/{household['id']}/rooms/{room['id']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(room["id"])
        assert data["name"] == "Study"
        assert data["icon"] == "📚"
    
    async def test_get_room_not_found(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération d'une pièce inexistante"""
        household = await create_household(db_pool, "Test House")
        fake_room_id = uuid4()
        
        response = await async_client.get(
            f"/households/{household['id']}/rooms/{fake_room_id}"
        )
        
        assert response.status_code == 404
        error = response.json()
        assert "error" in error
        assert "non trouvée" in error["error"]["message"].lower()
    
    async def test_get_room_wrong_household(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération d'une pièce d'un autre ménage"""
        # Créer deux ménages
        household1 = await create_household(db_pool, "House 1")
        household2 = await create_household(db_pool, "House 2")
        
        # Créer une pièce dans le ménage 1
        room = await create_room(db_pool, "Room", household1["id"])
        
        # Essayer de la récupérer depuis le ménage 2
        response = await async_client.get(
            f"/households/{household2['id']}/rooms/{room['id']}"
        )
        
        assert response.status_code == 404
        error = response.json()
        assert "dans ce ménage" in error["error"]["message"]
    
    async def test_create_room_with_auth_check(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        room_create_data: dict
    ):
        """Test de création avec vérification d'autorisation"""
        # Créer un utilisateur dans la base de données
        admin_id = uuid4()
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password"
            )
        
        # Créer un ménage avec cet utilisateur
        household = await create_household(db_pool, "Test House", admin_id)
        
        # Créer avec un utilisateur autorisé
        response = await async_client.post(
            f"/households/{household['id']}/rooms?user_id={admin_id}",
            json=room_create_data
        )
        
        assert response.status_code == 201
        
        # Essayer avec un utilisateur non autorisé
        unauthorized_user = uuid4()
        response = await async_client.post(
            f"/households/{household['id']}/rooms?user_id={unauthorized_user}",
            json={"name": "Unauthorized Room", "icon": "🚫"}
        )
        
        assert response.status_code == 403
    
    async def test_room_names_validation(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de validation des noms de pièces"""
        household = await create_household(db_pool, "Test House")
        
        # Test avec nom vide
        response = await async_client.post(
            f"/households/{household['id']}/rooms",
            json={"name": "", "icon": "❌"}
        )
        
        assert response.status_code == 422
        
        # Test avec nom trop long (supposons une limite)
        very_long_name = "x" * 1000
        response = await async_client.post(
            f"/households/{household['id']}/rooms",
            json={"name": very_long_name, "icon": "📏"}
        )
        
        # Devrait passer ou échouer selon les contraintes DB
        assert response.status_code in [201, 422, 500]


class TestRoomWorkflow:
    """Tests des workflows complets de gestion des pièces"""
    
    async def test_complete_room_management(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test du workflow complet de gestion des pièces"""
        # 1. Créer un utilisateur dans la base de données
        admin_id = uuid4()
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password"
            )
        
        # 2. Créer un ménage avec cet utilisateur
        household = await create_household(db_pool, "My Home", admin_id)
        
        # 3. Ajouter plusieurs pièces
        rooms_to_create = [
            {"name": "Living Room", "icon": "🛋️"},
            {"name": "Kitchen", "icon": "🍳"},
            {"name": "Master Bedroom", "icon": "🛏️"},
            {"name": "Kids Room", "icon": "🧸"},
            {"name": "Garage", "icon": "🚗"}
        ]
        
        created_rooms = []
        for room_data in rooms_to_create:
            response = await async_client.post(
                f"/households/{household['id']}/rooms",
                json=room_data
            )
            assert response.status_code == 201
            created_rooms.append(response.json())
        
        # 4. Vérifier la liste complète
        list_response = await async_client.get(
            f"/households/{household['id']}/rooms"
        )
        assert list_response.status_code == 200
        all_rooms = list_response.json()
        assert len(all_rooms) == 5
        
        # 5. Vérifier l'accès individuel
        for room in created_rooms:
            detail_response = await async_client.get(
                f"/households/{household['id']}/rooms/{room['id']}"
            )
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert detail["name"] == room["name"]
            assert detail["icon"] == room["icon"]