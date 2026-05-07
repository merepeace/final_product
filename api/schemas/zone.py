from typing import Optional

from pydantic import BaseModel, Field


class ZoneBase(BaseModel):
    name: str = Field(min_length=1)
    zone_type: str = Field(default="destination")
    is_active: bool = True


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    zone_type: Optional[str] = None
    is_active: Optional[bool] = None


class Zone(ZoneBase):
    id: int
    is_occupied: bool = False

    class Config:
        from_attributes = True
