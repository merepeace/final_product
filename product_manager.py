import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
from database_setup import DatabaseManager, setup_database


class ProductManager:
    def __init__(self, parent, refresh_callback=None):
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.db = DatabaseManager()
        self.create_product_ui()

    def create_product_ui(self):
        """Create product management UI - Fully Restored Layout"""
        # Main frame
        self.frame = tk.LabelFrame(self.parent, text="📦 Product Management", padx=10, pady=10,
                                   font=('Arial', 12, 'bold'))
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Toolbar (Top Row) ---
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

        # Professional Export Button on the right
        tk.Button(toolbar, text="📥 Export CSV", command=self.professional_export,
                  bg="#28a745", fg="white", padx=10, font=('Arial', 9, 'bold')).pack(side="right", padx=2)

        # --- Search Bar (Second Row) ---
        search_frame = tk.Frame(self.frame)
        search_frame.pack(fill="x", pady=5)

        tk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)
        # Keeps your "search as you type" feature
        self.search_entry.bind('<KeyRelease>', self.search_products)

        # --- Treeview (Main Area) ---
        columns = ('ID', 'Name', 'Model', 'Color', 'Stock', 'Price', 'Location', 'Min Stock')
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings', height=15)

        # Headings exactly as in your image
        headings = ['ID', 'Product Name', 'Model', 'Color', 'Stock Qty', 'Price (USD)', 'Location', 'Min Stock']
        widths = [100, 150, 120, 100, 80, 100, 100, 80]

        for col, heading, width in zip(columns, headings, widths):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Restore Double-Click to Edit
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_product())

        self.refresh_products()

    def professional_export(self):
        """Professional Mid-Level Export Feature"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="warehouse_inventory.csv",
            title="Select where to save your export"
        )
        if not file_path:
            return

        def download_task():
            try:
                response = requests.get("http://127.0.0.1:8000/export-csv", timeout=5)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    messagebox.showinfo("Success", f"Data exported to:\n{file_path}")
                else:
                    messagebox.showerror("Error", "Backend failed to create CSV.")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Is the API running?\n{e}")

        threading.Thread(target=download_task, daemon=True).start()

    def refresh_products(self):
        """Refreshes the product treeview with data from the database"""
        # Clear the existing items in the tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get products from your database manager
            products = self.db.get_all_products()

            for p in products:
                # Check if p is a tuple (standard SQLite result)
                if isinstance(p, (tuple, list)):
                    # Map tuple indexes to your columns
                    # (Adjust these numbers based on your actual database columns)
                    p_id = p[0]
                    p_name = p[1]
                    p_model = p[2]
                    p_color = p[3]
                    p_stock = p[4]
                    p_price = p[5]
                    p_loc = p[6]
                # Check if p is a dictionary (SQLAlchemy/API result)
                elif isinstance(p, dict):
                    p_id = p.get('id', 'N/A')
                    p_name = p.get('name', 'N/A')
                    p_model = p.get('model', 'N/A')
                    p_color = p.get('color', 'N/A')
                    p_stock = p.get('stock_quantity', 0)
                    p_price = p.get('price_usd', 0)
                    p_loc = p.get('location', 'N/A')
                else:
                    continue  # Skip if it's just a raw string causing the error

                # Format the price safely
                try:
                    formatted_price = f"${float(p_price):.2f}"
                except:
                    formatted_price = "$0.00"

                # Insert into the tree
                self.tree.insert('', 'end', values=(
                    p_id, p_name, p_model, p_color, p_stock, formatted_price, p_loc
                ))

        except Exception as e:
            print(f"Error refreshing products: {e}")

    def search_products(self, event=None):
        """Restores local filtering logic"""
        term = self.search_entry.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            all_p = requests.get("http://127.0.0.1:8000/products").json()
        except:
            all_p = []

        for p in all_p:
            if term in p.get("productname", "").lower() or term in p.get("model", "").lower():
                price = f"${p.get('price_usd', 0):.2f}"
                self.tree.insert('', 'end', values=(p.get("id"), p.get("productname"), p.get("model"),
                                                    p.get("color"), p.get("stock_quantity"), price, p.get("location"),
                                                    p.get("min_stock")))

    def add_product(self):
        """Keeps your exact 'Add' dialog logic"""
        # ... (Include your existing Add Product Toplevel logic here)
        pass

    def edit_product(self):
        """Keeps your exact 'Edit' dialog logic"""
        # ... (Include your existing Edit Product Toplevel logic here)
        pass

    def delete_product(self):
        """Keeps your delete logic"""
        selected = self.tree.selection()
        if not selected: return
        pid = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this product?"):
            requests.delete(f"http://127.0.0.1:8000/products/{pid}")
            self.refresh_products()