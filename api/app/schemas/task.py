from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from enum import Enum


# Enums pour les statuts
class TaskStatus(str, Enum):
    PENDING = "pending"
    SNOOZED = "snoozed"
    DONE = "done"
    SKIPPED = "skipped"
    OVERDUE = "overdue"


# ============================================================================
# TASK DEFINITIONS (Templates de tâches)
# ============================================================================

class TaskDefinitionBase(BaseModel):
    title: str
    description: Optional[str] = None
    recurrence_rule: Optional[str] = None  # RRULE format (ex: "FREQ=WEEKLY;BYDAY=MO,FR")
    estimated_minutes: Optional[int] = None
    room_id: Optional[UUID] = None
    is_catalog: bool = False

    model_config = ConfigDict(strict=False)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Valider que le titre n'est pas vide"""
        if not v or v.strip() == "":
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip()

    @field_validator("recurrence_rule")
    @classmethod
    def validate_recurrence_rule(cls, v: Optional[str]) -> Optional[str]:
        """Valider le format basique de la règle de récurrence"""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None  # Sera validé dans le routeur pour retourner HTTP 400
        return v.strip() if v else v

    @field_validator("estimated_minutes")
    @classmethod
    def validate_estimated_minutes(cls, v: Optional[int]) -> Optional[int]:
        """Valider que la durée estimée est positive"""
        if v is not None and v <= 0:
            raise ValueError("La durée estimée doit être positive")
        return v


class TaskDefinitionCreate(TaskDefinitionBase):
    household_id: Optional[UUID] = None  # None pour les tâches du catalogue global

    @model_validator(mode="after")
    def validate_household_for_catalog(self) -> "TaskDefinitionCreate":
        """Valider la cohérence entre is_catalog et household_id"""
        if self.is_catalog and self.household_id is not None:
            raise ValueError("Les tâches du catalogue ne doivent pas avoir de household_id")
        if not self.is_catalog and self.household_id is None:
            raise ValueError("Les tâches personnalisées doivent avoir un household_id")
        return self


class TaskDefinitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    recurrence_rule: Optional[str] = None
    estimated_minutes: Optional[int] = None
    room_id: Optional[UUID] = None

    model_config = ConfigDict(strict=False)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Valider que le titre n'est pas vide s'il est fourni"""
        if v is not None and v.strip() == "":
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip() if v else v

    @field_validator("estimated_minutes")
    @classmethod
    def validate_estimated_minutes(cls, v: Optional[int]) -> Optional[int]:
        """Valider que la durée estimée est positive si fournie"""
        if v is not None and v <= 0:
            raise ValueError("La durée estimée doit être positive")
        return v


class TaskDefinition(TaskDefinitionBase):
    id: UUID
    household_id: Optional[UUID]
    created_by: Optional[UUID]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TASK OCCURRENCES (Instances de tâches)
# ============================================================================

class TaskOccurrenceBase(BaseModel):
    task_id: UUID
    scheduled_date: date
    due_at: datetime
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[UUID] = None
    snoozed_until: Optional[datetime] = None

    model_config = ConfigDict(strict=False, use_enum_values=True)

    @field_validator("snoozed_until")
    @classmethod
    def validate_snoozed_until(cls, v: Optional[datetime], values) -> Optional[datetime]:
        """Valider que snoozed_until est cohérent avec le statut"""
        status = values.data.get("status", TaskStatus.PENDING)
        if v is not None and status != TaskStatus.SNOOZED:
            raise ValueError("snoozed_until ne peut être défini que si le statut est 'snoozed'")
        if status == TaskStatus.SNOOZED and v is None:
            raise ValueError("snoozed_until doit être défini si le statut est 'snoozed'")
        return v


class TaskOccurrenceCreate(BaseModel):
    task_id: UUID
    scheduled_date: date
    due_at: datetime
    assigned_to: Optional[UUID] = None

    model_config = ConfigDict(strict=False)


class TaskOccurrenceUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    assigned_to: Optional[UUID] = None
    snoozed_until: Optional[datetime] = None

    model_config = ConfigDict(strict=False, use_enum_values=True)

    @field_validator("snoozed_until")
    @classmethod
    def validate_snoozed_until(cls, v: Optional[datetime], values) -> Optional[datetime]:
        """Valider que snoozed_until est dans le futur"""
        if v is not None and v <= datetime.now():
            raise ValueError("snoozed_until doit être dans le futur")
        return v


class TaskOccurrence(TaskOccurrenceBase):
    id: UUID
    created_at: datetime
    # Informations jointes de la définition de tâche
    task_definition: Optional[TaskDefinition] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TASK COMPLETIONS (Historique des complétions)
# ============================================================================

class TaskCompletionBase(BaseModel):
    occurrence_id: UUID
    completed_by: UUID
    completed_at: datetime
    duration_minutes: Optional[int] = None
    comment: Optional[str] = None
    photo_url: Optional[str] = None

    model_config = ConfigDict(strict=False)

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        """Valider que la durée est positive"""
        if v is not None and v <= 0:
            raise ValueError("La durée doit être positive")
        return v


class TaskCompletionCreate(BaseModel):
    duration_minutes: Optional[int] = None
    comment: Optional[str] = None
    photo_url: Optional[str] = None

    model_config = ConfigDict(strict=False)


class TaskCompletion(TaskCompletionBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ACTIONS SUR LES OCCURRENCES
# ============================================================================

class TaskOccurrenceComplete(BaseModel):
    """Payload pour marquer une occurrence comme complétée"""
    duration_minutes: Optional[int] = None
    comment: Optional[str] = None
    photo_url: Optional[str] = None

    model_config = ConfigDict(strict=False)


class TaskOccurrenceSnooze(BaseModel):
    """Payload pour reporter une occurrence"""
    snoozed_until: datetime

    model_config = ConfigDict(strict=False)

    @field_validator("snoozed_until")
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        """Valider que la date de report est dans le futur"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Si v n'a pas de timezone, on assume UTC
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError("La date de report doit être dans le futur")
        return v


class TaskOccurrenceSkip(BaseModel):
    """Payload pour ignorer une occurrence"""
    reason: Optional[str] = None

    model_config = ConfigDict(strict=False)


# ============================================================================
# REQUÊTES ET FILTRES
# ============================================================================

class TaskOccurrenceFilter(BaseModel):
    """Filtres pour la recherche d'occurrences"""
    household_id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    assigned_to: Optional[UUID] = None
    room_id: Optional[UUID] = None

    model_config = ConfigDict(strict=False, use_enum_values=True)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[date], values) -> Optional[date]:
        """Valider que end_date >= start_date"""
        start_date = values.data.get("start_date")
        if start_date and v and v < start_date:
            raise ValueError("end_date doit être après start_date")
        return v


class TaskDefinitionFilter(BaseModel):
    """Filtres pour la recherche de définitions de tâches"""
    household_id: Optional[UUID] = None
    is_catalog: Optional[bool] = None
    room_id: Optional[UUID] = None
    created_by: Optional[UUID] = None

    model_config = ConfigDict(strict=False)


# ============================================================================
# RÉPONSES AGRÉGÉES
# ============================================================================

class TaskOccurrenceWithDefinition(TaskOccurrence):
    """Occurrence avec les détails de sa définition"""
    definition_title: str
    definition_description: Optional[str]
    room_name: Optional[str]
    assigned_user_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TaskStats(BaseModel):
    """Statistiques sur les tâches"""
    total_occurrences: int
    completed_occurrences: int
    overdue_occurrences: int
    completion_rate: float
    average_duration_minutes: Optional[float] = None

    model_config = ConfigDict(strict=False)