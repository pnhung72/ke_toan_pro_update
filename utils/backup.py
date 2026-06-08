# -*- coding: utf-8 -*-
"""
Hệ thống sao lưu dữ liệu - Phiên bản Bảo toàn Tính năng & Sửa lỗi triệt để
ĐÃ CẢI TIẾN: 
- Kiểm tra tính toàn vẹn backup và database
- Xử lý Database is locked (checkpoint)
- Logging thay vì print
- Backup ngay khi khởi động nếu đã quá 24h kể từ lần cuối
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
import zipfile
import threading
import time
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger
import logging
# Khởi tạo logger
logger = get_logger(__name__)

# --- PHẦN 1: ĐỒNG BỘ ĐƯỜNG DẪN (SỬA LỖI IMPORT & EXE) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from config import BACKUP_DIR as config_BACKUP_DIR, REAL_DATA_DIR
    BACKUP_DIR = Path(config_BACKUP_DIR)
    DATA_DIR = Path(REAL_DATA_DIR)
except ImportError:
    BACKUP_DIR = Path(os.path.join(BASE_DIR, "backup"))
    DATA_DIR = Path(os.path.join(BASE_DIR, "ke_toan_data"))

MAX_BACKUPS = 5
BACKUP_STATE_FILE = os.path.join(BASE_DIR, "configs", "backup_state.json")
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")

# --- PHẦN 2: QUẢN LÝ TRẠNG THÁI BACKUP (LƯU LẦN BACKUP CUỐI) ---

def _ensure_configs_dir():
    """Đảm bảo thư mục configs tồn tại"""
    configs_dir = os.path.join(BASE_DIR, "configs")
    os.makedirs(configs_dir, exist_ok=True)
    return configs_dir


def _load_backup_state():
    """Tải thông tin lần backup cuối từ file cấu hình"""
    try:
        if os.path.exists(BACKUP_STATE_FILE):
            with open(BACKUP_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                return state.get('last_backup_time', 0)
    except Exception as e:
        logger.warning(f"Không thể đọc trạng thái backup: {e}")
    return 0


def _save_backup_state():
    """Lưu thời gian backup hiện tại vào file cấu hình"""
    try:
        _ensure_configs_dir()
        state = {'last_backup_time': time.time()}
        with open(BACKUP_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        logger.debug("Đã lưu trạng thái backup")
    except Exception as e:
        logger.warning(f"Không thể lưu trạng thái backup: {e}")


def _should_backup_now(interval_hours=24):
    """Kiểm tra xem có cần backup ngay không (dựa trên lần backup cuối)"""
    last_backup = _load_backup_state()
    if last_backup == 0:
        # Chưa bao giờ backup, cần backup
        return True
    elapsed = time.time() - last_backup
    return elapsed >= interval_hours * 3600


# --- PHẦN 3: XỬ LÝ DATABASE LOCK (WAL CHECKPOINT) ---

def _checkpoint_database(db_path):
    """
    Ép SQLite đẩy toàn bộ dữ liệu từ file -wal vào file chính .db
    Giải phóng lock và đảm bảo backup chính xác
    """
    if not db_path.exists():
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA wal_checkpoint(FULL)")
        conn.close()
        logger.debug(f"Đã thực hiện checkpoint cho database: {db_path.name}")
    except Exception as e:
        logger.warning(f"Không thể checkpoint database: {e}")


# --- PHẦN 4: CÁC HÀM KIỂM TRA TÍNH TOÀN VẸN ---

def test_backup_integrity(zip_path):
    """Kiểm tra tính toàn vẹn của file backup zip"""
    if isinstance(zip_path, str):
        zip_path = Path(zip_path)
    
    if not zip_path.exists():
        logger.warning(f"File backup không tồn tại: {zip_path.name}")
        return False
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            bad_file = zf.testzip()
            if bad_file:
                logger.error(f"File backup bị hỏng: {bad_file} trong {zip_path.name}")
                return False
            
            for info in zf.infolist():
                if info.file_size > 0:
                    try:
                        zf.read(info.filename)
                    except Exception as e:
                        logger.error(f"Không thể đọc file {info.filename} trong backup: {e}")
                        return False
            
            logger.debug(f"Backup integrity OK: {zip_path.name}")
            return True
            
    except zipfile.BadZipFile:
        logger.error(f"File {zip_path.name} không phải zip hợp lệ")
        return False
    except Exception as e:
        logger.error(f"Lỗi kiểm tra backup {zip_path.name}: {e}")
        return False


def check_database_integrity(db_path):
    """Kiểm tra tính toàn vẹn của database trước khi backup"""
    if isinstance(db_path, str):
        db_path = Path(db_path)
    
    if not db_path.exists():
        logger.warning(f"Database không tồn tại: {db_path.name}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        
        if result == "ok":
            logger.debug(f"Database integrity OK: {db_path.name}")
            return True
        else:
            logger.error(f"Database integrity FAILED: {result}")
            return False
    except Exception as e:
        logger.error(f"Lỗi kiểm tra database: {e}")
        return False


def get_backup_status():
    """Lấy trạng thái backup hiện tại"""
    backups = sorted(BACKUP_DIR.glob("backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    latest = backups[0] if backups else None
    latest_size_mb = round(latest.stat().st_size / (1024 * 1024), 2) if latest else 0
    total_size_mb = round(sum(b.stat().st_size for b in backups) / (1024 * 1024), 2) if backups else 0
    latest_integrity = test_backup_integrity(latest) if latest else False
    
    last_backup_time = _load_backup_state()
    last_backup_str = datetime.fromtimestamp(last_backup_time).strftime("%Y-%m-%d %H:%M:%S") if last_backup_time else "Chưa có"
    
    return {
        'total_backups': len(backups),
        'max_backups': MAX_BACKUPS,
        'latest_backup': latest.name if latest else None,
        'latest_backup_size_mb': latest_size_mb,
        'latest_backup_integrity': latest_integrity,
        'need_cleanup': len(backups) > MAX_BACKUPS,
        'total_size_mb': total_size_mb,
        'last_backup_time': last_backup_str
    }


# --- PHẦN 5: CÁC HÀM TIỆN ÍCH ---

def get_backup_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{timestamp}.zip"

def get_backup_path():
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR / get_backup_filename()

def clean_old_backups(keep_count=MAX_BACKUPS):
    """Dọn dẹp các bản backup cũ (CHỈ xóa nếu còn nguyên vẹn)"""
    try:
        backups = sorted(BACKUP_DIR.glob("backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
        if len(backups) > keep_count:
            for old_backup in backups[keep_count:]:
                if test_backup_integrity(old_backup):
                    old_backup.unlink()
                    logger.info(f"Đã xóa backup cũ: {old_backup.name}")
                else:
                    logger.warning(f"Giữ lại backup nghi ngờ (có thể bị hỏng): {old_backup.name}")
    except Exception as e:
        logger.error(f"Lỗi dọn dẹp: {e}")


# --- PHẦN 6: HÀM BACKUP LÕI ---

def auto_backup():
    """Hàm sao lưu lõi - Có checkpoint và kiểm tra tính toàn vẹn"""
    try:
        if not BACKUP_DIR.exists(): 
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        db_path = DATA_DIR / "ke_toan.db"
        
        # 1. Kiểm tra database trước khi backup
        if db_path.exists():
            if not check_database_integrity(db_path):
                logger.error("Database bị hỏng, bỏ qua backup!")
                return None
            # 2. Ép checkpoint để giải phóng lock
            _checkpoint_database(db_path)
        
        backup_path = get_backup_path()
        
        if not DATA_DIR.exists():
            logger.warning(f"Thư mục dữ liệu không tồn tại: {DATA_DIR}")
            return None

        # 3. Tạo backup
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(DATA_DIR):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.join(os.path.basename(DATA_DIR), os.path.relpath(full_path, DATA_DIR))
                    zipf.write(full_path, arcname)
        
        # 4. Kiểm tra backup vừa tạo
        if test_backup_integrity(backup_path):
            clean_old_backups()
            _save_backup_state()  # Lưu thời gian backup thành công
            logger.info(f"✅ Đã tạo backup: {backup_path.name} ({backup_path.stat().st_size / (1024*1024):.1f} MB)")
            return backup_path
        else:
            logger.error(f"Backup thất bại: file không integrity, đã xóa")
            backup_path.unlink()
            return None
            
    except Exception as e:
        logger.error(f"Lỗi tự động sao lưu: {e}")
        return None


def manual_backup():
    """Sao lưu thủ công có hiển thị thông báo"""
    try:
        print(f"\n📦 Đang sao lưu dữ liệu từ: {DATA_DIR}")
        logger.info(f"Bắt đầu sao lưu thủ công từ: {DATA_DIR}")
        
        db_path = DATA_DIR / "ke_toan.db"
        if db_path.exists():
            print("🔍 Đang kiểm tra database...")
            check_database_integrity(db_path)
        
        result = auto_backup()
        if result:
            size_mb = result.stat().st_size / (1024 * 1024)
            print(f"✅ Đã sao lưu thành công: {result.name} ({size_mb:.2f} MB)")
            logger.info(f"Sao lưu thủ công thành công: {result.name}")
            return result
        return None
    except Exception as e:
        logger.error(f"Lỗi sao lưu: {e}")
        logger.error(f"Lỗi sao lưu thủ công: {e}")
        return None


def start_auto_backup_loop(interval_hours=24):
    """
    Khởi động vòng lặp backup tự động chạy ngầm
    Kiểm tra ngay khi khởi động nếu đã quá 24h kể từ lần backup cuối
    """
    def backup_loop():
        # Đợi app ổn định 30 giây
        time.sleep(30)
        
        # Kiểm tra xem có cần backup ngay không
        if _should_backup_now(interval_hours):
            logger.info("Đã quá 24h kể từ lần backup cuối, thực hiện backup ngay")
            auto_backup()
        
        while True:
            time.sleep(interval_hours * 3600)
            auto_backup()
    
    thread = threading.Thread(target=backup_loop, daemon=True)
    thread.start()
    logger.info(f"Đã khởi động backup tự động (mỗi {interval_hours} giờ)")


def on_exit_backup():
    """
    Backup khi thoát - NHANH, KHÔNG TREO
    Chỉ backup khi có thay đổi, copy trực tiếp (không nén)
    """
    import hashlib
    import shutil
    import os
    from datetime import datetime
    
    logger.info("Đang kiểm tra dữ liệu trước khi thoát...")
    print("\n🔄 Đang kiểm tra dữ liệu trước khi thoát...")
    
    db_path = DATA_DIR / "ke_toan.db"
    last_hash_file = BACKUP_DIR / ".last_db_hash"
    
    if not db_path.exists():
        print("⚠️ Chưa có dữ liệu, bỏ qua backup")
        return True
    
    try:
        # 1. Tính hash (kiểm tra thay đổi)
        current_hash = hashlib.md5(db_path.read_bytes()).hexdigest()
        
        # 2. So sánh với lần trước
        if last_hash_file.exists():
            if current_hash == last_hash_file.read_text():
                print("⏭️ Không có thay đổi dữ liệu, bỏ qua backup")
                logger.info("Không có thay đổi, bỏ qua backup khi thoát")
                return True
        
        # 3. Backup nhanh (copy trực tiếp, không nén)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quick_backup = BACKUP_DIR / f"quick_backup_{timestamp}.db"
        
        shutil.copy2(db_path, quick_backup)
        logger.info(f"Đã backup nhanh: {quick_backup.name}")
        print(f"✅ Đã sao lưu nhanh: {quick_backup.name}")
        
        # 4. Cập nhật hash
        last_hash_file.write_text(current_hash)
        
        # 5. Dọn dẹp (chỉ giữ 3 bản nhanh gần nhất)
        quick_backups = sorted(BACKUP_DIR.glob("quick_backup_*.db"), key=os.path.getmtime)
        for old in quick_backups[:-3]:
            old.unlink()
            logger.debug(f"Đã xóa backup cũ: {old.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Backup khi thoát thất bại: {e}")
        logger.warning(f"Sao lưu thất bại: {e}")
        return False


def list_backups():
    """Liệt kê danh sách các bản backup (có kiểm tra integrity)"""
    if not BACKUP_DIR.exists(): 
        print("\n📁 Thư mục backup chưa được tạo.")
        return []
    
    backups = sorted(BACKUP_DIR.glob("backup_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    print("\n" + "=" * 70)
    print("   DANH SÁCH CÁC BẢN BACKUP HIỆN CÓ")
    print("=" * 70)
    
    if not backups:
        print("   Chưa có bản backup nào.")
        return []
    
    print(f"   {'STT':<4} {'Tên file':<35} {'Dung lượng':<12} {'Ngày tạo':<20} {'Trạng thái':<10}")
    print("   " + "-" * 68)
    
    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S")
        is_valid = test_backup_integrity(backup)
        status = "✅ OK" if is_valid else "❌ Hỏng"
        
        print(f"   {i:<4} {backup.name:<35} {size_mb:<10.2f}MB {mtime:<20} {status:<10}")
    
    print("=" * 70)
    
    status = get_backup_status()
    print(f"\n📊 Tổng kết: {status['total_backups']}/{status['max_backups']} backup, "
          f"tổng dung lượng: {status['total_size_mb']:.2f} MB")
    print(f"🕐 Lần backup gần nhất: {status['last_backup_time']}")
    
    return backups


def restore_backup(backup_name=None):
    """Khôi phục dữ liệu từ bản sao lưu (có kiểm tra integrity)"""
    if backup_name is None:
        backups = list_backups()
        if not backups:
            print("❌ Không có backup nào để khôi phục.")
            return False
        
        print("\nNhập số thứ tự backup muốn khôi phục (hoặc tên file):")
        choice = input("> ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                backup_path = backups[idx]
            else:
                logger.warning("Lựa chọn không hợp lệ.")
                return False
        except ValueError:
            backup_path = BACKUP_DIR / choice
    else:
        backup_path = BACKUP_DIR / backup_name
    
    if not backup_path.exists():
        logger.error(f"Không tìm thấy file: {backup_path}")
        return False
    
    print(f"\n🔍 Đang kiểm tra tính toàn vẹn của file backup...")
    if not test_backup_integrity(backup_path):
        logger.error("File backup bị hỏng, không thể khôi phục!")
        return False
    
    try:
        print(f"\n🔄 Đang khôi phục từ {backup_path.name}...")
        logger.info(f"Bắt đầu khôi phục từ backup: {backup_path.name}")
        
        # Backup dữ liệu hiện tại trước khi restore
        current_backup = auto_backup()
        if current_backup:
            print(f"📦 Đã tạo backup dữ liệu hiện tại: {current_backup.name}")
        
        if DATA_DIR.exists():
            shutil.rmtree(DATA_DIR)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(DATA_DIR.parent)
        
        db_path = DATA_DIR / "ke_toan.db"
        if db_path.exists():
            print("🔍 Đang kiểm tra database sau khi khôi phục...")
            if check_database_integrity(db_path):
                print("✅ Database khôi phục thành công và còn nguyên vẹn!")
            else:
                logger.warning("Database sau khôi phục có vấn đề!")
        
        print("✅ Khôi phục thành công!")
        logger.info(f"Khôi phục thành công từ: {backup_path.name}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi khôi phục: {e}")
        logger.error(f"Lỗi khôi phục: {e}")
        return False


# --- PHẦN 7: GIAO DIỆN DÒNG LỆNH (CLI) ---

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Công cụ Quản lý Backup Kế Toán Pro')
    parser.add_argument('command', choices=['list', 'backup', 'restore', 'status'], 
                        help='Lệnh thực hiện')
    args = parser.parse_args()
    
    if args.command == 'list':
        list_backups()
    elif args.command == 'backup':
        manual_backup()
    elif args.command == 'restore':
        restore_backup()
    elif args.command == 'status':
        status = get_backup_status()
        print("\n" + "=" * 50)
        print("   TRẠNG THÁI BACKUP")
        print("=" * 50)
        print(f"   Số lượng backup: {status['total_backups']}/{status['max_backups']}")
        print(f"   Backup mới nhất: {status['latest_backup'] or 'Chưa có'}")
        print(f"   Dung lượng mới nhất: {status['latest_backup_size_mb']} MB")
        print(f"   Integrity mới nhất: {'✅ OK' if status['latest_backup_integrity'] else '❌ Hỏng'}")
        print(f"   Tổng dung lượng: {status['total_size_mb']} MB")
        print(f"   Cần dọn dẹp: {'Có' if status['need_cleanup'] else 'Không'}")
        print(f"   Lần backup cuối: {status['last_backup_time']}")
        print("=" * 50)