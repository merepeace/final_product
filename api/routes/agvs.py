from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers.agv as agvController
from dependencies import get_current_user, get_db
from schemas.agv import AGV, AGVCreate, AGVUpdate
from services.file_export import export_snapshot_safe

router = APIRouter(
    prefix="/agvs",
    tags=["AGVs"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[AGV])
def read_agvs(db: Session = Depends(get_db)):
    return agvController.list_agvs(db)


@router.get("/{agv_id}", response_model=AGV)
def read_agv(agv_id: int, db: Session = Depends(get_db)):
    agv = agvController.get_agv(db, agv_id)
    if not agv:
        raise HTTPException(status_code=404, detail="AGV not found")
    return agv


@router.post("/", response_model=AGV, status_code=201)
def add_agv(payload: AGVCreate, db: Session = Depends(get_db)):
    agv = agvController.create_agv(db, payload)
    export_snapshot_safe()
    return agv


@router.put("/{agv_id}", response_model=AGV)
def update_existing_agv(
    agv_id: int, payload: AGVUpdate, db: Session = Depends(get_db)
):
    updated = agvController.update_agv(db, agv_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="AGV not found")
    export_snapshot_safe()
    return updated


@router.delete("/{agv_id}")
def remove_agv(agv_id: int, db: Session = Depends(get_db)):
    deleted = agvController.delete_agv(db, agv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="AGV not found")
    export_snapshot_safe()
    return {"message": "AGV deleted successfully"}
