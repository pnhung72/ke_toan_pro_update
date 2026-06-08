import os
import zipfile
import glob
from datetime import datetime

def smart_backup(db_path, backup_dir="backups"):
    # 1. Tạo thư mục backup nếu chưa có
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # 2. Tạo tên file theo thời gian
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = os.path.join(backup_dir, f"backup_{timestamp}.zip")

    # 3. Nén file database vào zip
    with zipfile.ZipFile(backup_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(db_path, os.path.basename(db_path))

    # 4. Cơ chế vòng xoáy: Chỉ giữ lại 5 bản gần nhất
    files = sorted(glob.glob(os.path.join(backup_dir, "backup_*.zip")), key=os.path.getmtime)
    if len(files) > 5:
        for file_to_delete in files[:-5]: # Xóa các file cũ hơn 5 file gần nhất
            os.remove(file_to_delete)