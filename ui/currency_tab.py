# ui/currency_tab.py
# Tab quản lý ngoại tệ

import tkinter as tk
from tkinter import ttk, messagebox
import logging

try:
    from theme import get_font
except ImportError:
    def get_font(size="normal"):
        fonts = {"title": ("Segoe UI", 12, "bold"), "label": ("Segoe UI", 10)}
        return fonts.get(size, ("Segoe UI", 10))

from core.currency_manager import CurrencyManager

class CurrencyTab(ttk.Frame):
    """Tab quản lý ngoại tệ và tỷ giá"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Khởi tạo CurrencyManager
        self.cm = CurrencyManager()
        logging.info("CurrencyTab: CurrencyManager đã sẵn sàng")
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Tạo giao diện"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="💱 QUẢN LÝ NGOẠI TỆ VÀ TỶ GIÁ", 
                                 font=get_font("title"))
        title_label.pack(pady=(0, 10))
        
        # Treeview
        columns = ("code", "name", "symbol", "rate", "is_base")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("code", text="Mã")
        self.tree.heading("name", text="Tên ngoại tệ")
        self.tree.heading("symbol", text="Ký hiệu")
        self.tree.heading("rate", text="Tỷ giá (VND)")
        self.tree.heading("is_base", text="Tiền tệ cơ sở")
        
        self.tree.column("code", width=80)
        self.tree.column("name", width=180)
        self.tree.column("symbol", width=80)
        self.tree.column("rate", width=140)
        self.tree.column("is_base", width=120)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="🔄 Làm mới", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Cập nhật tỷ giá", command=self.update_rates).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="", font=get_font("small"))
        self.status_label.pack(pady=(10, 0))
    
    def load_data(self):
        """Tải dữ liệu từ database"""
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            currencies = self.cm.get_all_currencies()
            self.status_label.config(text=f"✅ Đã tải {len(currencies)} ngoại tệ", foreground="green")
            
            for curr in currencies:
                code = curr["code"]
                name = curr["name"]
                symbol = curr.get("symbol", code)
                is_base = "✓" if curr.get("is_base", False) else ""
                
                # Lấy tỷ giá
                if code == "VND":
                    rate_str = "1"
                else:
                    rate = self.cm.get_exchange_rate(code, "VND")
                    rate_str = f"{rate:,.0f}"
                
                self.tree.insert("", tk.END, values=(code, name, symbol, rate_str, is_base))
            
            logging.info(f"Đã tải {len(currencies)} ngoại tệ lên giao diện")
            
        except Exception as e:
            self.status_label.config(text=f"❌ Lỗi: {e}", foreground="red")
            logging.error(f"Lỗi load_data: {e}")
    
    def update_rates(self):
        """Cập nhật tỷ giá từ API"""
        self.status_label.config(text="🔄 Đang cập nhật tỷ giá...", foreground="blue")
        self.update_idletasks()
        
        try:
            self.cm.update_exchange_rate_daily()
            self.load_data()
            self.status_label.config(text="✅ Đã cập nhật tỷ giá thành công", foreground="green")
            messagebox.showinfo("Thành công", "Đã cập nhật tỷ giá từ API")
        except Exception as e:
            self.status_label.config(text=f"❌ Lỗi: {e}", foreground="red")
            messagebox.showerror("Lỗi", f"Không thể cập nhật tỷ giá:\n{e}")
