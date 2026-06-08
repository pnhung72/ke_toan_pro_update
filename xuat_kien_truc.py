# xuat_kien_truc.py
# CHUYEN XUAT KIEN TRUC PHAN MEM KE TOAN PRO V3

import os
import sqlite3
from datetime import datetime
from pathlib import Path

def export_architecture():
    base_path = r"D:\ke_toan_pro_v3"
    version = "3.1.0"
    
    # Đọc phiên bản từ file nếu có
    version_file = Path(base_path) / "version.txt"
    if version_file.exists():
        with open(version_file, 'r', encoding='utf-8') as vf:
            # Chỉ lấy dòng đầu tiên để làm tên file cho đúng quy định Windows
            version = vf.readline().strip()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"D:\\KienTrucPhanMem_{version}_{timestamp}.txt")
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        out_f.write("=" * 60 + "\n")
        out_f.write(f"KIEN TRUC PHAN MEM KE TOAN PRO v{version}\n")
        out_f.write(f"Ngay xuat: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        out_f.write("=" * 60 + "\n\n")
        
        # 1. CẤU TRÚC THƯ MỤC
        out_f.write("[1. Cau truc thu muc]\n")
        out_f.write("-" * 40 + "\n")
        for root, dirs, files in os.walk(base_path):
            # Bỏ qua thư mục __pycache__, build, dist
            dirs[:] = [d for d in dirs if d not in ["__pycache__", "build", "dist"]]
            level = root.replace(base_path, "").count(os.sep)
            indent = " " * 2 * level
            folder_name = os.path.basename(root)
            if level > 0:
                out_f.write(f"{indent}+---{folder_name}\n")
        
        # 2. THỐNG KÊ FILE PYTHON
        out_f.write("\n[2. Thong ke file Python]\n")
        out_f.write("-" * 40 + "\n")
        py_files = list(Path(base_path).rglob("*.py"))
        py_files = [p for p in py_files if "__pycache__" not in str(p) and "build" not in str(p) and "dist" not in str(p)]
        out_f.write(f"Tong so file .py: {len(py_files)}\n")
        
        total_size = sum(p.stat().st_size for p in py_files)
        out_f.write(f"Tong dung luong file .py: {total_size / 1024:.2f} KB\n")
        
        # 3. CÁC MODULE CHÍNH
        out_f.write("\n[3. Cac module chinh]\n")
        out_f.write("-" * 40 + "\n")
        modules = ["core", "models", "views", "controllers", "services", "utils", "ui", "reports"]
        for mod in modules:
            mod_path = Path(base_path) / mod
            if mod_path.exists():
                count = len(list(mod_path.glob("*.py")))
                out_f.write(f"\n  {mod.upper()}: {count} file\n")
        
        # 4. CẤU TRÚC DATABASE
        out_f.write("\n[4. Cau truc Database]\n")
        out_f.write("-" * 40 + "\n")
        db_path = Path(base_path) / "ke_toan_data" / "ke_toan.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = cursor.fetchall()
                out_f.write(f"Tong so bang: {len(tables)}\n\n")
                for table in tables:
                    out_f.write(f"  - {table[0]}\n")
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM '{table[0]}'")
                        count = cursor.fetchone()[0]
                        out_f.write(f"      (so dong: {count})\n")
                    except:
                        pass
                conn.close()
            except Exception as e:
                out_f.write(f"  Loi doc database: {e}\n")
        else:
            out_f.write(f"  Khong tim thay database tai: {db_path}\n")
        
        # 5. FILE CẤU HÌNH
        out_f.write("\n[5. File cau hinh]\n")
        out_f.write("-" * 40 + "\n")
        config_extensions = [".json", ".config", ".txt", ".md", ".ini"]
        for ext in config_extensions:
            config_files = list(Path(base_path).glob(f"*{ext}"))
            for cfg in config_files:
                out_f.write(f"  - {cfg.name}\n")
        
        # 6. TÍNH NĂNG PHÁT HIỆN
        out_f.write("\n[6. Tinh nang phat hien tu code]\n")
        out_f.write("-" * 40 + "\n")
        
        security_path = Path(base_path) / "core" / "security"
        if security_path.exists():
            out_f.write("  ✓ Bao mat: Co (audit log, phan quyen, ma hoa)\n")
        
        reports_path = Path(base_path) / "reports"
        if reports_path.exists():
            out_f.write("  ✓ Bao cao tai chinh: Co (Thong tu 99/2025)\n")
        
        export_path = Path(base_path) / "services" / "export_service.py"
        if export_path.exists():
            out_f.write("  ✓ Xuat Excel: Co\n")
        
        license_path = Path(base_path) / "utils" / "license_manager.py"
        if license_path.exists():
            out_f.write("  ✓ Quan ly license: Co\n")
        
        rclone_path = Path(base_path) / "rclone.exe"
        if rclone_path.exists():
            out_f.write("  ✓ Sao luu dong bo: Co (rclone)\n")
        
        font_path = Path(base_path) / "core" / "font_manager.py"
        if font_path.exists():
            out_f.write("  ✓ Font toan cuc: Co\n")
        
        # 7. THỐNG KÊ TỔNG HỢP
        out_f.write("\n[7. Thong ke tong hop]\n")
        out_f.write("-" * 40 + "\n")
        
        total_dirs = 0
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in ["__pycache__", "build", "dist"]]
            total_dirs += len(dirs)
        out_f.write(f"So thu muc: {total_dirs}\n")
        
        all_files = list(Path(base_path).rglob("*"))
        all_files = [f for f in all_files if f.is_file() and "__pycache__" not in str(f) and "build" not in str(f) and "dist" not in str(f)]
        total_size_bytes = sum(f.stat().st_size for f in all_files)
        total_size_mb = total_size_bytes / (1024 * 1024)
        out_f.write(f"Tong dung luong du an: {total_size_mb:.2f} MB\n")
        
        # 8. DEPENDENCIES
        out_f.write("\n[8. Dependencies (requirements.txt)]\n")
        out_f.write("-" * 40 + "\n")
        req_path = Path(base_path) / "requirements.txt"
        if req_path.exists():
            with open(req_path, 'r', encoding='utf-8') as req:
                for line in req:
                    if line.strip() and not line.startswith("#"):
                        out_f.write(f"  - {line.strip()}\n")
        else:
            out_f.write("  Khong tim thay requirements.txt\n")
        
        out_f.write("\n" + "=" * 60 + "\n")
        out_f.write("HOAN TAT XUAT KIEN TRUC\n")
        out_f.write("=" * 60 + "\n")
    
    print(f"\n✅ DA XUAT THANH CONG!")
    print(f"📄 File: {output_file}")
    print(f"📏 Dung luong: {output_file.stat().st_size / 1024:.2f} KB")
    return str(output_file)

def print_quick_summary():
    """In tóm tắt nhanh ra màn hình"""
    base_path = r"D:\ke_toan_pro_v3"
    print("\n" + "=" * 50)
    print("TOM TAT NHANH PHAN MEM KE TOAN PRO")
    print("=" * 50)
    
    py_files = list(Path(base_path).rglob("*.py"))
    py_files = [p for p in py_files if "__pycache__" not in str(p)]
    print(f"  File Python: {len(py_files)}")
    
    modules = ["core", "models", "views", "controllers", "services", "utils", "ui", "reports"]
    for mod in modules:
        mod_path = Path(base_path) / mod
        if mod_path.exists():
            count = len(list(mod_path.glob("*.py")))
            print(f"  {mod}: {count} file")
    
    db_path = Path(base_path) / "ke_toan_data" / "ke_toan.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"  Database: {size_mb:.2f} MB")
    
    print("=" * 50)

if __name__ == "__main__":
    print_quick_summary()
    export_architecture()
