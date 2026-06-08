import sqlite3
import os
from models.transaction import Transaction

def buoc_1_tim_hieu():
    print("=== KIỂM TRA HỆ THỐNG KẾ TOÁN YATRANG ===")
    db_path = r"D:\ke_toan_pro_v3\ke_toan_data\ke_toan.db"
    
    # 1. Kiểm tra cấu trúc bảng (Lỗi opening_balance)
    print("\n[1] Kiểm tra cột opening_balance:")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'opening_balance' in columns:
            print("✅ Cột opening_balance đã tồn tại.")
        else:
            print("❌ THIẾU CỘT: opening_balance trong bảng accounts.")
    except Exception as e:
        print(f"❌ Lỗi kết nối DB: {e}")

    # 2. Kiểm tra hàm get_all (Lỗi unexpected keyword argument 'conn')
    print("\n[2] Kiểm tra định nghĩa hàm Transaction.get_all:")
    import inspect
    sig = inspect.signature(Transaction.get_all)
    if 'conn' in sig.parameters:
        print("✅ Hàm get_all đã sẵn sàng nhận tham số 'conn'.")
    else:
        print("❌ LỖI: Hàm get_all chưa có tham số 'conn'. Cần sửa file models/transaction.py")

    # 3. Kiểm tra biến Font toàn cục
    print("\n[3] Gợi ý tìm vị trí lỗi Font:")
    print("Thầy hãy nhấn Ctrl+Shift+F trong VS Code, tìm cụm từ: font.Font")
    print("Nếu nó nằm ngoài class hoặc hàm, đó chính là 'thủ phạm'.")

    conn.close()

if __name__ == "__main__":
    buoc_1_tim_hieu()