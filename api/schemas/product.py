from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    productname: str
    model: str
    color: str
    stock_quantity: int = Field(ge=0)
    price_usd: float = Field(gt=0)
    location: str
    min_stock: int = Field(ge=0)

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: str

    class Config:
        from_attributes = True