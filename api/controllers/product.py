from sqlalchemy.orm import Session
import models.product as model
import schemas.product as schema

def create_product(db: Session, product: schema.ProductCreate):
    db_product = model.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_all_products(db: Session):
    return db.query(model.Product).all()

def get_product(db: Session, product_id: str):
    return db.query(model.Product).filter(model.Product.id == product_id).first()

def search_products(db, query: str):
    return db.query(model.Product).filter(
        model.Product.productname.ilike(f"%{query}%")
    ).all()

def update_product(db: Session, product_id: str, updated: schema.ProductCreate):
    product = get_product(db, product_id)
    if not product:
        return None

    for key, value in updated.dict().items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: str):
    product = get_product(db, product_id)
    if not product:
        return None

    db.delete(product)
    db.commit()
    return product