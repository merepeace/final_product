from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class SystemLogModel(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    level = Column(String, nullable=False, default="INFO")
    source = Column(String, nullable=False, default="API")
    message = Column(String, nullable=False)
