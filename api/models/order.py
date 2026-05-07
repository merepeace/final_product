from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_name = Column(String, nullable=False)
    product = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    agv = Column(String, nullable=True)
    priority = Column(Integer, nullable=False, default=3)
    from_location = Column(String, nullable=False)
    to_location = Column(String, nullable=False)
    order_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_timestamp = Column(DateTime, nullable=True)
    confirmed_by = Column(String, nullable=True)
