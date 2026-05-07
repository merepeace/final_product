from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from models.agv import AGVModel
from schemas.agv import AGVCreate, AGVUpdate


def list_agvs(db: Session) -> List[AGVModel]:
    return db.query(AGVModel).order_by(AGVModel.id.asc()).all()


def get_agv(db: Session, agv_id: int) -> Optional[AGVModel]:
    return db.query(AGVModel).filter(AGVModel.id == agv_id).first()


def get_agv_by_name(db: Session, name: str) -> Optional[AGVModel]:
    return db.query(AGVModel).filter(AGVModel.name == name).first()


def create_agv(db: Session, payload: AGVCreate) -> AGVModel:
    agv = AGVModel(name=payload.name, status="idle", last_active=datetime.utcnow())
    db.add(agv)
    db.commit()
    db.refresh(agv)
    return agv


def update_agv(db: Session, agv_id: int, payload: AGVUpdate) -> Optional[AGVModel]:
    agv = get_agv(db, agv_id)
    if not agv:
        return None
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(agv, key, value)
    agv.last_active = datetime.utcnow()
    db.commit()
    db.refresh(agv)
    return agv


def delete_agv(db: Session, agv_id: int) -> Optional[AGVModel]:
    agv = get_agv(db, agv_id)
    if not agv:
        return None
    db.delete(agv)
    db.commit()
    return agv


def first_idle_agv(db: Session) -> Optional[AGVModel]:
    return (
        db.query(AGVModel)
        .filter(AGVModel.status == "idle")
        .order_by(AGVModel.id.asc())
        .first()
    )


def mark_busy(db: Session, agv: AGVModel, order_id: int) -> AGVModel:
    agv.status = "busy"
    agv.current_order_id = order_id
    agv.last_active = datetime.utcnow()
    db.commit()
    db.refresh(agv)
    return agv


def mark_idle(db: Session, agv: AGVModel) -> AGVModel:
    agv.status = "idle"
    agv.current_order_id = None
    agv.last_active = datetime.utcnow()
    db.commit()
    db.refresh(agv)
    return agv
