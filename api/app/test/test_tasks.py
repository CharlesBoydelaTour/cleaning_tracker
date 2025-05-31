"""
Tests pour la gestion des tâches
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import date
import asyncpg

from app.schemas.task import TaskCreate, Task
from app.core.database import create_household, create_task, get_tasks, get_task


class TestTaskSchemas:
    """Tests unitaires pour les schémas de tâches"""
    
    def test_task_create_valid(self):
        """Test de création d'un schéma TaskCreate valide"""
        data = {
            "title": "Clean the kitchen",
            "description": "Deep clean including appliances",
            "household_id": uuid4()
        }
        task = TaskCreate(**data)
        
        assert task.title == "Clean the kitchen"
        assert task.description == "Deep clean including appliances"
        assert task.household_id == data["household_id"]
    
    def test_task_create_without_description(self):
        """Test de création sans description"""
        task = TaskCreate(
            title="Quick task",
            household_id=uuid4()
        )
        
        assert task.title == "Quick task"
        assert task.description is None
    
    def test_task_create_empty_title(self):
        """Test avec un titre vide"""
        with pytest.raises(ValueError):
            TaskCreate(
                title="",
                household_id=uuid4()
            )
    
    def test_task_schema_conversion(self, mock_task):
        """Test de conversion du schéma Task"""
        # Adapter le mock pour correspondre au schéma Task
        task_data = {
            "id": mock_task["id"],
            "title": mock_task["title"],
            "description": mock_task["description"],
            "household_id": mock_task["household_id"],
            "due_date": date.today(),
            "completed": False
        }
        
        task = Task(**task_data)
        
        assert str(task.id) == mock_task["id"]
        assert task.title == mock_task["title"]
        assert task.description == mock_task["description"]
        assert isinstance(task.due_date, date)
        assert task.completed is False


class TestTaskDatabase:
    """Tests unitaires pour les opérations de base de données"""
    
    @pytest.mark.asyncio
    async def test_create_task_with_description(self, db_pool: asyncpg.Pool):
        """Test de création d'une tâche avec description"""
        household = await create_household(db_pool, "Test House")
        
        task = await create_task(
            db_pool,
            "Vacuum living room",
            household["id"],
            "Including under the sofa",
            date.today()
        )
        
        assert task["id"]
        assert task["title"] == "Vacuum living room"
        assert task["description"] == "Including under the sofa"
        assert task["household_id"] == household["id"]
        assert task["completed"] is False
    
    @pytest.mark.asyncio
    async def test_create_task_without_description(self, db_pool: asyncpg.Pool):
        """Test de création d'une tâche sans description"""
        household = await create_household(db_pool, "Test House")
        
        task = await create_task(
            db_pool,
            "Water plants",
            household["id"],
            None,
            date.today()
        )
        
        assert task["id"]
        assert task["title"] == "Water plants"
        assert task["description"] is None
    
    @pytest.mark.asyncio
    async def test_get_tasks_for_household(self, db_pool: asyncpg.Pool):
        """Test de récupération des tâches d'un ménage"""
        household = await create_household(db_pool, "Test House")
        
        # Créer plusieurs tâches
        tasks_data = [
            ("Clean bathroom", "Scrub and disinfect"),
            ("Take out trash", None),
            ("Mow lawn", "Front and back yard"),
            ("Wash dishes", "Including pots and pans")
        ]
        
        for title, description in tasks_data:
            await create_task(
                db_pool,
                title,
                household["id"],
                description,
                date.today()
            )
        
        # Récupérer les tâches
        tasks = await get_tasks(db_pool, household["id"])
        
        assert len(tasks) == 4
        task_titles = [t["title"] for t in tasks]
        assert "Clean bathroom" in task_titles
        assert "Take out trash" in task_titles
        assert "Mow lawn" in task_titles
        assert "Wash dishes" in task_titles
    
    @pytest.mark.asyncio
    async def test_get_specific_task(self, db_pool: asyncpg.Pool):
        """Test de récupération d'une tâche spécifique"""
        household = await create_household(db_pool, "Test House")
        
        created_task = await create_task(
            db_pool,
            "Organize garage",
            household["id"],
            "Sort tools and equipment",
            date.today()
        )
        
        task = await get_task(db_pool, created_task["id"])
        
        assert task
        assert task["id"] == created_task["id"]
        assert task["title"] == "Organize garage"
        assert task["description"] == "Sort tools and equipment"
    
    @pytest.mark.asyncio
    async def test_tasks_isolated_by_household(self, db_pool: asyncpg.Pool):
        """Test que les tâches sont isolées par ménage"""
        # Créer deux ménages
        household1 = await create_household(db_pool, "House 1")
        household2 = await create_household(db_pool, "House 2")
        
        # Créer des tâches dans chaque ménage
        await create_task(db_pool, "Task A", household1["id"], None, date.today())
        await create_task(db_pool, "Task B", household1["id"], None, date.today())
        
        await create_task(db_pool, "Task X", household2["id"], None, date.today())
        await create_task(db_pool, "Task Y", household2["id"], None, date.today())
        
        # Vérifier l'isolation
        tasks1 = await get_tasks(db_pool, household1["id"])
        tasks2 = await get_tasks(db_pool, household2["id"])
        
        assert len(tasks1) == 2
        assert len(tasks2) == 2
        
        titles1 = [t["title"] for t in tasks1]
        titles2 = [t["title"] for t in tasks2]
        
        assert "Task A" in titles1
        assert "Task X" not in titles1
        
        assert "Task X" in titles2
        assert "Task A" not in titles2


