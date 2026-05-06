import sqlite3
from datetime import datetime
import time
import os


def setup_database():
    """Create all tables for the warehouse system"""

    conn = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
            conn.execute('PRAGMA journal_mode=WAL')  # Use WAL mode for better concurrency
            cursor = conn.cursor()

            # Create orders table
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS orders
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               order_name
                               TEXT
                               NOT
                               NULL,
                               timestamp
                               TEXT
                               NOT
                               NULL,
                               order_time
                               TEXT
                               NOT
                               NULL,
                               status
                               TEXT
                               DEFAULT
                               'pending',
                               assigned_agv
                               INTEGER,
                               product_id
                               INTEGER,
                               product_name
                               TEXT,
                               quantity
                               INTEGER
                               DEFAULT
                               1,
                               priority
                               INTEGER
                               DEFAULT
                               1,
                               from_location
                               TEXT
                               DEFAULT
                               'Warehouse',
                               to_location
                               TEXT
                               DEFAULT
                               'Zone A',
                               completed_timestamp
                               TEXT,
                               confirmed_by
                               TEXT
                           )
                           ''')

            # Create products table with all required properties
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS products
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               name
                               TEXT
                               NOT
                               NULL,
                               model
                               TEXT
                               NOT
                               NULL,
                               color
                               TEXT,
                               stock_quantity
                               INTEGER
                               DEFAULT
                               0,
                               price
                               REAL,
                               location
                               TEXT
                               DEFAULT
                               'Warehouse',
                               min_stock_level
                               INTEGER
                               DEFAULT
                               5,
                               description
                               TEXT,
                               weight
                               REAL,
                               dimensions
                               TEXT,
                               created_date
                               TEXT,
                               last_updated
                               TEXT
                           )
                           ''')

            # Create AGVs table
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS agvs
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY,
                               name
                               TEXT
                               NOT
                               NULL,
                               status
                               TEXT
                               DEFAULT
                               'idle',
                               current_order_id
                               INTEGER,
                               last_active
                               TEXT
                           )
                           ''')

            # Create zones table for valid locations
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS valid_zones
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY,
                               zone_name
                               TEXT
                               UNIQUE,
                               zone_type
                               TEXT,
                               is_active
                               INTEGER
                               DEFAULT
                               1
                           )
                           ''')

            # Create system logs table
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS system_logs
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               timestamp
                               TEXT
                               NOT
                               NULL,
                               level
                               TEXT
                               NOT
                               NULL,
                               source
                               TEXT
                               NOT
                               NULL,
                               message
                               TEXT
                               NOT
                               NULL
                           )
                           ''')

            # Insert default AGVs if not exists
            cursor.execute("SELECT COUNT(*) FROM agvs")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO agvs (id, name, status) VALUES (1, 'AGV-1', 'idle')")
                cursor.execute("INSERT INTO agvs (id, name, status) VALUES (2, 'AGV-2', 'idle')")

            # Insert valid zones
            cursor.execute("SELECT COUNT(*) FROM valid_zones")
            if cursor.fetchone()[0] == 0:
                zones = [
                    ('Warehouse', 'source', 1),
                    ('Zone A', 'destination', 1),
                    ('Zone B', 'destination', 1),
                    ('Zone C', 'destination', 1),
                    ('Zone D', 'destination', 1),
                    ('Production Line', 'source', 1)
                ]
                for zone in zones:
                    cursor.execute("INSERT INTO valid_zones (zone_name, zone_type, is_active) VALUES (?, ?, ?)", zone)

            # Insert sample products if none exist
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                sample_products = [
                    ('Laptop', 'XPS 15', 'Silver', 25, 1299.99, 'Warehouse', 5, 'High performance laptop', 1.8,
                     '35x24x2 cm',
                     datetime.now().isoformat(), datetime.now().isoformat()),
                    ('Mouse', 'MX Master 3', 'Black', 100, 89.99, 'Warehouse', 20, 'Wireless ergonomic mouse', 0.2,
                     '12x8x4 cm',
                     datetime.now().isoformat(), datetime.now().isoformat()),
                    ('Keyboard', 'Mechanical', 'RGB', 50, 149.99, 'Warehouse', 10, 'Mechanical gaming keyboard', 1.2,
                     '45x15x4 cm',
                     datetime.now().isoformat(), datetime.now().isoformat()),
                    ('Monitor', '27" 4K', 'Black', 15, 399.99, 'Warehouse', 5, '4K UHD Monitor', 5.5, '62x37x5 cm',
                     datetime.now().isoformat(), datetime.now().isoformat()),
                    ('Desk', 'Standing Desk', 'White', 10, 499.99, 'Zone A', 3, 'Electric standing desk', 25.0,
                     '120x60x70 cm',
                     datetime.now().isoformat(), datetime.now().isoformat())
                ]
                for product in sample_products:
                    cursor.execute('''
                                   INSERT INTO products (name, model, color, stock_quantity, price, location,
                                                         min_stock_level,
                                                         description, weight, dimensions, created_date, last_updated)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', product)

            conn.commit()
            print("✓ Database created successfully with all tables!")
            print("✓ Sample products loaded!")
            print("✓ AGVs initialized!")
            print("✓ Valid zones configured!")
            break

        except sqlite3.OperationalError as e:
            print(f"Database error (attempt {attempt + 1}/{max_retries}): {e}")
            if conn:
                conn.close()
            time.sleep(1)
        except Exception as e:
            print(f"Error creating database: {e}")
            if conn:
                conn.close()
            break
        finally:
            if conn:
                conn.close()


