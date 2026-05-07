from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AGVStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


class AGVBase(BaseModel):
    name: str = Field(min_length=1)


class AGVCreate(AGVBase):
    pass


class AGVUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    status: Optional[AGVStatus] = None


class AGV(AGVBase):
    id: int
    status: AGVStatus
    current_order_id: Optional[int] = None
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True
