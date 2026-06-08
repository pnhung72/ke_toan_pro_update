import os
import tempfile
import subprocess
import platform
from tkinter import messagebox

def print_text(content, title="In tài liệu"):
    """Gửi nội dung văn bản tới máy in mặc định"""
    try:
        # Tạo file tạm
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_file = f.name
        
        if platform.system() == "Windows":
            # Dùng notepad để in (có thể dùng win32print, nhưng đơn giản là mở notepad)
            os.startfile(tmp_file, 'print')
        else:
            # Linux/Mac: dùng lp
            subprocess.run(['lp', tmp_file], check=True)
            os.unlink(tmp_file)
        return True
    except Exception as e:
        messagebox.showerror("Lỗi in", f"Không thể in: {str(e)}")
        return False

def show_print_preview(content, title="Xem trước khi in", parent=None):
    """Hiển thị cửa sổ xem trước với nút In và Đóng"""
    from tkinter import Toplevel, Text, Scrollbar, END, DISABLED, NORMAL
    from tkinter import ttk
    from theme import get_font
    
    preview = Toplevel(parent)
    preview.title(title)
    preview.geometry("600x700")
    preview.minsize(500, 600)
    
    main_frame = ttk.Frame(preview)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Khung hiển thị
    text_widget = Text(main_frame, wrap="word", font=get_font("small"), bg='white', fg='black')
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Chèn nội dung
    text_widget.insert(END, content)
    text_widget.config(state=DISABLED)
    
    # Nút
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill="x", pady=10)
    ttk.Button(btn_frame, text="In", command=lambda: [print_text(content, title), preview.destroy()]).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Đóng", command=preview.destroy).pack(side="right", padx=5)