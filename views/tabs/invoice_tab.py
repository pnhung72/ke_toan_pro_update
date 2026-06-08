# -*- coding: utf-8 -*-
"""
InvoiceTab - Quan ly hoa don theo kien truc MVC
"""

import tkinter as tk
from tkinter import ttk, messagebox
from views.tabs.base_tab import BaseTab
from theme import get_font

class InvoiceTab(BaseTab):
    """Tab quan ly hoa don"""
    
    def __init__(self, parent, notebook, controller):
        self.controller = controller
        self.cart_items = []
        super().__init__(parent, notebook, controller)
    
    def setup_ui(self):
        """Tao giao dien"""
        # Style cho font
        style = ttk.Style()
        style.configure("Invoice.Treeview", font=get_font("small"), rowheight=28)
        style.configure("Invoice.Treeview.Heading", font=get_font("bold"))
        style.configure("Invoice.TLabel", font=get_font("label"))
        style.configure("Invoice.TButton", font=get_font("label"))
        
        # Paned window chia 2 phan
        paned = ttk.PanedWindow(self.frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Khung trai: Danh sach hoa don
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="DANH SACH HOA DON", font=get_font("bold")).pack(pady=5)
        
        # Treeview hoa don
        columns = ("id", "date", "customer", "total", "status")
        self.invoice_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15, style="Invoice.Treeview")
        
        self.invoice_tree.heading("id", text="ID")
        self.invoice_tree.heading("date", text="Ngay")
        self.invoice_tree.heading("customer", text="Khach hang")
        self.invoice_tree.heading("total", text="Tong tien")
        self.invoice_tree.heading("status", text="Trang thai")
        
        self.invoice_tree.column("id", width=50, anchor="center")
        self.invoice_tree.column("date", width=100, anchor="center")
        self.invoice_tree.column("customer", width=150, anchor="w")
        self.invoice_tree.column("total", width=120, anchor="e")
        self.invoice_tree.column("status", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        self.invoice_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Khung phai: Tao hoa don moi
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="TAO HOA DON MOI", font=get_font("bold")).pack(pady=5)
        
        # Form nhap
        form_frame = ttk.Frame(right_frame)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(form_frame, text="Khach hang:", font=get_font("label")).grid(row=0, column=0, sticky="w", pady=2)
        self.customer_entry = ttk.Entry(form_frame, width=30, font=get_font("label"))
        self.customer_entry.grid(row=0, column=1, pady=2)
        
        ttk.Label(form_frame, text="San pham:", font=get_font("label")).grid(row=1, column=0, sticky="w", pady=2)
        self.product_combo = ttk.Combobox(form_frame, width=27, font=get_font("label"))
        self.product_combo.grid(row=1, column=1, pady=2)
        
        ttk.Label(form_frame, text="So luong:", font=get_font("label")).grid(row=2, column=0, sticky="w", pady=2)
        self.quantity_entry = ttk.Entry(form_frame, width=30, font=get_font("label"))
        self.quantity_entry.grid(row=2, column=1, pady=2)
        self.quantity_entry.insert(0, "1")
        
        ttk.Button(form_frame, text="Them vao hoa don", command=self.add_to_cart, style="Invoice.TButton").grid(row=3, column=0, columnspan=2, pady=5)
        
        # Gio hang
        ttk.Label(right_frame, text="GIO HANG", font=get_font("bold")).pack(pady=5)
        
        cart_frame = ttk.Frame(right_frame)
        cart_frame.pack(fill="both", expand=True, padx=10)
        
        cart_columns = ("product", "quantity", "price", "total")
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=8, style="Invoice.Treeview")
        
        self.cart_tree.heading("product", text="San pham")
        self.cart_tree.heading("quantity", text="So luong")
        self.cart_tree.heading("price", text="Don gia")
        self.cart_tree.heading("total", text="Thanh tien")
        
        self.cart_tree.column("product", width=150, anchor="w")
        self.cart_tree.column("quantity", width=70, anchor="center")
        self.cart_tree.column("price", width=100, anchor="e")
        self.cart_tree.column("total", width=100, anchor="e")
        
        cart_scroll = ttk.Scrollbar(cart_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        
        self.cart_tree.pack(side="left", fill="both", expand=True)
        cart_scroll.pack(side="right", fill="y")
        
        # Tong tien
        total_frame = ttk.Frame(right_frame)
        total_frame.pack(fill="x", pady=5)
        ttk.Label(total_frame, text="Tong cong:", font=get_font("label")).pack(side="left", padx=10)
        self.total_label = ttk.Label(total_frame, text="0 VND", font=get_font("bold"))
        self.total_label.pack(side="left")
        
        # Buttons
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Luu hoa don", command=self.save_invoice, style="Invoice.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Xoa gio hang", command=self.clear_cart, style="Invoice.TButton").pack(side="left", padx=5)
    
    def bind_events(self):
        """Rang buoc su kien"""
        self.invoice_tree.bind("<Double-1>", lambda e: self.view_invoice_detail())
    
    def load_data(self):
        """Tai du lieu hoa don"""
        try:
            invoices = self.controller.get_all_invoices()
            products = self.controller.get_products()
            
            # Cap nhat combobox san pham
            product_names = [p.get("name", "") for p in products]
            self.product_combo['values'] = product_names
            self.product_list = products
            
            # Xoa du lieu cu
            for item in self.invoice_tree.get_children():
                self.invoice_tree.delete(item)
            
            # Them du lieu moi
            for inv in invoices:
                self.invoice_tree.insert("", "end", values=(
                    inv.get("id", ""),
                    inv.get("date", ""),
                    inv.get("customer", ""),
                    f"{inv.get('total', 0):,.0f}",
                    inv.get("status", "pending")
                ))
            
            self.show_message(f"Da tai {len(invoices)} hoa don")
        except Exception as e:
            self.show_error(f"Loi tai du lieu: {e}")
    
    def add_to_cart(self):
        """Them san pham vao gio hang"""
        product_name = self.product_combo.get()
        quantity = self.quantity_entry.get()
        
        if not product_name:
            self.show_message("Vui long chon san pham", True)
            return
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            self.show_message("So luong khong hop le", True)
            return
        
        # Tim san pham
        product = None
        for p in self.product_list:
            if p.get("name") == product_name:
                product = p
                break
        
        if product:
            price = product.get("price", 0)
            total = price * quantity
            
            self.cart_items.append({
                "product": product_name,
                "quantity": quantity,
                "price": price,
                "total": total,
                "product_id": product.get("id")
            })
            
            self.refresh_cart()
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, "1")
    
    def refresh_cart(self):
        """Lam moi gio hang"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        total_amount = 0
        for item in self.cart_items:
            self.cart_tree.insert("", "end", values=(
                item["product"],
                item["quantity"],
                f"{item['price']:,.0f}",
                f"{item['total']:,.0f}"
            ))
            total_amount += item["total"]
        
        self.total_label.config(text=f"{total_amount:,.0f} VND")
    
    def clear_cart(self):
        """Xoa gio hang"""
        if messagebox.askyesno("Xac nhan", "Ban co muon xoa toan bo gio hang?"):
            self.cart_items = []
            self.refresh_cart()
    
    def save_invoice(self):
        """Luu hoa don"""
        customer = self.customer_entry.get()
        
        if not customer:
            self.show_message("Vui long nhap ten khach hang", True)
            return
        
        if not self.cart_items:
            self.show_message("Gio hang trong", True)
            return
        
        invoice_data = {
            "customer": customer,
            "date": self.get_current_date(),
            "items": self.cart_items,
            "total": self.controller.calculate_total(self.cart_items)
        }
        
        result = self.controller.create_invoice(invoice_data)
        if result:
            self.show_message("Da luu hoa don thanh cong")
            self.customer_entry.delete(0, tk.END)
            self.cart_items = []
            self.refresh_cart()
            self.load_data()
    
    def get_current_date(self):
        """Lay ngay hien tai"""
        from datetime import datetime
        return datetime.now().strftime("%d/%m/%Y")
    
    def view_invoice_detail(self):
        """Xem chi tiet hoa don"""
        selected = self.invoice_tree.selection()
        if selected:
            self.show_message("Chuc nang dang phat trien")