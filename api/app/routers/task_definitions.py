from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.schemas.task import (
    TaskDefinition,
    TaskDefinitionWithRoom,
    TaskDefinitionCreate,
    TaskDefinitionUpdate,
    TaskOccurrence
)
from app.core.database import (
    create_task_definition,
    get_task_definitions,
    get_task_definition,
    update_task_definition,
    delete_task_definition,
    generate_occurrences_for_definition
)
from app.routers.households import get_db_pool, check_household_access
from app.core.exceptions import (
    TaskNotFound,
    UnauthorizedAccess,
    InvalidInput,
    DatabaseError
)
from app.core.security import get_current_user
from app.services.recurrence import recurrence_service
import asyncpg

router = APIRouter()
household_router = APIRouter()  # Nouveau router pour les routes de ménage


@router.get("/catalog", response_model=List[TaskDefinitionWithRoom])
async def list_catalog_tasks(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    room_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Récupérer les tâches du catalogue global.
    
    Ces tâches peuvent être copiées dans n'importe quel ménage.
    """
    try:
        # Récupérer uniquement les tâches du catalogue
        tasks = await get_task_definitions(
            db_pool,
            is_catalog=True,
            room_id=room_id
        )
        
        # Appliquer la pagination
        return tasks[offset:offset + limit]
        
    except Exception as e:
        raise DatabaseError(
            operation="récupération du catalogue",
            details=str(e)
        )


@household_router.get("/{household_id}/task-definitions", response_model=List[TaskDefinitionWithRoom])
async def list_household_task_definitions(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    room_id: Optional[UUID] = Query(None),
    created_by: Optional[UUID] = Query(None)
):
    """
    Récupérer les définitions de tâches d'un ménage.
    
    Nécessite d'être membre du ménage.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="view_tasks"
            )
        
        # Récupérer les définitions
        tasks = await get_task_definitions(
            db_pool,
            household_id=household_id,
            room_id=room_id,
            created_by=created_by
        )
        
        return tasks
        
    except (UnauthorizedAccess,):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération des définitions de tâches",
            details=str(e)
        )


@household_router.get("/{household_id}/task-definitions/{task_def_id}", response_model=TaskDefinitionWithRoom)
async def get_task_definition_details(
    household_id: UUID,
    task_def_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les détails d'une définition de tâche.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="view_task"
            )
        
        # Récupérer la définition
        task_def = await get_task_definition(db_pool, task_def_id)
        
        if not task_def:
            raise TaskNotFound(task_id=str(task_def_id))
        
        # Vérifier que la tâche appartient au ménage
        if task_def["household_id"] != household_id:
            raise TaskNotFound(task_id=str(task_def_id))
        
        return task_def
        
    except (UnauthorizedAccess, TaskNotFound):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération de la définition",
            details=str(e)
        )


@household_router.post(
    "/{household_id}/task-definitions",
    response_model=TaskDefinition,
    status_code=status.HTTP_201_CREATED
)
async def create_household_task_definition(
    household_id: UUID,
    task_data: TaskDefinitionCreate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Créer une nouvelle définition de tâche pour un ménage.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="create_task"
            )
        
        # Valider la règle de récurrence
        if not task_data.recurrence_rule or task_data.recurrence_rule.strip() == "":
            raise InvalidInput(
                field="recurrence_rule",
                value=task_data.recurrence_rule or "",
                reason="La règle de récurrence ne peut pas être vide"
            )
            
        validation = recurrence_service.validate_rrule(task_data.recurrence_rule)
        if not validation.is_valid:
            raise InvalidInput(
                field="recurrence_rule",
                value=task_data.recurrence_rule,
                reason=validation.error_message or "Règle de récurrence invalide"
            )
        
        # S'assurer que household_id correspond
        if task_data.household_id and task_data.household_id != household_id:
            raise InvalidInput(
                field="household_id",
                value=str(task_data.household_id),
                reason="L'ID du ménage ne correspond pas à l'URL"
            )
        
        # Créer la définition
        new_task = await create_task_definition(
            db_pool,
            title=task_data.title,
            recurrence_rule=task_data.recurrence_rule,
            household_id=household_id,
            description=task_data.description,
            estimated_minutes=task_data.estimated_minutes,
            room_id=task_data.room_id,
            is_catalog=False,
            created_by=UUID(current_user["id"])
        )
        
        # Optionnel: générer une occurrence à la date de démarrage si fournie
        try:
            if task_data.start_date is not None:
                await generate_occurrences_for_definition(
                    db_pool,
                    new_task["id"],
                    task_data.start_date,
                    task_data.start_date,
                    max_occurrences=1
                )
        except Exception as _:
            # Ne pas bloquer la création si la génération initiale échoue
            pass
        
        return new_task
        
    except (UnauthorizedAccess, InvalidInput):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="création de la définition",
            details=str(e)
        )


