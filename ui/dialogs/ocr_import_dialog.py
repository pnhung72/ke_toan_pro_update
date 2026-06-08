import tkinter as tk
from tkinter import ttk, filedialog, messagebox
try:
    from theme import get_font
except ImportError:
    def get_font(style="label"):
        return ("Arial", 10)
import threading
import sqlite3
from datetime import datetime
import traceback
import sys
from utils.sync_lock import ocr_started, ocr_finished
import logging

class OCRImportDialog(tk.Toplevel):
    def __init__(self, parent, db_path="ke_toan_data/ke_toan.db"):
        #print("[DEBUG] OCRImportDialog __init__ - bắt đầu")
        #print(f"[DEBUG] parent = {parent}, type = {type(parent)}")
        try:
            super().__init__(parent)
            #print("[DEBUG] super() ok")
            self.db_path = db_path
            self.title("Nhập hóa đơn bằng OCR")
            self.geometry("700x600")
            #print("[DEBUG] Đang gọi create_widgets...")
            self.create_widgets()
            #print("[DEBUG] create_widgets ok")
            self.current_image_path = None
            #print("[DEBUG] __init__ hoàn tất")
            self.protocol("WM_DELETE_WINDOW", self.on_close)
            # Render xong mới grab
            self.update_idletasks()
            self.lift()
            self.focus_force()
            self.grab_set()
            #print("[DEBUG] grab_set ok")
        except Exception as e:
            #print(f"[LỖI] __init__: {e}")
            import traceback
            traceback.print_exc()

    def create_widgets(self):
        #print("[DEBUG] create_widgets - bắt đầu")
        try:
            # Khung chọn file
            file_frame = ttk.LabelFrame(self, text="Chọn file hóa đơn (ảnh hoặc PDF)", padding=5)
            file_frame.pack(fill="x", padx=10, pady=5)
            self.file_path_var = tk.StringVar(master=self)
            ttk.Entry(file_frame, textvariable=self.file_path_var, font=get_font("label"), width=60).pack(side="left", padx=5)
            ttk.Button(file_frame, text="📂 Duyệt", command=self.select_file).pack(side="left", padx=5)
            ttk.Button(file_frame, text="🔍 OCR", command=self.start_ocr).pack(side="left", padx=5)

            # Khung tiến trình
            self.progress = ttk.Progressbar(self, mode='determinate')
            self.progress.pack(fill="x", padx=10, pady=5)

            # Khung kết quả OCR (text)
            result_frame = ttk.LabelFrame(self, text="Kết quả OCR", padding=5)
            result_frame.pack(fill="both", expand=True, padx=10, pady=5)
            self.text_result = tk.Text(result_frame, font=get_font("small"), wrap="word")
            self.text_result.pack(side="left", fill="both", expand=True)
            scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.text_result.yview)
            scroll.pack(side="right", fill="y")
            self.text_result.config(yscrollcommand=scroll.set)

            # Khung thông tin đã parse
            info_frame = ttk.LabelFrame(self, text="Thông tin hóa đơn (có thể sửa)", padding=5)
            info_frame.pack(fill="x", padx=10, pady=5)
            row = 0
            ttk.Label(info_frame, text="Số hóa đơn:", font=get_font("label")).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            self.so_hd = ttk.Entry(info_frame, width=20, font=get_font("label"))
            self.so_hd.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            row += 1
            ttk.Label(info_frame, text="Ngày hóa đơn:", font=get_font("label")).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            self.ngay_hd = ttk.Entry(info_frame, width=20, font=get_font("label"))
            self.ngay_hd.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            row += 1
            ttk.Label(info_frame, text="Số tiền:", font=get_font("label")).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            self.tien = ttk.Entry(info_frame, width=20, font=get_font("label"))
            self.tien.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            row += 1
            ttk.Label(info_frame, text="Thuế GTGT:", font=get_font("label")).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            self.thue = ttk.Entry(info_frame, width=20, font=get_font("label"))
            self.thue.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            row += 1
            ttk.Label(info_frame, text="Tổng cộng:", font=get_font("label")).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            self.tong = ttk.Entry(info_frame, width=20, font=get_font("label"))
            self.tong.grid(row=row, column=1, padx=5, pady=2, sticky="w")

            # Nút lưu
            btn_frame = ttk.Frame(self)
            btn_frame.pack(fill="x", padx=10, pady=10)
            ttk.Button(btn_frame, text="Lưu vào hàng đợi", command=self.save_to_queue).pack(side="right", padx=5)
            ttk.Button(btn_frame, text="Đóng", command=self.destroy).pack(side="right", padx=5)
            #print("[DEBUG] create_widgets - tạo widget thành công")
        except Exception as e:
            logging.error(f"Lỗi create_widgets OCRImportDialog: {e}")
            traceback.print_exc()

    def select_file(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Chọn file hóa đơn", filetypes=filetypes)
        if path:
            self.file_path_var.set(path)
            self.current_image_path = path

    def start_ocr(self):
        ocr_started()  # Đánh dấu OCR bắt đầu
        if not self.current_image_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file trước!")
            return
        self.progress['value'] = 0
        self.text_result.delete(1.0, tk.END)
        threading.Thread(target=self.do_ocr, daemon=True).start()
        
    def do_ocr(self):
        try:
            try:
                from ai.engine.ocr_engine import ocr_engine
            except ImportError as ie:
                self.after(0, lambda: messagebox.showerror("Lỗi Import", f"Không tìm thấy OCR engine:\n{ie}"))
                return
            full_text, parsed = ocr_engine.process_image(
                self.current_image_path, 
                progress_callback=lambda v: self.progress.configure(value=v)
            )
            self.after(0, lambda: self.display_result(full_text, parsed))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Lỗi", f"OCR thất bại: {e}"))
        finally:
            ocr_finished()  # ← LUÔN giải phóng lock dù thành công hay lỗi

    def display_result(self, full_text, parsed):
        self.text_result.insert(tk.END, full_text or "Không đọc được nội dung")
        if parsed:
            self.so_hd.delete(0, tk.END)
            self.so_hd.insert(0, parsed.get('so_hoa_don', ''))
            self.ngay_hd.delete(0, tk.END)
            self.ngay_hd.insert(0, parsed.get('ngay', ''))
            self.tien.delete(0, tk.END)
            self.tien.insert(0, f"{parsed.get('tien', 0)}")
            self.thue.delete(0, tk.END)
            self.thue.insert(0, f"{parsed.get('thue', 0)}")
            self.tong.delete(0, tk.END)
            self.tong.insert(0, f"{parsed.get('tong', 0)}")
            
    def on_close(self):
        """Đóng dialog và đánh dấu OCR kết thúc"""
        ocr_finished()
        self.destroy()

    def save_to_queue(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoice_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    so_hoa_don TEXT,
                    ngay TEXT,
                    tien REAL,
                    thue REAL,
                    tong REAL,
                    ocr_text TEXT,
                    trang_thai TEXT DEFAULT 'pending_review',
                    created_at TEXT
                )
            ''')
            cursor.execute('''
                INSERT INTO invoice_queue (so_hoa_don, ngay, tien, thue, tong, ocr_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.so_hd.get(),
                self.ngay_hd.get(),
                float(self.tien.get()) if self.tien.get() else 0,
                float(self.thue.get()) if self.thue.get() else 0,
                float(self.tong.get()) if self.tong.get() else 0,
                self.text_result.get(1.0, tk.END),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Thành công", "Đã lưu hóa đơn vào hàng đợi duyệt!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")
            logging.error(f"Lỗi save_to_queue: {e}")
            traceback.print_exc()