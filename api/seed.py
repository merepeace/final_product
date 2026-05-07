"""One-time seed of default zones and AGVs (idempotent: only inserts when empty)."""

from datetime import datetime

from sqlalchemy.orm import Session

from controllers.system_log import create_log
from database import SessionLocal
from models.agv import AGVModel
from models.zone import ZoneModel

DEFAULT_ZONES = [
    ("Warehouse", "source"),
    ("Zone A", "destination"),
    ("Zone B", "destination"),
    ("Zone C", "destination"),
    ("Zone D", "destination"),
    ("Production Line", "source"),
]

DEFAULT_AGVS = ["AGV-1", "AGV-2"]


def seed_defaults() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(ZoneModel).count() == 0:
            for name, zone_type in DEFAULT_ZONES:
                db.add(ZoneModel(name=name, zone_type=zone_type, is_active=True))
            db.commit()
            create_log(db, message="Seeded default zones", source="SEED")

        if db.query(AGVModel).count() == 0:
            for name in DEFAULT_AGVS:
                db.add(
                    AGVModel(
                        name=name,
                        status="idle",
                        last_active=datetime.utcnow(),
                    )
                )
            db.commit()
            create_log(db, message="Seeded default AGVs", source="SEED")
    finally:
        db.close()
