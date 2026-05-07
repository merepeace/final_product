from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers.zone as zoneController
from dependencies import get_current_user, get_db
from schemas.zone import Zone, ZoneCreate, ZoneUpdate

router = APIRouter(
    prefix="/zones",
    tags=["Zones"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[Zone])
def read_zones(db: Session = Depends(get_db)):
    return zoneController.list_zones(db)


@router.get("/{zone_id}", response_model=Zone)
def read_zone(zone_id: int, db: Session = Depends(get_db)):
    zone = zoneController.get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.post("/", response_model=Zone, status_code=201)
def add_zone(payload: ZoneCreate, db: Session = Depends(get_db)):
    return zoneController.create_zone(db, payload)


@router.put("/{zone_id}", response_model=Zone)
def update_existing_zone(
    zone_id: int, payload: ZoneUpdate, db: Session = Depends(get_db)
):
    updated = zoneController.update_zone(db, zone_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Zone not found")
    return updated


@router.delete("/{zone_id}")
def remove_zone(zone_id: int, db: Session = Depends(get_db)):
    deleted = zoneController.delete_zone(db, zone_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"message": "Zone deleted successfully"}
