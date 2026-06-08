import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import logging

def upload_to_drive(file_path):
    """
    Tự động đẩy file lên Google Drive cá nhân của anh Hùng.
    Dùng Client ID anh đã đăng ký.
    """
    try:
        gauth = GoogleAuth()
        
        # Tự động tìm file client_secrets.json trong thư mục gốc
        # Anh cần tải file json từ Google Console về và đổi tên thành client_secrets.json
        gauth.LocalWebserverAuth() 

        drive = GoogleDrive(gauth)

        # Lấy tên file từ đường dẫn cục bộ
        file_name = os.path.basename(file_path)

        # Khởi tạo file trên Drive
        folder_id = "" # Nếu anh muốn cho vào thư mục riêng thì điền ID vào đây
        file_metadata = {'title': file_name}
        if folder_id:
            file_metadata['parents'] = [{'id': folder_id}]

        file_drive = drive.CreateFile(file_metadata)
        file_drive.SetContentFile(file_path)
        file_drive.Upload()
        
        logging.info(f"Đã sao lưu thành công lên Đám mây: {file_name}")
        return True
    except Exception as e:
        logging.error(f"Lỗi sao lưu đám mây: {e}")
        return False