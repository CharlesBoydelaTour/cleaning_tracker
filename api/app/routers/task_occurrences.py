from fastapi import APIRouter, Depends, Query, Body
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.schemas.task import (
    TaskOccurrence,
    TaskOccurrenceComplete,
    TaskOccurrenceSnooze,
    TaskOccurrenceSkip,
    TaskCompletion,
    TaskStatus,
    TaskOccurrenceWithDefinition
)
from app.core.database import (
    get_task_occurrences,
    get_task_occurrence,
    delete_task_occurrence,
    update_task_occurrence_status,
    complete_task_occurrence,
    generate_occurrences_for_household,
    check_and_update_overdue_occurrences
)
from app.routers.households import get_db_pool, check_household_access
from app.core.exceptions import (
    OccurrenceNotFound,
    UnauthorizedAccess,
    InvalidInput,
    DatabaseError,
    BusinessRuleViolation
)
from app.core.security import get_current_user
from app.core.logging import get_logger, with_context
import asyncpg

router = APIRouter()
household_router = APIRouter()  # Nouveau router pour les routes de ménage
logger = get_logger(__name__)


@household_router.get("/{household_id}/occurrences", response_model=List[TaskOccurrenceWithDefinition])
async def list_household_occurrences(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Date de début (incluse)"),
    end_date: Optional[date] = Query(None, description="Date de fin (incluse)"),
    status: Optional[TaskStatus] = Query(None, description="Filtrer par statut"),
    assigned_to: Optional[UUID] = Query(None, description="Filtrer par assignation"),
    room_id: Optional[UUID] = Query(None, description="Filtrer par pièce")
):
    """
    Récupérer les occurrences de tâches d'un ménage.
    
    Idéal pour afficher le calendrier des tâches.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="view_occurrences"
            )
        
        # Si pas de dates fournies, utiliser une période par défaut
        if not start_date and not end_date:
            start_date = date.today()
            from datetime import timedelta
            end_date = start_date + timedelta(days=30)
        # Si la fenêtre couvre aujourd'hui, recalculer les retards avant de lister
        today = date.today()
        window_start = start_date or today
        window_end = end_date or today
        if window_start <= today <= window_end:
            try:
                await check_and_update_overdue_occurrences(db_pool, household_id=household_id)
            except Exception as e:
                logger.warning(
                    "Échec check_overdue (continuation)",
                    extra=with_context(household_id=str(household_id), error=str(e))
                )

        # Récupérer les occurrences de la fenêtre demandée
        occurrences = await get_task_occurrences(
            db_pool,
            household_id=household_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            assigned_to=assigned_to,
            room_id=room_id
        )

        # Si la fenêtre couvre aujourd'hui et aucun filtre de statut n'est imposé,
        # ajouter aussi les occurrences OVERDUE antérieures à aujourd'hui
        if window_start <= today <= window_end and status is None:
            from datetime import timedelta as _td
            overdue_until_yesterday = await get_task_occurrences(
                db_pool,
                household_id=household_id,
                start_date=None,
                end_date=today - _td(days=1),
                status=TaskStatus.OVERDUE,
                assigned_to=assigned_to,
                room_id=room_id
            )
            # Concaténer; pas de doublons attendus car fenêtres disjointes
            occurrences.extend(overdue_until_yesterday)
        
        # Transformer en TaskOccurrenceWithDefinition
        enriched_occurrences = []
        for occ in occurrences:
            enriched = TaskOccurrenceWithDefinition(
                id=occ["id"],
                task_id=occ["task_id"],
                scheduled_date=occ["scheduled_date"],
                due_at=occ["due_at"],
                status=occ["status"],
                assigned_to=occ.get("assigned_to"),
                snoozed_until=occ.get("snoozed_until"),
                created_at=occ["created_at"],
                definition_title=occ["task_title"],
                definition_description=occ.get("task_description"),
                room_name=occ.get("room_name"),
                assigned_user_name=occ.get("assigned_user_email"),
                definition_priority=occ.get("definition_priority")
            )
            enriched_occurrences.append(enriched)
        
        return enriched_occurrences
        
    except (UnauthorizedAccess,):
        raise
    except Exception as e:
        logger.error(
            "Erreur lors de la récupération des occurrences",
            extra=with_context(
                household_id=str(household_id),
                error=str(e)
            )
        )
        raise DatabaseError(
            operation="récupération des occurrences",
            details=str(e)
        )


@router.get("/occurrences/{occurrence_id}", response_model=TaskOccurrenceWithDefinition)
async def get_occurrence_details(
    occurrence_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les détails d'une occurrence spécifique.
    """
    try:
        # Récupérer l'occurrence
        occurrence = await get_task_occurrence(db_pool, occurrence_id)
        
        if not occurrence:
            raise OccurrenceNotFound(occurrence_id=str(occurrence_id))
        
        # Vérifier l'accès au ménage
        household_id = occurrence["household_id"]
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="occurrence",
                action="view"
            )
        
        # Retourner l'occurrence enrichie
        return TaskOccurrenceWithDefinition(
            id=occurrence["id"],
            task_id=occurrence["task_id"],
            scheduled_date=occurrence["scheduled_date"],
            due_at=occurrence["due_at"],
            status=occurrence["status"],
            assigned_to=occurrence.get("assigned_to"),
            snoozed_until=occurrence.get("snoozed_until"),
            created_at=occurrence["created_at"],
            definition_title=occurrence["task_title"],
            definition_description=occurrence.get("task_description"),
            room_name=occurrence.get("room_name"),
            assigned_user_name=occurrence.get("assigned_user_email"),
            definition_priority=occurrence.get("definition_priority")
        )
        
    except (UnauthorizedAccess, OccurrenceNotFound):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="récupération de l'occurrence",
            details=str(e)
        )


