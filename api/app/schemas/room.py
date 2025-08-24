from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID


class RoomBase(BaseModel):
    name: str
    icon: Optional[str] = None

    model_config = {"strict": False}

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Le nom de la pièce ne peut pas être vide')
        return v.strip()


class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None

    model_config = {"strict": False}

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Le nom de la pièce ne peut pas être vide')
        return v.strip()


class Room(RoomBase):
    id: UUID
    household_id: UUID
    
    model_config = {"from_attributes": True}
