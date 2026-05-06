import sqlite3
import threading
import time
from datetime import datetime


class VirtualAGV:
    def __init__(self, agv_id, name):
        self.agv_id = agv_id
        self.name = name
        self.current_order_id = None
        self.status = 'idle'  # idle, busy
        self.lock = threading.Lock()

    def log(self, message):
        """Simple logging"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{self.name}] {message}")

    def is_free(self):
        """Check if AGV is free"""
        with self.lock:
            return self.status == 'idle'

    def update_order_status(self, order_id, status):
        """Update order status in database with retry"""
        max_retries = 3
        for attempt in range(max_retries):
            conn = None
            try:
                conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
                conn.execute('PRAGMA journal_mode=WAL')
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

                if status == 'assigned':
                    cursor.execute("UPDATE agvs SET status = 'busy', last_active = ? WHERE id = ?",
                                   (datetime.now().isoformat(), self.agv_id))
                elif status == 'delivering':
                    cursor.execute("UPDATE agvs SET last_active = ? WHERE id = ?",
                                   (datetime.now().isoformat(), self.agv_id))

                conn.commit()
                return True
            except sqlite3.OperationalError as e:
                self.log(f"Database error (attempt {attempt + 1}/{max_retries}): {e}")
                if conn:
                    conn.close()
                time.sleep(1)
            except Exception as e:
                self.log(f"Error: {e}")
                if conn:
                    conn.close()
                return False
            finally:
                if conn:
                    conn.close()
        return False

    def deliver_order(self, order_id, order_name, from_loc, to_loc):
        """Simulate delivery"""
        with self.lock:
            if self.status != 'idle':
                self.log(f"Cannot deliver - AGV is {self.status}")
                return False
            self.status = 'busy'
            self.current_order_id = order_id

        self.log(f"🚚 Started delivery - Order #{order_id}: {order_name} from {from_loc} to {to_loc}")

        # Calculate delivery time based on zone
        zone_times = {'A': 3, 'B': 5, 'C': 7, 'D': 9}
        zone = to_loc.split()[-1] if 'Zone' in to_loc else 'A'
        delivery_time = zone_times.get(zone, 5)

        # Pickup
        time.sleep(2)
        if not self.update_order_status(order_id, 'assigned'):
            self.log(f"Failed to update order status to assigned")
            with self.lock:
                self.status = 'idle'
                self.current_order_id = None
            return False
        self.log(f"📦 Picked up order from {from_loc}")

        # Travel to destination
        self.log(f"🚚 Traveling to {to_loc} (ETA: {delivery_time} seconds)")
        time.sleep(delivery_time)

        # Arrived
        if not self.update_order_status(order_id, 'delivering'):
            self.log(f"Failed to update order status to delivering")
            with self.lock:
                self.status = 'idle'
                self.current_order_id = None
            return False
        self.log(f"📍 Arrived at {to_loc} - Waiting for confirmation")

        # Wait for confirmation (maximum 60 seconds)
        timeout = 60
        start = time.time()
        confirmed = False
        while time.time() - start < timeout:
            conn = None
            try:
                conn = sqlite3.connect('warehouse.db', timeout=30)
                conn.execute('PRAGMA journal_mode=WAL')
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
                result = cursor.fetchone()

                if result and result[0] == 'done':
                    confirmed = True
                    self.log(f"✅ Delivery completed and confirmed!")
                    break
            except Exception as e:
                self.log(f"Error checking status: {e}")
            finally:
                if conn:
                    conn.close()
            time.sleep(2)

        if not confirmed:
            self.log(f"⚠️ Warning: Delivery confirmation timeout for Order #{order_id}")

        # Free the AGV
        with self.lock:
            self.status = 'idle'
            self.current_order_id = None

        # Update AGV status in database
        conn = None
        try:
            conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            cursor.execute("UPDATE agvs SET status = 'idle', current_order_id = NULL WHERE id = ?", (self.agv_id,))
            conn.commit()
        except Exception as e:
            self.log(f"Error freeing AGV in DB: {e}")
        finally:
            if conn:
                conn.close()

        self.log("✅ Ready for next order")
        return True


class WarehouseManagementSystem:
    def __init__(self):
        self.running = True
        self.agvs = {
            1: VirtualAGV(1, "AGV-1"),
            2: VirtualAGV(2, "AGV-2")
        }
        self.processing_lock = threading.Lock()

        print("\n" + "=" * 60)
        print("🤖 WAREHOUSE MANAGEMENT SYSTEM STARTED")
        print("=" * 60)
        print(f"✅ {len(self.agvs)} AGVs initialized and ready")
        print("✅ Monitoring for pending orders...")
        print("=" * 60 + "\n")

    def get_free_agv(self):
        """Get first available AGV (only if truly idle)"""
        for agv_id, agv in self.agvs.items():
            if agv.is_free():
                return agv_id, agv.name
        return None, None

    def assign_order_to_agv(self, order_id, agv_id):
        """Assign order to AGV in database"""
        conn = None
        try:
            conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()

            # Check if order is still pending (prevent duplicate assignment)
            cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
            result = cursor.fetchone()
            if not result or result[0] != 'pending':
                return False

            cursor.execute("UPDATE orders SET assigned_agv = ? WHERE id = ? AND status = 'pending'", (agv_id, order_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error assigning order: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def process_orders(self):
        """Main processing loop - only assigns to free AGVs"""
        while self.running:
            try:
                # First, check which AGVs are free
                free_agvs = []
                for agv_id, agv in self.agvs.items():
                    if agv.is_free():
                        free_agvs.append(agv_id)

                if not free_agvs:
                    # No free AGVs, wait and check again
                    time.sleep(2)
                    continue

                # Get pending orders (limit to number of free AGVs)
                conn = None
                try:
                    conn = sqlite3.connect('warehouse.db', timeout=30)
                    conn.execute('PRAGMA journal_mode=WAL')
                    cursor = conn.cursor()
                    cursor.execute('''
                                   SELECT id, order_name, from_location, to_location, priority
                                   FROM orders
                                   WHERE status = 'pending'
                                   ORDER BY priority DESC, timestamp ASC
                                       LIMIT ?
                                   ''', (len(free_agvs),))
                    pending = cursor.fetchall()
                except Exception as e:
                    print(f"Error reading orders: {e}")
                    pending = []
                finally:
                    if conn:
                        conn.close()

                # Assign each pending order to a free AGV
                for i, order in enumerate(pending):
                    if i < len(free_agvs):
                        agv_id = free_agvs[i]
                        agv = self.agvs[agv_id]
                        order_id = order[0]

                        print(f"\n📋 New Order Detected: #{order_id} - Priority: {order[4]}")
                        print(f"🎯 Assigning to {agv.name} (AGV is free)")

                        # Assign order in database
                        if self.assign_order_to_agv(order_id, agv_id):
                            # Start delivery in a separate thread
                            thread = threading.Thread(
                                target=agv.deliver_order,
                                args=(order_id, order[1], order[2], order[3])
                            )
                            thread.daemon = True
                            thread.start()
                            time.sleep(0.5)  # Small delay between assignments
                        else:
                            print(f"⚠️ Failed to assign order #{order_id} - might have been taken")

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                print(f"❌ Error in processing: {e}")
                time.sleep(5)

    def start(self):
        """Start the system"""
        thread = threading.Thread(target=self.process_orders)
        thread.daemon = True
        thread.start()

        try:
            # Display status every 10 seconds
            while self.running:
                time.sleep(10)
                status = []
                for agv in self.agvs.values():
                    if agv.is_free():
                        status.append(f"{agv.name}: ✅ FREE")
                    else:
                        status.append(f"{agv.name}: 🔴 BUSY (Order #{agv.current_order_id})")
                print(f"\r💡 AGV Status: {' | '.join(status)}", end="", flush=True)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the system"""
        self.running = False
        print("\n\n" + "=" * 60)
        print("🛑 WAREHOUSE MANAGEMENT SYSTEM STOPPED")
        print("=" * 60)


if __name__ == "__main__":
    wms = WarehouseManagementSystem()
    wms.start()