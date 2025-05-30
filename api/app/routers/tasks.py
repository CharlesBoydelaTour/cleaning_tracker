from fastapi import APIRouter, Depends, status
from app.schemas.task import TaskCreate, Task
from app.core.database import get_tasks, get_task, create_task
import asyncpg
from app.routers.households import get_db_pool, check_household_access
from app.core.exceptions import (
    UnauthorizedAccess,
    TaskNotFound,
    TaskNotInHousehold,
    DatabaseError,
    InvalidInput,
)
from typing import List
from datetime import date
from uuid import UUID

router = APIRouter()


@router.get("/{household_id}/tasks", response_model=List[Task])
async def list_tasks(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère la liste des tâches d'un ménage spécifique.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise UnauthorizedAccess(
                    resource="ménage",
                    resource_id=str(household_id),
                    user_id=str(user_id),
                )

        tasks = await get_tasks(db_pool, household_id)
        return tasks
    except (UnauthorizedAccess, TaskNotFound, TaskNotInHousehold):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération des tâches",
            details=str(e),
        )


@router.get("/{household_id}/tasks/{task_id}", response_model=Task)
async def get_task_details(
    household_id: UUID,
    task_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Récupère les détails d'une tâche spécifique.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise UnauthorizedAccess(
                    resource="ménage",
                    resource_id=str(household_id),
                    user_id=str(user_id),
                )

        task = await get_task(db_pool, task_id)
        if not task:
            raise TaskNotFound(task_id=str(task_id))

        # Vérifier que la tâche appartient bien au ménage spécifié
        if task["household_id"] != household_id:
            raise TaskNotInHousehold(
                task_id=str(task_id),
                household_id=str(household_id),
            )

        return task
    except (UnauthorizedAccess, TaskNotFound, TaskNotInHousehold):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération de la tâche",
            details=str(e),
        )


@router.post(
    "/{household_id}/tasks", response_model=Task, status_code=status.HTTP_201_CREATED
)
async def create_new_task(
    household_id: UUID,
    task: TaskCreate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    user_id: str = None,  # Dans un vrai système, cela viendrait d'un token JWT
):
    """
    Ajoute une nouvelle tâche à un ménage.
    """
    try:
        # Vérifier que l'utilisateur a accès à ce ménage
        if user_id:
            has_access = await check_household_access(db_pool, household_id, user_id)
            if not has_access:
                raise UnauthorizedAccess(
                    resource="ménage",
                    resource_id=str(household_id),
                    user_id=str(user_id),
                )

        # S'assurer que l'ID du ménage dans le chemin correspond à celui dans la requête
        if task.household_id != household_id:
            raise InvalidInput(
                field="household_id",
                message="L'ID du ménage dans le chemin ne correspond pas à celui dans la requête",
                received_value=str(task.household_id),
                expected_value=str(household_id),
            )

        # Par défaut, la date d'échéance est aujourd'hui si non spécifiée
        due_date = date.today()

        new_task = await create_task(
            db_pool, task.title, task.household_id, task.description, due_date
        )
        return new_task
    except (UnauthorizedAccess, InvalidInput):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="création de la tâche",
            details=str(e),
        )
