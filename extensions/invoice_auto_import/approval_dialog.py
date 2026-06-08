"""
Cửa sổ duyệt hóa đơn bằng Tkinter (đồng bộ với main_window Tkinter)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
import subprocess

from .queue_db import get_pending_invoices, update_invoice_status, get_invoice_by_id
from .integrator import approve_invoice_sync
from .logger import get_logger

logger = get_logger()


class ApprovalDialog(tk.Toplevel):
    def __init__(self, parent, global_font=None):
        super().__init__(parent)
        self.parent = parent
        self.title("Duyệt hóa đơn đầu vào (XML)")
        self.geometry("1000x600")
        self.global_font = global_font
        self.pending_data = []
        
        self.init_ui()
        self.load_pending_invoices()
        self.apply_font()
    
    def apply_font(self):
        if self.global_font:
            # Áp dụng font cho tất cả widget con (có thể viết đệ quy)
            def apply_font_recursive(widget):
                try:
                    widget.configure(font=self.global_font)
                except:
                    pass
                for child in widget.winfo_children():
                    apply_font_recursive(child)
            apply_font_recursive(self)
    
    def init_ui(self):
        # Frame chính
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label tiêu đề
        lbl_title = ttk.Label(main_frame, text="Danh sách hóa đơn chờ duyệt (từ email)", font=('', 12, 'bold'))
        lbl_title.pack(anchor=tk.W, pady=(0,5))
        
        # Treeview (bảng)
        columns = ('ID', 'invoice_no', 'seller_tax_code', 'seller_name', 'issue_date', 
                   'total_amount_wo_tax', 'tax_amount', 'total_amount')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings')
        
        # Định nghĩa heading
        self.tree.heading('ID', text='ID')
        self.tree.heading('invoice_no', text='Số hóa đơn')
        self.tree.heading('seller_tax_code', text='MST người bán')
        self.tree.heading('seller_name', text='Tên người bán')
        self.tree.heading('issue_date', text='Ngày lập')
        self.tree.heading('total_amount_wo_tax', text='Tiền hàng')
        self.tree.heading('tax_amount', text='Tiền thuế')
        self.tree.heading('total_amount', text='Tổng thanh toán')
        
        # Căn chỉnh cột
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('invoice_no', width=120, anchor='center')
        self.tree.column('seller_tax_code', width=120, anchor='center')
        self.tree.column('seller_name', width=200)
        self.tree.column('issue_date', width=100, anchor='center')
        self.tree.column('total_amount_wo_tax', width=100, anchor='e')
        self.tree.column('tax_amount', width=100, anchor='e')
        self.tree.column('total_amount', width=100, anchor='e')
        
        # Thanh cuộn
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame nút bấm
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10,0))
        
        ttk.Button(btn_frame, text="Duyệt hóa đơn được chọn", command=self.approve_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Từ chối", command=self.reject_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Xem file XML gốc", command=self.view_xml).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Làm mới", command=self.load_pending_invoices).pack(side=tk.LEFT, padx=5)
    
    def load_pending_invoices(self):
        # Xóa dữ liệu cũ
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        self.pending_data = get_pending_invoices()
        for inv in self.pending_data:
            self.tree.insert('', tk.END, values=(
                inv['id'],
                inv.get('invoice_no', ''),
                inv.get('seller_tax_code', ''),
                inv.get('seller_name', ''),
                inv.get('issue_date', ''),
                f"{inv.get('total_amount_wo_tax', 0):,.0f}",
                f"{inv.get('tax_amount', 0):,.0f}",
                f"{inv.get('total_amount', 0):,.0f}"
            ))
        logger.info(f"Đã tải {len(self.pending_data)} hóa đơn pending")
    
    def get_selected_invoice_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một hóa đơn trong danh sách.")
            return None
        item = selected[0]
        values = self.tree.item(item, 'values')
        if values:
            return int(values[0])
        return None
    
    def approve_selected(self):
        inv_id = self.get_selected_invoice_id()
        if not inv_id:
            return
        inv = get_invoice_by_id(inv_id)
        if not inv:
            return
        if messagebox.askyesno("Xác nhận duyệt", f"Duyệt hóa đơn số {inv.get('invoice_no')} từ {inv.get('seller_name')}?"):
            success = approve_invoice_sync(inv_id)
            if success:
                messagebox.showinfo("Thành công", "Hóa đơn đã được duyệt và ghi vào sổ.")
                self.load_pending_invoices()
            else:
                messagebox.showerror("Lỗi", "Có lỗi khi duyệt hóa đơn, xem log để biết chi tiết.")
    
    def reject_selected(self):
        inv_id = self.get_selected_invoice_id()
        if not inv_id:
            return
        inv = get_invoice_by_id(inv_id)
        reason = simpledialog.askstring("Lý do từ chối", "Nhập lý do từ chối:")
        if reason is not None:
            update_invoice_status(inv_id, 'rejected', rejection_reason=reason)
            messagebox.showinfo("Đã từ chối", f"Hóa đơn {inv.get('invoice_no')} bị từ chối.")
            self.load_pending_invoices()
    
    def view_xml(self):
        inv_id = self.get_selected_invoice_id()
        if not inv_id:
            return
        inv = get_invoice_by_id(inv_id)
        if not inv:
            return
        xml_path = inv.get('xml_path')
        if not xml_path or not Path(xml_path).exists():
            messagebox.showerror("Lỗi", "File XML gốc không tồn tại (đã được backup?).")
            return
        try:
            subprocess.Popen(['notepad.exe', xml_path])
        except:
            messagebox.showerror("Lỗi", "Không thể mở file XML.")