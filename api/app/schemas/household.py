from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class HouseholdBase(BaseModel):
    name: str

    model_config = {"strict": True}


class HouseholdCreate(HouseholdBase):
    pass


class Household(HouseholdBase):
    id: UUID
    created_at: datetime
    name: str

    model_config = {"from_attributes": True}  # Pas de strict ici, c'est pour la sortie
