"""
Tests pour la gestion des occurrences de tâches
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import date, datetime, timedelta, timezone
import asyncpg

from app.schemas.task import (
    TaskOccurrenceComplete,
    TaskOccurrenceSnooze,
    TaskStatus
)
from app.core.database import (
    create_task_occurrence,
    get_task_occurrences,
    get_task_occurrence,
    update_task_occurrence_status,
    complete_task_occurrence,
    generate_occurrences_for_definition,
    check_and_update_overdue_occurrences
)


class TestTaskOccurrenceSchemas:
    """Tests unitaires pour les schémas d'occurrences"""
    
    def test_task_occurrence_complete_valid(self):
        """Test du schéma de complétion"""
        data = {
            "duration_minutes": 25,
            "comment": "Fait rapidement",
            "photo_url": "https://example.com/photo.jpg"
        }
        completion = TaskOccurrenceComplete(**data)
        
        assert completion.duration_minutes == 25
        assert completion.comment == "Fait rapidement"
        assert completion.photo_url == "https://example.com/photo.jpg"
    
    def test_task_occurrence_snooze_valid(self):
        """Test du schéma de report"""
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        snooze = TaskOccurrenceSnooze(snoozed_until=future_time)
        
        assert snooze.snoozed_until == future_time
    
    def test_task_occurrence_snooze_past_date(self):
        """Test de report avec une date passée"""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        with pytest.raises(ValueError) as exc_info:
            TaskOccurrenceSnooze(snoozed_until=past_time)
        
        assert "futur" in str(exc_info.value).lower()


class TestTaskOccurrenceDatabase:
    """Tests unitaires pour les opérations de base de données"""
    
    @pytest.mark.asyncio
    async def test_create_task_occurrence(
        self, db_pool: asyncpg.Pool, test_task_definition
    ):
        """Test de création d'une occurrence"""
        scheduled_date = date.today()
        due_at = datetime.combine(scheduled_date, datetime.max.time())
        
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=scheduled_date,
            due_at=due_at
        )
        
        assert occurrence["id"]
        assert occurrence["task_id"] == test_task_definition["id"]
        assert occurrence["scheduled_date"] == scheduled_date
        assert occurrence["status"] == TaskStatus.PENDING.value
    
    @pytest.mark.asyncio
    async def test_create_duplicate_occurrence(
        self, db_pool: asyncpg.Pool, test_task_definition
    ):
        """Test de création d'occurrence dupliquée"""
        scheduled_date = date.today()
        due_at = datetime.combine(scheduled_date, datetime.max.time())
        
        # Créer la première occurrence
        first = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=scheduled_date,
            due_at=due_at
        )
        
        # Essayer de créer une duplicate
        duplicate = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=scheduled_date,
            due_at=due_at
        )
        
        # Devrait retourner l'occurrence existante
        assert duplicate["id"] == first["id"]
    
    @pytest.mark.asyncio
    async def test_get_task_occurrences_by_date_range(
        self, db_pool: asyncpg.Pool, test_household_with_user, test_task_definition
    ):
        """Test de récupération par plage de dates"""
        household = test_household_with_user["household"]
        
        # Créer des occurrences sur plusieurs jours
        base_date = date.today()
        for i in range(5):
            scheduled_date = base_date + timedelta(days=i)
            await create_task_occurrence(
                db_pool,
                task_id=test_task_definition["id"],
                scheduled_date=scheduled_date,
                due_at=datetime.combine(scheduled_date, datetime.max.time())
            )
        
        # Récupérer les 3 premiers jours
        occurrences = await get_task_occurrences(
            db_pool,
            household_id=household["id"],
            start_date=base_date,
            end_date=base_date + timedelta(days=2)
        )
        
        assert len(occurrences) == 3
    
    @pytest.mark.asyncio
    async def test_update_occurrence_status(
        self, db_pool: asyncpg.Pool, test_task_definition
    ):
        """Test de mise à jour du statut"""
        # Créer une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        # La reporter
        snoozed_until = datetime.now(timezone.utc) + timedelta(hours=2)
        updated = await update_task_occurrence_status(
            db_pool,
            occurrence["id"],
            TaskStatus.SNOOZED,
            snoozed_until=snoozed_until
        )
        
        assert updated["status"] == TaskStatus.SNOOZED.value
        assert updated["snoozed_until"] is not None
    
    @pytest.mark.asyncio
    async def test_complete_task_occurrence_db(
        self, db_pool: asyncpg.Pool, test_task_definition, test_household_with_user
    ):
        """Test de complétion d'une occurrence"""
        user_id = test_household_with_user["user_id"]
        
        # Créer une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        # La compléter
        completion = await complete_task_occurrence(
            db_pool,
            occurrence["id"],
            completed_by=user_id,
            duration_minutes=20,
            comment="Bien fait"
        )
        
        assert completion["occurrence_id"] == occurrence["id"]
        assert completion["completed_by"] == user_id
        assert completion["duration_minutes"] == 20
        assert completion["comment"] == "Bien fait"
        
        # Vérifier que le statut est mis à jour
        updated = await get_task_occurrence(db_pool, occurrence["id"])
        assert updated["status"] == TaskStatus.DONE.value
    
    @pytest.mark.asyncio
    async def test_generate_occurrences_for_definition(
        self, db_pool: asyncpg.Pool, test_task_definition
    ):
        """Test de génération d'occurrences pour une définition"""
        start_date = date.today()
        end_date = start_date + timedelta(days=14)
        
        occurrences = await generate_occurrences_for_definition(
            db_pool,
            test_task_definition["id"],
            start_date,
            end_date
        )
        
        # La tâche est MO,WE,FR donc environ 6 occurrences sur 2 semaines
        assert len(occurrences) >= 4
        assert all(occ["task_id"] == test_task_definition["id"] for occ in occurrences)
    
    @pytest.mark.asyncio
    async def test_check_and_update_overdue(
        self, db_pool: asyncpg.Pool, test_task_definition
    ):
        """Test de mise à jour des tâches en retard"""
        # Créer une occurrence dans le passé
        past_date = date.today() - timedelta(days=2)
        past_due = datetime.combine(past_date, datetime.max.time())
        
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=past_date,
            due_at=past_due
        )
        
        # Vérifier les retards
        count = await check_and_update_overdue_occurrences(db_pool)
        
        assert count >= 1
        
        # Vérifier que l'occurrence est marquée en retard
        updated = await get_task_occurrence(db_pool, occurrence["id"])
        assert updated["status"] == TaskStatus.OVERDUE.value


