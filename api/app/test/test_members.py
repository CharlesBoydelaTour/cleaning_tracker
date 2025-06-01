"""
Tests pour la gestion des membres de ménages
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
import asyncpg

from app.schemas.member import HouseholdMemberCreate
from app.core.database import (
    create_household, 
    create_household_member,
    get_household_members,
    get_household_member
)


class TestMemberSchemas:
    """Tests unitaires pour les schémas de membres"""
    
    def test_member_create_valid(self):
        """Test de création d'un schéma HouseholdMemberCreate valide"""
        data = {
            "user_id": uuid4(),
            "role": "member"
        }
        member = HouseholdMemberCreate(**data)
        
        assert member.user_id == data["user_id"]
        assert member.role == "member"
    
    def test_member_create_invalid_role(self):
        """Test avec un rôle invalide"""
        with pytest.raises(ValueError):
            HouseholdMemberCreate(
                user_id=uuid4(),
                role="superadmin"  # Rôle non valide
            )
    
    def test_member_roles(self):
        """Test des rôles valides"""
        valid_roles = ["admin", "member", "guest"]
        user_id = uuid4()
        
        for role in valid_roles:
            member = HouseholdMemberCreate(user_id=user_id, role=role)
            assert member.role == role
    
    def test_member_default_role(self):
        """Test du rôle par défaut"""
        member = HouseholdMemberCreate(user_id=uuid4())
        assert member.role == "member"


class TestMemberDatabase:
    """Tests unitaires pour les opérations de base de données"""
    
    @pytest.mark.asyncio
    async def test_create_member(self, db_pool: asyncpg.Pool):
        """Test de création d'un membre"""
        user_id = uuid4()
        
        # Créer un utilisateur fictif pour satisfaire la contrainte de clé étrangère
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                user_id, f"test_{user_id}@example.com", "hashed_password"
            )
            
        household = await create_household(db_pool, "Test House")
        
        member = await create_household_member(
            db_pool, 
            household["id"], 
            user_id, 
            "member"
        )
        
        assert member["id"]
        assert member["household_id"] == household["id"]
        assert member["user_id"] == user_id
        assert member["role"] == "member"
    
    @pytest.mark.asyncio
    async def test_create_duplicate_member(self, db_pool: asyncpg.Pool):
        """Test d'ajout d'un membre déjà existant"""
        user_id = uuid4()
        
        # Créer un utilisateur fictif pour satisfaire la contrainte de clé étrangère
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                user_id, f"test_{user_id}@example.com", "hashed_password"
            )
            
        household = await create_household(db_pool, "Test House", user_id)
        
        # Essayer d'ajouter le même utilisateur une deuxième fois
        with pytest.raises(ValueError) as exc_info:
            await create_household_member(
                db_pool,
                household["id"],
                user_id,
                "member"
            )
        
        assert "déjà membre" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_household_members(self, db_pool: asyncpg.Pool):
        """Test de récupération des membres d'un ménage"""
        household = await create_household(db_pool, "Test House")
        
        # Ajouter plusieurs membres
        user1 = uuid4()
        user2 = uuid4()
        user3 = uuid4()
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6), ($7, $8, $9)",
                user1, f"test_{user1}@example.com", "hashed_password",
                user2, f"test_{user2}@example.com", "hashed_password",
                user3, f"test_{user3}@example.com", "hashed_password"
            )

        await create_household_member(db_pool, household["id"], user1, "admin")
        await create_household_member(db_pool, household["id"], user2, "member")
        await create_household_member(db_pool, household["id"], user3, "guest")
        
        members = await get_household_members(db_pool, household["id"])
        
        assert len(members) == 3
        roles = [m["role"] for m in members]
        assert "admin" in roles
        assert "member" in roles
        assert "guest" in roles
    
    @pytest.mark.asyncio
    async def test_get_specific_member(self, db_pool: asyncpg.Pool):
        """Test de récupération d'un membre spécifique"""
        user_id = uuid4()
        
        # Créer un utilisateur fictif pour satisfaire la contrainte de clé étrangère
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                user_id, f"test_{user_id}@example.com", "hashed_password"
            )
            
        household = await create_household(db_pool, "Test House")
        
        created_member = await create_household_member(
            db_pool,
            household["id"],
            user_id,
            "admin"
        )
        
        member = await get_household_member(
            db_pool,
            household["id"],
            created_member["id"]
        )
        
        assert member
        assert member["id"] == created_member["id"]
        assert member["user_id"] == user_id
        assert member["role"] == "admin"


