# core/cloud_thread.py
"""
Quản lý đồng bộ dữ liệu lên Google Drive
ĐÃ CẢI TIẾN:
- Tách biệt logic NÉN (Backup) và TRUYỀN TẢI (Upload)
- Xử lý lỗi mạng, thử lại khi thất bại
- Tăng timeout cho file lớn (cấu hình được)
- Callback cập nhật giao diện (progress, thông báo)
- Dọn dẹp backup cũ sau khi upload thành công
"""

import os
import sys
import time
import threading
import subprocess
import shutil
import sqlite3
import csv
import urllib.request
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
import logging

# Đảm bảo có thể import config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.logger import get_logger
from utils.backup import auto_backup, test_backup_integrity, clean_old_backups, BACKUP_DIR

logger = get_logger(__name__)

# Cấu hình
MAX_RETRIES = 3
RETRY_DELAY = 30  # giây
UPLOAD_TIMEOUT = 600  # 10 phút (cho file lớn)
CLOUD_SYNC_INTERVAL = 3600  # 1 giờ
RCLONE_PATH = os.path.join(BASE_DIR, "rclone.exe")
CLOUD_DIR_NAME = "KeToanPro_Cloud_Data"

# Thư mục data thật (dist\ke_toan_data)
DATA_DIR = Path(BASE_DIR) / "ke_toan_data"

# URL Apps Script — dán URL deploy của bạn vào đây
APPS_SCRIPT_URL = "https://script.google.com/macros/s/THAY_BANG_URL_THAT/exec"


