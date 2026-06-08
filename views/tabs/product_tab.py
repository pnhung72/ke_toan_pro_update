# -*- coding: utf-8 -*-
"""
ProductTab - Quan ly san pham theo kien truc MVC
"""

import tkinter as tk
from tkinter import ttk, messagebox
from views.tabs.base_tab import BaseTab

class ProductTab(BaseTab):
    """Tab quan ly san pham"""
    
    def __init__(self, parent, notebook, controller):
        self.controller = controller
        super().__init__(parent, notebook, controller)
    
    def setup_ui(self):
        """Tao giao dien"""
        # Frame chinh
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=5)
        
        ttk.Button(toolbar, text="Them moi", command=self.add_product).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Sua", command=self.edit_product).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Xoa", command=self.delete_product).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Lam moi", command=self.refresh).pack(side="left", padx=2)
        
        # Treeview hien thi san pham
        columns = ("id", "name", "price", "stock")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Ten san pham")
        self.tree.heading("price", text="Gia ban")
        self.tree.heading("stock", text="Ton kho")
        
        self.tree.column("id", width=50)
        self.tree.column("name", width=300)
        self.tree.column("price", width=120)
        self.tree.column("stock", width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def bind_events(self):
        """Rang buoc su kien"""
        self.tree.bind("<Double-1>", lambda e: self.edit_product())
    
    def load_data(self):
        """Tai du lieu tu controller"""
        try:
            products = self.controller.get_all_products()
            
            # Xoa du lieu cu
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Them du lieu moi
            for product in products:
                self.tree.insert("", "end", values=(
                    product.get("id", ""),
                    product.get("name", ""),
                    product.get("price", 0),
                    product.get("stock", 0)
                ))
            
            self.show_message(f"Da tai {len(products)} san pham")
        except Exception as e:
            self.show_error(f"Loi tai du lieu: {e}")
    
    def add_product(self):
        """Them san pham moi"""
        # Tao dialog them san pham
        dialog = tk.Toplevel(self.frame)
        dialog.title("Them san pham")
        dialog.geometry("400x300")
        dialog.grab_set()
        
        ttk.Label(dialog, text="Ten san pham:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Gia ban:").pack(pady=5)
        price_entry = ttk.Entry(dialog, width=40)
        price_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Ton kho:").pack(pady=5)
        stock_entry = ttk.Entry(dialog, width=40)
        stock_entry.pack(pady=5)
        
        def save():
            data = {
                "name": name_entry.get(),
                "price": float(price_entry.get() or 0),
                "stock": int(stock_entry.get() or 0)
            }
            self.controller.add_product(data)
            dialog.destroy()
            self.refresh()
        
        ttk.Button(dialog, text="Luu", command=save).pack(pady=10)
    
    def edit_product(self):
        """Sua san pham"""
        selected = self.tree.selection()
        if not selected:
            self.show_message("Vui long chon san pham can sua", True)
            return
        
        item = self.tree.item(selected[0])
        product_id = item["values"][0]
        
        self.show_message(f"Dang sua san pham ID: {product_id}")
        # TODO: Mo dialog sua
    
    def delete_product(self):
        """Xoa san pham"""
        selected = self.tree.selection()
        if not selected:
            self.show_message("Vui long chon san pham can xoa", True)
            return
        
        if messagebox.askyesno("Xac nhan", "Ban co muon xoa san pham nay?"):
            item = self.tree.item(selected[0])
            product_id = item["values"][0]
            self.controller.delete_product(product_id)
            self.refresh()