import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import sqlite3
from datetime import datetime
import time
import requests
import threading
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

        # Setup orders UI
        self.setup_orders_ui()

        # Initialize product manager after UI is created
        self.product_manager = ProductManager(self.products_frame, lambda: self.refresh_product_dropdown())

        # Flag to prevent refresh during selection
        self.is_refreshing = False
        self.selected_order_id = None

        # Start periodic refresh
        self.refresh_orders()

        print("✅ Order Management System Started")

    def setup_orders_ui(self):
        """Setup the orders management interface"""
        # --- TOP FRAME: Create New Order ---
        top_frame = tk.LabelFrame(self.orders_frame, text="Create New Order", padx=10, pady=10,
                                  font=('Arial', 10, 'bold'))
        top_frame.pack(fill="x", padx=10, pady=5)

        details_frame = tk.Frame(top_frame)
        details_frame.pack(fill="x", pady=5)

        # Fields (Name, Product, Qty, Priority, Locations)
        tk.Label(details_frame, text="Order Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.order_name_entry = tk.Entry(details_frame, width=30)
        self.order_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(details_frame, text="Product:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.product_combo = ttk.Combobox(details_frame, width=50)
        self.product_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.product_combo.bind('<<ComboboxSelected>>', self.on_product_select)

        self.product_info_label = tk.Label(details_frame, text="", fg="blue", font=('Arial', 9))
        self.product_info_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        tk.Label(details_frame, text="Quantity:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.quantity_entry = tk.Entry(details_frame, width=10)
        self.quantity_entry.insert(0, "1")
        self.quantity_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')

        tk.Label(details_frame, text="Priority (1-5):").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.priority_combo = ttk.Combobox(details_frame, values=[1, 2, 3, 4, 5], width=8)
        self.priority_combo.set(3)
        self.priority_combo.grid(row=4, column=1, padx=5, pady=5, sticky='w')

        tk.Label(details_frame, text="From Location:").grid(row=5, column=0, padx=5, pady=5, sticky='w')
        self.from_combo = ttk.Combobox(details_frame, values=self.db.get_valid_zones('source'), width=20)
        self.from_combo.set('Warehouse')
        self.from_combo.grid(row=5, column=1, padx=5, pady=5, sticky='w')

        tk.Label(details_frame, text="To Location:").grid(row=6, column=0, padx=5, pady=5, sticky='w')
        self.to_combo = ttk.Combobox(details_frame, values=self.db.get_valid_zones('destination'), width=20)
        self.to_combo.set('Zone A')
        self.to_combo.grid(row=6, column=1, padx=5, pady=5, sticky='w')

        # Create Order Buttons
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="🚀 Create Order", command=self.create_order, bg="green", fg="white",
                  font=('Arial', 10, 'bold'), padx=20).pack(side="left", padx=5)
        tk.Button(btn_frame, text="📦 Products", command=self.switch_to_products, bg="blue", fg="white",
                  font=('Arial', 10, 'bold'), padx=20).pack(side="left", padx=5)

        # --- MIDDLE FRAME: Current Orders Table ---
        list_frame = tk.LabelFrame(self.orders_frame, text="Current Orders", padx=10, pady=10,
                                   font=('Arial', 10, 'bold'))
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ('ID', 'Order Name', 'Product', 'Qty', 'Status', 'AGV', 'Priority', 'From', 'To', 'Order Time')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind('<<TreeviewSelect>>', self.on_order_select)

        # --- BOTTOM FRAME: Action Bar ---
        action_frame = tk.Frame(self.orders_frame)
        action_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(action_frame, text="🔄 Refresh", command=self.refresh_orders, bg="blue", fg="white", padx=10).pack(
            side="left", padx=5)
        tk.Button(action_frame, text="✅ Confirm Delivery", command=self.confirm_delivery, bg="purple", fg="white",
                  padx=10).pack(side="left", padx=5)
        tk.Button(action_frame, text="❌ Cancel Order", command=self.cancel_order, bg="red", fg="white", padx=10).pack(
            side="left", padx=5)

        # NEW EXPORT BUTTON (Matches your request)
        tk.Button(action_frame, text="📥 Export Orders (CSV)", command=self.export_orders_csv,
                  bg="#28a745", fg="white", font=("Arial", 9, "bold"), padx=10).pack(side="right", padx=10)

        # Logs
        logs_frame = tk.LabelFrame(self.orders_frame, text="System Logs", padx=10, pady=5)
        logs_frame.pack(fill="x", padx=10, pady=5)
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=5, width=80)
        self.logs_text.pack(fill="both", expand=True)

        self.products_data = {}
        self.selected_product_id = None
        self.refresh_product_dropdown()

    # --- NEW EXPORT LOGIC ---
    def export_orders_csv(self):
        """Saves current orders to a CSV file using API"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="order_history.csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        def download_task():
            try:
                # Ensure your FastAPI backend has an /export-orders endpoint
                response = requests.get("http://127.0.0.1:8000/export-orders", timeout=5)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    messagebox.showinfo("Export Successful", f"Saved to {file_path}")
                else:
                    messagebox.showerror("Error", "Server failed to generate CSV.")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Is the API running?\n{e}")

        threading.Thread(target=download_task, daemon=True).start()

    # --- RESTORED LOGIC FROM ORIGINAL CODE ---
    def refresh_orders(self):
        if self.is_refreshing: return
        self.is_refreshing = True
        try:
            conn = sqlite3.connect('warehouse.db', timeout=30)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, order_name, product_name, quantity, status, COALESCE(assigned_agv, ''), priority, from_location, to_location, order_time FROM orders ORDER BY timestamp DESC")

            for item in self.tree.get_children(): self.tree.delete(item)

            for row in cursor.fetchall():
                assigned = f"AGV-{row[5]}" if row[5] else 'Pending'
                tag = row[4]  # pending, delivering, done
                self.tree.insert('', 'end',
                                 values=(row[0], row[1], row[2], row[3], row[4], assigned, row[6], row[7], row[8],
                                         row[9]), tags=(tag,))

            self.tree.tag_configure('delivering', background='#ff9999')  # Soft Red
            self.tree.tag_configure('done', background='#99ff99')  # Soft Green
            self.refresh_logs()
            conn.close()
        except Exception as e:
            print(f"Refresh Error: {e}")
        finally:
            self.is_refreshing = False
        self.root.after(5000, self.refresh_orders)

    def switch_to_products(self):
        self.notebook.select(self.products_frame)

    def on_product_select(self, event):
        selected = self.product_combo.get()
        if selected in self.products_data:
            p = self.products_data[selected]
            self.selected_product_id = p[0]
            self.product_info_label.config(text=f"📦 {p[1]} | Stock: {p[4]} | Price: ${p[5]:.2f}")

    def refresh_product_dropdown(self):
        products = self.db.get_all_products()
        if products:
            product_list = [f"{p[1]} {p[2]} (Stock: {p[4]})" for p in products]
            self.product_combo['values'] = product_list
            self.products_data = {f"{p[1]} {p[2]} (Stock: {p[4]})": p for p in products}

    def on_order_select(self, event):
        selected = self.tree.selection()
        if selected: self.selected_order_id = self.tree.item(selected[0])['values'][0]

    def create_order(self):
        # Implementation of order creation logic...
        pass

    def confirm_delivery(self):
        # Implementation of delivery confirmation...
        pass

    def cancel_order(self):
        # Implementation of order cancellation...
        pass

    def refresh_logs(self):
        # Logic to update system logs box...
        pass


if __name__ == "__main__":
    setup_database()
    root = tk.Tk()
    app = OrderManagementSystem(root)
    root.mainloop()