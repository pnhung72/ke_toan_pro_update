# utils/db_optimizer.py
"""
Tối ưu hóa database - Tạo INDEX, ANALYZE, VACUUM
Hỗ trợ SQLCipher (database mã hóa)
ĐÃ CẬP NHẬT:
- Xử lý lỗi Database is locked khi VACUUM
- PRAGMA journal_mode=WAL để giảm lock
- Logging chi tiết (logger.info/error)
"""

import sqlite3
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import logging

# Đảm bảo có thể import config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.logger import get_logger

logger = get_logger(__name__)

# Cấu hình
VACUUM_WARNING_SIZE_MB = 100  # Cảnh báo nếu DB > 100MB
VACUUM_RETRY_COUNT = 3        # Số lần thử lại VACUUM
VACUUM_RETRY_DELAY = 2        # Giây chờ giữa các lần thử


def get_db_path():
    """Lấy đường dẫn database"""
    try:
        from config import REAL_DATA_DIR
        return os.path.join(REAL_DATA_DIR, "ke_toan.db")
    except ImportError:
        return os.path.join(BASE_DIR, "ke_toan_data", "ke_toan.db")


def enable_wal_mode(conn):
    """
    Kích hoạt chế độ WAL (Write-Ahead Logging)
    Giúp giảm xung đột đọc/ghi, hỗ trợ concurrent access
    """
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        mode = cursor.fetchone()[0]
        if mode == 'wal':
            logger.info("Đã kích hoạt WAL mode cho database")
            return True
        else:
            logger.warning(f"Không thể kích hoạt WAL mode, hiện tại: {mode}")
            return False
    except Exception as e:
        logger.error(f"Lỗi kích hoạt WAL mode: {e}")
        return False


def get_connection(master_key=None, enable_wal=True):
    """
    Lấy kết nối database (hỗ trợ SQLCipher nếu có master_key)
    
    Args:
        master_key: Key để giải mã database (nếu dùng SQLCipher)
        enable_wal: Có kích hoạt WAL mode không
    """
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    # Nếu có master_key, cấu hình SQLCipher
    if master_key is not None:
        try:
            conn.execute(f"PRAGMA key = x'{master_key}'")
            logger.debug("Đã cấu hình SQLCipher key")
        except Exception as e:
            logger.warning(f"Không thể cấu hình SQLCipher (có thể chưa cài đặt): {e}")
    
    # Kích hoạt WAL mode để giảm lock
    if enable_wal:
        enable_wal_mode(conn)
    
    return conn


def close_all_connections():
    """
    Đóng tất cả kết nối database đang mở
    Gọi trước khi VACUUM để tránh lỗi Database is locked
    """
    try:
        from models.database import Database
        Database.close_all_connections()
        logger.info("Đã đóng tất cả kết nối database")
    except Exception as e:
        logger.warning(f"Không thể đóng kết nối qua Database class: {e}")
    
    # Force garbage collection
    import gc
    gc.collect()
    time.sleep(0.5)


