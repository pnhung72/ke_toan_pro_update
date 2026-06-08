"""
Đồng bộ hóa đơn đã duyệt từ queue vào bảng invoices CŨ của phần mềm chính.
CẢNH BÁO: Bạn cần điều chỉnh hàm insert_into_invoices() cho phù hợp với
cấu trúc bảng invoices thực tế của dự án.
"""

import sqlite3
from pathlib import Path
from .queue_db import get_invoice_by_id, update_invoice_status, get_db_connection as get_queue_conn
from .logger import get_logger

logger = get_logger()

# Đường dẫn database chính (cùng file với ke_toan.db)
DB_PATH = Path("ke_toan.db")

def insert_into_invoices(invoice_data):
    """
    Chèn dữ liệu từ invoice_data (dict lấy từ queue) vào bảng invoices cũ.
    HIỆN TẠI MỚI CHỈ GHI LOG, BẠN PHẢI SỬA LẠI PHẦN NÀY THEO ĐÚNG CẤU TRÚC BẢNG CỦA BẠN.
    """
    logger.warning("=== BẠN CẦN SỬA HÀM insert_into_invoices() trong integrator.py ===")
    logger.warning(f"Dữ liệu cần insert: {invoice_data}")
    
    # Ví dụ: Giả sử bảng invoices của bạn có các cột: invoice_number, supplier_tax_code, supplier_name, date, subtotal, tax, total, status
    # Bạn hãy mở file models/invoice.py hoặc xem cấu trúc bảng bằng công cụ DB Browser, sau đó sửa đoạn dưới đây.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, supplier_tax_code, supplier_name, date,
                subtotal, tax, total, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_data.get('invoice_no'),
            invoice_data.get('seller_tax_code'),
            invoice_data.get('seller_name'),
            invoice_data.get('issue_date'),
            invoice_data.get('total_amount_wo_tax'),
            invoice_data.get('tax_amount'),
            invoice_data.get('total_amount'),
            'approved'
        ))
        conn.commit()
        logger.info("Insert thành công vào bảng invoices")
        return True
    except Exception as e:
        logger.error(f"Lỗi insert: {e}")
        return False
    finally:
        conn.close()
    """
    
    # Tạm thời trả về False để tránh insert lung tung
    return False


def approve_invoice_sync(invoice_id, approved_by=1):
    """
    Đồng bộ một hóa đơn đã duyệt từ queue vào bảng invoices cũ.
    approved_by: mã người dùng (mặc định 1 là admin)
    """
    invoice = get_invoice_by_id(invoice_id)
    if not invoice:
        logger.error(f"Không tìm thấy hóa đơn queue id={invoice_id}")
        return False
    if invoice['status'] != 'pending':
        logger.warning(f"Hóa đơn {invoice_id} không ở trạng thái pending")
        return False
    
    # Chèn vào bảng invoices cũ
    success = insert_into_invoices(invoice)
    if success:
        # Cập nhật status trong queue
        update_invoice_status(invoice_id, 'approved', approved_by=approved_by)
        logger.info(f"Hóa đơn {invoice_id} đã được đồng bộ và đánh dấu approved")
        return True
    else:
        logger.error(f"Không thể đồng bộ hóa đơn {invoice_id}, insert thất bại")
        return False