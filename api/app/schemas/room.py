from pydantic import BaseModel
from typing import Optional


class RoomBase(BaseModel):
    name: str
    icon: Optional[str] = None

    model_config = {"strict": True}


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    model_config = {"from_attributes": True}
