from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class AGVModel(Base):
    __tablename__ = "agvs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False, default="idle")
    current_order_id = Column(Integer, nullable=True)
    last_active = Column(DateTime, nullable=True, default=datetime.utcnow)
