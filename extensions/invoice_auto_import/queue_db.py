import sqlite3
import json
from datetime import datetime
from pathlib import Path
from .logger import get_logger

logger = get_logger()

# Đường dẫn chính xác đến database (theo cấu trúc dự án của bạn)
DB_PATH = Path("ke_toan_data/ke_toan.db")

def get_db_connection():
    return sqlite3.connect(str(DB_PATH))

def init_queue_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                xml_path TEXT NOT NULL,
                seller_tax_code TEXT,
                seller_name TEXT,
                invoice_no TEXT,
                issue_date TEXT,
                total_amount_wo_tax REAL,
                tax_amount REAL,
                total_amount REAL,
                raw_json TEXT,
                status TEXT DEFAULT 'pending',
                rejection_reason TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by INTEGER,
                approved_at TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("Bảng invoice_queue đã sẵn sàng")
        print("✅ [queue_db] Bảng invoice_queue đã được tạo/kiểm tra")

def insert_invoice_queue(data, xml_path):
    print(f"[queue_db] Đang chèn hóa đơn: {data.get('invoice_no')}")
    raw_json = json.dumps(data, ensure_ascii=False)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoice_queue (
                xml_path, seller_tax_code, seller_name, invoice_no, issue_date,
                total_amount_wo_tax, tax_amount, total_amount, raw_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            xml_path, data.get('seller_tax_code', ''), data.get('seller_name', ''),
            data.get('invoice_no', ''), data.get('issue_date', ''),
            data.get('total_amount_wo_tax', 0.0), data.get('tax_amount', 0.0),
            data.get('total_amount', 0.0), raw_json, 'pending'
        ))
        conn.commit()
        invoice_id = cursor.lastrowid
        logger.info(f"Đã thêm hóa đơn vào queue, id={invoice_id}")
        print(f"✅ [queue_db] Đã chèn thành công, id={invoice_id}")
        return invoice_id

def is_duplicate(invoice_no, seller_tax_code):
    # Giữ nguyên logic cũ
    if not invoice_no or not seller_tax_code:
        return False
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM invoice_queue
            WHERE invoice_no = ? AND seller_tax_code = ?
            AND status IN ('pending', 'approved')
        """, (invoice_no, seller_tax_code))
        return cursor.fetchone() is not None

def get_pending_invoices():
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoice_queue WHERE status='pending' ORDER BY imported_at ASC")
        return [dict(row) for row in cursor.fetchall()]

def update_invoice_status(invoice_id, status, rejection_reason='', approved_by=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if status == 'approved':
            cursor.execute("UPDATE invoice_queue SET status=?, approved_by=?, approved_at=CURRENT_TIMESTAMP WHERE id=?", (status, approved_by, invoice_id))
        else:
            cursor.execute("UPDATE invoice_queue SET status=?, rejection_reason=? WHERE id=?", (status, rejection_reason, invoice_id))
        conn.commit()

def get_invoice_by_id(invoice_id):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoice_queue WHERE id=?", (invoice_id,))
        row = cursor.fetchone()
        return dict(row) if row else None