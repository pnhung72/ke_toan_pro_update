import os

def find_file_in_project(project_dir, file_name):
    print("======================================================================")
    # Tìm kiếm chính xác vị trí file trong dự án Kế Toán Pro
    print(f"🔍 ĐANG TRUY QUÉT TỰ ĐỘNG FILE '{file_name}'...")
    print("======================================================================")
    
    found_paths = []
    
    # Quét qua toàn bộ cây thư mục
    for root, dirs, files in os.walk(project_dir):
        if file_name in files:
            full_path = os.path.join(root, file_name)
            found_paths.append(full_path)
            
    if found_paths:
        print(f"\n🎉 THÀNH CÔNG! ĐÃ TÌM THẤY {len(found_paths)} VỊ TRÍ:")
        for i, path in enumerate(found_paths, 1):
            print(f" 👉 Vị trí {i}: {path}")
            
        print("\n💡 HƯỚNG DẪN DÀNH CHO THẦY:")
        print("Thầy chỉ cần copy đúng đường dẫn ở trên, dán vào thanh địa chỉ của File Explorer")
        print("hoặc mở trực tiếp bằng phần mềm viết code (VS Code) để sửa dòng 12 nhé!")
    else:
        print(f"\n❌ Không tìm thấy file nào có tên chính xác là '{file_name}'.")
        print("Có thể file đang viết hoa viết thường khác nhau. Để em quét thử tên gần giống...")
        
        # Quét không phân biệt hoa thường để dự phòng
        for root, dirs, files in os.walk(project_dir):
            for f in files:
                if file_name.lower() in f.lower():
                    print(f" ❓ Có phải file này không Thầy: {os.path.join(root, f)}")

    print("======================================================================")

# Chạy lệnh quét trên thư mục gốc dự án của Thầy
project_directory = r"D:\ke_toan_pro_v3"
target_file = "admin_dashboard.py"

find_file_in_project(project_directory, target_file)