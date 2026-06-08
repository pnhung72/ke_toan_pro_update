# -*- coding: utf-8 -*-
"""
DebtTab - Quan ly cong no theo kien truc MVC
"""

import tkinter as tk
from tkinter import ttk, messagebox
from views.tabs.base_tab import BaseTab
from theme import get_font
class DebtTab(BaseTab):
    """Tab quan ly cong no khach hang"""
    
    def __init__(self, parent, notebook, controller):
        self.controller = controller
        super().__init__(parent, notebook, controller)
    
    def setup_ui(self):
        """Tao giao dien"""
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=5)
        
        ttk.Button(toolbar, text="Lam moi", command=self.refresh).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Thanh toan", command=self.pay_debt).pack(side="left", padx=2)
        
        # Khung tong ket
        summary_frame = ttk.LabelFrame(main_frame, text="TONG KET CONG NO", padding=10)
        summary_frame.pack(fill="x", pady=5)
        
        self.total_debt_label = ttk.Label(summary_frame, text="Tong cong no: 0 VND", font=get_font("bold"))
        self.total_debt_label.pack(side="left", padx=20)
        
        self.overdue_label = ttk.Label(summary_frame, text="Qua han: 0 VND", foreground="red", font=get_font("label"))
        self.overdue_label.pack(side="left", padx=20)
        
        # Treeview hien thi cong no
        columns = ("customer", "total_debt", "paid", "remaining", "due_date", "status")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15, style="Debt.Treeview")
        
        self.tree.heading("customer", text="Khach hang")
        self.tree.heading("total_debt", text="Tong no")
        self.tree.heading("paid", text="Da tra")
        self.tree.heading("remaining", text="Con lai")
        self.tree.heading("due_date", text="Han tra")
        self.tree.heading("status", text="Trang thai")
        
        self.tree.column("customer", width=200, anchor="w")
        self.tree.column("total_debt", width=120, anchor="e")
        self.tree.column("paid", width=120, anchor="e")
        self.tree.column("remaining", width=120, anchor="e")
        self.tree.column("due_date", width=100, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        
        self.tree.tag_configure("overdue", foreground="red")
        self.tree.tag_configure("good", foreground="green")
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def bind_events(self):
        """Rang buoc su kien"""
        self.tree.bind("<Double-1>", lambda e: self.view_detail())
    
    def load_data(self):
        """Tai du lieu cong no"""
        try:
            debts = self.controller.get_all_debts()
            summary = self.controller.get_summary()
            
            # Xoa du lieu cu
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Them du lieu moi
            for debt in debts:
                remaining = debt.get("remaining", 0)
                status = debt.get("status", "good")
                tag = "overdue" if status == "overdue" else "good"
                
                self.tree.insert("", "end", values=(
                    debt.get("customer", ""),
                    f"{debt.get('total_debt', 0):,.0f}",
                    f"{debt.get('paid', 0):,.0f}",
                    f"{remaining:,.0f}",
                    debt.get("due_date", ""),
                    "Qua han" if status == "overdue" else "Con han"
                ), tags=(tag,))
            
            # Cap nhat tong ket
            self.total_debt_label.config(text=f"Tong cong no: {summary.get('total_debt', 0):,.0f} VND")
            self.overdue_label.config(text=f"Qua han: {summary.get('overdue', 0):,.0f} VND")
            
            self.show_message(f"Da tai {len(debts)} khach hang cong no")
        except Exception as e:
            self.show_error(f"Loi tai du lieu: {e}")
    
    def pay_debt(self):
        """Thanh toan cong no"""
        selected = self.tree.selection()
        if not selected:
            self.show_message("Vui long chon khach hang can thanh toan", True)
            return
        
        item = self.tree.item(selected[0])
        customer = item["values"][0]
        remaining = float(item["values"][3].replace(",", ""))
        
        if remaining <= 0:
            self.show_message("Khach hang nay khong con cong no", True)
            return
        
        # Dialog thanh toan
        dialog = tk.Toplevel(self.frame)
        dialog.title("Thanh toan cong no")
        dialog.geometry("350x200")
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Khach hang: {customer}").pack(pady=5)
        ttk.Label(dialog, text=f"So tien con no: {remaining:,.0f} VND").pack(pady=5)
        
        ttk.Label(dialog, text="So tien thanh toan:").pack(pady=5)
        amount_entry = ttk.Entry(dialog, width=30)
        amount_entry.pack(pady=5)
        amount_entry.insert(0, str(remaining))
        
        def save():
            try:
                amount = float(amount_entry.get())
            except ValueError:
                messagebox.showerror("Loi", "So tien khong hop le")
                return
            
            if amount > remaining:
                messagebox.showerror("Loi", "So tien thanh toan vuot qua cong no")
                return
            
            self.controller.make_payment(customer, amount)
            dialog.destroy()
            self.refresh()
            self.show_message(f"Da thanh toan {amount:,.0f} VND cho {customer}")
        
        ttk.Button(dialog, text="Thanh toan", command=save).pack(pady=20)
    
    def view_detail(self):
        """Xem chi tiet cong no"""
        selected = self.tree.selection()
        if selected:
            self.show_message("Chuc nang dang phat trien")