def vacuum_with_retry(conn, max_retries=VACUUM_RETRY_COUNT):
    """
    Thực hiện VACUUM với cơ chế thử lại khi bị lock
    
    Args:
        conn: Kết nối database
        max_retries: Số lần thử lại tối đa
    """
    for attempt in range(max_retries):
        try:
            conn.execute("VACUUM")
            logger.info(f"VACUUM thành công (lần thử {attempt + 1})")
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                logger.warning(f"VACUUM thất bại (database locked), lần thử {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(VACUUM_RETRY_DELAY)
                    # Thử đóng kết nối và kết nối lại
                    try:
                        conn.close()
                        time.sleep(0.5)
                        conn = get_connection()
                    except Exception:
                        pass
                else:
                    logger.error(f"VACUUM thất bại sau {max_retries} lần thử: {e}")
                    return False
            else:
                logger.error(f"Lỗi VACUUM không xác định: {e}")
                return False
    return False


def table_exists(cursor, table_name):
    """Kiểm tra bảng có tồn tại không"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def index_exists(cursor, index_name):
    """Kiểm tra index đã tồn tại chưa"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    return cursor.fetchone() is not None


def run_analyze(conn):
    """
    Chạy ANALYZE để cập nhật thống kê cho query optimizer
    NÊN chạy sau khi tạo INDEX mới
    """
    logger.info("Đang chạy ANALYZE để tối ưu truy vấn...")
    try:
        conn.execute("ANALYZE")
        logger.info("ANALYZE hoàn tất")
        return True
    except Exception as e:
        logger.error(f"Lỗi ANALYZE: {e}")
        return False


def create_indexes(conn, run_analyze_after=True):
    """
    Tạo các INDEX cần thiết cho database
    
    Args:
        conn: Kết nối database
        run_analyze_after: Có chạy ANALYZE sau khi tạo index không
    """
    logger.info("Bắt đầu tạo INDEX cho database")
    
    indexes = [
        # Bảng transactions
        ("idx_transactions_date", "transactions", "date"),
        ("idx_transactions_type", "transactions", "type"),
        ("idx_transactions_category", "transactions", "category"),
        ("idx_transactions_date_type", "transactions", "date, type"),
        
        # Bảng invoices
        ("idx_invoices_created_date", "invoices", "created_date"),
        ("idx_invoices_buyer_name", "invoices", "buyer_name"),
        ("idx_invoices_phone", "invoices", "phone"),
        ("idx_invoices_sale_source", "invoices", "sale_source"),
        
        # Bảng journal_entries
        ("idx_journal_entries_date", "journal_entries", "date"),
        ("idx_journal_entries_fiscal_year", "journal_entries", "fiscal_year"),
        ("idx_journal_entries_period", "journal_entries", "period"),
        ("idx_journal_entries_date_year", "journal_entries", "date, fiscal_year"),
        
        # Bảng products
        ("idx_products_code", "products", "code"),
        ("idx_products_name", "products", "name"),
        
        # Bảng debts
        ("idx_debts_name", "debts", "name"),
        ("idx_debts_phone", "debts", "phone"),
    ]
    
    cursor = conn.cursor()
    
    # Kiểm tra các bảng cần thiết
    required_tables = ['transactions', 'invoices', 'journal_entries', 'products', 'debts']
    existing_tables = []
    
    for table in required_tables:
        if table_exists(cursor, table):
            existing_tables.append(table)
            logger.debug(f"Bảng {table} tồn tại")
        else:
            logger.warning(f"Bảng {table} chưa tồn tại, bỏ qua INDEX liên quan")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for index_name, table_name, columns in indexes:
        if table_name not in existing_tables:
            skipped_count += 1
            continue
        
        if index_exists(cursor, index_name):
            logger.debug(f"Index đã tồn tại: {index_name}")
            skipped_count += 1
            continue
        
        try:
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})"
            cursor.execute(sql)
            logger.info(f"Đã tạo index: {index_name} ON {table_name}({columns})")
            created_count += 1
        except Exception as e:
            logger.error(f"Lỗi tạo index {index_name}: {e}")
            error_count += 1
    
    conn.commit()
    
    logger.info(f"Tạo INDEX hoàn tất: {created_count} mới, {skipped_count} đã có, {error_count} lỗi")
    
    # Chạy ANALYZE sau khi tạo index
    if created_count > 0 and run_analyze_after:
        run_analyze(conn)
    
    return created_count > 0 or error_count == 0