class CloudSyncService:
    """Dịch vụ đồng bộ dữ liệu lên Google Drive"""
    
    def __init__(self, rclone_path=RCLONE_PATH, upload_timeout=UPLOAD_TIMEOUT):
        self.rclone_path = rclone_path
        self.upload_timeout = upload_timeout
        self.is_syncing = False
        self.last_sync_time = 0
        self.last_sync_status = None
        self._stop_flag = False
        self._progress_callback = None
        self._status_callback = None
        self._current_progress = 0
    
    def set_callbacks(self, progress_callback: Optional[Callable] = None, 
                      status_callback: Optional[Callable] = None):
        """
        Đặt callback để cập nhật giao diện
        
        Args:
            progress_callback: Hàm nhận giá trị progress (0-100)
            status_callback: Hàm nhận thông báo trạng thái
        """
        self._progress_callback = progress_callback
        self._status_callback = status_callback
    
    def _update_progress(self, value: int):
        """Cập nhật progress (gọi callback nếu có)"""
        self._current_progress = value
        if self._progress_callback:
            try:
                self._progress_callback(value)
            except Exception as e:
                logger.warning(f"Lỗi progress callback: {e}")
    
    def _update_status(self, message: str, is_error: bool = False):
        """Cập nhật trạng thái (gọi callback nếu có)"""
        if self._status_callback:
            try:
                self._status_callback(message, is_error)
            except Exception as e:
                logger.warning(f"Lỗi status callback: {e}")
        
        if is_error:
            logger.error(message)
        else:
            logger.info(message)
    
    def check_rclone(self):
        """Kiểm tra rclone có sẵn sàng không"""
        if not os.path.exists(self.rclone_path):
            self._update_status(f"Không tìm thấy rclone tại: {self.rclone_path}", True)
            return False
        
        try:
            result = subprocess.run(
                [self.rclone_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.splitlines()[0] if result.stdout else "unknown"
                logger.debug(f"rclone version: {version}")
                return True
            else:
                self._update_status(f"rclone lỗi: {result.stderr}", True)
                return False
        except Exception as e:
            logger.error(f"Lỗi kiểm tra rclone: {e}")
            return False
    
    def check_network(self):
        """Kiểm tra kết nối mạng (ping Google)"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            self._update_status("Không có kết nối mạng", True)
            return False
    
    def get_file_size_mb(self, file_path):
        """Lấy kích thước file (MB)"""
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except Exception:
            return 0
    
    def create_backup(self):
        """
        Bước 1: TẠO BACKUP (nén dữ liệu)
        Trả về đường dẫn file backup hoặc None
        """
        try:
            self._update_status("Đang tạo backup dữ liệu...")
            self._update_progress(10)
            
            backup_path = auto_backup()
            
            if backup_path and os.path.exists(backup_path):
                self._update_progress(40)
                
                # Kiểm tra integrity
                self._update_status("Đang kiểm tra tính toàn vẹn backup...")
                if test_backup_integrity(backup_path):
                    size_mb = self.get_file_size_mb(backup_path)
                    self._update_status(f"Tạo backup thành công: {os.path.basename(backup_path)} ({size_mb:.1f} MB)")
                    self._update_progress(50)
                    return backup_path
                else:
                    self._update_status("Backup bị hỏng, không thể upload", True)
                    return None
            else:
                self._update_status("Tạo backup thất bại", True)
                return None
                
        except Exception as e:
            self._update_status(f"Lỗi tạo backup: {e}", True)
            logger.error(f"Lỗi tạo backup: {e}")
            return None
    
    def upload_file(self, file_path, remote_name=None):
        """
        Bước 2: TRUYỀN TẢI (upload lên Drive)
        
        Args:
            file_path: Đường dẫn file cần upload
            remote_name: Tên file trên Drive (mặc định: dùng tên gốc)
        """
        if not self.check_rclone():
            return False
        
        if not self.check_network():
            return False
        
        if remote_name is None:
            remote_name = os.path.basename(file_path)
        
        remote_path = f"gdrive:{CLOUD_DIR_NAME}/{remote_name}"
        
        # Tính toán thời gian ước lượng
        file_size_mb = self.get_file_size_mb(file_path)
        estimated_time = int(file_size_mb / 5)  # Giả sử 5 MB/giây
        estimated_time = max(30, min(estimated_time, 600))  # Giữa 30s và 600s
        
        self._update_status(f"Đang upload {remote_name} ({file_size_mb:.1f} MB)...")
        self._update_status(f"Thời gian ước lượng: {estimated_time} giây")
        self._update_progress(60)
        
        for attempt in range(MAX_RETRIES):
            try:
                self._update_status(f"Upload lần {attempt + 1}/{MAX_RETRIES}...")
                
                # Sử dụng timeout động dựa trên kích thước file
                timeout = max(self.upload_timeout, int(file_size_mb / 2))
                
                result = subprocess.run(
                    [self.rclone_path, "copyto", file_path, remote_path,
                     "--drive-allow-import-name-change", "--progress"],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    self._update_status(f"Upload thành công: {remote_name}")
                    self._update_progress(90)
                    return True
                else:
                    error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                    self._update_status(f"Upload thất bại (lần {attempt + 1}): {error_msg}", True)
                    logger.error(f"Upload thất bại: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self._update_status(f"Upload timeout sau {timeout} giây (lần {attempt + 1})", True)
                logger.error(f"Upload timeout: {file_path}")
            except Exception as e:
                self._update_status(f"Lỗi upload (lần {attempt + 1}): {e}", True)
                logger.error(f"Lỗi upload: {e}")
            
            if attempt < MAX_RETRIES - 1:
                self._update_status(f"Chờ {RETRY_DELAY} giây trước khi thử lại...")
                time.sleep(RETRY_DELAY)
        
        return False
    
    def cleanup_old_backups(self):
        """
        Dọn dẹp backup cũ sau khi upload thành công
        Giữ lại MAX_BACKUPS bản gần nhất
        """
        try:
            self._update_status("Đang dọn dẹp backup cũ...")
            clean_old_backups()
            self._update_status("Đã dọn dẹp backup cũ")
            logger.info("Dọn dẹp backup cũ sau upload thành công")
        except Exception as e:
            logger.warning(f"Lỗi dọn dẹp backup cũ: {e}")
    
    def xuat_csv(self):
        """
        Xuất toàn bộ dữ liệu từ ke_toan.db ra các file CSV.
        Đây là bước BẮT BUỘC trước khi upload lên Drive.
        """
        db_path = DATA_DIR / "ke_toan.db"
        if not db_path.exists():
            self._update_status(f"Không tìm thấy database: {db_path}", True)
            return False

        try:
            conn = sqlite3.connect(db_path)
            cur  = conn.cursor()

            # --- hoa_don.csv ---
            cur.execute("""
                SELECT id,
                       buyer_name    AS "Người mua",
                       phone         AS "SĐT",
                       address       AS "Địa chỉ",
                       product_name  AS "Sản phẩm",
                       quantity      AS "Số lượng",
                       unit_price    AS "Đơn giá",
                       total_payment AS "Thành tiền",
                       sale_source   AS "Nguồn đơn",
                       created_date  AS "Ngày tạo"
                FROM invoices ORDER BY id ASC
            """)
            self._ghi_csv(cur, DATA_DIR / "Hóa đơn.csv")

            # --- Nợ khách hàng.csv ---
            cur.execute("""
                SELECT id,
                       buyer_name                 AS "Khách hàng",
                       phone                      AS "SĐT",
                       total_payment              AS "Tổng tiền",
                       paid                       AS "Đã thanh toán",
                       (total_payment - paid)     AS "Còn nợ",
                       payment_method             AS "Hình thức TT",
                       created_date               AS "Ngày tạo"
                FROM invoices
                WHERE (total_payment - paid) > 0
                ORDER BY id ASC
            """)
            self._ghi_csv(cur, DATA_DIR / "Nợ khách hàng.csv")

            # --- Tổng hợp.csv (tổng hợp theo tháng) ---
            cur.execute("""
                SELECT substr(created_date,1,7)  AS "Tháng",
                       COUNT(*)                  AS "Số hóa đơn",
                       SUM(total_payment)        AS "Doanh thu",
                       SUM(paid)                 AS "Đã thu",
                       SUM(total_payment - paid) AS "Còn nợ"
                FROM invoices
                GROUP BY substr(created_date,1,7)
                ORDER BY 1 ASC
            """)
            self._ghi_csv(cur, DATA_DIR / "Tổng hợp.csv")

            conn.close()
            self._update_status("Xuất CSV hoàn tất (Hóa đơn, Nợ khách hàng, Tổng hợp)")
            return True

        except Exception as e:
            self._update_status(f"Lỗi xuất CSV: {e}", True)
            logger.error(f"Lỗi xuất CSV: {e}")
            return False

    def _ghi_csv(self, cursor, csv_path: Path):
        """Ghi kết quả query ra file CSV UTF-8"""
        rows    = cursor.fetchall()
        headers = [d[0] for d in cursor.description]
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        self._update_status(f"  → {csv_path.name}: {len(rows)} dòng")

    def goi_apps_script_sync(self):
        """Gọi Apps Script để đồng bộ CSV trên Drive vào Google Sheets"""
        if "THAY_BANG_URL_THAT" in APPS_SCRIPT_URL:
            self._update_status("⚠ Chưa cấu hình APPS_SCRIPT_URL, bỏ qua bước sync Sheets")
            return
        try:
            url = f"{APPS_SCRIPT_URL}?action=sync_all"
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read().decode())
                if data.get("status") == "success":
                    self._update_status("Google Sheets đã được cập nhật")
                else:
                    self._update_status(f"Apps Script trả về: {data}", True)
        except Exception as e:
            self._update_status(f"Lỗi gọi Apps Script: {e}", True)
            logger.warning(f"Apps Script lỗi (không chặn sync): {e}")

    def sync_data(self):
        """
        Đồng bộ dữ liệu: Backup + Upload
        Trả về True nếu thành công, False nếu thất bại
        """
        if self.is_syncing:
            self._update_status("Đồng bộ đang chạy, vui lòng chờ...", True)
            return False
        
        self.is_syncing = True
        self.last_sync_time = time.time()
        self._update_progress(0)
        
        try:
            # Bước 1: Xuất CSV từ database (MỚI — đây là bước còn thiếu)
            self._update_status("Bước 1/4: Xuất dữ liệu ra CSV...")
            self._update_progress(5)
            if not self.xuat_csv():
                self.last_sync_status = "csv_export_failed"
                self._update_progress(0)
                return False
            self._update_progress(20)

            # Bước 2: Tạo backup DB
            self._update_status("Bước 2/4: Tạo backup database...")
            backup_file = self.create_backup()
            if not backup_file:
                self.last_sync_status = "backup_failed"
                self._update_status("Đồng bộ thất bại ở bước tạo backup", True)
                self._update_progress(0)
                return False

            # Bước 3: Upload CSV + backup lên Drive
            self._update_status("Bước 3/4: Upload lên Google Drive...")
            csv_files = ["hoa_don.csv", "no_khach_hang.csv", "giao_dich.csv"]
            for csv_name in csv_files:
                csv_path = DATA_DIR / csv_name
                if csv_path.exists():
                    ok = self.upload_file(str(csv_path), csv_name)
                    if not ok:
                        self.last_sync_status = "upload_failed"
                        self._update_status(f"Upload thất bại: {csv_name}", True)
                        self._update_progress(0)
                        return False

            success = self.upload_file(backup_file)

            if success:
                self.last_sync_status = "success"
                self._update_progress(95)

                # Bước 4: Cập nhật Google Sheets qua Apps Script
                self._update_status("Bước 4/4: Cập nhật Google Sheets...")
                self.goi_apps_script_sync()

                self._update_status("✅ Đồng bộ dữ liệu hoàn tất!")
                self._update_progress(100)
                logger.info("Đồng bộ thành công")
            else:
                self.last_sync_status = "upload_failed"
                self._update_status("Đồng bộ thất bại ở bước upload", True)
                self._update_progress(0)

            return success
            
        except Exception as e:
            self.last_sync_status = "error"
            self._update_status(f"Lỗi đồng bộ: {e}", True)
            logger.error(f"Lỗi đồng bộ: {e}")
            self._update_progress(0)
            return False
        finally:
            self.is_syncing = False
    
    def sync_if_needed(self, force=False):
        """
        Đồng bộ nếu cần (kiểm tra thời gian)
        
        Args:
            force: Bỏ qua kiểm tra thời gian, đồng bộ ngay
        """
        if force:
            self._update_status("Đồng bộ theo yêu cầu...")
            return self.sync_data()
        
        # Kiểm tra thời gian
        elapsed = time.time() - self.last_sync_time
        if elapsed >= CLOUD_SYNC_INTERVAL:
            self._update_status(f"Đã qua {elapsed/3600:.1f} giờ, bắt đầu đồng bộ tự động...")
            return self.sync_data()
        
        logger.debug(f"Chưa đến giờ đồng bộ (còn {int((CLOUD_SYNC_INTERVAL - elapsed)/60)} phút)")
        return None
    
    def get_status(self):
        """Lấy trạng thái đồng bộ"""
        return {
            'is_syncing': self.is_syncing,
            'last_sync_time': self.last_sync_time,
            'last_sync_status': self.last_sync_status,
            'rclone_available': self.check_rclone(),
            'network_available': self.check_network(),
            'current_progress': self._current_progress,
            'last_sync_time_str': datetime.fromtimestamp(self.last_sync_time).strftime("%Y-%m-%d %H:%M:%S") if self.last_sync_time else "Chưa đồng bộ"
        }
    
    def stop(self):
        """Dừng đồng bộ"""
        self._stop_flag = True
        self._update_status("Đã yêu cầu dừng đồng bộ")
        logger.info("Đã yêu cầu dừng đồng bộ")


# Singleton instance
_cloud_sync_service = None


def get_cloud_sync_service() -> CloudSyncService:
    """Lấy instance của CloudSyncService (singleton)"""
    global _cloud_sync_service
    if _cloud_sync_service is None:
        _cloud_sync_service = CloudSyncService()
    return _cloud_sync_service


def sync_now(callbacks: tuple = None) -> bool:
    """
    Đồng bộ ngay lập tức (gọi từ giao diện)
    
    Args:
        callbacks: (progress_callback, status_callback) để cập nhật UI
    """
    service = get_cloud_sync_service()
    if callbacks:
        progress_cb, status_cb = callbacks
        service.set_callbacks(progress_cb, status_cb)
    return service.sync_data()


def get_sync_status() -> dict:
    """Lấy trạng thái đồng bộ (gọi từ giao diện)"""
    service = get_cloud_sync_service()
    return service.get_status()


# ============================================================
# KIỂM TRA VÀ TEST
# ============================================================

def test_with_ui():
    """Test với UI giả lập (in ra console)"""
    
    def progress_cb(value):
        logging.info(f"[PROGRESS] {value}%")
    
    def status_cb(message, is_error):
        prefix = "❌" if is_error else "✅"
        logging.info(f"[STATUS] {prefix} {message}")
    
    print("=" * 60)
    print("   TEST ĐỒNG BỘ CLOUD (CÓ UI GIẢ LẬP)")
    print("=" * 60)
    
    success = sync_now(callbacks=(progress_cb, status_cb))
    
    print("\n" + "=" * 60)
    if success:
        print("   🎉 TEST THÀNH CÔNG!")
    else:
        print("   ❌ TEST THẤT BẠI!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Công cụ đồng bộ cloud Kế Toán Pro')
    parser.add_argument('command', 
                        choices=['sync', 'status', 'test', 'cleanup'],
                        default='status', nargs='?',
                        help='Lệnh thực hiện')
    args = parser.parse_args()
    
    print("=" * 60)
    print("   CÔNG CỤ ĐỒNG BỘ CLOUD - KẾ TOÁN PRO")
    print("=" * 60)
    
    service = get_cloud_sync_service()
    
    if args.command == 'sync':
        success = sync_now()
        if success:
            print("\n✅ Đồng bộ thành công!")
        else:
            print("\n❌ Đồng bộ thất bại!")
            
    elif args.command == 'status':
        status = get_sync_status()
        print(f"\n📊 TRẠNG THÁI ĐỒNG BỘ:")
        print(f"   - Đang đồng bộ: {'Có' if status['is_syncing'] else 'Không'}")
        print(f"   - Lần đồng bộ cuối: {status['last_sync_time_str']}")
        print(f"   - Trạng thái cuối: {status['last_sync_status'] or 'Chưa có'}")
        print(f"   - Tiến trình hiện tại: {status['current_progress']}%")
        print(f"   - rclone: {'✅ Sẵn sàng' if status['rclone_available'] else '❌ Không tìm thấy'}")
        print(f"   - Mạng: {'✅ Kết nối' if status['network_available'] else '❌ Mất kết nối'}")
        
    elif args.command == 'test':
        test_with_ui()
        
    elif args.command == 'cleanup':
        print("\n🧹 Đang dọn dẹp backup cũ...")
        clean_old_backups()
        print("✅ Đã dọn dẹp backup cũ (giữ lại 5 bản gần nhất)")