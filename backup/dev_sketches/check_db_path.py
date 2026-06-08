import sqlite3
import os
import sys

def dieu_tra_nguon_du_lieu():
    print("=== HE THONG DIEU TRA DU LIEU KE TOAN PRO ===")
    
    # 1. Chỉnh sửa đường dẫn về thư mục gốc (Nơi chứa dữ liệu thật)
    base_dir = r"D:\ke_toan_pro_v3\ke_toan_data"
    db_path = None

    print(f"[*] Dang kiem tra thu muc: {base_dir}")

    if os.path.exists(base_dir) and os.path.isdir(base_dir):
        # Tìm tất cả các file database
        db_files = [f for f in os.listdir(base_dir) if f.endswith(('.db', '.sqlite', '.sqlite3'))]
        
        if db_files:
            # SẮP XẾP: Chọn file có dung lượng lớn nhất (thường là file chứa dữ liệu thật)
            full_paths = [os.path.join(base_dir, f) for f in db_files]
            db_path = max(full_paths, key=os.path.getsize)
            
            file_size = os.path.getsize(db_path) / 1024 # Tính KB
            print(f"[+] Da tim thay file database: {os.path.basename(db_path)}")
            print(f"[+] Dung luong file: {file_size:.2f} KB")
        else:
            print(f"[-] Khong tim thay file .db nao trong {base_dir}")
    else:
        print(f"[-] Thu muc {base_dir} khong ton tai.")

    # 2. Kiểm tra module hệ thống
    print("\n[+] Kiem tra module he thong:")
    found_module = False
    for module_name in list(sys.modules.keys()):
        if "services" in module_name or "core.database" in module_name:
            module = sys.modules[module_name]
            file_path = getattr(module, '__file__', 'Unknown')
            print(f"  - {module_name}: {file_path}")
            found_module = True
    if not found_module:
        print("  - Khong co module services nao dang chay ngam.")

    # 3. Truy vấn thực tế để đối chiếu với giao diện phần mềm
    if db_path:
        try:
            # Kết nối Read-Only
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # Lấy danh sách bảng (loại bỏ các bảng hệ thống của sqlite)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
            
            print(f"\n[+] KET QUA DOI CHIEU VOI KIEN TRUC V5.0.4:")
            print(f"  - So luong bang: {len(tables)}/26 bang")
            
            # Đối chiếu số lượng giao dịch với con số "25 GD" trên giao diện
            if 'transactions' in tables:
                cursor.execute("SELECT COUNT(*) FROM transactions")
                count = cursor.fetchone()[0]
                print(f"  - So luong giao dich: {count} dòng (Khớp với UI: {'DUNG' if count==25 else 'KHAC'})")
                
                # Tính thử tổng thu để khớp với con số 38.960.000đ
                cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income' OR type='Thu'")
                total_thu = cursor.fetchone()[0] or 0
                print(f"  - Tong thu tinh toan tu DB: {total_thu:,.0f} VND")

            print("\n[+] Chi tiet danh sach 26 bang:")
            for i, table in enumerate(sorted(tables), 1):
                print(f"  {i:2d}. {table}")
                
            conn.close()
        except Exception as e:
            print(f"[-] Loi khi truy van database: {e}")
    else:
        print("\n[!] Khong tim thay file du lieu de kiem tra.")

if __name__ == "__main__":
    dieu_tra_nguon_du_lieu()