import threading
import time
import os
import json
from datetime import datetime
from services.reports.update_service import CloudSyncService
from utils.sync_lock import wait_for_ocr_to_finish
import logging

class BackgroundSyncManager:
    def __init__(self, interval_minutes=15, backup_interval_minutes=30):
        """
        interval_minutes      : Chu kỳ đồng bộ cấu trúc Drive (mặc định 15 phút)
        backup_interval_minutes: Chu kỳ backup dữ liệu thật lên Drive (mặc định 30 phút)
        """
        self.sync_service = CloudSyncService()
        self.interval_seconds = interval_minutes * 60
        self.backup_interval_seconds = backup_interval_minutes * 60
        self.is_running = False
        self.sync_thread = None
        self.backup_thread = None
        self.status_message = "Hệ thống Cloud: Sẵn sàng"

    # ============================================================
    # LUỒNG 1: Đồng bộ cấu trúc Drive (15 phút/lần) - GIỮ NGUYÊN
    # ============================================================
    def _loop_dong_bo_ngam(self):
        logging.info("Đã kích hoạt luồng đồng bộ cấu trúc Drive...")
        while self.is_running:
            try:
                wait_for_ocr_to_finish(timeout=300)
                self.status_message = "Đang đồng bộ ngầm..."
                success, data = self.sync_service.khoi_tao_va_dong_bo_id()
                if success:
                    self.status_message = f"Đồng bộ OK ({datetime.now().strftime('%H:%M')})"
                    logging.info("Đồng bộ cấu trúc Drive thành công.")
                else:
                    self.status_message = "Lỗi đồng bộ Cloud"
                    logging.error("Thất bại, thử lại sau.")
            except Exception as e:
                self.status_message = "Sự cố kết nối"
                logging.info(f"Luồng ngầm gặp sự cố: {str(e)}")
            time.sleep(self.interval_seconds)

    # ============================================================
    # LUỒNG 2: Backup dữ liệu thật lên Drive (30 phút/lần) - MỚI
    # ============================================================
    def _loop_backup_dinh_ky(self):
        logging.info("Đã kích hoạt luồng backup định kỳ (30 phút/lần)...")
        
        # Chờ 2 phút sau khi app khởi động mới bắt đầu backup lần đầu
        time.sleep(120)
        
        while self.is_running:
            try:
                # Chờ OCR xong mới backup
                wait_for_ocr_to_finish(timeout=300)
                
                logging.info("Đang backup dữ liệu thật lên Drive...")
                
                # Bước 1: Tạo file ZIP backup cục bộ
                from utils.backup import auto_backup
                backup_path = auto_backup()
                
                if backup_path:
                    # Bước 2: Upload ZIP lên Google Drive
                    try:
                        from utils.cloud_backup import upload_to_drive
                        success = upload_to_drive(str(backup_path))
                        if success:
                            self.status_message = f"Backup Cloud OK ({datetime.now().strftime('%H:%M')})"
                            logging.info("Backup dữ liệu thật lên Drive thành công!")
                        else:
                            logging.warning("Upload Drive thất bại, đã có backup cục bộ.")
                    except ImportError:
                        logging.warning("Chưa cài cloud_backup, chỉ backup cục bộ.")
                    except Exception as e:
                        logging.warning(f"Lỗi upload Drive: {e}")
                else:
                    logging.error("Tạo file backup thất bại!")
                    
            except Exception as e:
                logging.error(f"Lỗi backup định kỳ: {e}")
            
            time.sleep(self.backup_interval_seconds)

    # ============================================================
    # KHỞI ĐỘNG / DỪNG
    # ============================================================
    def start_auto_sync(self):
        """Khởi động cả 2 luồng: đồng bộ cấu trúc + backup định kỳ"""
        if not self.is_running:
            self.is_running = True
            
            # Luồng 1: Đồng bộ cấu trúc Drive
            self.sync_thread = threading.Thread(
                target=self._loop_dong_bo_ngam, daemon=True)
            self.sync_thread.start()
            
            # Luồng 2: Backup dữ liệu thật
            self.backup_thread = threading.Thread(
                target=self._loop_backup_dinh_ky, daemon=True)
            self.backup_thread.start()
            
            logging.info("Đã khởi động: Đồng bộ 15 phút + Backup 30 phút")

    def stop_auto_sync(self):
        """Dừng tất cả luồng"""
        self.is_running = False

    # ============================================================
    # ĐỒNG BỘ THỦ CÔNG (nút bấm trên giao diện)
    # ============================================================
    def click_dong_bo_thu_cong(self, callback_ui=None):
        """Bấm nút Đồng bộ: chạy cả cấu trúc Drive + backup ngay lập tức"""
        def run_manual():
            logging.info("Đồng bộ thủ công...")
            wait_for_ocr_to_finish(timeout=300)
            
            if callback_ui:
                callback_ui("Đang đồng bộ...")

            # Đồng bộ cấu trúc
            success, data = self.sync_service.khoi_tao_va_dong_bo_id()

            # Backup dữ liệu thật
            try:
                from utils.backup import auto_backup
                from utils.cloud_backup import upload_to_drive
                backup_path = auto_backup()
                if backup_path:
                    upload_to_drive(str(backup_path))
            except Exception as e:
                logging.error(f"Lỗi backup thủ công: {e}")

            if success:
                msg = f"Đồng bộ + Backup xong! ({datetime.now().strftime('%H:%M:%S')})"
                logging.info("Thành công!")
            else:
                msg = "Đồng bộ thất bại!"
                
            if callback_ui:
                callback_ui(msg)

        threading.Thread(target=run_manual, daemon=True).start()