@router.put("/occurrences/{occurrence_id}/complete", response_model=TaskCompletion)
async def complete_occurrence(
    occurrence_id: UUID,
    completion_data: TaskOccurrenceComplete = Body(...),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Marquer une occurrence comme complétée.
    """
    try:
        # Récupérer l'occurrence
        occurrence = await get_task_occurrence(db_pool, occurrence_id)
        
        if not occurrence:
            raise OccurrenceNotFound(occurrence_id=str(occurrence_id))
        
        # Vérifier l'accès au ménage
        household_id = occurrence["household_id"]
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="occurrence",
                action="complete"
            )
        
        # Vérifier que l'occurrence n'est pas déjà complétée
        if occurrence["status"] == TaskStatus.DONE.value:
            raise BusinessRuleViolation(
                rule="ALREADY_COMPLETED",
                details="Cette occurrence est déjà marquée comme complétée"
            )
        
        # Marquer comme complétée
        completion = await complete_task_occurrence(
            db_pool,
            occurrence_id,
            completed_by=UUID(current_user["id"]),
            duration_minutes=completion_data.duration_minutes,
            comment=completion_data.comment,
            photo_url=completion_data.photo_url
        )
        
        logger.info(
            "Occurrence complétée",
            extra=with_context(
                occurrence_id=str(occurrence_id),
                completed_by=current_user["id"],
                duration_minutes=completion_data.duration_minutes
            )
        )
        
        return completion
        
    except (UnauthorizedAccess, OccurrenceNotFound, BusinessRuleViolation):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="complétion de l'occurrence",
            details=str(e)
        )


@router.put("/occurrences/{occurrence_id}/snooze", response_model=TaskOccurrence)
async def snooze_occurrence(
    occurrence_id: UUID,
    snooze_data: TaskOccurrenceSnooze = Body(...),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Reporter une occurrence à plus tard.
    """
    try:
        # Récupérer l'occurrence
        occurrence = await get_task_occurrence(db_pool, occurrence_id)
        
        if not occurrence:
            raise OccurrenceNotFound(occurrence_id=str(occurrence_id))
        
        # Vérifier l'accès au ménage
        household_id = occurrence["household_id"]
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="occurrence",
                action="snooze"
            )
        
        # Vérifier que l'occurrence peut être reportée
        if occurrence["status"] in [TaskStatus.DONE.value, TaskStatus.SKIPPED.value]:
            raise BusinessRuleViolation(
                rule="CANNOT_SNOOZE",
                details=f"Une occurrence {occurrence['status']} ne peut pas être reportée"
            )
        
        # Mettre à jour le statut
        updated_occurrence = await update_task_occurrence_status(
            db_pool,
            occurrence_id,
            TaskStatus.SNOOZED,
            snoozed_until=snooze_data.snoozed_until
        )
        
        logger.info(
            "Occurrence reportée",
            extra=with_context(
                occurrence_id=str(occurrence_id),
                snoozed_until=snooze_data.snoozed_until.isoformat(),
                snoozed_by=current_user["id"]
            )
        )
        
        return updated_occurrence
        
    except (UnauthorizedAccess, OccurrenceNotFound, BusinessRuleViolation):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="report de l'occurrence",
            details=str(e)
        )


