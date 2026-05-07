from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers.product as productController
import schemas.product as schema
from dependencies import get_current_user, get_db

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=schema.ProductResponse, status_code=201)
def create(product: schema.ProductCreate, db: Session = Depends(get_db)):
    return productController.create_product(db, product)


@router.get("/", response_model=list[schema.ProductResponse])
def get_all(db: Session = Depends(get_db)):
    return productController.get_all_products(db)


@router.get("/{product_id}", response_model=schema.ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = productController.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=schema.ProductResponse)
def update(
    product_id: str, product: schema.ProductCreate, db: Session = Depends(get_db)
):
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
