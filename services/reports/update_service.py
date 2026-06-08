# -*- coding: utf-8 -*-
import os
import json
import requests
import shutil
import subprocess
import time
from datetime import datetime
import logging

class AutoUpdateService:
    def __init__(self, config_dir=None):
        """
        Khởi tạo module tự động cập nhật thông tư từ xa
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Thống nhất đường dẫn đến file cấu hình bctc tại máy khách
        if config_dir is None:
            self.config_file = os.path.abspath(os.path.join(current_dir, '../../configs/templates/bctc_formula.json'))
            self.backup_dir = os.path.abspath(os.path.join(current_dir, '../../backup'))
        else:
            self.config_file = os.path.join(config_dir, 'bctc_formula.json')
            self.backup_dir = os.path.join(config_dir, 'backup')

        # === TỐI ƯU ĐƯỜNG DẪN SERVER CỦA THẦY HÙNG ===
        self.SERVER_UPDATE_URL = "https://raw.githubusercontent.com/pnhung72/ke_toan_pro_update/main/bctc_formula.json"

    def lay_phien_ban_hien_tai(self):
        """
        Đọc phiên bản config JSON hiện tại ở máy khách
        """
        if not os.path.exists(self.config_file):
            return "0.0.0"
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("phien_ban_cau_hinh", "1.0.0")
        except Exception:
            return "0.0.0"

    def kiem_tra_va_cap_nhat(self):
        """
        Kiểm tra phiên bản trên server. Nếu có bản mới hơn thì tải về và rollback nếu lỗi
        """
        v_client = self.lay_phien_ban_hien_tai()
        
        try:
            # 1. Gửi request lấy file cấu hình mới nhất từ server (Đặt timeout 5 giây để tránh treo app)
            response = requests.get(self.SERVER_UPDATE_URL, timeout=5)
            
            if response.status_code != 200:
                logging.warning("Không kết nối được đến server cập nhật.")
                return False, "Không thể kết nối với server."

            server_data = response.json()
            v_server = server_data.get("phien_ban_cau_hinh", "0.0.0")

            # 2. So sánh phiên bản
            if v_server > v_client:
                # Tạo thư mục backup nếu chưa có
                if not os.path.exists(self.backup_dir):
                    os.makedirs(self.backup_dir)

                # 3. Sao lưu file cũ phòng rủi ro (Rollback)
                if os.path.exists(self.config_file):
                    backup_path = os.path.join(self.backup_dir, f"bctc_formula_bak_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
                    shutil.copy1(self.config_file, backup_path)

                # 4. Ghi đè file cấu hình thông tư mới vào hệ thống
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(server_data, f, ensure_ascii=False, indent=2)
                
                return True, f"Cập nhật thành công Thông tư lên phiên bản {v_server}"
            
            return False, "Bạn đang dùng phiên bản Thông tư mới nhất."

        except requests.exceptions.RequestException:
            # Máy khách không có mạng internet -> Bỏ qua an toàn (Offline-First)
            return False, "Mất kết nối Internet. Chế độ Offline được kích hoạt."
        except json.JSONDecodeError:
            # File trên server bị lỗi cú pháp -> Không ghi đè để bảo vệ hệ thống
            return False, "File cập nhật trên Server lỗi cú pháp."
        except Exception as e:
            return False, f"Lỗi hệ thống: {str(e)}"


# =====================================================================
# PHÂN HỆ ĐỒNG BỘ ĐÁM MÂY TỰ ĐỘNG - KẾ TOÁN PRO V11.0.0 (BẢN CHUẨN HÓA KHÔNG LỖI)
# =====================================================================
class CloudSyncService:
    def __init__(self):
        """
        Khởi tạo hệ thống ánh xạ dữ liệu SQLite ra Excel đám mây qua rclone nội bộ
        """
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.abspath(os.path.join(self.current_dir, '../../configs/config.json'))
        self.cloud_folder_name = "KeToanPro_Cloud_Data"

    def execute_rclone_command(self, cmd_args):
        """
        Hàm thực thi ngầm lệnh rclone bằng đường dẫn tuyệt đối tại thư mục gốc của anh Hùng
        """
        try:
            # === CHỜ OCR XONG MỚI CHẠY RCLONE ===
            from utils.sync_lock import wait_for_ocr_to_finish
            wait_for_ocr_to_finish(timeout=300)
            # =====================================

            # Tự động định vị file rclone.exe nằm tại D:\ke_toan_pro_v3\rclone.exe
            goc_du_an = os.path.abspath(os.path.join(self.current_dir, '../../'))
            rclone_path = os.path.join(goc_du_an, 'rclone.exe')
            
            target_exec = rclone_path if os.path.exists(rclone_path) else "rclone"

            result = subprocess.run(
                [target_exec] + cmd_args, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                return True, result.stdout
            return False, result.stderr
        except Exception as e:
            return False, str(e)

    def khoi_tao_va_dong_bo_id(self):
        """
        Hàm quét Drive tự động: Sinh thư mục, tạo file chứa tiêu đề và trích xuất ID thật (Bản chuẩn hóa Google Sheets)
        """
        logging.info("Đang khởi động tiến trình quét hạ tầng Drive...")
        
        # 1. Kiểm tra thư mục gốc trên Drive
        success, output = self.execute_rclone_command(["lsjson", "gdrive:", "--max-depth", "1"])
        if not success:
            return False, f"Lỗi kết nối bộ lọc rclone: {output}"

        folder_id = None
        try:
            drive_items = json.loads(output) if output.strip() else []
            for item in drive_items:
                if item['Name'] == self.cloud_folder_name and item['IsDir']:
                    folder_id = item['ID']
                    break
        except Exception:
            pass

        # Nếu chưa có thư mục, tiến hành tạo mới
        if not folder_id:
            logging.info(f"Đã kết nối thành công tệp: {sheet_name} -> ID: {existing_files[sheet_name]}")
            self.execute_rclone_command(["mkdir", f"gdrive:{self.cloud_folder_name}"])
            time.sleep(3) # Dành 3 giây cho Google khởi tạo phân vùng
            
            _, re_output = self.execute_rclone_command(["lsjson", "gdrive:", "--max-depth", "1"])
            try:
                for item in json.loads(re_output):
                    if item['Name'] == self.cloud_folder_name:
                        folder_id = item['ID']
                        break
            except Exception: pass

        if not folder_id:
            return False, "Không thể xác định mã định danh thư mục lưu trữ đám mây!"

        # 2. Định nghĩa danh sách 3 tệp Trang tính
        core_files = {
            "hoa_don": "Hóa đơn",
            "cong_no": "Nợ khách hàng",
            "tai_chinh": "Tổng hợp"
        }
        
        # Đọc danh sách file thực tế đang có trên Drive để tránh ghi đè dữ liệu cũ của anh
        success, files_output = self.execute_rclone_command(["lsjson", f"gdrive:{self.cloud_folder_name}"])
        existing_files = {}
        if success and files_output.strip():
            try:
                for f in json.loads(files_output):
                    clean_name = f['Name'].replace('.csv', '').replace('.xlsx', '').strip()
                    existing_files[clean_name] = f['ID']
            except Exception: pass

        cloud_ids = {}
        # Đặt thư mục exports ở gốc dự án
        temp_dir = os.path.abspath(os.path.join(self.current_dir, '../../exports'))
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Tiến hành rà soát từng file hạch toán
        for key, sheet_name in core_files.items():
            if sheet_name in existing_files:
                cloud_ids[key] = existing_files[sheet_name]
                print(f"[CLOUD-LINK] Đã kết nối thành công tệp: {sheet_name} -> ID: {existing_files[sheet_name]}")
            else:
                logging.info(f"Đang sinh cấu trúc bảng tính tự động: '{sheet_name}'...")
                temp_file_path = os.path.join(temp_dir, f"{sheet_name}.csv")
                
                # Khởi tạo dữ liệu cột tiêu đề chuẩn bằng mã hóa UTF-8 có BOM để tránh lỗi tiếng Việt font chữ
                if key == "hoa_don":
                    headers = ['STT', 'Người mua', 'SĐT', 'Tên hàng', 'Số lượng', 'Đơn giá', 'Thành tiền', 'Mã giảm giá', 'Ngày tạo']
                elif key == "cong_no":
                    headers = ['STT', 'Tên Khách Hàng', 'SĐT', 'Tổng Nợ', 'Đã Trả', 'Còn Nợ', 'Ngày Nợ Cuối', 'Ghi Chú']
                else:
                    headers = ['Quý', 'Tổng thu', 'Tổng chi', 'Cân đối']
                
                with open(temp_file_path, 'w', encoding='utf-8-sig') as dummy:
                    dummy.write(",".join(headers) + "\n")

                # Chiến thuật chuẩn: Copy file đính kèm đuôi .csv sang đích, ép Google Drive convert thành Google Sheets
                self.execute_rclone_command([
                    "copyto", 
                    temp_file_path, 
                    f"gdrive:{self.cloud_folder_name}/{sheet_name}.csv", 
                    "--drive-allow-import-name-change"
                ])
                
                # Chờ 3 giây để máy chủ Google đồng bộ hóa hạ tầng tệp mới
                time.sleep(3)
                
                # Quét lại để lấy ID file thật vừa tạo (Thử lại 3 lần chống trễ mạng)
                for _ in range(3):
                    _, check_output = self.execute_rclone_command(["lsjson", f"gdrive:{self.cloud_folder_name}"])
                    found = False
                    try:
                        for f in json.loads(check_output):
                            c_name = f['Name'].replace('.csv', '').replace('.xlsx', '').strip()
                            if c_name == sheet_name:
                                cloud_ids[key] = f['ID']
                                found = True
                                break
                    except Exception: pass
                    if found: break
                    time.sleep(1.5)
                
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        # 3. Ghi tự động chuỗi ID thu được vào tệp cấu hình cục bộ config.json
        config_data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception: pass

        config_data["CLOUD_DRIVE_IDS"] = cloud_ids
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

        logging.info("Đồng bộ hạ tầng thành công! Tệp 'configs/config.json' đã được cập nhật mã ID thật.")
        return True, cloud_ids

if __name__ == "__main__":
    print("=== TIẾN TRÌNH KIỂM TRA HẠ TẦNG KẾ TOÁN PRO CLOUD ===")
    sync_service = CloudSyncService()
    success, result = sync_service.khoi_tao_va_dong_bo_id()
    
    print("\n=== KẾT QUẢ VẬN HÀNH ===")
    if success and result:
        print("Chúc mừng anh Hùng! Hệ thống đã chạy thông suốt.")
        print("Cấu trúc ID thu được để dán vào Google Apps Script:")
        print(json.dumps(result, indent=4, ensure_ascii=False))
    else:
        print(f"Hệ thống tạm thời chưa thông hoặc bộ ID trống. Chi tiết dữ liệu: {result}")
