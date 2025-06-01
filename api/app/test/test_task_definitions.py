"""
Tests pour la gestion des définitions de tâches
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import date
import asyncpg

from app.schemas.task import TaskDefinitionCreate
from app.core.database import (
    create_household,
    create_task_definition,
    get_task_definitions,
    get_task_definition,
    update_task_definition,
    delete_task_definition
)


class TestTaskDefinitionSchemas:
    """Tests unitaires pour les schémas de définitions de tâches"""
    
    def test_task_definition_create_valid(self):
        """Test de création d'un schéma TaskDefinitionCreate valide"""
        data = {
            "title": "Nettoyer la cuisine",
            "description": "Nettoyer plan de travail et évier",
            "recurrence_rule": "FREQ=DAILY",
            "estimated_minutes": 20,
            "household_id": uuid4(),
            "is_catalog": False
        }
        task_def = TaskDefinitionCreate(**data)
        
        assert task_def.title == "Nettoyer la cuisine"
        assert task_def.description == "Nettoyer plan de travail et évier"
        assert task_def.recurrence_rule == "FREQ=DAILY"
        assert task_def.estimated_minutes == 20
        assert not task_def.is_catalog
    
    def test_task_definition_create_catalog(self):
        """Test de création d'une tâche catalogue"""
        task_def = TaskDefinitionCreate(
            title="Nettoyer les vitres",
            recurrence_rule="FREQ=MONTHLY",
            is_catalog=True
        )
        
        assert task_def.title == "Nettoyer les vitres"
        assert task_def.is_catalog
        assert task_def.household_id is None
    
    def test_task_definition_empty_title(self):
        """Test avec un titre vide"""
        with pytest.raises(ValueError):
            TaskDefinitionCreate(
                title="",
                recurrence_rule="FREQ=DAILY",
                household_id=uuid4()
            )
    
    def test_task_definition_invalid_recurrence(self):
        """Test avec une règle de récurrence vide"""
        # Les règles vides passent maintenant la validation Pydantic
        # mais sont converties en None
        task = TaskDefinitionCreate(
            title="Test",
            recurrence_rule="",
            household_id=uuid4()
        )
        assert task.recurrence_rule is None
    
    def test_task_definition_negative_duration(self):
        """Test avec une durée négative"""
        with pytest.raises(ValueError):
            TaskDefinitionCreate(
                title="Test",
                recurrence_rule="FREQ=DAILY",
                household_id=uuid4(),
                estimated_minutes=-10
            )
    
    def test_catalog_task_with_household_id(self):
        """Test qu'une tâche catalogue ne peut pas avoir de household_id"""
        with pytest.raises(ValueError) as exc_info:
            TaskDefinitionCreate(
                title="Test",
                recurrence_rule="FREQ=DAILY",
                is_catalog=True,
                household_id=uuid4()
            )
        assert "catalogue" in str(exc_info.value).lower()
    
    def test_non_catalog_task_without_household_id(self):
        """Test qu'une tâche non-catalogue doit avoir un household_id"""
        with pytest.raises(ValueError) as exc_info:
            TaskDefinitionCreate(
                title="Test",
                recurrence_rule="FREQ=DAILY",
                is_catalog=False
            )
        assert "household_id" in str(exc_info.value).lower()


