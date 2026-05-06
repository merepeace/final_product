from sqlalchemy import Column, String, Integer, Float
from database import Base
import uuid

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    productname = Column(String, nullable=False)
    model = Column(String, nullable=False)
    color = Column(String, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    price_usd = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    min_stock = Column(Integer, nullable=False)