class TestTaskOccurrenceEndpoints:
    """Tests d'intégration pour les endpoints d'occurrences"""
    
    async def test_list_occurrences_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_household_with_user,
        test_task_definition,
        auth_headers: dict
    ):
        """Test de listing des occurrences"""
        household = test_household_with_user["household"]
        
        # Créer quelques occurrences
        for i in range(3):
            await create_task_occurrence(
                db_pool,
                task_id=test_task_definition["id"],
                scheduled_date=date.today() + timedelta(days=i),
                due_at=datetime.now(timezone.utc) + timedelta(days=i)
            )
        
        response = await async_client.get(
            f"/households/{household['id']}/occurrences",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        occurrences = response.json()
        assert len(occurrences) >= 3
        assert all("definition_title" in occ for occ in occurrences)
    
    async def test_complete_occurrence_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_task_definition,
        auth_headers: dict,
        task_completion_data: dict
    ):
        """Test de complétion via l'API"""
        # Créer une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        response = await async_client.put(
            f"/occurrences/{occurrence['id']}/complete",
            json=task_completion_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        completion = response.json()
        assert completion["duration_minutes"] == task_completion_data["duration_minutes"]
        assert completion["comment"] == task_completion_data["comment"]
    
    async def test_snooze_occurrence_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_task_definition,
        auth_headers: dict,
        task_snooze_data: dict
    ):
        """Test de report via l'API"""
        # Créer une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        response = await async_client.put(
            f"/occurrences/{occurrence['id']}/snooze",
            json=task_snooze_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["status"] == TaskStatus.SNOOZED.value
        assert updated["snoozed_until"] is not None
    
    async def test_skip_occurrence_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_task_definition,
        auth_headers: dict
    ):
        """Test pour ignorer une occurrence"""
        # Créer une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        response = await async_client.put(
            f"/occurrences/{occurrence['id']}/skip",
            json={"reason": "Pas le temps aujourd'hui"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["status"] == TaskStatus.SKIPPED.value
    
    async def test_assign_occurrence_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_household_with_user,
        test_task_definition,
        auth_headers: dict
    ):
        """Test d'assignation d'une occurrence"""
        user_id = test_household_with_user["user_id"]
        
        # Créer une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        response = await async_client.put(
            f"/occurrences/{occurrence['id']}/assign",
            json={"assigned_to": str(user_id)},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["assigned_to"] == str(user_id)
    
    async def test_generate_household_occurrences(
        self,
        async_client: AsyncClient,
        test_household_with_user,
        test_task_definition,
        auth_headers: dict
    ):
        """Test de génération pour tout le ménage"""
        household = test_household_with_user["household"]
        
        response = await async_client.post(
            f"/households/{household['id']}/occurrences/generate",
            params={"days_ahead": 7},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "count" in result
        assert result["count"] >= 0
    
    async def test_occurrence_stats_endpoint(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_household_with_user,
        test_task_definition,
        auth_headers: dict
    ):
        """Test des statistiques d'occurrences"""
        household = test_household_with_user["household"]
        user_id = test_household_with_user["user_id"]
        
        # Créer et compléter quelques occurrences
        for i in range(5):
            occurrence = await create_task_occurrence(
                db_pool,
                task_id=test_task_definition["id"],
                scheduled_date=date.today() - timedelta(days=i),
                due_at=datetime.now(timezone.utc) - timedelta(days=i)
            )
            
            if i % 2 == 0:  # Compléter une sur deux
                await complete_task_occurrence(
                    db_pool,
                    occurrence["id"],
                    completed_by=user_id
                )
        
        response = await async_client.get(
            f"/households/{household['id']}/occurrences/stats",
            params={
                "start_date": (date.today() - timedelta(days=7)).isoformat(),
                "end_date": date.today().isoformat()
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] >= 5
        assert stats["by_status"]["done"] >= 2
        assert 0 <= stats["completion_rate"] <= 100


class TestOccurrenceBusinessRules:
    """Tests des règles métier pour les occurrences"""
    
    async def test_cannot_complete_already_done(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_task_definition,
        test_household_with_user,
        auth_headers: dict
    ):
        """Test qu'on ne peut pas compléter une tâche déjà faite"""
        user_id = test_household_with_user["user_id"]
        
        # Créer et compléter une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        await complete_task_occurrence(
            db_pool,
            occurrence["id"],
            completed_by=user_id
        )
        
        # Essayer de la compléter à nouveau
        response = await async_client.put(
            f"/occurrences/{occurrence['id']}/complete",
            json={"duration_minutes": 10},
            headers=auth_headers
        )
        
        assert response.status_code == 409
        error = response.json()
        assert "déjà" in error["error"]["message"].lower()
    
    async def test_cannot_snooze_completed_task(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_task_definition,
        test_household_with_user,
        auth_headers: dict,
        task_snooze_data: dict
    ):
        """Test qu'on ne peut pas reporter une tâche complétée"""
        user_id = test_household_with_user["user_id"]
        
        # Créer et compléter une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        await complete_task_occurrence(
            db_pool,
            occurrence["id"],
            completed_by=user_id
        )
        
        # Essayer de la reporter
        response = await async_client.put(
            f"/occurrences/{occurrence['id']}/snooze",
            json=task_snooze_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        error = response.json()
        assert "ne peut pas être reportée" in error["error"]["message"]
    
    async def test_assign_to_non_member(
        self,
        async_client: AsyncClient,
        db_pool: asyncpg.Pool,
        test_task_definition,
        auth_headers: dict
    ):
        """Test d'assignation à un non-membre du ménage"""
        # Créer une occurrence
        occurrence = await create_task_occurrence(
            db_pool,
            task_id=test_task_definition["id"],
            scheduled_date=date.today(),
            due_at=datetime.now(timezone.utc)
        )
        
        # Essayer d'assigner à un utilisateur non membre
        non_member_id = uuid4()
        
        response = await async_client.put(
            f"/occurrences/{occurrence['id']}/assign",
            json={"assigned_to": str(non_member_id)},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "pas membre" in error["error"]["message"]