class TestMemberEndpoints:
    """Tests d'intégration pour les endpoints de membres"""
    
    async def test_add_member_to_household(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        auth_headers: dict
    ):
        """Test d'ajout d'un membre à un ménage"""
        admin_id = uuid4()
        new_user_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                new_user_id, f"user_{new_user_id}@example.com", "hashed_password"
            )
        # household = await create_household(db_pool, "Test House", admin_id) # This line was causing FK error if admin_id not created
        # The above user creation should fix it.

        household = await create_household(db_pool, "Test House", admin_id)
        
        member_data = {
            "user_id": str(new_user_id),
            "role": "member"
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={admin_id}",
            json=member_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["user_id"] == str(new_user_id)
        assert data["role"] == "member"
        assert data["household_id"] == str(household["id"])
    
    async def test_add_self_as_admin(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test d'auto-ajout comme admin (cas spécial)"""
        # Créer un ménage sans membres
        household = await create_household(db_pool, "Empty House")
        
        # Un utilisateur s'ajoute lui-même comme admin
        user_id = uuid4()
        # Créer l'utilisateur dans la base de données
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                user_id, f"user_{user_id}@example.com", "hashed_password"
            )

        member_data = {
            "user_id": str(user_id),
            "role": "admin"
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={user_id}",
            json=member_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"
    
    async def test_add_member_unauthorized(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test d'ajout de membre sans autorisation"""
        # Créer un ménage
        admin_id = uuid4() # Utilisateur qui crée le ménage
        non_member_id = uuid4()
        new_user_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6), ($7, $8, $9)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                non_member_id, f"non_member_{non_member_id}@example.com", "hashed_password",
                new_user_id, f"new_user_{new_user_id}@example.com", "hashed_password"
            )

        household = await create_household(db_pool, "Private House", admin_id)
        
        # Un utilisateur non membre essaie d'ajouter quelqu'un
        member_data = {
            "user_id": str(new_user_id),
            "role": "member"
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={non_member_id}",
            json=member_data
        )
        
        assert response.status_code == 403
        error = response.json()
        assert "permissions" in error["error"]["message"].lower()
    
    async def test_list_household_members(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération de la liste des membres"""
        # Créer un ménage avec des membres
        admin_id = uuid4()
        user_member_id = uuid4()
        user_guest_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6), ($7, $8, $9)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                user_member_id, f"member_{user_member_id}@example.com", "hashed_password",
                user_guest_id, f"guest_{user_guest_id}@example.com", "hashed_password"
            )
        household = await create_household(db_pool, "Test House", admin_id)
        
        # Ajouter d'autres membres
        await create_household_member(db_pool, household["id"], user_member_id, "member")
        await create_household_member(db_pool, household["id"], user_guest_id, "guest")
        
        response = await async_client.get(
            f"/households/{household['id']}/members?user_id={admin_id}"
        )
        
        assert response.status_code == 200
        members = response.json()
        
        assert len(members) >= 3  # Au moins l'admin + 2 membres ajoutés
        roles = [m["role"] for m in members]
        assert "admin" in roles
        assert "member" in roles
        assert "guest" in roles
    
    async def test_get_member_details(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération des détails d'un membre"""
        admin_id = uuid4()
        user_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                user_id, f"user_{user_id}@example.com", "hashed_password"
            )

        household = await create_household(db_pool, "Test House", admin_id)
        
        member = await create_household_member(
            db_pool,
            household["id"],
            user_id,
            "member"
        )
        
        response = await async_client.get(
            f"/households/{household['id']}/members/{member['id']}?user_id={admin_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(member["id"])
        assert data["user_id"] == str(user_id)
        assert data["role"] == "member"
    
    async def test_get_member_not_found(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération d'un membre inexistant"""
        admin_id = uuid4()
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password"
            )
        household = await create_household(db_pool, "Test House", admin_id)
        
        fake_member_id = uuid4()
        response = await async_client.get(
            f"/households/{household['id']}/members/{fake_member_id}?user_id={admin_id}"
        )
        
        assert response.status_code == 404
        error = response.json()
        assert "error" in error
        assert "non trouvé" in error["error"]["message"].lower()
    
    async def test_add_member_with_invalid_role(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test d'ajout avec un rôle invalide"""
        admin_id = uuid4()
        new_user_id = uuid4() # Ajouté pour la cohérence du test, même si non utilisé directement ici pour l'erreur initiale
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                new_user_id, f"user_{new_user_id}@example.com", "hashed_password"
            )
        household = await create_household(db_pool, "Test House", admin_id)
        
        member_data = {
            "user_id": str(new_user_id),
            "role": "superuser"  # Rôle invalide
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={admin_id}",
            json=member_data
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "validation" in error["error"]["message"].lower()
    
    async def test_add_duplicate_member(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test d'ajout d'un membre déjà existant"""
        admin_id = uuid4()
        user_to_add_id = uuid4() # Ajouté pour la cohérence du test
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                user_to_add_id, f"user_{user_to_add_id}@example.com", "hashed_password"
            )
        household = await create_household(db_pool, "Test House", admin_id)
        
        # Ajouter un membre
        await create_household_member(db_pool, household["id"], user_to_add_id, "member")
        
        # Essayer de l'ajouter à nouveau
        member_data = {
            "user_id": str(user_to_add_id),
            "role": "guest"
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={admin_id}",
            json=member_data
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "déjà membre" in error["error"]["message"]


class TestMemberPermissions:
    """Tests pour les permissions des membres"""
    
    @pytest.mark.asyncio
    async def test_member_cannot_add_admin(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test qu'un membre simple ne peut pas ajouter un admin"""
        admin_id = uuid4()
        member_id = uuid4()
        new_admin_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6), ($7, $8, $9)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                member_id, f"member_{member_id}@example.com", "hashed_password",
                new_admin_id, f"new_admin_{new_admin_id}@example.com", "hashed_password"
            )

        household = await create_household(db_pool, "Test House", admin_id)
        await create_household_member(db_pool, household["id"], member_id, "member")

        member_data = {
            "user_id": str(new_admin_id),
            "role": "admin"
        }

        response = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={member_id}",
            json=member_data
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_guest_cannot_add_members(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test qu'un invité ne peut pas ajouter de membres"""
        admin_id = uuid4()
        guest_id = uuid4()
        new_user_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6), ($7, $8, $9)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                guest_id, f"guest_{guest_id}@example.com", "hashed_password",
                new_user_id, f"new_user_{new_user_id}@example.com", "hashed_password"
            )

        household = await create_household(db_pool, "Test House", admin_id)
        await create_household_member(db_pool, household["id"], guest_id, "guest")

        member_data = {
            "user_id": str(new_user_id),
            "role": "member"
        }

        response = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={guest_id}",
            json=member_data
        )
        assert response.status_code == 403