class TestTaskDefinitionDatabase:
    """Tests unitaires pour les opérations de base de données"""
    
    @pytest.mark.asyncio
    async def test_create_task_definition(self, db_pool: asyncpg.Pool, test_household_with_user):
        """Test de création d'une définition de tâche"""
        household = test_household_with_user["household"]
        user_id = test_household_with_user["user_id"]
        
        task_def = await create_task_definition(
            db_pool,
            title="Passer l'aspirateur",
            recurrence_rule="FREQ=WEEKLY;BYDAY=SA",
            household_id=household["id"],
            description="Dans toutes les pièces",
            estimated_minutes=45,
            created_by=user_id
        )
        
        assert task_def["id"]
        assert task_def["title"] == "Passer l'aspirateur"
        assert task_def["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=SA"
        assert task_def["household_id"] == household["id"]
        assert task_def["estimated_minutes"] == 45
        assert not task_def["is_catalog"]
    
    @pytest.mark.asyncio
    async def test_create_catalog_task(self, db_pool: asyncpg.Pool):
        """Test de création d'une tâche catalogue"""
        task_def = await create_task_definition(
            db_pool,
            title="Dégivrer le congélateur",
            recurrence_rule="FREQ=MONTHLY;INTERVAL=3",
            is_catalog=True,
            description="Tâche catalogue pour dégivrage",
            estimated_minutes=120
        )
        
        assert task_def["id"]
        assert task_def["is_catalog"]
        assert task_def["household_id"] is None
        assert task_def["title"] == "Dégivrer le congélateur"
    
    @pytest.mark.asyncio
    async def test_get_task_definitions_by_household(self, db_pool: asyncpg.Pool, test_household_with_user):
        """Test de récupération des définitions d'un ménage"""
        household = test_household_with_user["household"]
        user_id = test_household_with_user["user_id"]
        
        # Créer plusieurs définitions
        tasks_data = [
            ("Cuisine - Quotidien", "FREQ=DAILY"),
            ("Salle de bain - Hebdo", "FREQ=WEEKLY;BYDAY=SU"),
            ("Poussière - Bihebdo", "FREQ=WEEKLY;INTERVAL=2"),
        ]
        
        for title, rrule in tasks_data:
            await create_task_definition(
                db_pool,
                title=title,
                recurrence_rule=rrule,
                household_id=household["id"],
                created_by=user_id
            )
        
        # Récupérer les définitions
        definitions = await get_task_definitions(db_pool, household_id=household["id"])
        
        assert len(definitions) >= 3
        titles = [d["title"] for d in definitions]
        assert "Cuisine - Quotidien" in titles
        assert "Salle de bain - Hebdo" in titles
        assert "Poussière - Bihebdo" in titles
    
    @pytest.mark.asyncio
    async def test_get_catalog_tasks(self, db_pool: asyncpg.Pool):
        """Test de récupération des tâches catalogue"""
        # Créer des tâches catalogue
        catalog_tasks = [
            ("Nettoyer le four", "FREQ=MONTHLY"),
            ("Laver les rideaux", "FREQ=MONTHLY;INTERVAL=6"),
            ("Nettoyer derrière les meubles", "FREQ=YEARLY"),
        ]
        
        for title, rrule in catalog_tasks:
            await create_task_definition(
                db_pool,
                title=title,
                recurrence_rule=rrule,
                is_catalog=True
            )
        
        # Récupérer uniquement les tâches catalogue
        definitions = await get_task_definitions(db_pool, is_catalog=True)
        
        catalog_titles = [d["title"] for d in definitions if d["is_catalog"]]
        assert "Nettoyer le four" in catalog_titles
        assert "Laver les rideaux" in catalog_titles
        assert "Nettoyer derrière les meubles" in catalog_titles
    
    @pytest.mark.asyncio
    async def test_update_task_definition(self, db_pool: asyncpg.Pool, test_task_definition):
        """Test de mise à jour d'une définition"""
        # Mettre à jour plusieurs champs
        updated = await update_task_definition(
            db_pool,
            test_task_definition["id"],
            title="Tâche mise à jour",
            description="Nouvelle description",
            estimated_minutes=60,
            recurrence_rule="FREQ=DAILY"
        )
        
        assert updated["title"] == "Tâche mise à jour"
        assert updated["description"] == "Nouvelle description"
        assert updated["estimated_minutes"] == 60
        assert updated["recurrence_rule"] == "FREQ=DAILY"
    
    @pytest.mark.asyncio
    async def test_delete_task_definition(self, db_pool: asyncpg.Pool, test_household_with_user):
        """Test de suppression d'une définition"""
        household = test_household_with_user["household"]
        
        # Créer une définition
        task_def = await create_task_definition(
            db_pool,
            title="À supprimer",
            recurrence_rule="FREQ=DAILY",
            household_id=household["id"]
        )
        
        # La supprimer
        success = await delete_task_definition(db_pool, task_def["id"])
        assert success
        
        # Vérifier qu'elle n'existe plus
        deleted = await get_task_definition(db_pool, task_def["id"])
        assert deleted is None


class TestTaskDefinitionEndpoints:
    """Tests d'intégration pour les endpoints de définitions de tâches"""
    
    async def test_list_catalog_tasks(self, async_client: AsyncClient, db_pool: asyncpg.Pool):
        """Test de l'endpoint de listing du catalogue"""
        # Créer des tâches catalogue
        for i in range(3):
            await create_task_definition(
                db_pool,
                title=f"Tâche catalogue {i}",
                recurrence_rule="FREQ=WEEKLY",
                is_catalog=True
            )
        
        response = await async_client.get("/catalog")
        
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 3
        assert all(task["is_catalog"] for task in tasks)
    
    async def test_create_task_definition_endpoint(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        auth_headers: dict,
        recurrence_rules: dict
    ):
        """Test de création d'une définition via l'API"""
        household = test_household_with_user["household"]
        
        task_data = {
            "title": "Nouvelle tâche",
            "description": "Description de test",
            "recurrence_rule": recurrence_rules["weekly_monday"],
            "estimated_minutes": 30,
            "household_id": str(household["id"])
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/task-definitions",
            json=task_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        created = response.json()
        assert created["title"] == "Nouvelle tâche"
        assert created["recurrence_rule"] == recurrence_rules["weekly_monday"]
    
    async def test_create_task_with_invalid_rrule(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        auth_headers: dict
    ):
        """Test de création avec une règle invalide"""
        household = test_household_with_user["household"]
        
        task_data = {
            "title": "Tâche invalide",
            "recurrence_rule": "INVALID_RULE",
            "household_id": str(household["id"])
        }
        
        response = await async_client.post(
            f"/households/{household['id']}/task-definitions",
            json=task_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "recurrence_rule" in error["error"]["message"].lower()
    
    async def test_copy_from_catalog(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_household_with_user,
        auth_headers: dict
    ):
        """Test de copie d'une tâche du catalogue"""
        household = test_household_with_user["household"]
        
        # Créer une tâche catalogue
        catalog_task = await create_task_definition(
            db_pool,
            title="Tâche catalogue à copier",
            recurrence_rule="FREQ=MONTHLY",
            description="Template de tâche",
            estimated_minutes=90,
            is_catalog=True
        )
        
        # La copier dans le ménage
        response = await async_client.post(
            f"/households/{household['id']}/task-definitions/{catalog_task['id']}/copy",
            headers=auth_headers
        )
        
        assert response.status_code == 201
        copied = response.json()
        assert copied["title"] == catalog_task["title"]
        assert copied["household_id"] == str(household["id"])
        assert not copied["is_catalog"]
    
    async def test_update_task_definition_endpoint(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        test_task_definition,
        auth_headers: dict
    ):
        """Test de mise à jour via l'API"""
        household = test_household_with_user["household"]
        
        update_data = {
            "title": "Titre modifié",
            "estimated_minutes": 45
        }
        
        response = await async_client.put(
            f"/households/{household['id']}/task-definitions/{test_task_definition['id']}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["title"] == "Titre modifié"
        assert updated["estimated_minutes"] == 45
    
    async def test_delete_task_definition_endpoint(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        auth_headers: dict,
        db_pool: asyncpg.Pool
    ):
        """Test de suppression via l'API"""
        household = test_household_with_user["household"]
        
        # Créer une définition
        task_def = await create_task_definition(
            db_pool,
            title="À supprimer via API",
            recurrence_rule="FREQ=DAILY",
            household_id=household["id"]
        )
        
        response = await async_client.delete(
            f"/households/{household['id']}/task-definitions/{task_def['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Vérifier la suppression
        check_response = await async_client.get(
            f"/households/{household['id']}/task-definitions/{task_def['id']}",
            headers=auth_headers
        )
        assert check_response.status_code == 404
    
    async def test_generate_occurrences_endpoint(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        test_task_definition,
        auth_headers: dict
    ):
        """Test de génération manuelle d'occurrences"""
        household = test_household_with_user["household"]
        
        response = await async_client.post(
            f"/households/{household['id']}/task-definitions/{test_task_definition['id']}/generate-occurrences",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today().replace(day=28) if date.today().day < 28 else date.today()).isoformat(),
                "max_occurrences": 10
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        occurrences = response.json()
        assert isinstance(occurrences, list)
        assert len(occurrences) > 0
        assert all("scheduled_date" in occ for occ in occurrences)


class TestTaskDefinitionAccessControl:
    """Tests de contrôle d'accès aux définitions"""
    
    async def test_cannot_access_other_household_tasks(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        auth_headers: dict
    ):
        """Test qu'on ne peut pas accéder aux tâches d'un autre ménage"""
        # Créer un autre ménage
        other_household = await create_household(db_pool, "Other House")
        
        response = await async_client.get(
            f"/households/{other_household['id']}/task-definitions",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_catalog_tasks_are_public(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool
    ):
        """Test que les tâches catalogue sont publiques"""
        # Créer une tâche catalogue
        await create_task_definition(
            db_pool,
            title="Tâche publique",
            recurrence_rule="FREQ=WEEKLY",
            is_catalog=True
        )
        
        # Accès sans authentification
        response = await async_client.get("/catalog")
        
        assert response.status_code == 200
        tasks = response.json()
        assert any(t["title"] == "Tâche publique" for t in tasks)


class TestRecurrenceValidation:
    """Tests de validation des règles de récurrence"""
    
    async def test_valid_recurrence_rules(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        auth_headers: dict,
        recurrence_rules: dict
    ):
        """Test avec différentes règles valides"""
        household = test_household_with_user["household"]
        
        for name, rule in recurrence_rules.items():
            task_data = {
                "title": f"Test {name}",
                "recurrence_rule": rule,
                "household_id": str(household["id"])
            }
            
            response = await async_client.post(
                f"/households/{household['id']}/task-definitions",
                json=task_data,
                headers=auth_headers
            )
            
            # Toutes les règles du fixture doivent être valides
            assert response.status_code == 201, f"Rule {name} failed: {response.text}"
    
    async def test_invalid_recurrence_rules(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        auth_headers: dict
    ):
        """Test avec des règles invalides"""
        household = test_household_with_user["household"]
        
        invalid_rules = [
            "NOT_A_RULE",
            "FREQ=INVALID",
            "FREQ=DAILY;INVALID=YES",
            "",
            "FREQ=",
        ]
        
        for rule in invalid_rules:
            task_data = {
                "title": "Test invalide",
                "recurrence_rule": rule,
                "household_id": str(household["id"])
            }
            
            response = await async_client.post(
                f"/households/{household['id']}/task-definitions",
                json=task_data,
                headers=auth_headers
            )
            
            assert response.status_code == 400, f"Rule '{rule}' should have failed"