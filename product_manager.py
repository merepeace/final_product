import tkinter as tk
from random import sample
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

import requests

from database_setup import DatabaseManager, setup_database


class ProductManager:
    def __init__(self, parent, refresh_callback=None):
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.db = DatabaseManager()
        self.create_product_ui()

    def create_product_ui(self):
        """Create product management UI"""
        # Main frame
        self.frame = tk.LabelFrame(self.parent, text="📦 Product Management", padx=10, pady=10,
                                   font=('Arial', 12, 'bold'))
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Toolbar
        toolbar = tk.Frame(self.frame)
        toolbar.pack(fill="x", pady=5)

        tk.Button(toolbar, text="➕ Add Product", command=self.add_product,
                  bg="green", fg="white", padx=10).pack(side="left", padx=2)
        tk.Button(toolbar, text="✏️ Edit Product", command=self.edit_product,
                  bg="orange", padx=10).pack(side="left", padx=2)
        tk.Button(toolbar, text="🗑️ Delete Product", command=self.delete_product,
                  bg="red", fg="white", padx=10).pack(side="left", padx=2)
        tk.Button(toolbar, text="🔄 Refresh", command=self.refresh_products,
                  bg="blue", fg="white", padx=10).pack(side="left", padx=2)

        # Search frame
        search_frame = tk.Frame(self.frame)
        search_frame.pack(fill="x", pady=5)

        tk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_products)

        # Products treeview
        columns = ('ID', 'Name', 'Model', 'Color', 'Stock', 'Price', 'Location', 'Min Stock')
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings', height=15)

        # Define headings
        headings = ['ID', 'Product Name', 'Model', 'Color', 'Stock Qty', 'Price (USD)', 'Location', 'Min Stock']
        widths = [50, 150, 120, 80, 80, 100, 100, 80]

        for i, (col, heading, width) in enumerate(zip(columns, headings, widths)):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind double-click to edit
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_product())

        # Load products
        self.refresh_products()

    def refresh_products(self):
        """Refresh products list"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            response = requests.get("http://127.0.0.1:8000/products")
            response.raise_for_status()
            products = response.json()
        except Exception as e:
            print("Error fetching products:", e)
            products = []

        for product in products:
            # Extract values from JSON (dict)
            product_id = product.get("id")
            name = product.get("productname")
            model = product.get("model")
            color = product.get("color", "N/A")
            stock = product.get("stock_quantity", 0)
            price_val = product.get("price_usd")
            location = product.get("location")
            min_stock = product.get("min_stock", 0)

            # Format price
            price = f"${price_val:.2f}" if price_val else "N/A"

            values = (
                product_id,
                name,
                model,
                color,
                stock,
                price,
                location,
                min_stock
            )

            # Color coding
            if stock == 0:
                tag = 'critical'
            elif stock < min_stock:
                tag = 'low'
            else:
                tag = 'normal'

            self.tree.insert('', 'end', values=values, tags=(tag,))

        # Configure tags
        self.tree.tag_configure('critical', background='red', foreground='white')
        self.tree.tag_configure('low', background='yellow')
        self.tree.tag_configure('normal', background='white')

        if self.refresh_callback:
            self.refresh_callback()

    def search_products(self, event=None):
        """Search products locally (no API search endpoint used)"""


        search_term = self.search_entry.get().strip().lower()

        # clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            response = requests.get("http://127.0.0.1:8000/products", timeout=5)
            response.raise_for_status()
            all_products = response.json()

        except Exception as e:
            print("API Error:", e)
            all_products = []

        for product in all_products:
            name = product.get("productname", "").lower()
            model = product.get("model", "").lower()

            # LOCAL FILTER ONLY
            if search_term and search_term not in name and search_term not in model:
                continue

            product_id = product.get("id")
            color = product.get("color", "N/A")
            stock = product.get("stock_quantity", 0)
            price_val = product.get("price_usd")
            location = product.get("location", "")
            min_stock = product.get("min_stock", 0)

            price = f"${price_val:.2f}" if price_val else "N/A"

            values = (
                product_id,
                product.get("productname"),
                product.get("model"),
                color,
                stock,
                price,
                location,
                min_stock
            )

            # stock status
            if stock == 0:
                tag = 'critical'
            elif stock < min_stock:
                tag = 'low'
            else:
                tag = 'normal'

            self.tree.insert('', 'end', values=values, tags=(tag,))

    def add_product(self):
        """Add new product dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add New Product")
        dialog.geometry("600x550")
        dialog.resizable(False, False)

        # Make dialog modal
        dialog.transient(self.parent)
        dialog.grab_set()

        # Create form
        form = tk.Frame(dialog, padx=20, pady=20)
        form.pack(fill="both", expand=True)

        # Form fields
        labels = [
            ('Product Name:', '*'), ('Model:', '*'), ('Color:', ''),
            ('Stock Quantity:', '*'), ('Price (USD):', ''), ('Location:', ''),
            ('Minimum Stock Level:', '*'), ('Description:', ''), ('Weight (kg):', ''),
            ('Dimensions (LxWxH cm):', '')
        ]

        entries = []

        for label, required in labels:
            frame = tk.Frame(form)
            frame.pack(fill="x", pady=5)

            tk.Label(frame, text=label, width=20, anchor='w').pack(side="left")

            if label == 'Description:':
                entry = tk.Text(frame, height=3, width=40)
                entry.pack(side="left", padx=5)
            else:
                entry = tk.Entry(frame, width=40)
                entry.pack(side="left", padx=5)

            if required == '*':
                tk.Label(frame, text="* Required", fg="red").pack(side="left")

            entries.append(entry)

        # Set default values
        entries[5].insert(0, 'Warehouse')  # Location
        entries[6].insert(0, '5')  # Min stock level

        def save_product():
            try:
                # Get values
                name = entries[0].get().strip()
                model = entries[1].get().strip()
                color = entries[2].get().strip() or ""

                # Validate required fields
                if not name or not model:
                    messagebox.showerror("Error", "Product Name and Model are required!")
                    return

                # Stock
                try:
                    stock = int(entries[3].get())
                    if stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Stock quantity must be a positive number!")
                    return

                # Price (must be > 0 for API)
                try:
                    price = float(entries[4].get())
                    if price <= 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Price must be a valid number greater than 0!")
                    return

                # Location
                location = entries[5].get().strip() or "Warehouse"

                # Min stock
                try:
                    min_stock = int(entries[6].get())
                    if min_stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Minimum stock must be a positive number!")
                    return

                # Prepare payload (ONLY fields API expects)
                payload = {
                    "productname": name,
                    "model": model,
                    "color": color,
                    "stock_quantity": stock,
                    "price_usd": price,
                    "location": location,
                    "min_stock": min_stock
                }

                # POST to API
                response = requests.post(
                    "http://127.0.0.1:8000/products",
                    json=payload,
                    timeout=5
                )

                if response.ok:
                    messagebox.showinfo("Success", f"Product '{name}' added successfully!")
                    dialog.destroy()
                    self.refresh_products()
                else:
                    messagebox.showerror("Error", f"API Error:\n{response.text}")

            except requests.exceptions.RequestException as e:
                messagebox.showerror("Error", f"Connection failed:\n{str(e)}")

            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Save Product", command=save_product,
                  bg="green", fg="white", padx=20).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                  bg="gray", fg="white", padx=20).pack(side="left", padx=5)

    def edit_product(self):
        import requests
        from tkinter import messagebox
        import tkinter as tk

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a product to edit")
            return

        product_id = self.tree.item(selected[0])['values'][0]

        # Fetch product from API
        try:
            response = requests.get(f"http://127.0.0.1:8000/products/{product_id}", timeout=5)
            response.raise_for_status()
            product = response.json()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch product:\n{str(e)}")
            return

        if not product:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Edit Product - {product.get('productname')}")
        dialog.geometry("600x550")
        dialog.resizable(False, False)

        dialog.transient(self.parent)
        dialog.grab_set()

        form = tk.Frame(dialog, padx=20, pady=20)
        form.pack(fill="both", expand=True)

        labels = [
            'Product Name:', 'Model:', 'Color:', 'Stock Quantity:',
            'Price (USD):', 'Location:', 'Minimum Stock Level:',
            'Description:', 'Weight (kg):', 'Dimensions (LxWxH cm):'
        ]

        entries = []

        for i, label in enumerate(labels):
            frame = tk.Frame(form)
            frame.pack(fill="x", pady=5)

            tk.Label(frame, text=label, width=20, anchor='w').pack(side="left")

            if label == 'Description:':
                entry = tk.Text(frame, height=3, width=40)
                entry.pack(side="left", padx=5)
            else:
                entry = tk.Entry(frame, width=40)
                entry.pack(side="left", padx=5)

                # Fill values from API (DICT ACCESS)
                if i == 0:
                    entry.insert(0, product.get("productname", ""))
                elif i == 1:
                    entry.insert(0, product.get("model", ""))
                elif i == 2:
                    entry.insert(0, product.get("color", ""))
                elif i == 3:
                    entry.insert(0, product.get("stock_quantity", 0))
                elif i == 4:
                    entry.insert(0, product.get("price_usd", 0))
                elif i == 5:
                    entry.insert(0, product.get("location", ""))
                elif i == 6:
                    entry.insert(0, product.get("min_stock", 0))

            entries.append(entry)

        def update_product():
            try:
                name = entries[0].get().strip()
                model = entries[1].get().strip()

                if not name or not model:
                    messagebox.showerror("Error", "Product Name and Model are required!")
                    return

                color = entries[2].get().strip() or ""

                # Stock
                try:
                    stock = int(entries[3].get())
                    if stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Stock quantity must be a positive number!")
                    return

                # Price
                try:
                    price = float(entries[4].get())
                    if price <= 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Price must be a valid positive number!")
                    return

                location = entries[5].get().strip() or "Warehouse"

                # Min stock
                try:
                    min_stock = int(entries[6].get())
                    if min_stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Minimum stock level must be a positive number!")
                    return

                # Get product ID (important)
                product_id = self.tree.item(self.tree.selection()[0])['values'][0]

                # Payload (ONLY backend fields)
                payload = {
                    "productname": name,
                    "model": model,
                    "color": color,
                    "stock_quantity": stock,
                    "price_usd": price,
                    "location": location,
                    "min_stock": min_stock
                }

                # PUT request
                response = requests.put(
                    f"http://127.0.0.1:8000/products/{product_id}",
                    json=payload,
                    timeout=5
                )

                if response.ok:
                    messagebox.showinfo("Success", f"Product '{name}' updated successfully!")
                    dialog.destroy()
                    self.refresh_products()
                else:
                    messagebox.showerror("Error", f"API Error:\n{response.text}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to update product:\n{str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Update Product", command=update_product,
                  bg="green", fg="white", padx=20).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                  bg="gray", fg="white", padx=20).pack(side="left", padx=5)

    def delete_product(self):
        """Delete selected product"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a product to delete")
            return

        product_id = self.tree.item(selected[0])['values'][0]
        product_name = self.tree.item(selected[0])['values'][1]

        # Optional: confirm delete
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{product_name}'?"
        )

        if not confirm:
            return

        try:
            response = requests.delete(
                f"http://127.0.0.1:8000/products/{product_id}",
                timeout=5
            )

            if response.ok:
                messagebox.showinfo("Success", f"Product '{product_name}' deleted successfully!")
                self.refresh_products()
            else:
                messagebox.showerror("Error", f"API Error:\n{response.text}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete product:\n{str(e)}")


if __name__ == "__main__":
    # Setup database first
    setup_database()

    # Test the product manager standalone
    root = tk.Tk()
    root.title("Product Management System")
    root.geometry("1000x600")

    app = ProductManager(root)
    root.mainloop()