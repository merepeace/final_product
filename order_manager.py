import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from datetime import datetime
import requests
from api_client import get_zones, get_products

from product_manager import ProductManager

BASE_URL = "http://127.0.0.1:8000"


class OrderManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Order Management System - Complete")
        self.root.geometry("1400x800")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.orders_frame = tk.Frame(self.notebook)
        self.notebook.add(self.orders_frame, text="📋 Orders")

        self.products_frame = tk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text="📦 Products")

        self.setup_orders_ui()

        self.product_manager = ProductManager(self.products_frame, lambda: self.refresh_product_dropdown())

        self.is_refreshing = False
        self.selected_order_id = None

        self.refresh_orders()

        print("✅ Order Management System Started")

    def setup_orders_ui(self):
        """Setup the orders management interface"""
        top_frame = tk.LabelFrame(self.orders_frame, text="Create New Order", padx=10, pady=10,
                                  font=('Arial', 10, 'bold'))
        top_frame.pack(fill="x", padx=10, pady=5)

        details_frame = tk.Frame(top_frame)
        details_frame.pack(fill="x", pady=5)

        # Row 0: Order Name
        tk.Label(details_frame, text="Order ID:", width=15, anchor='w').grid(row=0, column=0, padx=5, pady=5)
        self.order_name_entry = tk.Entry(details_frame, width=30)
        self.order_name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Row 1: Product Selection
        tk.Label(details_frame, text="Product:", width=15, anchor='w').grid(row=1, column=0, padx=5, pady=5)
        self.product_combo = ttk.Combobox(details_frame, width=50)
        self.product_combo.grid(row=1, column=1, padx=5, pady=5)
        self.product_combo.bind('<<ComboboxSelected>>', self.on_product_select)

        self.product_info_label = tk.Label(details_frame, text="", fg="blue", font=('Arial', 9))
        self.product_info_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        # Row 3: Quantity
        tk.Label(details_frame, text="values:", width=25, anchor='w').grid(row=5, column=0, padx=7, pady=9)
        self.quantity_entry = tk.Entry(details_frame, width=10)
        self.quantity_entry.insert(0, "1")
        self.quantity_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # Row 4: Priority
        tk.Label(details_frame, text="Priority (1-5):", width=15, anchor='w').grid(row=4, column=0, padx=5, pady=5)
        self.priority_combo = ttk.Combobox(details_frame, values=[1, 2, 3, 4, 5], width=8)
        self.priority_combo.set(3)
        self.priority_combo.grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # Row 5-6: Locations — fetch zones once
        zone_names = [z["name"] for z in get_zones()]

        tk.Label(details_frame, text="From Location:", width=15, anchor='w').grid(row=5, column=0, padx=5, pady=5)
        self.from_combo = ttk.Combobox(details_frame, values=zone_names, width=20)
        if zone_names:
            self.from_combo.set(zone_names[0])
        self.from_combo.grid(row=5, column=1, sticky='w', padx=5, pady=5)

        tk.Label(details_frame, text="To Location:", width=15, anchor='w').grid(row=6, column=0, padx=5, pady=5)
        self.to_combo = ttk.Combobox(details_frame, values=zone_names, width=20)
        if zone_names:
            self.to_combo.set(zone_names[0])
        self.to_combo.grid(row=6, column=1, sticky='w', padx=5, pady=5)

        # Buttons
        buttons_frame = tk.Frame(top_frame)
        buttons_frame.pack(pady=10)

        tk.Button(buttons_frame, text="🚀 Create Order", command=self.create_order,
                  bg="green", fg="white", font=('Arial', 10, 'bold'), padx=20).pack(side="left", padx=5)
        tk.Button(buttons_frame, text="📦 Products", command=self.switch_to_products,
                  bg="blue", fg="white", font=('Arial', 10, 'bold'), padx=20).pack(side="left", padx=5)

        # Orders list
        list_frame = tk.LabelFrame(self.orders_frame, text="Current Orders", padx=10, pady=10,
                                   font=('Arial', 10, 'bold'))
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ('ID', 'Order ID', 'Product', 'Qty', 'Status', 'AGV', 'Priority', 'From', 'To', 'Order Time')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)

        headings = ['ID', 'Order ID', 'Product', 'Qty', 'Status', 'Assigned AGV', 'Priority', 'From', 'To', 'Order Time']
        widths   = [50,   150,          150,       60,    100,      100,            60,         100,    100,  150]

        for col, heading, width in zip(columns, headings, widths):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind('<<TreeviewSelect>>', self.on_order_select)

        # Action buttons
        action_frame = tk.Frame(self.orders_frame)
        action_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(action_frame, text="🔄 Refresh", command=self.refresh_orders,
                  bg="blue", fg="white").pack(side="left", padx=5)
        tk.Button(action_frame, text="✅ Confirm Delivery", command=self.confirm_delivery,
                  bg="purple", fg="white").pack(side="left", padx=5)
        tk.Button(action_frame, text="❌ Cancel Order", command=self.cancel_order,
                  bg="red", fg="white").pack(side="left", padx=5)

        # Logs
        logs_frame = tk.LabelFrame(self.orders_frame, text="System Logs", padx=10, pady=10)
        logs_frame.pack(fill="x", padx=10, pady=5)

        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=8, width=80)
        self.logs_text.pack(fill="both", expand=True)

        # Products data cache
        self.products_data = {}
        self.selected_product_id = None

        self.refresh_product_dropdown()

    def switch_to_products(self):
        self.notebook.select(self.products_frame)

    def on_order_select(self, event):
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
        """Fetch products from API and populate the dropdown"""
        try:
            products = get_products()
            if not products:
                return

            # Build name → product dict (was recursively calling itself before — fixed)
            self.products_data = {p["productname"]: p for p in products}

            self.product_combo["values"] = list(self.products_data.keys())

        except Exception as e:
            print(f"Product refresh error: {e}")

    def on_product_select(self, event):
        try:
            selected = self.product_combo.get()
            product = self.products_data.get(selected)

            if product:
                self.selected_product_id = product["id"]
                stock = int(product.get("stock_quantity", 0))
                price = product.get("price_usd", 0)
                info = (f"📦 {product['productname']} | Stock: {stock} | Price: ${price}")
                self.product_info_label.config(text=info)
            else:
                self.selected_product_id = None
                self.product_info_label.config(text="")

        except Exception as e:
            print(f"Product select error: {e}")

    def create_order(self):
        """Create order via API"""
        try:
            order_name = self.order_name_entry.get().strip()
            if not order_name:
                messagebox.showwarning("Validation Error", "Order ID is required!")
                return

            if not self.selected_product_id:
                messagebox.showwarning("Validation Error", "Please select a product!")
                return

            try:
                quantity = int(self.quantity_entry.get())
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Validation Error", "Quantity must be a positive integer!")
                return

            from_loc = self.from_combo.get()
            to_loc   = self.to_combo.get()

            zone_names = [z["name"] for z in get_zones()]

            if from_loc not in zone_names or to_loc not in zone_names:
                messagebox.showerror("Invalid Location", "Invalid zone selected!")
                return

            if from_loc == to_loc:
                messagebox.showerror("Invalid Locations", "From and To locations cannot be the same!")
                return

            # Find product in cache
            product = next((p for p in self.products_data.values() if p["id"] == self.selected_product_id), None)
            if not product:
                messagebox.showerror("Error", "Product not found!")
                return

            stock = int(product.get("stock_quantity", 0))
            if quantity > stock:
                messagebox.showerror("Insufficient Stock", f"Only {stock} units available!")
                return

            payload = {
                "order_name":    order_name,
                "product":       product["productname"],
                "qty":           quantity,
                "status":        "Pending",
                "agv":           "AGV-01",
                "priority":      int(self.priority_combo.get()),
                "from_location": from_loc,
                "to_location":   to_loc,
            }

            response = requests.post(f"{BASE_URL}/orders", json=payload)

            if response.status_code in (200, 201):
                self.clear_form()
                self.refresh_orders()
                messagebox.showinfo("Success", "Order created successfully!")
            else:
                messagebox.showerror("API Error", response.text)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_form(self):
        """Reset the create-order form"""
        self.order_name_entry.delete(0, tk.END)
        self.product_combo.set("")
        self.product_info_label.config(text="")
        self.quantity_entry.delete(0, tk.END)
        self.quantity_entry.insert(0, "1")
        self.priority_combo.set(3)
        self.selected_product_id = None

    def confirm_delivery(self):
        """Confirm delivery of selected order via API"""
        if not self.selected_order_id:
            messagebox.showwarning("No Selection", "Please select an order to confirm delivery.")
            return

        # Fetch current order status from API
        try:
            response = requests.get(f"{BASE_URL}/orders/{self.selected_order_id}")
            response.raise_for_status()
            order = response.json()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch order: {e}")
            return

        if order.get("status", "").lower() != "delivering":
            messagebox.showwarning(
                "Cannot Confirm",
                f"Order {self.selected_order_id} is '{order.get('status')}'. "
                "Only 'delivering' orders can be confirmed."
            )
            return

        operator = simpledialog.askstring("Confirm Delivery", "Enter your name for confirmation:")
        if not operator:
            return

        try:
            payload = {
                "confirmed_by":         operator,
                "completed_timestamp":  datetime.now().isoformat(),
            }
            response = requests.post(
                f"{BASE_URL}/orders/{self.selected_order_id}/confirm",
                json=payload
            )

            if response.status_code == 200:
                messagebox.showinfo(
                    "Success",
                    f"✅ Delivery confirmed for Order #{self.selected_order_id} by {operator}!"
                )
                self.selected_order_id = None
                self.refresh_orders()
            else:
                messagebox.showerror("API Error", response.text)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to confirm delivery: {e}")

    def cancel_order(self):
        """Cancel selected order via API"""
        if not self.selected_order_id:
            messagebox.showwarning("No Selection", "Please select an order to cancel.")
            return

        if not messagebox.askyesno("Confirm", "Are you sure you want to cancel this order?"):
            return

        try:
            response = requests.post(
                f"{BASE_URL}/orders/{self.selected_order_id}/cancel",
                json={}
            )

            if response.status_code == 200:
                self.selected_order_id = None
                self.refresh_orders()
                messagebox.showinfo("Success", "Order cancelled successfully.")
            else:
                messagebox.showerror("API Error", response.text)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_orders(self):
        """Fetch orders from API and repopulate the treeview"""
        if self.is_refreshing:
            return

        self.is_refreshing = True

        try:
            previous_selection = self.selected_order_id

            response = requests.get(f"{BASE_URL}/orders")
            response.raise_for_status()
            orders = response.json()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for order in orders:
                assigned = order["agv"] if order.get("agv") else "Not assigned"

                values = (
                    order["id"],
                    order["order_name"],
                    order["product"],
                    order["qty"],
                    order["status"],
                    assigned,
                    order["priority"],
                    order["from_location"],
                    order["to_location"],
                    order["order_time"],
                )

                status = order["status"].lower()
                tag = status if status in ("pending", "assigned", "delivering", "done", "cancelled") else ""

                item_id = self.tree.insert("", "end", values=values, tags=(tag,))

                if previous_selection and order["id"] == previous_selection:
                    self.tree.selection_set(item_id)
                    self.selected_order_id = previous_selection

            self.tree.tag_configure("pending",    background="yellow")
            self.tree.tag_configure("assigned",   background="orange")
            self.tree.tag_configure("delivering", background="lightcoral")
            self.tree.tag_configure("done",       background="lightgreen")
            self.tree.tag_configure("cancelled",  background="gray")

            self.refresh_logs()

        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
        except Exception as e:
            print(f"Error refreshing orders: {e}")
        finally:
            self.is_refreshing = False

        self.root.after(5000, self.refresh_orders)

    def refresh_logs(self):
        """Fetch system logs from API and display them"""
        try:
            response = requests.get(f"{BASE_URL}/logs", params={"limit": 20})
            response.raise_for_status()
            logs = response.json()

            self.logs_text.delete(1.0, tk.END)

            for log in logs:
                # Accept both flat fields and nested dicts from the API
                timestamp = log.get("timestamp", "")[:19]
                source    = log.get("source", "")
                level     = log.get("level", "")
                message   = log.get("message", "")
                entry = f"[{timestamp}] [{source}] {level}: {message}\n"
                self.logs_text.insert(tk.END, entry)

            self.logs_text.see(tk.END)

        except requests.exceptions.RequestException as e:
            # Logs endpoint may not exist yet — fail silently so orders still work
            print(f"Logs fetch error: {e}")
        except Exception as e:
            print(f"Error refreshing logs: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = OrderManagementSystem(root)
    root.mainloop()
