import os
import sys

def investigate():
    print("=== CUỘC ĐIỀU TRA ĐƯỜNG DẪN HỆ THỐNG ===")
    
    # 1. Kiểm tra vị trí đứng của script
    current_dir = os.getcwd()
    print(f"1. Thư mục hiện hành (Working Dir): {current_dir}")
    
    # 2. Kiểm tra vị trí file thực thi
    base_path = os.path.dirname(os.path.abspath(__file__))
    print(f"2. Thư mục gốc dự kiến: {base_path}")
    
    # 3. Danh sách file đang hiện diện tại thư mục gốc
    print("\n3. Danh sách file nhìn thấy tại thư mục gốc:")
    files = os.listdir(base_path)
    found_db = False
    for f in files:
        if f == "database.db":
            found_db = True
            print(f"   [!] ĐÃ THẤY: {f} (Dung lượng: {os.path.getsize(os.path.join(base_path, f))} bytes)")
        else:
            print(f"   - {f}")
            
    if not found_db:
        print("\n[CẢNH BÁO] Không tìm thấy database.db tại thư mục gốc!")
    
    # 4. Kiểm tra logic mà hàm Backup đang dùng
    # Giả sử hàm backup dùng đường dẫn tương đối
    test_db_path = "database.db"
    print(f"\n4. Thử truy cập database bằng đường dẫn tương đối: {test_db_path}")
    print(f"   Kết quả: {'THÀNH CÔNG' if os.path.exists(test_db_path) else 'THẤT BẠI'}")

    print("=========================================")

if __name__ == "__main__":
    investigate()