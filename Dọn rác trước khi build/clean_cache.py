import os
import shutil

def delete_pycache(root_dir):
    """Xóa tất cả thư mục __pycache__"""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            cache_path = os.path.join(dirpath, '__pycache__')
            print(f"Đang xóa: {cache_path}")
            shutil.rmtree(cache_path)
            count += 1
    print(f"✅ Đã xóa {count} thư mục __pycache__")

def delete_pycs(root_dir):
    """Xóa tất cả file .pyc"""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(dirpath, file)
                print(f"Đang xóa: {pyc_path}")
                os.remove(pyc_path)
                count += 1
    print(f"✅ Đã xóa {count} file .pyc")

if __name__ == "__main__":
    print("=== DỌN DẸP CACHE PYTHON ===")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    delete_pycache(current_dir)
    delete_pycs(current_dir)
    print("=== HOÀN TẤT ===")