from sqlalchemy import Boolean, Column, Integer, String

from database import Base


class ZoneModel(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    zone_type = Column(String, nullable=False, default="destination")
    is_active = Column(Boolean, nullable=False, default=True)
