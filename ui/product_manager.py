import tkinter as tk
from tkinter import ttk, messagebox
from models.product import Product

class ProductManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Quản lý sản phẩm")
        self.geometry("800x500")
        self.parent = parent
        
        # Frame nhập liệu
        input_frame = ttk.LabelFrame(self, text="Thông tin sản phẩm")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Mã SP
        ttk.Label(input_frame, text="Mã SP:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_code = ttk.Entry(input_frame, width=15)
        self.entry_code.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Tên SP
        ttk.Label(input_frame, text="Tên SP:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_name = ttk.Entry(input_frame, width=25)
        self.entry_name.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Đơn vị
        ttk.Label(input_frame, text="Đơn vị:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_unit = ttk.Entry(input_frame, width=15)
        self.entry_unit.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Giá bán
        ttk.Label(input_frame, text="Giá bán:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.entry_price_sell = ttk.Entry(input_frame, width=15)
        self.entry_price_sell.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Giá nhập
        ttk.Label(input_frame, text="Giá nhập:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_price_buy = ttk.Entry(input_frame, width=15)
        self.entry_price_buy.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Tồn kho
        ttk.Label(input_frame, text="Tồn kho:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.entry_stock = ttk.Entry(input_frame, width=15)
        self.entry_stock.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.entry_stock.insert(0, "0")
        
        # Tồn tối thiểu
        ttk.Label(input_frame, text="Tồn tối thiểu:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_min_stock = ttk.Entry(input_frame, width=15)
        self.entry_min_stock.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.entry_min_stock.insert(0, "0")
        
        # Nút chức năng
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Thêm", command=self.add_product).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cập nhật", command=self.update_product).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Xóa", command=self.delete_product).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Làm mới", command=self.clear_input).pack(side="left", padx=5)
        
        # Frame danh sách
        list_frame = ttk.LabelFrame(self, text="Danh sách sản phẩm")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("Mã SP", "Tên SP", "Đơn vị", "Giá bán", "Giá nhập", "Tồn kho", "Tồn tối thiểu")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col != "Tên SP" else 200, anchor="w" if col in ["Mã SP","Tên SP","Đơn vị"] else "e")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        self.load_data()
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        products = Product.get_all()
        for p in products:
            self.tree.insert("", "end", values=(
                p["code"],
                p["name"],
                p["unit"],
                f"{p['price_sell']:,.0f}".replace(",", "."),
                f"{p['price_buy']:,.0f}".replace(",", "."),
                f"{p['stock']:,.0f}".replace(",", "."),
                f"{p['min_stock']:,.0f}".replace(",", ".")
            ))
    
    def add_product(self):
        code = self.entry_code.get().strip()
        name = self.entry_name.get().strip()
        unit = self.entry_unit.get().strip()
        try:
            price_sell = float(self.entry_price_sell.get().replace(".", ""))
            price_buy = float(self.entry_price_buy.get().replace(".", ""))
            stock = float(self.entry_stock.get().replace(",", "."))
            min_stock = float(self.entry_min_stock.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Lỗi", "Giá trị số không hợp lệ")
            return
        
        if not code or not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã và tên sản phẩm")
            return
        
        try:
            Product.create(code, name, unit, price_sell, price_buy, stock, min_stock)
            messagebox.showinfo("Thành công", "Đã thêm sản phẩm")
            self.load_data()
            self.clear_input()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm: {str(e)}")
    
    def update_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm cần sửa")
            return
        
        code = self.entry_code.get().strip()
        name = self.entry_name.get().strip()
        unit = self.entry_unit.get().strip()
        try:
            price_sell = float(self.entry_price_sell.get().replace(".", ""))
            price_buy = float(self.entry_price_buy.get().replace(".", ""))
            stock = float(self.entry_stock.get().replace(",", "."))
            min_stock = float(self.entry_min_stock.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Lỗi", "Giá trị số không hợp lệ")
            return
        
        Product.update(code, name=name, unit=unit, price_sell=price_sell, price_buy=price_buy, stock=stock, min_stock=min_stock)
        self.load_data()
        self.clear_input()
        messagebox.showinfo("Thành công", "Đã cập nhật")
    
    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            return
        code = self.tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Xác nhận", f"Xóa sản phẩm {code}?"):
            Product.delete(code)
            self.load_data()
            self.clear_input()
    
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
        self.entry_min_stock.delete(0, tk.END)
        self.entry_min_stock.insert(0, values[6].replace(",", "."))
    
    def clear_input(self):
        self.entry_code.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self.entry_unit.delete(0, tk.END)
        self.entry_price_sell.delete(0, tk.END)
        self.entry_price_buy.delete(0, tk.END)
        self.entry_stock.delete(0, tk.END)
        self.entry_stock.insert(0, "0")
        self.entry_min_stock.delete(0, tk.END)
        self.entry_min_stock.insert(0, "0")
        self.entry_code.focus_set()