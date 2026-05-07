import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers.system_log import log_event
from database import Base, engine

# Importing the models registers them with SQLAlchemy's Base metadata.
from models import agv as _agv_model  # noqa: F401
from models import order as _order_model  # noqa: F401
from models import product as _product_model  # noqa: F401
from models import system_log as _system_log_model  # noqa: F401
from models import zone as _zone_model  # noqa: F401
from routes.agvs import router as agvs_router
from routes.auth import router as auth_router
from routes.logs import router as logs_router
from routes.orders import router as orders_router
from routes.product import router as products_router
from routes.zones import router as zones_router
from seed import seed_defaults
from services.agv_simulator import simulator

logger = logging.getLogger("wms-api")

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_defaults()
    await simulator.start()
    try:
        yield
    finally:
        await simulator.stop()


app = FastAPI(title="Warehouse Management System API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    try:
        log_event(
            f"Unhandled error on {request.method} {request.url.path}: {exc}",
            level="ERROR",
            source="API",
        )
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(zones_router)
app.include_router(agvs_router)
app.include_router(logs_router)


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "service": "wms-api"}


# to run the api
# uvicorn api:app --reload
