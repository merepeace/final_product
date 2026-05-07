import csv
import io
from fastapi import FastAPI, Response, Depends
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import product
from models.product import Product  # Adjust this if your Product model is named differently

# This creates your tables if they don't exist
product.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/export-csv")
def export_products(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).all()
        output = io.StringIO()
        writer = csv.writer(output)

        # Header Row - matching your Product Management screenshot
        writer.writerow(["ID", "Product Name", "Model", "Color", "Stock Qty", "Price (USD)", "Location"])

        for p in products:
            writer.writerow([
                getattr(p, 'id', ''),
                getattr(p, 'productname', ''),  # Make sure these match your models.py attributes
                getattr(p, 'model', ''),
                getattr(p, 'color', ''),
                getattr(p, 'stock_quantity', 0),
                getattr(p, 'price_usd', 0),
                getattr(p, 'location', '')
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=products.csv"}
        )
    except Exception as e:
        return {"error": str(e)}


@app.get("/export-orders")
def export_orders():
    """Using Raw SQLite for orders since your Order system uses it directly"""
    import sqlite3
    try:
        # Connect directly to the db file
        conn = sqlite3.connect('warehouse.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders")
        orders = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header Row - matching your Order Management screenshot
        writer.writerow(["ID", "Order Name", "Product", "Qty", "Status", "Priority", "From", "To", "Time"])

        for o in orders:
            writer.writerow(o)

        conn.close()
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=orders.csv"}
        )
    except Exception as e:
        return {"error": str(e)}