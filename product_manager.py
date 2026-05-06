import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
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

        products = self.db.get_all_products()

        for product in products:
            # Format price
            price = f"${product[5]:.2f}" if product[5] else "N/A"
            values = (product[0], product[1], product[2], product[3] or 'N/A', product[4], price, product[6],
                      product[7])

            # Color coding based on stock level
            if product[4] == 0:
                tag = 'critical'
            elif product[4] < product[7]:
                tag = 'low'
            else:
                tag = 'normal'

            self.tree.insert('', 'end', values=values, tags=(tag,))

        # Configure tags
        self.tree.tag_configure('critical', background='red', foreground='white')
        self.tree.tag_configure('low', background='yellow')
        self.tree.tag_configure('normal', background='white')

        # Call refresh callback if provided
        if self.refresh_callback:
            self.refresh_callback()

    def search_products(self, event=None):
        """Search products by name or model"""
        search_term = self.search_entry.get().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        all_products = self.db.get_all_products()

        for product in all_products:
            if search_term in product[1].lower() or search_term in product[2].lower():
                price = f"${product[5]:.2f}" if product[5] else "N/A"
                values = (product[0], product[1], product[2], product[3] or 'N/A', product[4], price, product[6],
                          product[7])

                if product[4] == 0:
                    tag = 'critical'
                elif product[4] < product[7]:
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
                color = entries[2].get().strip() or None

                # Validate required fields
                if not name or not model:
                    messagebox.showerror("Error", "Product Name and Model are required!")
                    return

                try:
                    stock = int(entries[3].get())
                    if stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Stock quantity must be a positive number!")
                    return

                price = None
                if entries[4].get():
                    try:
                        price = float(entries[4].get())
                        if price < 0:
                            raise ValueError
                    except:
                        messagebox.showerror("Error", "Price must be a valid positive number!")
                        return

                location = entries[5].get().strip() or 'Warehouse'

                try:
                    min_stock = int(entries[6].get())
                    if min_stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Minimum stock level must be a positive number!")
                    return

                description = entries[7].get("1.0", "end-1c").strip() or None

                weight = None
                if entries[8].get():
                    try:
                        weight = float(entries[8].get())
                        if weight < 0:
                            raise ValueError
                    except:
                        messagebox.showerror("Error", "Weight must be a valid positive number!")
                        return

                dimensions = entries[9].get().strip() or None

                # Add product using DatabaseManager
                self.db.add_product(name, model, color, stock, price, location, min_stock, description, weight,
                                    dimensions)

                messagebox.showinfo("Success", f"Product '{name}' added successfully!")
                dialog.destroy()
                self.refresh_products()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add product: {str(e)}")

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Save Product", command=save_product,
                  bg="green", fg="white", padx=20).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                  bg="gray", fg="white", padx=20).pack(side="left", padx=5)

    def edit_product(self):
        """Edit selected product"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a product to edit")
            return

        product_id = self.tree.item(selected[0])['values'][0]

        # Get product details
        product = self.db.get_product_by_id(product_id)

        if not product:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Edit Product - {product[1]}")
        dialog.geometry("600x550")
        dialog.resizable(False, False)

        dialog.transient(self.parent)
        dialog.grab_set()

        form = tk.Frame(dialog, padx=20, pady=20)
        form.pack(fill="both", expand=True)

        # Form fields with current values
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
                if product[8]:
                    entry.insert("1.0", product[8])
            else:
                entry = tk.Entry(frame, width=40)
                entry.pack(side="left", padx=5)

                # Set current values (index mapping)
                if i == 0:  # Name
                    entry.insert(0, product[1])
                elif i == 1:  # Model
                    entry.insert(0, product[2])
                elif i == 2:  # Color
                    if product[3]:
                        entry.insert(0, product[3])
                elif i == 3:  # Stock
                    entry.insert(0, product[4])
                elif i == 4:  # Price
                    if product[5]:
                        entry.insert(0, str(product[5]))
                elif i == 5:  # Location
                    entry.insert(0, product[6])
                elif i == 6:  # Min stock
                    entry.insert(0, product[7])
                elif i == 8:  # Weight
                    if product[9]:
                        entry.insert(0, str(product[9]))
                elif i == 9:  # Dimensions
                    if product[10]:
                        entry.insert(0, product[10])

            entries.append(entry)

        def update_product():
            try:
                name = entries[0].get().strip()
                model = entries[1].get().strip()

                if not name or not model:
                    messagebox.showerror("Error", "Product Name and Model are required!")
                    return

                color = entries[2].get().strip() or None

                try:
                    stock = int(entries[3].get())
                    if stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Stock quantity must be a positive number!")
                    return

                price = None
                if entries[4].get():
                    try:
                        price = float(entries[4].get())
                        if price < 0:
                            raise ValueError
                    except:
                        messagebox.showerror("Error", "Price must be a valid positive number!")
                        return

                location = entries[5].get().strip() or 'Warehouse'

                try:
                    min_stock = int(entries[6].get())
                    if min_stock < 0:
                        raise ValueError
                except:
                    messagebox.showerror("Error", "Minimum stock level must be a positive number!")
                    return

                description = entries[7].get("1.0", "end-1c").strip() or None

                weight = None
                if entries[8].get():
                    try:
                        weight = float(entries[8].get())
                        if weight < 0:
                            raise ValueError
                    except:
                        messagebox.showerror("Error", "Weight must be a valid positive number!")
                        return

                dimensions = entries[9].get().strip() or None

                # Update product
                self.db.update_product(product_id, name, model, color, stock, price, location, min_stock, description,
                                       weight, dimensions)

                messagebox.showinfo("Success", f"Product '{name}' updated successfully!")
                dialog.destroy()
                self.refresh_products()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to update product: {str(e)}")

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

        # Check if product has any orders
        conn = sqlite3.connect('warehouse.db', timeout=20)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders WHERE product_id = ? AND status != 'done'", (product_id,))
        active_orders = cursor.fetchone()[0]
        conn.close()

        if active_orders > 0:
            messagebox.showwarning("Cannot Delete",
                                   f"Cannot delete '{product_name}' because it has {active_orders} active orders!")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{product_name}'?"):
            try:
                self.db.delete_product(product_id)
                messagebox.showinfo("Success", f"Product '{product_name}' deleted successfully!")
                self.refresh_products()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")


if __name__ == "__main__":
    # Setup database first
    setup_database()

    # Test the product manager standalone
    root = tk.Tk()
    root.title("Product Management System")
    root.geometry("1000x600")

    app = ProductManager(root)
    root.mainloop()