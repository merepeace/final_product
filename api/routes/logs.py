from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import controllers.system_log as logController
from dependencies import get_current_user, get_db
from schemas.system_log import SystemLog

router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[SystemLog])
def read_logs(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    source: Optional[str] = None,
):
    return logController.list_logs(db, limit=limit, source=source)
