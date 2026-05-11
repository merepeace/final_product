from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from controllers.system_log import create_log
from models.agv import AGVModel
from models.order import OrderModel
from models.product import Product
from models.zone import ZoneModel
from schemas.order import OrderCreate, OrderStatus, OrderUpdate
from services.file_export import export_snapshot_safe

FINAL_STATUSES = {
    OrderStatus.DELIVERED.value,
    OrderStatus.CANCELLED.value,
    OrderStatus.FAILED.value,
}


def _ensure_zone(db: Session, zone_name: str) -> ZoneModel:
    zone = db.query(ZoneModel).filter(ZoneModel.name == zone_name).first()
    if not zone or not zone.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Zone '{zone_name}' does not exist or is inactive",
        )
    return zone


def _ensure_product(db: Session, product_name: str) -> Product:
    product = db.query(Product).filter(Product.productname == product_name).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product '{product_name}' not found",
        )
    return product


def queue_snapshot(db: Session) -> Dict[str, Any]:
    """Counts for UI: validated orders waiting for an idle AGV vs fleet capacity."""
    validated_waiting = (
        db.query(OrderModel)
        .filter(OrderModel.status == OrderStatus.VALIDATED.value)
        .count()
    )
    idle_agvs = (
        db.query(AGVModel).filter(AGVModel.status == "idle").count()
    )
    busy_agvs = (
        db.query(AGVModel).filter(AGVModel.status == "busy").count()
    )
    return {
        "validated_orders_waiting": validated_waiting,
        "idle_agvs": idle_agvs,
        "busy_agvs": busy_agvs,
        "note": "Orders in 'validated' are queued until an AGV becomes idle.",
    }


def list_orders(db: Session) -> List[OrderModel]:
    return (
        db.query(OrderModel)
        .order_by(OrderModel.priority.desc(), OrderModel.order_time.asc())
        .all()
    )


def get_order(db: Session, order_id: int) -> Optional[OrderModel]:
    return db.query(OrderModel).filter(OrderModel.id == order_id).first()


def create_order(db: Session, payload: OrderCreate) -> OrderModel:
    if payload.from_location == payload.to_location:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="From and To locations cannot be the same",
        )

    _ensure_zone(db, payload.from_location)
    _ensure_zone(db, payload.to_location)

    product = _ensure_product(db, payload.product)
    if product.stock_quantity < payload.qty:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient stock: {product.stock_quantity} available, {payload.qty} requested",
        )

    order = OrderModel(
        order_name=payload.order_name,
        product=payload.product,
        qty=payload.qty,
        status=OrderStatus.PENDING.value,
        agv=None,
        priority=payload.priority,
        from_location=payload.from_location,
        to_location=payload.to_location,
        order_time=datetime.utcnow(),
    )
    db.add(order)
    db.flush()
    order.status = OrderStatus.VALIDATED.value
    db.commit()
    db.refresh(order)

    create_log(
        db,
        message=f"Order #{order.id} '{order.order_name}' created and validated (priority={order.priority})",
        source="API",
    )
    export_snapshot_safe()
    return order


def update_order(
    db: Session, order_id: int, payload: OrderUpdate
) -> Optional[OrderModel]:
    order = get_order(db, order_id)
    if not order:
        return None

    data = payload.model_dump(exclude_unset=True)

    if "from_location" in data:
        _ensure_zone(db, data["from_location"])
    if "to_location" in data:
        _ensure_zone(db, data["to_location"])
    if "product" in data:
        _ensure_product(db, data["product"])

    for key, value in data.items():
        if isinstance(value, OrderStatus):
            value = value.value
        setattr(order, key, value)

    db.commit()
    db.refresh(order)
    create_log(db, message=f"Order #{order.id} updated", source="API")
    export_snapshot_safe()
    return order


def delete_order(db: Session, order_id: int) -> bool:
    order = get_order(db, order_id)
    if not order:
        return False
    db.delete(order)
    db.commit()
    create_log(db, message=f"Order #{order_id} deleted", source="API")
    export_snapshot_safe()
    return True


def cancel_order(db: Session, order_id: int) -> Optional[OrderModel]:
    order = get_order(db, order_id)
    if not order:
        return None
    if order.status in FINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order is already '{order.status}' and cannot be cancelled",
        )

    order.status = OrderStatus.CANCELLED.value
    db.commit()
    db.refresh(order)

    create_log(
        db,
        message=f"Order #{order.id} cancelled",
        level="WARN",
        source="API",
    )
    export_snapshot_safe()
    return order


def confirm_delivery(
    db: Session, order_id: int, confirmed_by: str
) -> Optional[OrderModel]:
    order = get_order(db, order_id)
    if not order:
        return None
    if order.status != OrderStatus.IN_TRANSIT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order status is '{order.status}'. Only 'in_transit' orders can be confirmed.",
        )

    product = (
        db.query(Product).filter(Product.productname == order.product).first()
    )
    if product:
        product.stock_quantity = max(0, product.stock_quantity - order.qty)

    order.status = OrderStatus.DELIVERED.value
    order.completed_timestamp = datetime.utcnow()
    order.confirmed_by = confirmed_by
    db.commit()
    db.refresh(order)

    create_log(
        db,
        message=f"Order #{order.id} delivery confirmed by {confirmed_by}",
        source="API",
    )
    export_snapshot_safe()
    return order
