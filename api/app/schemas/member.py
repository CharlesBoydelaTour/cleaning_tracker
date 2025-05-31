from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID


class HouseholdMemberBase(BaseModel):
    user_id: UUID  # household_id retiré, car il provient de l'URL
    role: Literal["admin", "member", "guest"] = "member"
    joined_at: Optional[datetime] = None

    model_config = {"strict": False}  # Permet la conversion automatique de string vers UUID


class HouseholdMemberCreate(HouseholdMemberBase):  # Hérite maintenant directement de HouseholdMemberBase modifié
    pass


class HouseholdMember(HouseholdMemberBase):
    id: UUID  # Ajout du champ id pour la réponse
    household_id: UUID  # Ajout du champ household_id pour la réponse
    user_id: UUID
    role: Literal["admin", "member", "guest"] = "member"
    model_config = {"from_attributes": True}  # Pas de strict ici


class HouseholdMemberUpdate(BaseModel):
    role: Optional[Literal["admin", "member", "guest"]] = None

    model_config = {"strict": False}  # Cohérence avec les autres schémas
