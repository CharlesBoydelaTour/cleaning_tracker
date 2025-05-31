from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID


class HouseholdBase(BaseModel):
    name: str

    model_config = {"strict": True}


class HouseholdCreate(HouseholdBase):
    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name must not be empty")
        return value


class Household(HouseholdBase):
    id: UUID
    created_at: datetime
    name: str

    model_config = {"from_attributes": True}  # Pas de strict ici, c'est pour la sortie
