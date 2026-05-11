from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers.order as orderController
from dependencies import get_current_user, get_db
from schemas.order import Order, OrderConfirm, OrderCreate, OrderUpdate

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=List[Order])
def read_orders(db: Session = Depends(get_db)):
    return orderController.list_orders(db)


@router.get("/queue", response_model=Dict[str, Any])
def orders_queue(db: Session = Depends(get_db)):
    """AGV queue vs validated orders (idle AGVs pick the next job automatically)."""
    return orderController.queue_snapshot(db)


@router.get("/{order_id}", response_model=Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    order = orderController.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=Order, status_code=201)
def create_new_order(payload: OrderCreate, db: Session = Depends(get_db)):
    return orderController.create_order(db, payload)


@router.put("/{order_id}", response_model=Order)
def update_existing_order(
    order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)
):
    updated = orderController.update_order(db, order_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated


@router.delete("/{order_id}")
def remove_order(order_id: int, db: Session = Depends(get_db)):
    success = orderController.delete_order(db, order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}


@router.post("/{order_id}/cancel", response_model=Order)
def cancel(order_id: int, db: Session = Depends(get_db)):
    cancelled = orderController.cancel_order(db, order_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Order not found")
    return cancelled


@router.post("/{order_id}/confirm", response_model=Order)
def confirm(order_id: int, payload: OrderConfirm, db: Session = Depends(get_db)):
    confirmed = orderController.confirm_delivery(db, order_id, payload.confirmed_by)
    if not confirmed:
        raise HTTPException(status_code=404, detail="Order not found")
    return confirmed
