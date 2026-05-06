from fastapi import FastAPI
from database import engine
from models import product  # important: register model
from routes import product as product_routes

product.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(product_routes.router)


# to run the api
# uvicorn api:app --reload