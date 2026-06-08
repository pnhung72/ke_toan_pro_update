import sqlite3

def kiem_tra_cau_truc():
    db_path = r'D:\ke_toan_pro_v3\ke_toan_data\ke_toan.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ['journal_entries', 'transaction_metadata']
        
        print("--- KẾT QUẢ KIỂM TRA CƠ SỞ DỮ LIỆU ---")
        for table in tables:
            print(f"\n[Bảng: {table}]")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            if not columns:
                print(f"  => LỖI: Không tìm thấy bảng {table}")
                continue
                
            has_amount = False
            for col in columns:
                col_name = col[1]
                print(f"  - Cột: {col_name}")
                if col_name.lower() == 'amount':
                    has_amount = True
            
            if has_amount:
                print(f"  => XÁC NHẬN: Bảng {table} CÓ cột 'amount'")
            else:
                print(f"  => CẢNH BÁO: Bảng {table} KHÔNG CÓ cột 'amount'")
        
        conn.close()
    except Exception as e:
        print(f"Lỗi khi thực thi kiểm tra: {e}")

if __name__ == "__main__":
    kiem_tra_cau_truc()