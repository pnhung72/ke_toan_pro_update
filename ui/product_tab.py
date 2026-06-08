# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from services.product_service import ProductService
from utils.license import is_full_version
from ui.theme_manager import (
    get_font, get_color, create_treeview, create_label, 
    create_button, get_padding, SIZES, FONTS, COLORS
)

class ProductTab(ttk.Frame):
    def __init__(self, main_window, notebook):
        """Khởi tạo Tab Hàng hóa theo chuẩn Kiến trúc đồng bộ 6.0"""
        # Kích hoạt lớp Frame gốc để đăng ký trực tiếp đối tượng với Notebook
        super().__init__(notebook)
        
        self.main_window = main_window
        self.notebook = notebook
        
        # Gọi các hàm thiết lập giao diện và nạp cơ sở dữ liệu
        self.create_widgets()
        self.load_products()
    
    def create_widgets(self):
        # Style cho form nhập liệu - DÙNG FONT TOÀN CỤC
        style = ttk.Style()
        style.configure("Form.TLabel", font=get_font('label'))
        style.configure("Form.TEntry", font=get_font('entry'))
        style.configure("Form.TButton", font=get_font('button'))
        
        # Frame nhập liệu
        input_frame = ttk.LabelFrame(self, text="Thông tin sản phẩm")
        # Đổi màu chữ tiêu đề thành xanh - DÙNG MÀU TOÀN CỤC
        style = ttk.Style()
        style.configure("Blue.TLabelframe.Label", foreground=COLORS['primary'], font=get_font('heading', bold=True))
        input_frame.configure(style="Blue.TLabelframe")
        input_frame.pack(fill="x", padx=get_padding('large'), pady=get_padding('medium'))
        
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)
        
        # Mã SP
        ttk.Label(input_frame, text="Mã SP:", style="Form.TLabel").grid(row=0, column=0, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        self.entry_code = ttk.Entry(input_frame, width=20, style="Form.TEntry")
        self.entry_code.grid(row=0, column=1, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        
        # Tên SP
        ttk.Label(input_frame, text="Tên SP:", style="Form.TLabel").grid(row=0, column=2, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        self.entry_name = ttk.Entry(input_frame, width=35, style="Form.TEntry")
        self.entry_name.grid(row=0, column=3, padx=get_padding('medium'), pady=get_padding('small'), sticky="we")
        
        # Đơn vị
        ttk.Label(input_frame, text="Đơn vị:", style="Form.TLabel").grid(row=1, column=0, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        self.entry_unit = ttk.Entry(input_frame, width=20, style="Form.TEntry")
        self.entry_unit.grid(row=1, column=1, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        
        # Giá bán
        ttk.Label(input_frame, text="Giá bán:", style="Form.TLabel").grid(row=1, column=2, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        self.entry_price_sell = ttk.Entry(input_frame, width=20, style="Form.TEntry")
        self.entry_price_sell.grid(row=1, column=3, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        
        # Giá nhập
        ttk.Label(input_frame, text="Giá nhập:", style="Form.TLabel").grid(row=2, column=0, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        self.entry_price_buy = ttk.Entry(input_frame, width=20, style="Form.TEntry")
        self.entry_price_buy.grid(row=2, column=1, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        
        # Tồn kho
        ttk.Label(input_frame, text="Tồn kho:", style="Form.TLabel").grid(row=2, column=2, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        self.entry_stock = ttk.Entry(input_frame, width=20, style="Form.TEntry")
        self.entry_stock.grid(row=2, column=3, padx=get_padding('medium'), pady=get_padding('small'), sticky="w")
        self.entry_stock.insert(0, "0")
        
        # Nút
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=get_padding('large'))
        
        ttk.Button(btn_frame, text="➕ Thêm", command=self.add_product, width=12, style="Form.TButton").pack(side="left", padx=get_padding('medium'))
        ttk.Button(btn_frame, text="✏️ Cập nhật", command=self.update_product, width=12, style="Form.TButton").pack(side="left", padx=get_padding('medium'))
        ttk.Button(btn_frame, text="🗑️ Xóa", command=self.delete_product, width=10, style="Form.TButton").pack(side="left", padx=get_padding('medium'))
        ttk.Button(btn_frame, text="🔄 Làm mới", command=self.clear_form, width=12, style="Form.TButton").pack(side="left", padx=get_padding('medium'))
        ttk.Button(btn_frame, text="📊 Xuất Excel", command=self.export_excel, width=12, style="Form.TButton").pack(side="left", padx=get_padding('medium'))
        
        # Treeview
        list_frame = ttk.LabelFrame(self, text="DANH SÁCH SẢN PHẨM", padding=get_padding('large'))
        list_frame.pack(fill="both", expand=True, padx=get_padding('large'), pady=get_padding('medium'))
        
        columns = ("Mã SP", "Tên SP", "Đơn vị", "Giá bán", "Giá nhập", "Tồn kho")
        
        # Style cho Treeview với font lớn - DÙNG FONT TOÀN CỤC
        style.configure("Product.Treeview", font=get_font('tree'), rowheight=SIZES['tree_rowheight'])
        style.configure("Product.Treeview.Heading", font=get_font('tree_header', bold=True))
        
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10, style="Product.Treeview")
        
        col_widths = [120, 300, 100, 160, 160, 120]
        for idx, col in enumerate(columns):
            self.tree.heading(col, text=col)
            if idx == 1:  # Tên SP: căn trái
                self.tree.column(col, width=col_widths[idx], anchor="w")
            elif idx in [0, 2]:  # Mã SP, Đơn vị: căn giữa
                self.tree.column(col, width=col_widths[idx], anchor="center")
            else:  # Giá bán, Giá nhập, Tồn kho: căn giữa
                self.tree.column(col, width=col_widths[idx], anchor="center")
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
    
    def load_products(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        products = ProductService.get_all_products()
        for p in products:
            # Định dạng số tiền
            price_sell_str = f"{p['price_sell']:,.0f}".replace(",", ".")
            price_buy_str = f"{p['price_buy']:,.0f}".replace(",", ".")
            if p['stock'] % 1 != 0:
                stock_str = f"{p['stock']:,.1f}".replace(".", ",")
            else:
                stock_str = f"{p['stock']:,.0f}".replace(",", ".")
            
            self.tree.insert("", "end", values=(
                p["code"],
                p["name"],
                p["unit"],
                price_sell_str,
                price_buy_str,
                stock_str
            ))
    
    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        
        self.entry_code.delete(0, tk.END)
        self.entry_code.insert(0, values[0])
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, values[1])
        self.entry_unit.delete(0, tk.END)
        self.entry_unit.insert(0, values[2])
        self.entry_price_sell.delete(0, tk.END)
        self.entry_price_sell.insert(0, values[3].replace(".", ""))
        self.entry_price_buy.delete(0, tk.END)
        self.entry_price_buy.insert(0, values[4].replace(".", ""))
        self.entry_stock.delete(0, tk.END)
        self.entry_stock.insert(0, values[5].replace(",", "."))
    
    def clear_form(self):
        self.entry_code.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self.entry_unit.delete(0, tk.END)
        self.entry_price_sell.delete(0, tk.END)
        self.entry_price_buy.delete(0, tk.END)
        self.entry_stock.delete(0, tk.END)
        self.entry_stock.insert(0, "0")
        self.entry_code.focus_set()
    
    def add_product(self):
        code = self.entry_code.get().strip()
        name = self.entry_name.get().strip()
        unit = self.entry_unit.get().strip()
        try:
            price_sell = float(self.entry_price_sell.get().replace(".", ""))
            price_buy = float(self.entry_price_buy.get().replace(".", ""))
            stock = float(self.entry_stock.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền hoặc tồn kho không hợp lệ")
            return
        
        if not code or not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã và tên sản phẩm")
            return
        
        success, message = ProductService.create_product(code, name, unit, price_sell, price_buy, stock)
        if success:
            self.load_products()
            self.clear_form()
        messagebox.showinfo("Kết quả", message)
    
    def update_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm cần cập nhật")
            return
        
        code = self.entry_code.get().strip()
        name = self.entry_name.get().strip()
        unit = self.entry_unit.get().strip()
        try:
            price_sell = float(self.entry_price_sell.get().replace(".", ""))
            price_buy = float(self.entry_price_buy.get().replace(".", ""))
            stock = float(self.entry_stock.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền hoặc tồn kho không hợp lệ")
            return
        
        success, message = ProductService.update_product(
            code, name=name, unit=unit, 
            price_sell=price_sell, price_buy=price_buy, stock=stock
        )
        if success:
            self.load_products()
            self.clear_form()
        messagebox.showinfo("Kết quả", message)
    
    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm cần xóa")
            return
        
        code = self.tree.item(selected[0], "values")[0]
        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa sản phẩm {code}?"):
            return
        
        success, message = ProductService.delete_product(code)
        if success:
            self.load_products()
            self.clear_form()
        messagebox.showinfo("Kết quả", message)
    
    def export_excel(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            price_sell = float(values[3].replace(".", ""))
            price_buy = float(values[4].replace(".", ""))
            stock = float(values[5].replace(",", "."))
            data.append({
                "Mã SP": values[0],
                "Tên SP": values[1],
                "Đơn vị": values[2],
                "Giá bán": price_sell,
                "Giá nhập": price_buy,
                "Tồn kho": stock
            })
        columns = ["Mã SP", "Tên SP", "Đơn vị", "Giá bán", "Giá nhập", "Tồn kho"]
        export_to_excel(data, columns, "Danh_sach_san_pham")