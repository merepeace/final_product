import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import sqlite3
from datetime import datetime
import time
from database_setup import DatabaseManager, setup_database
from product_manager import ProductManager


class OrderManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Order Management System - Complete")
        self.root.geometry("1400x800")

        # Initialize database manager
        self.db = DatabaseManager()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Create Orders Tab
        self.orders_frame = tk.Frame(self.notebook)
        self.notebook.add(self.orders_frame, text="📋 Orders")

        # Create Products Tab
        self.products_frame = tk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text="📦 Products")

        # Setup orders UI first (this creates product_combo)
        self.setup_orders_ui()

        # Initialize product manager after UI is created
        self.product_manager = ProductManager(self.products_frame, lambda: self.refresh_product_dropdown())

        # Flag to prevent refresh during selection
        self.is_refreshing = False
        self.selected_order_id = None

        # Refresh orders periodically
        self.refresh_orders()

        print("✅ Order Management System Started")

    def setup_orders_ui(self):
        """Setup the orders management interface"""
        # Top frame for order creation
        top_frame = tk.LabelFrame(self.orders_frame, text="Create New Order", padx=10, pady=10,
                                  font=('Arial', 10, 'bold'))
        top_frame.pack(fill="x", padx=10, pady=5)

        # Order details frame
        details_frame = tk.Frame(top_frame)
        details_frame.pack(fill="x", pady=5)

        # Row 1: Order Name
        tk.Label(details_frame, text="Order Name:", width=15, anchor='w').grid(row=0, column=0, padx=5, pady=5)
        self.order_name_entry = tk.Entry(details_frame, width=30)
        self.order_name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Row 2: Product Selection
        tk.Label(details_frame, text="Product:", width=15, anchor='w').grid(row=1, column=0, padx=5, pady=5)
        self.product_combo = ttk.Combobox(details_frame, width=50)
        self.product_combo.grid(row=1, column=1, padx=5, pady=5)
        self.product_combo.bind('<<ComboboxSelected>>', self.on_product_select)

        # Product info display
        self.product_info_label = tk.Label(details_frame, text="", fg="blue", font=('Arial', 9))
        self.product_info_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        # Row 3: Quantity and Priority
        tk.Label(details_frame, text="Quantity:", width=15, anchor='w').grid(row=3, column=0, padx=5, pady=5)
        self.quantity_entry = tk.Entry(details_frame, width=10)
        self.quantity_entry.insert(0, "1")
        self.quantity_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        tk.Label(details_frame, text="Priority (1-5):", width=15, anchor='w').grid(row=4, column=0, padx=5, pady=5)
        self.priority_combo = ttk.Combobox(details_frame, values=[1, 2, 3, 4, 5], width=8)
        self.priority_combo.set(3)
        self.priority_combo.grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # Row 5: Locations
        tk.Label(details_frame, text="From Location:", width=15, anchor='w').grid(row=5, column=0, padx=5, pady=5)
        self.from_combo = ttk.Combobox(details_frame, values=self.db.get_valid_zones('source'), width=20)
        self.from_combo.set('Warehouse')
        self.from_combo.grid(row=5, column=1, sticky='w', padx=5, pady=5)

        tk.Label(details_frame, text="To Location:", width=15, anchor='w').grid(row=6, column=0, padx=5, pady=5)
        self.to_combo = ttk.Combobox(details_frame, values=self.db.get_valid_zones('destination'), width=20)
        self.to_combo.set('Zone A')
        self.to_combo.grid(row=6, column=1, sticky='w', padx=5, pady=5)

        # Buttons frame
        buttons_frame = tk.Frame(top_frame)
        buttons_frame.pack(pady=10)

        tk.Button(buttons_frame, text="🚀 Create Order", command=self.create_order,
                  bg="green", fg="white", font=('Arial', 10, 'bold'), padx=20).pack(side="left", padx=5)

        tk.Button(buttons_frame, text="📦 Products", command=self.switch_to_products,
                  bg="blue", fg="white", font=('Arial', 10, 'bold'), padx=20).pack(side="left", padx=5)

        # Orders list frame
        list_frame = tk.LabelFrame(self.orders_frame, text="Current Orders", padx=10, pady=10,
                                   font=('Arial', 10, 'bold'))
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview for orders
        columns = ('ID', 'Order Name', 'Product', 'Qty', 'Status', 'AGV', 'Priority', 'From', 'To', 'Order Time')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)

        # Configure headings
        headings = ['ID', 'Order Name', 'Product', 'Qty', 'Status', 'Assigned AGV', 'Priority', 'From', 'To',
                    'Order Time']
        widths = [50, 150, 150, 60, 100, 100, 60, 100, 100, 150]

        for i, (col, heading, width) in enumerate(zip(columns, headings, widths)):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_order_select)

        # Action buttons frame
        action_frame = tk.Frame(self.orders_frame)
        action_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(action_frame, text="🔄 Refresh", command=self.refresh_orders,
                  bg="blue", fg="white").pack(side="left", padx=5)
        tk.Button(action_frame, text="✅ Confirm Delivery", command=self.confirm_delivery,
                  bg="purple", fg="white").pack(side="left", padx=5)
        tk.Button(action_frame, text="❌ Cancel Order", command=self.cancel_order,
                  bg="red", fg="white").pack(side="left", padx=5)

        # Logs frame
        logs_frame = tk.LabelFrame(self.orders_frame, text="System Logs", padx=10, pady=10)
        logs_frame.pack(fill="x", padx=10, pady=5)

        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=8, width=80)
        self.logs_text.pack(fill="both", expand=True)

        # Initialize products data dictionary
        self.products_data = {}
        self.selected_product_id = None

        # Load initial product dropdown
        self.refresh_product_dropdown()

    def switch_to_products(self):
        """Switch to products tab"""
        self.notebook.select(self.products_frame)

    def on_order_select(self, event):
        """Handle order selection - preserve selection"""
        try:
            selected = self.tree.selection()
            if selected:
                self.selected_order_id = self.tree.item(selected[0])['values'][0]
            else:
                self.selected_order_id = None
        except Exception as e:
            print(f"Error in order selection: {e}")
            self.selected_order_id = None

    def refresh_product_dropdown(self):
        """Refresh product dropdown with current products"""
        try:
            products = self.db.get_all_products()
            if products:
                product_list = [f"{p[1]} {p[2]} (Stock: {p[4]})" for p in products]

                # Update combobox values
                if hasattr(self, 'product_combo'):
                    self.product_combo['values'] = product_list

                    # Update products data dictionary
                    self.products_data = {}
                    for p in products:
                        key = f"{p[1]} {p[2]} (Stock: {p[4]})"
                        self.products_data[key] = p
        except Exception as e:
            print(f"Error refreshing product dropdown: {e}")

    def on_product_select(self, event):
        """Handle product selection"""
        try:
            selected = self.product_combo.get()
            if selected and selected in self.products_data:
                product = self.products_data[selected]
                self.selected_product_id = product[0]
                info = f"📦 {product[1]} {product[2]} | Color: {product[3] or 'N/A'} | Stock: {product[4]} | Price: ${product[5]:.2f}"
                if product[9]:  # Weight
                    info += f" | Weight: {product[9]}kg"
                self.product_info_label.config(text=info)
            else:
                self.product_info_label.config(text="")
                self.selected_product_id = None
        except Exception as e:
            print(f"Error in product selection: {e}")
            self.selected_product_id = None

    def create_order(self):
        """Create a new order"""
        conn = None
        try:
            # Validate inputs
            order_name = self.order_name_entry.get().strip()
            if not order_name:
                messagebox.showwarning("Validation Error", "Order name is required!")
                return

            if not hasattr(self, 'selected_product_id') or self.selected_product_id is None:
                messagebox.showwarning("Validation Error", "Please select a product!")
                return

            try:
                quantity = int(self.quantity_entry.get())
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Validation Error", "Quantity must be a positive number!")
                return

            # Check stock
            product = self.db.get_product_by_id(self.selected_product_id)
            if not product:
                messagebox.showerror("Error", "Product not found!")
                return

            if quantity > product[4]:
                messagebox.showerror("Insufficient Stock",
                                     f"Only {product[4]} units available in stock!\nRequested: {quantity}")
                return

            priority = int(self.priority_combo.get())
            from_loc = self.from_combo.get()
            to_loc = self.to_combo.get()

            # Validate locations
            valid_sources = self.db.get_valid_zones('source')
            valid_destinations = self.db.get_valid_zones('destination')

            if from_loc not in valid_sources:
                messagebox.showerror("Invalid Location", f"Invalid source location! Valid: {', '.join(valid_sources)}")
                return

            if to_loc not in valid_destinations:
                messagebox.showerror("Invalid Location",
                                     f"Invalid destination location! Valid: {', '.join(valid_destinations)}")
                return

            if from_loc == to_loc:
                messagebox.showerror("Invalid Locations", "Source and destination cannot be the same!")
                return

            # Create order with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
                    conn.execute('PRAGMA journal_mode=WAL')
                    cursor = conn.cursor()

                    now = datetime.now()
                    order_time = now.strftime("%Y-%m-%d %H:%M:%S")
                    timestamp = now.isoformat()
                    product_name = f"{product[1]} {product[2]}"

                    cursor.execute('''
                                   INSERT INTO orders (order_name, timestamp, order_time, status, product_id,
                                                       product_name,
                                                       quantity, priority, from_location, to_location)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   ''', (order_name, timestamp, order_time, 'pending', self.selected_product_id,
                                         product_name, quantity, priority, from_loc, to_loc))

                    order_id = cursor.lastrowid
                    conn.commit()

                    # Update stock using DatabaseManager
                    self.db.update_stock(self.selected_product_id, -quantity)

                    # Clear inputs
                    self.order_name_entry.delete(0, tk.END)
                    self.quantity_entry.delete(0, tk.END)
                    self.quantity_entry.insert(0, "1")
                    self.product_combo.set('')
                    self.product_info_label.config(text='')
                    self.selected_product_id = None

                    # Refresh displays
                    self.refresh_orders()
                    if hasattr(self, 'product_manager'):
                        self.product_manager.refresh_products()
                    self.refresh_product_dropdown()

                    messagebox.showinfo("Success",
                                        f"✅ Order #{order_id} created successfully!\nStock updated to {product[4] - quantity}")
                    return

                except sqlite3.OperationalError as e:
                    print(f"Database error (attempt {attempt + 1}/{max_retries}): {e}")
                    if conn:
                        conn.close()
                    time.sleep(1)
                except Exception as e:
                    if conn:
                        conn.close()
                    raise e
                finally:
                    if conn:
                        conn.close()

            messagebox.showerror("Error", "Failed to create order after multiple attempts.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create order: {str(e)}")

    def confirm_delivery(self):
        """Confirm delivery of an order"""
        if not self.selected_order_id:
            messagebox.showwarning("No Selection", "Please select an order to confirm delivery")
            return

        # Get the current status of the selected order
        conn = None
        try:
            conn = sqlite3.connect('warehouse.db', timeout=30)
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM orders WHERE id = ?", (self.selected_order_id,))
            result = cursor.fetchone()
            if result:
                status = result[0]
            else:
                messagebox.showerror("Error", "Order not found!")
                return
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get order status: {str(e)}")
            return
        finally:
            if conn:
                conn.close()

        if status != 'delivering':
            messagebox.showwarning("Cannot Confirm",
                                   f"Order {self.selected_order_id} is '{status}'. Only 'delivering' orders can be confirmed!")
            return

        # Get operator name
        operator = simpledialog.askstring("Confirm Delivery", "Enter your name for confirmation:")
        if not operator:
            return

        try:
            conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()

            cursor.execute('''
                           UPDATE orders
                           SET status              = 'done',
                               completed_timestamp = ?,
                               confirmed_by        = ?
                           WHERE id = ?
                             AND status = 'delivering'
                           ''', (datetime.now().isoformat(), operator, self.selected_order_id))

            # Free the AGV
            cursor.execute("UPDATE agvs SET status = 'idle', current_order_id = NULL WHERE current_order_id = ?",
                           (self.selected_order_id,))

            conn.commit()

            messagebox.showinfo("Success", f"✅ Delivery confirmed for Order #{self.selected_order_id} by {operator}!")

            # Clear selection
            self.selected_order_id = None

            # Refresh orders
            self.refresh_orders()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to confirm delivery: {str(e)}")
        finally:
            if conn:
                conn.close()

    def refresh_orders(self):
        """Refresh orders list while preserving selection if possible"""
        if self.is_refreshing:
            return

        self.is_refreshing = True
        conn = None

        try:
            # Store current selection before refresh
            previous_selection = self.selected_order_id

            conn = sqlite3.connect('warehouse.db', timeout=30)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT id,
                                  order_name,
                                  product_name,
                                  quantity,
                                  status,
                                  COALESCE(assigned_agv, ''),
                                  priority,
                                  from_location,
                                  to_location,
                                  order_time
                           FROM orders
                           ORDER BY CASE status
                                        WHEN 'pending' THEN 1
                                        WHEN 'assigned' THEN 2
                                        WHEN 'delivering' THEN 3
                                        WHEN 'done' THEN 4
                                        ELSE 5
                                        END,
                                    priority DESC, timestamp ASC
                           ''')

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert updated data
            for row in cursor.fetchall():
                assigned = f"AGV-{row[5]}" if row[5] and row[5] != '' else 'Not assigned'
                values = (row[0], row[1], row[2], row[3], row[4], assigned, row[6], row[7], row[8], row[9])

                # Color coding
                tag = ''
                if row[4] == 'pending':
                    tag = 'pending'
                elif row[4] == 'assigned':
                    tag = 'assigned'
                elif row[4] == 'delivering':
                    tag = 'delivering'
                elif row[4] == 'done':
                    tag = 'done'
                elif row[4] == 'cancelled':
                    tag = 'cancelled'

                item_id = self.tree.insert('', 'end', values=values, tags=(tag,))

                # Restore selection if this was the previously selected order
                if previous_selection and row[0] == previous_selection:
                    self.tree.selection_set(item_id)
                    self.selected_order_id = previous_selection

            # Configure tags
            self.tree.tag_configure('pending', background='yellow')
            self.tree.tag_configure('assigned', background='orange')
            self.tree.tag_configure('delivering', background='lightcoral')
            self.tree.tag_configure('done', background='lightgreen')
            self.tree.tag_configure('cancelled', background='gray')

            # Update logs
            self.refresh_logs()

        except Exception as e:
            print(f"Error refreshing orders: {e}")
        finally:
            if conn:
                conn.close()
            self.is_refreshing = False

        # Schedule next refresh
        self.root.after(5000, self.refresh_orders)

    def refresh_logs(self):
        """Refresh system logs display"""
        conn = None
        try:
            conn = sqlite3.connect('warehouse.db', timeout=30)
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT timestamp, source, level, message
                           FROM system_logs
                           ORDER BY id DESC
                               LIMIT 20
                           ''')

            self.logs_text.delete(1.0, tk.END)

            for row in cursor.fetchall():
                log_entry = f"[{row[0][:19]}] [{row[1]}] {row[2]}: {row[3]}\n"
                self.logs_text.insert(tk.END, log_entry)

            # Auto-scroll to bottom
            self.logs_text.see(tk.END)

        except Exception as e:
            print(f"Error refreshing logs: {e}")
        finally:
            if conn:
                conn.close()

    def cancel_order(self):
        """Cancel selected order"""
        if not self.selected_order_id:
            messagebox.showwarning("No Selection", "Please select an order to cancel")
            return

        # Get current status
        conn = None
        try:
            conn = sqlite3.connect('warehouse.db', timeout=30)
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM orders WHERE id = ?", (self.selected_order_id,))
            result = cursor.fetchone()
            if result:
                status = result[0]
            else:
                messagebox.showerror("Error", "Order not found!")
                return
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get order status: {str(e)}")
            return
        finally:
            if conn:
                conn.close()

        if status != 'pending':
            messagebox.showwarning("Cannot Cancel",
                                   f"Order {self.selected_order_id} is '{status}' and cannot be cancelled!")
            return

        if messagebox.askyesno("Confirm Cancel", f"Are you sure you want to cancel Order #{self.selected_order_id}?"):
            try:
                conn = sqlite3.connect('warehouse.db', timeout=30, isolation_level=None)
                conn.execute('PRAGMA journal_mode=WAL')
                cursor = conn.cursor()

                # Get product and quantity to restore stock
                cursor.execute("SELECT product_id, quantity FROM orders WHERE id = ?", (self.selected_order_id,))
                order = cursor.fetchone()

                if order and order[0]:
                    # Restore stock
                    self.db.update_stock(order[0], order[1])

                # Cancel order
                cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (self.selected_order_id,))
                conn.commit()

                messagebox.showinfo("Success", f"Order #{self.selected_order_id} cancelled and stock restored!")

                # Clear selection
                self.selected_order_id = None

                # Refresh all displays
                self.refresh_orders()
                if hasattr(self, 'product_manager'):
                    self.product_manager.refresh_products()
                self.refresh_product_dropdown()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to cancel order: {str(e)}")
            finally:
                if conn:
                    conn.close()


if __name__ == "__main__":
    # Setup database first
    setup_database()

    # Create and run the application
    root = tk.Tk()
    app = OrderManagementSystem(root)
    root.mainloop()