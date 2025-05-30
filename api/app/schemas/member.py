from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID


class HouseholdMemberBase(BaseModel):
    household_id: UUID
    user_id: UUID
    role: Literal["admin", "member", "guest"] = "member"
    joined_at: Optional[datetime] = None


class HouseholdMemberCreate(HouseholdMemberBase):
    household_id: Optional[UUID] = None  # Rendre optionnel
    pass


class HouseholdMember(HouseholdMemberBase):
    user_id: UUID
    role: Literal["admin", "member", "guest"] = "member"
    model_config = {"from_attributes": True}


class HouseholdMemberUpdate(BaseModel):
    role: Optional[Literal["admin", "member", "guest"]] = None
