from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    DELIVERING = "delivering"
    DONE = "done"
    CANCELLED = "cancelled"


class OrderBase(BaseModel):
    order_name: str = Field(min_length=1)
    product: str = Field(min_length=1)
    qty: int = Field(gt=0)
    priority: int = Field(ge=1, le=5)
    from_location: str = Field(min_length=1)
    to_location: str = Field(min_length=1)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    order_name: Optional[str] = None
    product: Optional[str] = None
    qty: Optional[int] = Field(default=None, gt=0)
    status: Optional[OrderStatus] = None
    agv: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    from_location: Optional[str] = None
    to_location: Optional[str] = None


class OrderConfirm(BaseModel):
    confirmed_by: str = Field(min_length=1)


class Order(OrderBase):
    id: int
    status: OrderStatus
    agv: Optional[str] = None
    order_time: datetime
    completed_timestamp: Optional[datetime] = None
    confirmed_by: Optional[str] = None

    class Config:
        from_attributes = True
