import pandas as pd
import os
from tkinter import filedialog, messagebox
from datetime import datetime

def export_to_excel(data, columns, default_filename, sheet_name="Sheet1"):
    """
    data: list of tuples/lists or list of dicts
    columns: list of column names
    default_filename: tên file mặc định (không bao gồm đuôi .xlsx)
    sheet_name: tên sheet trong Excel
    """
    try:
        # Tạo DataFrame
        df = pd.DataFrame(data, columns=columns)
        
        # Hỏi người dùng nơi lưu file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"{default_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if not file_path:
            return
        
        # Lưu file
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        messagebox.showinfo("Thành công", f"Đã xuất file:\n{file_path}")
        
        # Hỏi mở file
        if messagebox.askyesno("Mở file", "Bạn có muốn mở file vừa xuất không?"):
            os.startfile(file_path)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xuất Excel:\n{str(e)}")