@household_router.post(
    "/{household_id}/task-definitions/{task_def_id}/copy",
    response_model=TaskDefinition,
    status_code=status.HTTP_201_CREATED
)
async def copy_task_from_catalog(
    household_id: UUID,
    task_def_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    room_id: Optional[UUID] = Query(None, description="Pièce où affecter la tâche copiée")
):
    """
    Copier une tâche du catalogue vers un ménage.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="copy_task"
            )
        
        # Récupérer la tâche source
        source_task = await get_task_definition(db_pool, task_def_id)
        if not source_task:
            raise TaskNotFound(task_id=str(task_def_id))
        
        # Vérifier que c'est bien une tâche du catalogue
        if not source_task.get("is_catalog", False):
            raise InvalidInput(
                field="task_def_id",
                value=str(task_def_id),
                reason="Seules les tâches du catalogue peuvent être copiées"
            )
        
        # Créer la copie
        new_task = await create_task_definition(
            db_pool,
            title=source_task["title"],
            recurrence_rule=source_task["recurrence_rule"],
            household_id=household_id,
            description=source_task["description"],
            estimated_minutes=source_task["estimated_minutes"],
            room_id=room_id or source_task.get("room_id"),
            is_catalog=False,
            created_by=UUID(current_user["id"])
        )
        
        return new_task
        
    except (UnauthorizedAccess, TaskNotFound, InvalidInput):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="copie de la tâche",
            details=str(e)
        )


@household_router.put("/{household_id}/task-definitions/{task_def_id}", response_model=TaskDefinition)
async def update_household_task_definition(
    household_id: UUID,
    task_def_id: UUID,
    updates: TaskDefinitionUpdate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Mettre à jour une définition de tâche.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="update_task"
            )
        
        # Vérifier que la tâche existe et appartient au ménage
        existing_task = await get_task_definition(db_pool, task_def_id)
        if not existing_task:
            raise TaskNotFound(task_id=str(task_def_id))
        
        if existing_task["household_id"] != household_id:
            raise TaskNotFound(task_id=str(task_def_id))
        
        # Valider la nouvelle règle de récurrence si fournie
        if updates.recurrence_rule is not None:
            if updates.recurrence_rule.strip() == "":
                raise InvalidInput(
                    field="recurrence_rule",
                    value=updates.recurrence_rule,
                    reason="La règle de récurrence ne peut pas être vide"
                )
            validation = recurrence_service.validate_rrule(updates.recurrence_rule)
            if not validation.is_valid:
                raise InvalidInput(
                    field="recurrence_rule",
                    value=updates.recurrence_rule,
                    reason=validation.error_message or "Règle de récurrence invalide"
                )
        
        # Effectuer la mise à jour
        update_data = updates.model_dump(exclude_unset=True)
        updated_task = await update_task_definition(
            db_pool,
            task_def_id,
            **update_data
        )
        
        return updated_task
        
    except (UnauthorizedAccess, TaskNotFound, InvalidInput):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="mise à jour de la définition",
            details=str(e)
        )


@household_router.delete(
    "/{household_id}/task-definitions/{task_def_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_household_task_definition(
    household_id: UUID,
    task_def_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Supprimer une définition de tâche.
    
    Note: Toutes les occurrences associées seront également supprimées.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="delete_task"
            )
        
        # Vérifier que la tâche existe et appartient au ménage
        existing_task = await get_task_definition(db_pool, task_def_id)
        if not existing_task:
            raise TaskNotFound(task_id=str(task_def_id))
        
        if existing_task["household_id"] != household_id:
            raise TaskNotFound(task_id=str(task_def_id))
        
        # TODO: Vérifier les permissions admin si nécessaire
        
        # Supprimer la définition
        success = await delete_task_definition(db_pool, task_def_id)
        if not success:
            raise TaskNotFound(task_id=str(task_def_id))
        
    except (UnauthorizedAccess, TaskNotFound):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="suppression de la définition",
            details=str(e)
        )


@household_router.post(
    "/{household_id}/task-definitions/{task_def_id}/generate-occurrences",
    response_model=List[TaskOccurrence]
)
async def generate_task_occurrences(
    household_id: UUID,
    task_def_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    start_date: date = Query(date.today()),
    end_date: date = Query(..., description="Date de fin de génération"),
    max_occurrences: int = Query(50, ge=1, le=100)
):
    """
    Générer manuellement les occurrences pour une définition de tâche.
    
    Utile pour prévisualiser ou forcer la génération.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="generate_occurrences"
            )
        
        # Vérifier que la tâche existe et appartient au ménage
        task_def = await get_task_definition(db_pool, task_def_id)
        if not task_def:
            raise TaskNotFound(task_id=str(task_def_id))
        
        if task_def["household_id"] != household_id:
            raise TaskNotFound(task_id=str(task_def_id))
        
        # Générer les occurrences
        occurrences = await generate_occurrences_for_definition(
            db_pool,
            task_def_id,
            start_date,
            end_date,
            max_occurrences
        )
        
        return occurrences
        
    except (UnauthorizedAccess, TaskNotFound):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="génération des occurrences",
            details=str(e)
        )