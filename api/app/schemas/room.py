from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class RoomBase(BaseModel):
    name: str
    icon: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    model_config = {"from_attributes": True}
