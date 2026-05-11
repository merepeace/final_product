from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from database import SessionLocal
from models.system_log import SystemLogModel
from services.file_export import append_audit_line


def list_logs(db: Session, limit: int = 100, source: Optional[str] = None) -> List[SystemLogModel]:
    query = db.query(SystemLogModel)
    if source:
        query = query.filter(SystemLogModel.source == source)
    return query.order_by(SystemLogModel.timestamp.desc()).limit(limit).all()


def create_log(
    db: Session,
    message: str,
    level: str = "INFO",
    source: str = "API",
) -> SystemLogModel:
    entry = SystemLogModel(
        timestamp=datetime.utcnow(),
        level=level,
        source=source,
        message=message,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    ts = entry.timestamp.isoformat() if entry.timestamp else ""
    append_audit_line(ts, entry.level, entry.source, entry.message)
    return entry


def log_event(message: str, level: str = "INFO", source: str = "API") -> None:
    """Fire-and-forget log helper that opens its own session.

    Use from background tasks or places where a DB session is not available.
    """
    db = SessionLocal()
    try:
        create_log(db, message=message, level=level, source=source)
    except Exception:
        db.rollback()
    finally:
        db.close()
