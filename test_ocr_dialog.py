import tkinter as tk
from tkinter import ttk

print("=== BẮT ĐẦU TEST ===")

# Test 1: Import dialog
try:
    from ui.dialogs.ocr_import_dialog import OCRImportDialog
    print("✅ Import OCRImportDialog thành công")
except Exception as e:
    print(f"❌ Import lỗi: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Tạo cửa sổ và mở dialog
root = tk.Tk()
root.title("Test OCR")
root.geometry("300x200")

def open_dialog():
    print("Đang mở dialog...")
    try:
        # Thử với root (window)
        dialog = OCRImportDialog(root)
        print("✅ Dialog tạo thành công với root")
    except Exception as e:
        print(f"❌ Lỗi khi tạo dialog: {e}")
        traceback.print_exc()

btn = ttk.Button(root, text="Mở OCR", command=open_dialog)
btn.pack(pady=50)

print("Chạy chương trình, bấm nút để test")
root.mainloop()