@router.put("/occurrences/{occurrence_id}/skip", response_model=TaskOccurrence)
async def skip_occurrence(
    occurrence_id: UUID,
    skip_data: TaskOccurrenceSkip = Body(TaskOccurrenceSkip()),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Ignorer une occurrence (ne pas la faire).
    """
    try:
        # Récupérer l'occurrence
        occurrence = await get_task_occurrence(db_pool, occurrence_id)
        
        if not occurrence:
            raise OccurrenceNotFound(occurrence_id=str(occurrence_id))
        
        # Vérifier l'accès au ménage
        household_id = occurrence["household_id"]
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="occurrence",
                action="skip"
            )
        
        # Vérifier que l'occurrence peut être ignorée
        if occurrence["status"] in [TaskStatus.DONE.value, TaskStatus.SKIPPED.value]:
            raise BusinessRuleViolation(
                rule="ALREADY_PROCESSED",
                details=f"Cette occurrence est déjà {occurrence['status']}"
            )
        
        # Mettre à jour le statut: une tâche ignorée devient "en retard"
        updated_occurrence = await update_task_occurrence_status(
            db_pool,
            occurrence_id,
            TaskStatus.OVERDUE
        )
        
        logger.info(
            "Occurrence marquée en retard (ignore)",
            extra=with_context(
                occurrence_id=str(occurrence_id),
                skipped_by=current_user["id"],
                reason=skip_data.reason
            )
        )
        
        return updated_occurrence
        
    except (UnauthorizedAccess, OccurrenceNotFound, BusinessRuleViolation):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="ignorer l'occurrence",
            details=str(e)
        )


@router.put("/occurrences/{occurrence_id}/assign", response_model=TaskOccurrence)
async def assign_occurrence(
    occurrence_id: UUID,
    assigned_to: UUID = Body(..., embed=True),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Assigner une occurrence à un membre du ménage.
    """
    try:
        # Récupérer l'occurrence
        occurrence = await get_task_occurrence(db_pool, occurrence_id)
        
        if not occurrence:
            raise OccurrenceNotFound(occurrence_id=str(occurrence_id))
        
        # Vérifier l'accès au ménage
        household_id = occurrence["household_id"]
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="occurrence",
                action="assign"
            )
        
        # Vérifier que la personne assignée est membre du ménage
        assigned_member_access = await check_household_access(
            db_pool, household_id, str(assigned_to)
        )
        if not assigned_member_access:
            raise InvalidInput(
                field="assigned_to",
                value=str(assigned_to),
                reason="L'utilisateur assigné n'est pas membre du ménage"
            )
        
        # Vérifier que l'occurrence peut être assignée
        if occurrence["status"] in [TaskStatus.DONE.value, TaskStatus.SKIPPED.value]:
            raise BusinessRuleViolation(
                rule="CANNOT_ASSIGN_COMPLETED",
                details="Une occurrence terminée ne peut pas être réassignée"
            )
        
        # Mettre à jour l'assignation
        current_status = TaskStatus(occurrence["status"])
        updated_occurrence = await update_task_occurrence_status(
            db_pool,
            occurrence_id,
            current_status,
            assigned_to=assigned_to
        )
        
        logger.info(
            "Occurrence assignée",
            extra=with_context(
                occurrence_id=str(occurrence_id),
                assigned_to=str(assigned_to),
                assigned_by=current_user["id"]
            )
        )
        
        return updated_occurrence
        
    except (UnauthorizedAccess, OccurrenceNotFound, BusinessRuleViolation, InvalidInput):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="assignation de l'occurrence",
            details=str(e)
        )


