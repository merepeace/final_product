"""One-shot SQLite migrations for renamed order statuses (legacy rows)."""

from sqlalchemy import text

from database import engine


def migrate_legacy_order_statuses() -> None:
    mapping = [
        ("delivering", "in_transit"),
        ("done", "delivered"),
        ("pending", "validated"),
    ]
    with engine.begin() as conn:
        for old, new in mapping:
            conn.execute(
                text("UPDATE orders SET status = :new WHERE status = :old"),
                {"old": old, "new": new},
            )