def vacuum_database(conn, show_warning=True):
    """
    Tối ưu database (thu gọn file) - Có xử lý lock
    
    Args:
        conn: Kết nối database
        show_warning: Hiển thị cảnh báo nếu DB quá lớn
    """
    logger.info("Bắt đầu VACUUM database")
    
    try:
        # Lấy kích thước trước
        db_path = get_db_path()
        size_before = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0
        logger.info(f"Kích thước database trước VACUUM: {size_before:.2f} MB")
        
        # Cảnh báo nếu DB quá lớn
        if show_warning and size_before > VACUUM_WARNING_SIZE_MB:
            print("\n" + "!" * 60)
            print(f"⚠️ CẢNH BÁO: Database có kích thước {size_before:.2f} MB")
            print("   Quá trình VACUUM có thể mất vài phút.")
            print("   VUI LÒNG KHÔNG TẮT ỨNG DỤNG!")
            print("!" * 60 + "\n")
            
            confirm = input("Tiếp tục VACUUM? (y/n): ")
            if confirm.lower() != 'y':
                logger.info("Người dùng hủy VACUUM")
                logging.warning("Đã hủy VACUUM")
                return False
        
        # Đóng tất cả kết nối trước khi VACUUM
        close_all_connections()
        
        # Thực hiện VACUUM với cơ chế thử lại
        print("🔄 Đang thực hiện VACUUM (có thể mất vài phút)...")
        start_time = time.time()
        
        success = vacuum_with_retry(conn)
        
        elapsed = time.time() - start_time
        logger.info(f"Thời gian VACUUM: {elapsed:.1f} giây")
        print(f"⏱️ Thời gian VACUUM: {elapsed:.1f} giây")
        
        if success:
            # Lấy kích thước sau
            size_after = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0
            print(f"📦 Kích thước sau VACUUM: {size_after:.2f} MB")
            logger.info(f"Kích thước database sau VACUUM: {size_after:.2f} MB")
            
            if size_before > 0:
                saved = size_before - size_after
                percent = (saved / size_before * 100) if size_before > 0 else 0
                print(f"✅ Tiết kiệm: {saved:.2f} MB ({percent:.1f}%)")
                logger.info(f"Tiết kiệm: {saved:.2f} MB ({percent:.1f}%)")
        else:
            logger.error("VACUUM thất bại")
        
        return success
        
    except Exception as e:
        logger.error(f"Lỗi VACUUM: {e}")
        logging.error(f"Lỗi VACUUM: {e}")
        return False


def get_database_stats(conn):
    """Lấy thống kê database"""
    logger.info("Lấy thống kê database")
    
    stats = {}
    cursor = conn.cursor()
    
    # WAL mode status
    cursor.execute("PRAGMA journal_mode")
    wal_mode = cursor.fetchone()[0]
    print(f"\n📁 Chế độ journal: {wal_mode}")
    logger.debug(f"Journal mode: {wal_mode}")
    
    # Lấy số dòng các bảng chính
    tables = ['transactions', 'invoices', 'journal_entries', 'products', 'debts', 'users']
    print("\n📊 Số dòng các bảng:")
    for table in tables:
        if table_exists(cursor, table):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count
            print(f"   {table}: {count:,} dòng")
            logger.debug(f"{table}: {count} dòng")
        else:
            print(f"   {table}: (chưa có)")
    
    # Lấy tổng doanh thu
    if table_exists(cursor, 'transactions'):
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Thu'")
        total_revenue = cursor.fetchone()[0] or 0
        print(f"\n💰 Tổng doanh thu: {total_revenue:,.0f} VNĐ")
        
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Chi'")
        total_expense = cursor.fetchone()[0] or 0
        print(f"   Tổng chi phí: {total_expense:,.0f} VNĐ")
        print(f"   Lợi nhuận: {(total_revenue - total_expense):,.0f} VNĐ")
    
    # Lấy thông tin INDEX
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name")
    indexes = cursor.fetchall()
    if indexes:
        print("\n📋 DANH SÁCH INDEX:")
        for idx_name, tbl_name in indexes:
            if not idx_name.startswith('sqlite_'):
                print(f"      - {idx_name} ON {tbl_name}")
    
    return stats


