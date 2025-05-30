from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class HouseholdBase(BaseModel):
    name: str


class HouseholdCreate(HouseholdBase):
    pass


class Household(HouseholdBase):
    id: UUID
    created_at: datetime
    name: str

    model_config = {"from_attributes": True}
