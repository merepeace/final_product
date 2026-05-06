from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import schemas.product as schema
import controllers.product as productController

router = APIRouter(prefix="/products", tags=["Products"])

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schema.ProductResponse)
def create(product: schema.ProductCreate, db: Session = Depends(get_db)):
    return productController.create_product(db, product)

@router.get("/", response_model=list[schema.ProductResponse])
def get_all(db: Session = Depends(get_db)):
    return productController.get_all_products(db)

@router.put("/{product_id}", response_model=schema.ProductResponse)
def update(product_id: str, product: schema.ProductCreate, db: Session = Depends(get_db)):
    updated = productController.update_product(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated

@router.delete("/{product_id}")
def delete(product_id: str, db: Session = Depends(get_db)):
    deleted = productController.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}