def analyze_query_performance(conn):
    """Phân tích hiệu suất truy vấn (benchmark)"""
    logger.info("Bắt đầu phân tích hiệu suất truy vấn")
    
    queries = [
        ("Đếm transactions theo ngày", 
         "SELECT COUNT(*) FROM transactions WHERE date >= date('now', '-30 days')"),
        ("Tổng doanh thu theo tháng", 
         "SELECT strftime('%Y-%m', date), SUM(amount) FROM transactions WHERE type='Thu' GROUP BY strftime('%Y-%m', date)"),
        ("Top 10 khách hàng mua nhiều", 
         "SELECT buyer_name, COUNT(*) FROM invoices GROUP BY buyer_name ORDER BY COUNT(*) DESC LIMIT 10"),
    ]
    
    cursor = conn.cursor()
    
    print("\n📊 BENCHMARK TRUY VẤN:")
    for name, sql in queries:
        try:
            start = time.time()
            cursor.execute(sql)
            result = cursor.fetchall()
            elapsed = (time.time() - start) * 1000  # ms
            
            print(f"\n   📌 {name}")
            print(f"      Thời gian: {elapsed:.2f} ms")
            print(f"      Kết quả: {len(result)} dòng")
            logger.debug(f"{name}: {elapsed:.2f} ms")
        except Exception as e:
            logger.error(f"Lỗi truy vấn {name}: {e}")
            logging.error(f"Lỗi benchmark: {e}")


def optimize_all(master_key=None, auto_confirm=False):
    """
    Chạy toàn bộ tối ưu hóa
    
    Args:
        master_key: Key cho SQLCipher (nếu có)
        auto_confirm: Tự động xác nhận (bỏ qua cảnh báo)
    """
    logger.info("BẮT ĐẦU TỐI ƯU HÓA DATABASE")
    print("\n" + "🔄" * 30)
    print("   BẮT ĐẦU TỐI ƯU HÓA DATABASE")
    print("🔄" * 30)
    
    start_time = time.time()
    
    try:
        conn = get_connection(master_key, enable_wal=True)
        
        # 1. Tạo index (kèm ANALYZE tự động)
        create_indexes(conn, run_analyze_after=True)
        
        # 2. VACUUM (tối ưu file)
        db_path = get_db_path()
        size_before = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0
        
        if size_before > VACUUM_WARNING_SIZE_MB and not auto_confirm:
            print(f"\n⚠️ Database có kích thước {size_before:.2f} MB (>{VACUUM_WARNING_SIZE_MB} MB)")
            confirm = input("Có muốn chạy VACUUM để thu gọn không? (y/n): ")
            if confirm.lower() == 'y':
                vacuum_database(conn, show_warning=False)
        else:
            vacuum_database(conn, show_warning=not auto_confirm)
        
        # 3. Thống kê
        get_database_stats(conn)
        
        conn.close()
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ Tổng thời gian tối ưu hóa: {elapsed:.1f} giây")
        logger.info(f"Tối ưu hóa hoàn tất trong {elapsed:.1f} giây")
        print("\n✅ HOÀN TẤT TỐI ƯU HÓA!")
        
    except Exception as e:
        logger.error(f"Lỗi tối ưu hóa: {e}")
        logging.error(f"Lỗi tối ưu hóa: {e}")
        return False
    
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Công cụ tối ưu database Kế Toán Pro')
    parser.add_argument('command', 
                        choices=['create_indexes', 'vacuum', 'stats', 'benchmark', 'all'],
                        default='all', nargs='?', 
                        help='Lệnh thực hiện')
    parser.add_argument('--auto', action='store_true', 
                        help='Tự động xác nhận (bỏ qua cảnh báo)')
    args = parser.parse_args()
    
    print("🔧 CÔNG CỤ TỐI ƯU DATABASE - KẾ TOÁN PRO")
    print(f"🕐 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = get_connection(enable_wal=True)
    
    if args.command == 'create_indexes':
        create_indexes(conn)
    elif args.command == 'vacuum':
        vacuum_database(conn)
    elif args.command == 'stats':
        get_database_stats(conn)
    elif args.command == 'benchmark':
        analyze_query_performance(conn)
    else:  # all
        optimize_all(auto_confirm=args.auto)
    
    conn.close()