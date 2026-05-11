from fastapi import APIRouter, Depends

from dependencies import get_current_user
from services.file_export import DATA_DIR, export_snapshot_safe

router = APIRouter(
    prefix="/export",
    tags=["Export"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/snapshot")
def write_csv_snapshot():
    """Regenerate ``data/orders.csv``, ``data/agvs.csv``, and ``data/logs.csv``."""
    export_snapshot_safe()
    return {
        "ok": True,
        "directory": str(DATA_DIR.resolve()),
        "files": ["orders.csv", "agvs.csv", "logs.csv", "warehouse_audit.log"],
    }
