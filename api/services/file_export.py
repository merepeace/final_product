"""Mirror SQLite state to CSV files under ``api/data/`` (assignment + backups).

Failures are non-fatal for API requests: OSError is logged; DB remains canonical.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from database import SessionLocal
from models.agv import AGVModel
from models.order import OrderModel
from models.system_log import SystemLogModel

logger = logging.getLogger("wms-file-export")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _write_csv(path: Path, headers: list[str], rows: Iterable[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def export_all_csv(db: Session | None = None) -> None:
    """Write orders.csv, agvs.csv, logs.csv. Pass ``db`` to join an existing transaction (read-only)."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    assert db is not None
    try:
        orders = db.query(OrderModel).order_by(OrderModel.id.asc()).all()
        order_rows = [
            [
                o.id,
                o.order_name,
                o.product,
                o.qty,
                o.status,
                o.agv or "",
                o.priority,
                o.from_location,
                o.to_location,
                o.order_time.isoformat() if o.order_time else "",
                o.completed_timestamp.isoformat() if o.completed_timestamp else "",
                o.confirmed_by or "",
            ]
            for o in orders
        ]
        _write_csv(
            DATA_DIR / "orders.csv",
            [
                "id",
                "order_name",
                "product",
                "qty",
                "status",
                "agv",
                "priority",
                "from_location",
                "to_location",
                "order_time",
                "completed_timestamp",
                "confirmed_by",
            ],
            order_rows,
        )

        agvs = db.query(AGVModel).order_by(AGVModel.id.asc()).all()
        agv_rows = [
            [
                a.id,
                a.name,
                a.status,
                a.current_order_id or "",
                a.last_active.isoformat() if a.last_active else "",
            ]
            for a in agvs
        ]
        _write_csv(
            DATA_DIR / "agvs.csv",
            ["id", "name", "status", "current_order_id", "last_active"],
            agv_rows,
        )

        logs = (
            db.query(SystemLogModel)
            .order_by(SystemLogModel.id.asc())
            .limit(5000)
            .all()
        )
        log_rows = [
            [
                e.id,
                e.timestamp.isoformat() if e.timestamp else "",
                e.level,
                e.source,
                e.message.replace("\n", " ").replace("\r", ""),
            ]
            for e in logs
        ]
        _write_csv(
            DATA_DIR / "logs.csv",
            ["id", "timestamp", "level", "source", "message"],
            log_rows,
        )
    except OSError as exc:
        logger.warning("CSV export failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error during CSV export")
    finally:
        if own_session:
            db.close()


def export_snapshot_safe() -> None:
    """Public entry for routes / background; never raises."""
    try:
        export_all_csv()
    except Exception:
        logger.exception("export_snapshot_safe")


def append_audit_line(
    timestamp_iso: str, level: str, source: str, message: str
) -> None:
    """Append one line to ``warehouse_audit.log`` (text audit trail)."""
    try:
        audit_path = DATA_DIR / "warehouse_audit.log"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        safe = message.replace("\n", " ").replace("\r", " ")
        with audit_path.open("a", encoding="utf-8") as af:
            af.write(f"{timestamp_iso}\t{level}\t{source}\t{safe}\n")
    except OSError as exc:
        logger.warning("Audit log append failed: %s", exc)
