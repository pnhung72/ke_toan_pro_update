"""
Hook để gọi từ module email hiện tại của phần mềm.
Đã thêm xử lý database lock và log chi tiết.
"""

import shutil
from pathlib import Path
from datetime import datetime
import time
import sqlite3
from .xml_parser import parse_xml
from .logger import get_logger

logger = get_logger()

DATA_XML_DIR = Path("DATA_XML/HoaDon_DauVao")
BACKUP_DIR = Path("backup/processed_xml")
ERROR_DIR = Path("backup/xml_errors")
DUPLICATE_DIR = Path("backup/duplicates")

def ensure_dirs():
    for d in [DATA_XML_DIR, BACKUP_DIR, ERROR_DIR, DUPLICATE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def backup_file(file_path: Path, subdir: Path):
    date_str = datetime.now().strftime("%Y-%m-%d")
    dest_dir = subdir / date_str
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file_path.name
    shutil.move(str(file_path), str(dest_path))
    logger.info(f"Đã backup file {file_path.name} vào {dest_dir}")
    return dest_path

def insert_invoice_safe(data, xml_path, retries=3, delay=0.5):
    """Chèn hóa đơn vào queue, tự động thử lại nếu database locked"""
    from .queue_db import get_db_connection, is_duplicate
    # Kiểm tra duplicate trước
    if is_duplicate(data.get('invoice_no', ''), data.get('seller_tax_code', '')):
        logger.warning(f"Trùng lặp: {data.get('invoice_no')}")
        return None
    for i in range(retries):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoice_queue (
                    xml_path, seller_tax_code, seller_name, invoice_no, issue_date,
                    total_amount_wo_tax, tax_amount, total_amount, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                xml_path, data.get('seller_tax_code'), data.get('seller_name'),
                data.get('invoice_no'), data.get('issue_date'),
                data.get('total_amount_wo_tax', 0.0), data.get('tax_amount', 0.0),
                data.get('total_amount', 0.0), 'pending'
            ))
            conn.commit()
            invoice_id = cursor.lastrowid
            conn.close()
            logger.info(f"Đã thêm hóa đơn vào queue, id={invoice_id}")
            return invoice_id
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and i < retries - 1:
                logger.warning(f"DB locked, thử lại lần {i+2}...")
                time.sleep(delay)
                continue
            else:
                logger.error(f"Lỗi insert: {e}")
                raise
    return None

def handle_invoice_xml(attachment, email_from, save_dir=None):
    ensure_dirs()
    if save_dir is None:
        save_dir = DATA_XML_DIR
    else:
        save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = attachment.filename
    if not filename.lower().endswith('.xml') or 'hoadon' not in filename.lower():
        logger.debug(f"Bỏ qua {filename}")
        return

    logger.info(f"Phát hiện XML từ {email_from}: {filename}")
    try:
        temp_path = save_dir / filename
        attachment.save(str(temp_path))
        
        invoice_data = parse_xml(str(temp_path))
        if not invoice_data or not invoice_data.get('invoice_no'):
            logger.error(f"Parse thất bại {temp_path}")
            backup_file(temp_path, ERROR_DIR)
            return
        
        # Gọi hàm insert với retry
        insert_invoice_safe(invoice_data, str(temp_path))
        backup_file(temp_path, BACKUP_DIR)
        logger.info(f"Thành công: {invoice_data['invoice_no']}")
    except Exception as e:
        logger.error(f"Lỗi xử lý {filename}: {e}", exc_info=True)
        if temp_path and temp_path.exists():
            backup_file(temp_path, ERROR_DIR)