# -*- coding: utf-8 -*-
"""
AuditLogTab - Xem lich su thao tac
"""

import tkinter as tk
from tkinter import ttk
from views.tabs.base_tab import BaseTab
from utils.logger import get_logger
logger = get_logger(__name__)

class AuditLogTab(BaseTab):
    """Tab xem lich su he thong"""
    
    # Cập nhật thêm *args, **kwargs để tương thích với add_tab_safe
    def __init__(self, parent, notebook, db_security=None, *args, **kwargs):
        self.db_security = db_security
        super().__init__(parent, notebook)
    
    def setup_ui(self):
        """Tao giao dien - Dùng chính 'self' làm cha"""
        # Lưu ý: Đã đổi 'self.frame' thành 'self' theo kiến trúc BaseTab mới
        main_frame = ttk.Frame(self, padding=10) 
        main_frame.pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=5)
        
        ttk.Button(toolbar, text="Lam moi", command=self.refresh).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Xuat bao cao", command=self.export_report).pack(side="left", padx=2)
        
        # Treeview hien thi log
        columns = ("id", "action", "table", "record_id", "user", "timestamp", "details")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("action", text="Hanh dong")
        self.tree.heading("table", text="Bang")
        self.tree.heading("record_id", text="ID ban ghi")
        self.tree.heading("user", text="Nguoi dung")
        self.tree.heading("timestamp", text="Thoi gian")
        self.tree.heading("details", text="Chi tiet")
        
        self.tree.column("id", width=50)
        self.tree.column("action", width=100)
        self.tree.column("table", width=120)
        self.tree.column("record_id", width=80)
        self.tree.column("user", width=120)
        self.tree.column("timestamp", width=150)
        self.tree.column("details", width=250)
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def bind_events(self):
        pass
    
    def load_data(self):
        """Tai log tu database"""
        try:
            if self.db_security:
                logs = self.db_security.get_audit_trail(limit=500)
                
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                for log in logs:
                    self.tree.insert("", "end", values=(
                        log[0], log[1], log[2], log[3], log[4], log[5], log[6]
                    ))
                
                # Giả định show_message có trong BaseTab hoặc MainWindow
                logger.info(f"Đã tải {len(logs)} bản ghi log")
        except Exception as e:
            logger.error(f"Lỗi tải log: {e}")
    
    def export_report(self):
        """Xuat bao cao log"""
        from tkinter import filedialog, messagebox
        from datetime import datetime
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== AUDIT LOG REPORT ===\n")
                    f.write(f"Thoi gian xuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for item in self.tree.get_children():
                        values = self.tree.item(item)["values"]
                        f.write(f"ID: {values[0]}\n")
                        f.write(f"Hanh dong: {values[1]}\n")
                        f.write(f"Bang: {values[2]}\n")
                        f.write(f"ID ban ghi: {values[3]}\n")
                        f.write(f"Nguoi dung: {values[4]}\n")
                        f.write(f"Thoi gian: {values[5]}\n")
                        f.write(f"Chi tiet: {values[6]}\n")
                        f.write("-" * 40 + "\n")
                
                messagebox.showinfo("Thanh cong", f"Đã xuất báo cáo ra file:\n{filename}")
                logger.info(f"Đã xuất audit log ra: {filename}")
            except Exception as e:
                logger.error(f"Lỗi xuất audit log: {e}")
                messagebox.showerror("Lỗi", f"Không thể xuất file: {e}")