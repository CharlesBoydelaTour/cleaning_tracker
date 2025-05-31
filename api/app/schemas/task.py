from pydantic import BaseModel, field_validator
from datetime import date
from uuid import UUID


class TaskBase(BaseModel):
    title: str
    description: str | None = None

    model_config = {"strict": False}

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Valider que le titre n'est pas vide"""
        if not v or v.strip() == "":
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip()


class TaskCreate(TaskBase):
    household_id: UUID


class Task(TaskBase):
    id: UUID
    household_id: UUID
    due_date: date
    completed: bool

    model_config = {"strict": False}


class Occurrence(BaseModel):
    id: UUID
    task_id: UUID
    date: date
    completed: bool