class DatabaseManager:
    """Helper class to manage database operations with retry logic"""

    @staticmethod
    def _execute_with_retry(operation, max_retries=3):
        """Execute database operation with retry logic"""
        for attempt in range(max_retries):
            conn = None
            try:
                conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
                conn.execute('PRAGMA journal_mode=WAL')
                result = operation(conn)
                return result
            except sqlite3.OperationalError as e:
                print(f"Database operation error (attempt {attempt + 1}/{max_retries}): {e}")
                if conn:
                    conn.close()
                time.sleep(1)
            except Exception as e:
                print(f"Unexpected error: {e}")
                if conn:
                    conn.close()
                raise e
            finally:
                if conn:
                    conn.close()
        return None

    @staticmethod
    def get_all_products():
        """Get all products from database"""

        def operation(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY name")
            return cursor.fetchall()

        result = DatabaseManager._execute_with_retry(operation)
        return result if result is not None else []

    @staticmethod
    def get_product_by_id(product_id):
        """Get product by ID"""

        def operation(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            return cursor.fetchone()

        return DatabaseManager._execute_with_retry(operation)

    @staticmethod
    def add_product(name, model, color, stock_quantity, price, location, min_stock_level, description, weight,
                    dimensions):
        """Add new product"""

        def operation(conn):
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute('''
                           INSERT INTO products (name, model, color, stock_quantity, price, location, min_stock_level,
                                                 description, weight, dimensions, created_date, last_updated)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ''', (name, model, color, stock_quantity, price, location, min_stock_level,
                                 description, weight, dimensions, now, now))
            return cursor.lastrowid

        return DatabaseManager._execute_with_retry(operation)

    @staticmethod
    def update_product(product_id, name, model, color, stock_quantity, price, location, min_stock_level, description,
                       weight, dimensions):
        """Update existing product"""

        def operation(conn):
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE products
                           SET name            = ?,
                               model           = ?,
                               color           = ?,
                               stock_quantity  = ?,
                               price           = ?,
                               location        = ?,
                               min_stock_level = ?,
                               description     = ?,
                               weight          = ?,
                               dimensions      = ?,
                               last_updated    = ?
                           WHERE id = ?
                           ''', (name, model, color, stock_quantity, price, location, min_stock_level,
                                 description, weight, dimensions, datetime.now().isoformat(), product_id))
            return True

        return DatabaseManager._execute_with_retry(operation)

    @staticmethod
    def delete_product(product_id):
        """Delete product"""

        def operation(conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            return True

        return DatabaseManager._execute_with_retry(operation)

    @staticmethod
    def update_stock(product_id, quantity_change):
        """Update product stock"""

        def operation(conn):
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE products
                           SET stock_quantity = stock_quantity + ?,
                               last_updated   = ?
                           WHERE id = ?
                           ''', (quantity_change, datetime.now().isoformat(), product_id))
            return True

        return DatabaseManager._execute_with_retry(operation)

    @staticmethod
    def get_valid_zones(zone_type=None):
        """Get valid zones"""

        def operation(conn):
            cursor = conn.cursor()
            if zone_type:
                cursor.execute("SELECT zone_name FROM valid_zones WHERE zone_type = ? AND is_active = 1", (zone_type,))
            else:
                cursor.execute("SELECT zone_name FROM valid_zones WHERE is_active = 1")
            return [row[0] for row in cursor.fetchall()]

        result = DatabaseManager._execute_with_retry(operation)
        return result if result is not None else []


if __name__ == "__main__":
    setup_database()