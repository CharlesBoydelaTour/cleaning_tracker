from pydantic import BaseModel
from datetime import date
from uuid import UUID


class TaskBase(BaseModel):
    title: str
    description: str | None = None


class TaskCreate(TaskBase):
    household_id: UUID


class Task(TaskBase):
    id: UUID
    due_date: date
    completed: bool


class Occurrence(BaseModel):
    id: UUID
    task_id: UUID
    date: date
    completed: bool