@router.put("/occurrences/{occurrence_id}/reopen", response_model=TaskOccurrence)
async def reopen_occurrence(
    occurrence_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Remettre une occurrence effectuée à refaire aujourd'hui (repasser en pending).
    """
    try:
        occurrence = await get_task_occurrence(db_pool, occurrence_id)
        if not occurrence:
            raise OccurrenceNotFound(occurrence_id=str(occurrence_id))

        household_id = occurrence["household_id"]
        has_access = await check_household_access(db_pool, household_id, current_user["id"])
        if not has_access:
            raise UnauthorizedAccess(resource="occurrence", action="reopen")

        if occurrence["status"] != TaskStatus.DONE.value:
            raise BusinessRuleViolation(
                rule="NOT_COMPLETED",
                details="Seules les occurrences terminées peuvent être remises à faire"
            )

        updated_occurrence = await update_task_occurrence_status(db_pool, occurrence_id, TaskStatus.PENDING)

        logger.info(
            "Occurrence rouverte (à refaire)",
            extra=with_context(
                occurrence_id=str(occurrence_id),
                reopened_by=current_user["id"]
            )
        )

        return updated_occurrence

    except (UnauthorizedAccess, OccurrenceNotFound, BusinessRuleViolation):
        raise
    except Exception as e:
        raise DatabaseError(operation="réouverture de l'occurrence", details=str(e))


@router.delete("/occurrences/{occurrence_id}")
async def delete_occurrence(
    occurrence_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Supprimer une occurrence. Utilisé pour retirer une occurrence terminée du dashboard.
    """
    try:
        occurrence = await get_task_occurrence(db_pool, occurrence_id)
        if not occurrence:
            raise OccurrenceNotFound(occurrence_id=str(occurrence_id))

        household_id = occurrence["household_id"]
        has_access = await check_household_access(db_pool, household_id, current_user["id"])
        if not has_access:
            raise UnauthorizedAccess(resource="occurrence", action="delete")

        success = await delete_task_occurrence(db_pool, occurrence_id)
        if not success:
            raise DatabaseError(operation="suppression de l'occurrence", details="Aucune ligne supprimée")

        logger.info(
            "Occurrence supprimée",
            extra=with_context(occurrence_id=str(occurrence_id), deleted_by=current_user["id"])
        )
        return {"status": "deleted"}

    except (UnauthorizedAccess, OccurrenceNotFound):
        raise
    except Exception as e:
        raise DatabaseError(operation="suppression de l'occurrence", details=str(e))

@household_router.post("/{household_id}/occurrences/generate")
async def generate_household_occurrences(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    days_ahead: int = Query(30, ge=1, le=90, description="Nombre de jours à générer")
):
    """
    Générer les occurrences pour toutes les tâches du ménage.
    
    Cette action est normalement effectuée automatiquement par un job,
    mais peut être déclenchée manuellement.
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
        
        # Générer les occurrences
        occurrences = await generate_occurrences_for_household(
            db_pool,
            household_id,
            days_ahead=days_ahead
        )
        
        logger.info(
            "Occurrences générées pour le ménage",
            extra=with_context(
                household_id=str(household_id),
                days_ahead=days_ahead,
                occurrences_count=len(occurrences),
                generated_by=current_user["id"]
            )
        )
        
        return {
            "message": f"{len(occurrences)} occurrences générées",
            "count": len(occurrences),
            "days_ahead": days_ahead
        }
        
    except (UnauthorizedAccess,):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="génération des occurrences",
            details=str(e)
        )


@household_router.post("/{household_id}/occurrences/check-overdue")
async def check_overdue_occurrences(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Vérifier et marquer les occurrences en retard.
    
    Cette action est normalement effectuée automatiquement,
    mais peut être déclenchée manuellement.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="check_overdue"
            )
        
        # Mettre à jour les occurrences en retard
        count = await check_and_update_overdue_occurrences(
            db_pool,
            household_id=household_id
        )
        
        logger.info(
            "Vérification des tâches en retard",
            extra=with_context(
                household_id=str(household_id),
                overdue_count=count,
                checked_by=current_user["id"]
            )
        )
        
        return {
            "message": f"{count} occurrence(s) marquée(s) en retard",
            "count": count
        }
        
    except (UnauthorizedAccess,):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="vérification des retards",
            details=str(e)
        )


@household_router.get("/{household_id}/occurrences/stats")
async def get_occurrence_stats(
    household_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    start_date: date = Query(..., description="Date de début"),
    end_date: date = Query(..., description="Date de fin"),
    assigned_to: Optional[UUID] = Query(None, description="Filtrer par membre")
):
    """
    Obtenir des statistiques sur les occurrences.
    """
    try:
        # Vérifier l'accès au ménage
        has_access = await check_household_access(
            db_pool, household_id, current_user["id"]
        )
        if not has_access:
            raise UnauthorizedAccess(
                resource="ménage",
                action="view_stats"
            )
        
        # Récupérer toutes les occurrences de la période
        occurrences = await get_task_occurrences(
            db_pool,
            household_id=household_id,
            start_date=start_date,
            end_date=end_date,
            assigned_to=assigned_to
        )
        
        # Calculer les statistiques
        stats = {
            "total": len(occurrences),
            "by_status": {
                "pending": 0,
                "snoozed": 0,
                "done": 0,
                "skipped": 0,
                "overdue": 0
            },
            "completion_rate": 0.0,
            "by_room": {},
            "by_assignee": {}
        }
        
        for occ in occurrences:
            # Par statut
            status = occ["status"]
            if status in stats["by_status"]:
                stats["by_status"][status] += 1
            
            # Par pièce
            room_name = occ.get("room_name", "Sans pièce")
            if room_name not in stats["by_room"]:
                stats["by_room"][room_name] = {"total": 0, "done": 0}
            stats["by_room"][room_name]["total"] += 1
            if status == TaskStatus.DONE.value:
                stats["by_room"][room_name]["done"] += 1
            
            # Par assigné
            assignee = occ.get("assigned_user_email", "Non assigné")
            if assignee not in stats["by_assignee"]:
                stats["by_assignee"][assignee] = {"total": 0, "done": 0}
            stats["by_assignee"][assignee]["total"] += 1
            if status == TaskStatus.DONE.value:
                stats["by_assignee"][assignee]["done"] += 1
        
        # Calculer le taux de complétion
        if stats["total"] > 0:
            stats["completion_rate"] = (
                stats["by_status"]["done"] / stats["total"] * 100
            )
        
        return stats
        
    except (UnauthorizedAccess,):
        raise
    except Exception as e:
        raise DatabaseError(
            operation="calcul des statistiques",
            details=str(e)
        )