import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from pathlib import Path

class InvoiceApprovalTab(ttk.Frame):
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.db_path = db_path
        self.setup_ui()
        self.refresh_queue()

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        lbl = ttk.Label(main_frame, text="📄 HÓA ĐƠN ĐẦU VÀO CHỜ DUYỆT", font=('Arial', 12, 'bold'))
        lbl.pack(anchor=tk.W, pady=(0,5))

        columns = ('id', 'invoice_no', 'seller_name', 'total_amount', 'status')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('invoice_no', text='Số hóa đơn')
        self.tree.heading('seller_name', text='Người bán')
        self.tree.heading('total_amount', text='Tổng tiền (VNĐ)')
        self.tree.heading('status', text='Trạng thái')
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('invoice_no', width=120, anchor='center')
        self.tree.column('seller_name', width=250)
        self.tree.column('total_amount', width=120, anchor='e')
        self.tree.column('status', width=100, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10,0))
        ttk.Button(btn_frame, text="✅ Duyệt", command=self.approve).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Từ chối", command=self.reject).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Làm mới", command=self.refresh_queue).pack(side=tk.LEFT, padx=5)

    def get_conn(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def refresh_queue(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, invoice_no, seller_name, total_amount, status FROM invoice_queue WHERE status='pending'")
        for row in cursor.fetchall():
            self.tree.insert('', tk.END, values=row)
        conn.close()

    def get_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một hóa đơn")
            return None
        values = self.tree.item(selected[0], 'values')
        return {'id': values[0], 'invoice_no': values[1], 'seller_name': values[2], 'total_amount': values[3]}

    def approve(self):
        inv = self.get_selected()
        if not inv: return
        if messagebox.askyesno("Xác nhận", f"Duyệt hóa đơn {inv['invoice_no']}?"):
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE invoice_queue SET status='approved' WHERE id=?", (inv['id'],))
            conn.commit()
            conn.close()
            messagebox.showinfo("Thành công", "Đã duyệt hóa đơn")
            self.refresh_queue()

    def reject(self):
        inv = self.get_selected()
        if not inv: return
        reason = simpledialog.askstring("Lý do", "Nhập lý do từ chối:")
        if reason is not None:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE invoice_queue SET status='rejected', rejection_reason=? WHERE id=?", (reason, inv['id']))
            conn.commit()
            conn.close()
            messagebox.showinfo("Đã từ chối", f"Hóa đơn {inv['invoice_no']} bị từ chối")
            self.refresh_queue()