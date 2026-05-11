from typing import List, Optional

from sqlalchemy.orm import Session

from models.order import OrderModel
from models.zone import ZoneModel
from schemas.order import OrderStatus
from schemas.zone import ZoneCreate, ZoneUpdate

# Zones tied to an order route while the job is queued or moving on an AGV.
ACTIVE_ORDER_STATUSES = (
    OrderStatus.VALIDATED.value,
    OrderStatus.ASSIGNED.value,
    OrderStatus.IN_TRANSIT.value,
)


def _occupied_zone_names(db: Session) -> set[str]:
    rows = (
        db.query(OrderModel.from_location, OrderModel.to_location)
        .filter(OrderModel.status.in_(ACTIVE_ORDER_STATUSES))
        .all()
    )
    names: set[str] = set()
    for from_loc, to_loc in rows:
        if from_loc:
            names.add(from_loc)
        if to_loc:
            names.add(to_loc)
    return names


def _attach_occupancy(zones: List[ZoneModel], occupied: set[str]) -> List[ZoneModel]:
    for zone in zones:
        zone.is_occupied = zone.name in occupied
    return zones


def list_zones(db: Session) -> List[ZoneModel]:
    zones = db.query(ZoneModel).order_by(ZoneModel.id.asc()).all()
    return _attach_occupancy(zones, _occupied_zone_names(db))


def get_zone(db: Session, zone_id: int) -> Optional[ZoneModel]:
    zone = db.query(ZoneModel).filter(ZoneModel.id == zone_id).first()
    if not zone:
        return None
    occupied = _occupied_zone_names(db)
    zone.is_occupied = zone.name in occupied
    return zone


def get_zone_by_name(db: Session, name: str) -> Optional[ZoneModel]:
    return db.query(ZoneModel).filter(ZoneModel.name == name).first()


def create_zone(db: Session, payload: ZoneCreate) -> ZoneModel:
    zone = ZoneModel(
        name=payload.name,
        zone_type=payload.zone_type,
        is_active=payload.is_active,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    zone.is_occupied = False
    return zone


def update_zone(db: Session, zone_id: int, payload: ZoneUpdate) -> Optional[ZoneModel]:
    zone = db.query(ZoneModel).filter(ZoneModel.id == zone_id).first()
    if not zone:
        return None
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(zone, key, value)
    db.commit()
    db.refresh(zone)
    zone.is_occupied = zone.name in _occupied_zone_names(db)
    return zone


def delete_zone(db: Session, zone_id: int) -> Optional[ZoneModel]:
    zone = db.query(ZoneModel).filter(ZoneModel.id == zone_id).first()
    if not zone:
        return None
    db.delete(zone)
    db.commit()
    return zone
