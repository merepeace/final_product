"""AGV background simulator.

Runs as a single asyncio task launched from the FastAPI lifespan. Periodically
scans for validated orders and assigns each one to a free AGV. For every assigned
order, a per-order coroutine simulates the pickup -> travel -> waiting-for-
confirmation -> idle lifecycle, writing SystemLog entries at every transition.

The loop terminates cleanly when ``stop`` is set.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Literal, Optional

from sqlalchemy.orm import Session

from controllers.system_log import log_event
from database import SessionLocal
from models.agv import AGVModel
from models.order import OrderModel
from schemas.order import OrderStatus
from services.file_export import export_snapshot_safe

logger = logging.getLogger("agv-simulator")

POLL_INTERVAL_SECONDS = 2.0
PICKUP_DURATION_SECONDS = 2.0
TRAVEL_BASE_SECONDS = 4.0
CONFIRMATION_TIMEOUT_SECONDS = 60.0

ConfirmOutcome = Literal["delivered", "cancelled", "timeout", "missing"]


class AGVSimulator:
    def __init__(self) -> None:
        self._stop = asyncio.Event()
        self._main_task: Optional[asyncio.Task] = None
        self._delivery_tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        if self._main_task and not self._main_task.done():
            return
        self._stop.clear()
        self._main_task = asyncio.create_task(self._run(), name="agv-simulator")
        log_event("AGV simulator started", source="SIMULATOR")

    async def stop(self) -> None:
        self._stop.set()
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except (asyncio.CancelledError, Exception):
                pass
        for task in list(self._delivery_tasks):
            task.cancel()
        if self._delivery_tasks:
            await asyncio.gather(*self._delivery_tasks, return_exceptions=True)
        log_event("AGV simulator stopped", source="SIMULATOR")

    async def _run(self) -> None:
        try:
            while not self._stop.is_set():
                try:
                    self._dispatch_pending_orders()
                except Exception as exc:
                    logger.exception("dispatch error")
                    log_event(f"Simulator dispatch error: {exc}", level="ERROR", source="SIMULATOR")
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            return

    def _dispatch_pending_orders(self) -> None:
        db: Session = SessionLocal()
        try:
            free_agvs = (
                db.query(AGVModel)
                .filter(AGVModel.status == "idle")
                .order_by(AGVModel.id.asc())
                .all()
            )
            if not free_agvs:
                return

            pending = (
                db.query(OrderModel)
                .filter(OrderModel.status == OrderStatus.VALIDATED.value)
                .order_by(
                    OrderModel.priority.desc(),
                    OrderModel.order_time.asc(),
                )
                .limit(len(free_agvs))
                .all()
            )

            for agv, order in zip(free_agvs, pending):
                order.status = OrderStatus.ASSIGNED.value
                order.agv = agv.name
                agv.status = "busy"
                agv.current_order_id = order.id
                agv.last_active = datetime.utcnow()
                db.commit()

                log_event(
                    f"Order #{order.id} assigned to {agv.name} (priority={order.priority})",
                    source=agv.name,
                )

                task = asyncio.create_task(
                    self._run_delivery(order.id, agv.id, agv.name, order.to_location),
                    name=f"delivery-{order.id}",
                )
                self._delivery_tasks.add(task)
                task.add_done_callback(self._delivery_tasks.discard)
        finally:
            db.close()

    async def _run_delivery(
        self,
        order_id: int,
        agv_id: int,
        agv_name: str,
        to_location: str,
    ) -> None:
        try:
            await asyncio.sleep(PICKUP_DURATION_SECONDS)
            if self._should_abort_delivery(order_id):
                log_event(
                    f"{agv_name} Order #{order_id} aborted before pickup completed",
                    level="WARN",
                    source=agv_name,
                )
                return
            log_event(
                f"{agv_name} picked up Order #{order_id}",
                source=agv_name,
            )

            travel_time = self._estimate_travel_seconds(to_location)
            log_event(
                f"{agv_name} travelling to {to_location} (ETA {travel_time:.0f}s)",
                source=agv_name,
            )
            await asyncio.sleep(travel_time)

            if self._should_abort_delivery(order_id):
                log_event(
                    f"{agv_name} Order #{order_id} aborted before arrival",
                    level="WARN",
                    source=agv_name,
                )
                return

            self._set_order_status(order_id, OrderStatus.IN_TRANSIT.value, agv_name=agv_name)
            log_event(
                f"{agv_name} arrived at {to_location}, awaiting confirmation",
                source=agv_name,
            )

            outcome = await self._wait_for_confirmation(order_id)
            if outcome == "delivered":
                log_event(
                    f"{agv_name} delivery for Order #{order_id} confirmed",
                    source=agv_name,
                )
            elif outcome == "cancelled":
                log_event(
                    f"{agv_name} delivery for Order #{order_id} stopped (order cancelled)",
                    level="WARN",
                    source=agv_name,
                )
            elif outcome == "missing":
                log_event(
                    f"{agv_name} Order #{order_id} no longer exists",
                    level="ERROR",
                    source=agv_name,
                )
            else:
                self._set_order_status(order_id, OrderStatus.FAILED.value, agv_name=agv_name)
                log_event(
                    f"{agv_name} confirmation timeout for Order #{order_id} — marked failed",
                    level="ERROR",
                    source=agv_name,
                )
                export_snapshot_safe()
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.exception("delivery error for order %s", order_id)
            log_event(
                f"Delivery error for Order #{order_id}: {exc}",
                level="ERROR",
                source=agv_name,
            )
            self._set_order_status(order_id, OrderStatus.FAILED.value, agv_name=agv_name)
            export_snapshot_safe()
        finally:
            self._release_agv(agv_id, agv_name)

    @staticmethod
    def _should_abort_delivery(order_id: int) -> bool:
        db = SessionLocal()
        try:
            order = (
                db.query(OrderModel).filter(OrderModel.id == order_id).first()
            )
            if not order:
                return True
            return order.status in (
                OrderStatus.CANCELLED.value,
                OrderStatus.FAILED.value,
            )
        finally:
            db.close()

    @staticmethod
    def _estimate_travel_seconds(to_location: str) -> float:
        base = TRAVEL_BASE_SECONDS
        zone_map = {"A": 3.0, "B": 5.0, "C": 7.0, "D": 9.0}
        if to_location and "Zone" in to_location:
            tail = to_location.split()[-1].upper()
            return zone_map.get(tail, base)
        return base

    async def _wait_for_confirmation(self, order_id: int) -> ConfirmOutcome:
        deadline = asyncio.get_event_loop().time() + CONFIRMATION_TIMEOUT_SECONDS
        while asyncio.get_event_loop().time() < deadline and not self._stop.is_set():
            await asyncio.sleep(2.0)
            db = SessionLocal()
            try:
                order = (
                    db.query(OrderModel)
                    .filter(OrderModel.id == order_id)
                    .first()
                )
                if not order:
                    return "missing"
                if order.status == OrderStatus.DELIVERED.value:
                    return "delivered"
                if order.status == OrderStatus.CANCELLED.value:
                    return "cancelled"
                if order.status == OrderStatus.FAILED.value:
                    return "cancelled"
            finally:
                db.close()
        return "timeout"

    @staticmethod
    def _set_order_status(order_id: int, new_status: str, agv_name: Optional[str] = None) -> None:
        db = SessionLocal()
        try:
            order = (
                db.query(OrderModel).filter(OrderModel.id == order_id).first()
            )
            if not order:
                return
            order.status = new_status
            if agv_name is not None:
                order.agv = agv_name
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _release_agv(agv_id: int, agv_name: str) -> None:
        db = SessionLocal()
        try:
            agv = db.query(AGVModel).filter(AGVModel.id == agv_id).first()
            if not agv:
                return
            agv.status = "idle"
            agv.current_order_id = None
            agv.last_active = datetime.utcnow()
            db.commit()
        finally:
            db.close()
        log_event(f"{agv_name} idle, ready for next order", source=agv_name)


simulator = AGVSimulator()