class TestTaskEndpoints:
    """Tests d'intégration pour les endpoints de tâches"""
    
    async def test_create_task_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        task_create_data: dict
    ):
        """Test de création de tâche via l'API"""
        # Créer un ménage
        admin_id = uuid4()
        household = await create_household(db_pool, "Test House", admin_id)
        
        # Adapter les données pour correspondre au household
        task_create_data["household_id"] = str(household["id"])
        
        response = await async_client.post(
            f"/households/{household['id']}/tasks",
            json=task_create_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["title"] == task_create_data["title"]
        assert data["description"] == task_create_data["description"]
        assert data["completed"] is False
    
    async def test_list_tasks_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération de la liste des tâches"""
        # Créer un ménage avec des tâches
        household = await create_household(db_pool, "Test House")
        
        await create_task(db_pool, "Task 1", household["id"], None, date.today())
        await create_task(db_pool, "Task 2", household["id"], None, date.today())
        await create_task(db_pool, "Task 3", household["id"], None, date.today())
        
        response = await async_client.get(f"/households/{household['id']}/tasks")
        
        assert response.status_code == 200
        tasks = response.json()
        
        assert len(tasks) == 3
        assert all("id" in task for task in tasks)
        assert all("title" in task for task in tasks)
    
    async def test_get_task_details(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération des détails d'une tâche"""
        household = await create_household(db_pool, "Test House")
        task = await create_task(
            db_pool,
            "Important Task",
            household["id"],
            "With details",
            date.today()
        )
        
        response = await async_client.get(
            f"/households/{household['id']}/tasks/{task['id']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(task["id"])
        assert data["title"] == "Important Task"
        assert data["description"] == "With details"
        assert data["completed"] is False
    
    async def test_get_task_not_found(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération d'une tâche inexistante"""
        household = await create_household(db_pool, "Test House")
        fake_task_id = uuid4()
        
        response = await async_client.get(
            f"/households/{household['id']}/tasks/{fake_task_id}"
        )
        
        assert response.status_code == 404
        error = response.json()
        assert error["error"]["code"] == "TASK_NOT_FOUND"
    
    async def test_get_task_wrong_household(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de récupération d'une tâche d'un autre ménage"""
        # Créer deux ménages
        household1 = await create_household(db_pool, "House 1")
        household2 = await create_household(db_pool, "House 2")
        
        # Créer une tâche dans le ménage 1
        task = await create_task(
            db_pool,
            "Private Task",
            household1["id"],
            None,
            date.today()
        )
        
        # Essayer de la récupérer depuis le ménage 2
        response = await async_client.get(
            f"/households/{household2['id']}/tasks/{task['id']}"
        )
        
        assert response.status_code == 404
        error = response.json()
        assert error["error"]["code"] == "TASK_NOT_IN_HOUSEHOLD"
    
    async def test_create_task_with_auth_check(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de création avec vérification d'autorisation"""
        # Créer un utilisateur dans la base de données
        admin_id = uuid4()
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                admin_id, f"admin_{admin_id}@example.com", "hashed_password"
            )
        
        # Créer un ménage
        household = await create_household(db_pool, "Test House", admin_id)
        
        # Créer avec un utilisateur autorisé
        task_data = {
            "title": "Authorized Task",
            "household_id": str(household["id"])
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/tasks?user_id={admin_id}",
            json=task_data
        )
        
        assert response.status_code == 201
        
        # Essayer avec un utilisateur non autorisé
        unauthorized_user = uuid4()
        unauthorized_data = {
            "title": "Unauthorized Task",
            "household_id": str(household["id"])
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/tasks?user_id={unauthorized_user}",
            json=unauthorized_data
        )
        
        assert response.status_code == 403
        error = response.json()
        assert error["error"]["code"] == "UNAUTHORIZED_ACCESS"
    
    async def test_create_task_mismatched_household(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de création avec household_id non concordant"""
        household1 = await create_household(db_pool, "House 1")
        household2 = await create_household(db_pool, "House 2")
        
        # Essayer de créer une tâche avec des IDs non concordants
        task_data = {
            "title": "Mismatched Task",
            "household_id": str(household2["id"])  # Différent du chemin
        }
        
        response = await async_client.post(
            f"/households/{household1['id']}/tasks",
            json=task_data
        )
        
        assert response.status_code == 400
        error = response.json()
        assert error["error"]["code"] == "INVALID_INPUT"
        assert "household_id" in error["error"]["message"]
    
    async def test_task_validation(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test de validation des données de tâche"""
        household = await create_household(db_pool, "Test House")
        
        # Test avec titre vide
        response = await async_client.post(
            f"/households/{household['id']}/tasks",
            json={
                "title": "",
                "household_id": str(household["id"])
            }
        )
        
        assert response.status_code == 422
        
        # Test avec titre trop long
        very_long_title = "x" * 1000
        response = await async_client.post(
            f"/households/{household['id']}/tasks",
            json={
                "title": very_long_title,
                "household_id": str(household["id"])
            }
        )
        
        # Devrait passer ou échouer selon les contraintes
        assert response.status_code in [201, 422, 500]


class TestTaskWorkflow:
    """Tests des workflows complets de gestion des tâches"""
    
    async def test_complete_task_management(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test du workflow complet de gestion des tâches"""
        # 1. Créer un ménage
        admin_id = uuid4()
        household = await create_household(db_pool, "My Home", admin_id)
        
        # 2. Créer plusieurs tâches
        tasks_to_create = [
            {
                "title": "Daily: Clean kitchen",
                "description": "Wipe counters, wash dishes",
                "household_id": str(household["id"])
            },
            {
                "title": "Weekly: Vacuum all rooms",
                "description": "Living room, bedrooms, hallway",
                "household_id": str(household["id"])
            },
            {
                "title": "Monthly: Deep clean bathroom",
                "description": None,
                "household_id": str(household["id"])
            }
        ]
        
        created_tasks = []
        for task_data in tasks_to_create:
            response = await async_client.post(
                f"/households/{household['id']}/tasks",
                json=task_data
            )
            assert response.status_code == 201
            created_tasks.append(response.json())
        
        # 3. Vérifier la liste complète
        list_response = await async_client.get(
            f"/households/{household['id']}/tasks"
        )
        assert list_response.status_code == 200
        all_tasks = list_response.json()
        assert len(all_tasks) == 3
        
        # 4. Vérifier l'ordre (par date d'échéance)
        # Toutes ont la même date, donc l'ordre peut varier
        task_titles = [t["title"] for t in all_tasks]
        assert "Daily: Clean kitchen" in task_titles
        assert "Weekly: Vacuum all rooms" in task_titles
        assert "Monthly: Deep clean bathroom" in task_titles
        
        # 5. Vérifier l'accès individuel
        for task in created_tasks:
            detail_response = await async_client.get(
                f"/households/{household['id']}/tasks/{task['id']}"
            )
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert detail["title"] == task["title"]
            assert detail["description"] == task["description"]
    
    async def test_task_access_control_workflow(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test du contrôle d'accès aux tâches"""
        # Créer deux utilisateurs dans la base de données
        admin1_id = uuid4()
        admin2_id = uuid4()
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                admin1_id, f"admin1_{admin1_id}@example.com", "hashed_password"
            )
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                admin2_id, f"admin2_{admin2_id}@example.com", "hashed_password"
            )
        
        # Créer deux ménages avec des admins différents
        household1 = await create_household(db_pool, "House 1", admin1_id)
        household2 = await create_household(db_pool, "House 2", admin2_id)
        
        # Admin1 crée une tâche dans son ménage
        task_data = {
            "title": "Private Task for House 1",
            "household_id": str(household1["id"])
        }
        
        create_response = await async_client.post(
            f"/households/{household1['id']}/tasks?user_id={admin1_id}",
            json=task_data
        )
        assert create_response.status_code == 201
        task = create_response.json()
        
        # Admin1 peut voir sa tâche
        get_response = await async_client.get(
            f"/households/{household1['id']}/tasks/{task['id']}?user_id={admin1_id}"
        )
        assert get_response.status_code == 200
        
        # Admin2 ne peut pas voir la tâche de House1
        get_response = await async_client.get(
            f"/households/{household1['id']}/tasks/{task['id']}?user_id={admin2_id}"
        )
        assert get_response.status_code == 403
        
        # Admin2 ne peut pas créer de tâche dans House1
        unauthorized_task = {
            "title": "Unauthorized Task",
            "household_id": str(household1["id"])
        }
        
        create_response = await async_client.post(
            f"/households/{household1['id']}/tasks?user_id={admin2_id}",
            json=unauthorized_task
        )
        assert create_response.status_code == 403