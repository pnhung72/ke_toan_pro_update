import tkinter as tk
from tkinter import ttk, messagebox
from services.closing_service import ClosingService
from datetime import datetime
from theme import get_font

class PeriodClosingTab:
    def __init__(self, parent, notebook):
        self.parent = parent
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Khóa sổ")
        self.create_widgets()
        self.load_periods()

    def create_widgets(self):
        # === STYLE CHO FONT LỚN ===
        style = ttk.Style()
        style.configure("Closing.TLabelframe.Label", font=get_font("bold"))
        style.configure("Closing.TButton", font=get_font("label"), padding=8)
        style.configure("Closing.TLabel", font=get_font("label"))
        style.configure("Closing.Treeview", font=get_font("small"), rowheight=28)
        style.configure("Closing.Treeview.Heading", font=get_font("bold"))
        style.configure("Closing.TEntry", font=get_font("label"))
        
        # Frame tạo kỳ mới
        create_frame = ttk.LabelFrame(self.frame, text="Tạo kỳ kế toán mới", style="Closing.TLabelframe")
        create_frame.pack(fill="x", padx=10, pady=5)
        
        # Dòng 1
        row1_frame = ttk.Frame(create_frame)
        row1_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ttk.Label(row1_frame, text="Tên kỳ:", font=get_font("label"), width=10).pack(side="left", padx=(0, 10))
        self.entry_name = ttk.Entry(row1_frame, width=25, font=get_font("label"))
        self.entry_name.pack(side="left", padx=(0, 30))
        
        ttk.Label(row1_frame, text="Ngày bắt đầu:", font=get_font("label"), width=12).pack(side="left", padx=(0, 10))
        self.entry_start = ttk.Entry(row1_frame, width=15, font=get_font("label"))
        self.entry_start.pack(side="left", padx=(0, 5))
        self.entry_start.insert(0, "01/01/2025")
        
        # Dòng 2
        row2_frame = ttk.Frame(create_frame)
        row2_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ttk.Label(row2_frame, text="Ngày kết thúc:", font=get_font("label"), width=12).pack(side="left", padx=(0, 10))
        self.entry_end = ttk.Entry(row2_frame, width=15, font=get_font("label"))
        self.entry_end.pack(side="left", padx=(0, 30))
        self.entry_end.insert(0, "31/12/2025")
        
        ttk.Button(row2_frame, text="➕ Tạo kỳ", command=self.create_period,
                   style="Closing.TButton", width=12).pack(side="left", padx=5)

        # Frame danh sách kỳ
        list_frame = ttk.LabelFrame(self.frame, text="DANH SÁCH KỲ KẾ TOÁN", style="Closing.TLabelframe")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tạo Treeview
        columns = ("ID", "Tên kỳ", "Ngày bắt đầu", "Ngày kết thúc", "Trạng thái", "Đã khóa")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", 
                                  height=14, style="Closing.Treeview")
        
        # Cấu hình cột
        col_widths = {"ID": 60, "Tên kỳ": 250, "Ngày bắt đầu": 120, 
                      "Ngày kết thúc": 120, "Trạng thái": 100, "Đã khóa": 150}
        col_anchors = {"ID": "center", "Tên kỳ": "w", "Ngày bắt đầu": "center",
                       "Ngày kết thúc": "center", "Trạng thái": "center", "Đã khóa": "center"}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[col], anchor=col_anchors[col])
        
        # Thanh cuộn
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Frame nút chức năng dưới cùng
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="🔒 Khóa sổ", command=self.close_period,
                   style="Closing.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Làm mới", command=self.load_periods,
                   style="Closing.TButton", width=12).pack(side="left", padx=5)

    def load_periods(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        periods = ClosingService.get_periods()
        for p in periods:
            status = "🔴 Đã khóa" if p['is_closed'] else "🟢 Đang mở"
            closed_info = p['closed_date'] if p['closed_date'] else ("Chưa khóa" if not p['is_closed'] else "Đã khóa")
            
            # Màu sắc theo trạng thái
            tag = "closed" if p['is_closed'] else "open"
            
            self.tree.insert("", "end", values=(
                p['id'],
                p['period_name'],
                p['start_date'],
                p['end_date'],
                status,
                closed_info
            ), tags=(tag,))
        
        # Cấu hình màu sắc
        self.tree.tag_configure("closed", foreground="#F44336")
        self.tree.tag_configure("open", foreground="#4CAF50")

    def create_period(self):
        name = self.entry_name.get().strip()
        start = self.entry_start.get().strip()
        end = self.entry_end.get().strip()
        
        if not name or not start or not end:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin")
            return
        
        # Kiểm tra định dạng ngày
        try:
            datetime.strptime(start, "%d/%m/%Y")
            datetime.strptime(end, "%d/%m/%Y")
        except Exception:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ (dd/mm/yyyy)")
            return
        
        ClosingService.create_period(name, start, end)
        self.load_periods()
        self.clear_form()
        messagebox.showinfo("Thành công", "Đã tạo kỳ kế toán mới")

    def close_period(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Chọn kỳ cần khóa sổ")
            return
        
        values = self.tree.item(selected[0], "values")
        period_id = values[0]
        period_name = values[1]
        
        if values[4] == "🔴 Đã khóa":
            messagebox.showinfo("Thông báo", f"Kỳ '{period_name}' đã được khóa trước đó")
            return
        
        if messagebox.askyesno("Xác nhận", 
                               f"🔒 Khóa sổ kỳ '{period_name}'?\n\n"
                               "Khóa sổ sẽ tạo bút toán kết chuyển và không thể sửa dữ liệu trong kỳ.\n\n"
                               "Bạn có chắc chắn muốn tiếp tục?"):
            ClosingService.close_period(period_id)
            self.load_periods()
            messagebox.showinfo("Thành công", f"Đã khóa sổ kỳ kế toán: {period_name}")
    
    def clear_form(self):
        """Xóa dữ liệu trên form nhập"""
        self.entry_name.delete(0, tk.END)
        self.entry_start.delete(0, tk.END)
        self.entry_start.insert(0, "01/01/2025")
        self.entry_end.delete(0, tk.END)
        self.entry_end.insert(0, "31/12/2025")
        self.entry_name.focus_set()