class TestMemberWorkflow:
    """Tests des workflows complets de gestion des membres"""
    
    @pytest.mark.asyncio
    async def test_complete_member_lifecycle(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test du cycle de vie complet d'un membre"""
        admin_id = uuid4()
        user1_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password",
                user1_id, f"user1_{user1_id}@example.com", "hashed_password"
            )

        household = await create_household(db_pool, "Family House", admin_id)

        # 2. Ajouter un membre
        member_data_create = {"user_id": str(user1_id), "role": "member"}
        response_create = await async_client.post(
            f"/households/{household['id']}/members?requesting_user_id={admin_id}", json=member_data_create
        )
        assert response_create.status_code == 201
        member1_id = response_create.json()["id"]

        # 3. Lister les membres (vérifier que le membre est là)
        response_list = await async_client.get(f"/households/{household['id']}/members?user_id={admin_id}")
        assert response_list.status_code == 200
        members = response_list.json()
        assert any(m["user_id"] == str(user1_id) and m["id"] == member1_id for m in members)

        # 4. Obtenir les détails du membre
        response_get = await async_client.get(f"/households/{household['id']}/members/{member1_id}?user_id={admin_id}")
        assert response_get.status_code == 200
        assert response_get.json()["user_id"] == str(user1_id)

        # 5. Mettre à jour le rôle du membre
        member_data_update = {"role": "admin"} # Le membre devient admin
        response_update = await async_client.put(
            f"/households/{household['id']}/members/{member1_id}?requesting_user_id={admin_id}", json=member_data_update
        )
        assert response_update.status_code == 200
        assert response_update.json()["role"] == "admin"

        # 6. Supprimer le membre
        response_delete = await async_client.delete(f"/households/{household['id']}/members/{member1_id}?requesting_user_id={admin_id}")
        assert response_delete.status_code == 204

        # 7. Vérifier que le membre est supprimé
        response_get_after_delete = await async_client.get(f"/households/{household['id']}/members/{member1_id}?user_id={admin_id}")
        assert response_get_after_delete.status_code == 404

    @pytest.mark.asyncio
    async def test_multiple_households_membership(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test qu'un utilisateur peut être membre de plusieurs ménages"""
        user_id = uuid4()
        admin1_id = uuid4()
        admin2_id = uuid4()
        admin3_id = uuid4()

        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3), ($4, $5, $6), ($7, $8, $9), ($10, $11, $12)",
                user_id, f"user_{user_id}@example.com", "hashed_password",
                admin1_id, f"admin1_{admin1_id}@example.com", "hashed_password",
                admin2_id, f"admin2_{admin2_id}@example.com", "hashed_password",
                admin3_id, f"admin3_{admin3_id}@example.com", "hashed_password"
            )

        households_info = []
        roles = ["admin", "member", "guest"]
        admin_ids = [user_id, admin2_id, admin3_id] # user_id est admin de la première maison

        for i, role in enumerate(roles):
            current_admin_id = admin_ids[i]
            household = await create_household(db_pool, f"House {i+1}", current_admin_id)
            member_data = {"user_id": str(user_id), "role": role}
            
            # L'utilisateur s'ajoute lui-même si admin, sinon l'admin de la maison l'ajoute
            requesting_user = user_id if role == "admin" else current_admin_id
            
            # Si l'utilisateur est déjà l'admin (créé via create_household), on ne le rajoute pas
            if not (role == "admin" and current_admin_id == user_id):
                response_add = await async_client.post(
                    f"/households/{household['id']}/members?requesting_user_id={requesting_user}", json=member_data
                )
                assert response_add.status_code == 201
                member_id = response_add.json()["id"]
            else:
                # Trouver l'ID de membre de l'admin créé par create_household
                async with db_pool.acquire() as conn:
                    member_record = await conn.fetchrow(
                        "SELECT id FROM household_members WHERE household_id = $1 AND user_id = $2",
                        household['id'], user_id
                    )
                    member_id = member_record['id']
            
            households_info.append({"household_id": household["id"], "member_id": member_id, "role": role})

        # Vérifier l'appartenance et le rôle dans chaque ménage
        for info in households_info:
            response_get = await async_client.get(f"/households/{info['household_id']}/members/{info['member_id']}?user_id={user_id}")
            assert response_get.status_code == 200
            member_details = response_get.json()
            assert member_details["user_id"] == str(user_id)
            assert member_details["role"] == info["role"]
            assert member_details["household_id"] == str(info["household_id"])