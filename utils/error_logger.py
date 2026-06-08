import smtplib
import traceback
import sys
import platform
import socket
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path
import logging

def send_error_report(error_traceback):
    """
    Tự động gửi báo cáo lỗi về email pnhungc3nvt@gmail.com
    """
    sender_email = "pnhungc3nvt@gmail.com"
    receiver_email = "pnhungc3nvt@gmail.com"
    
    # ĐÂY LÀ MÃ 16 KÝ TỰ ANH VỪA TẠO TRÊN GOOGLE
    # Anh hãy dán mã đó vào giữa hai dấu ngoặc kép dưới đây
    password = "bhczlexkuxythqsc" 

    # Đọc phiên bản phần mềm từ file version.txt để anh biết khách đang dùng bản nào
    version = "Không rõ"
    version_file = Path("version.txt")
    if version_file.exists():
        with open(version_file, "r", encoding="utf-8") as f:
            version = f.readline().strip() 

    # Soạn tiêu đề email chuyên nghiệp
    subject = f"[LOI PHAN MEM] Ke Toan Pro v{version} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    # Lấy thông tin máy khách để dễ hỗ trợ
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "Không rõ"

    # Soạn nội dung chi tiết lỗi
    body = f"""
    THÔNG BÁO LỖI HỆ THỐNG - KẾ TOÁN PRO
    -----------------------------------------
    Phiên bản    : {version}
    Thời gian    : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    Máy tính     : {hostname}
    Hệ điều hành : {platform.platform()}
    Python       : {sys.version}

    CHI TIẾT LỖI (TRACEBACK):
    {error_traceback}

    -----------------------------------------
    Đây là báo cáo tự động từ hệ thống của Thầy Hùng.
    """

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        # Kết nối và gửi qua máy chủ Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        logging.info("[ErrorLogger] ✅ Đã gửi báo cáo lỗi về email admin.")
        return True
    except Exception as e:
        # Nếu không có internet hoặc lỗi gửi mail thì ghi tạm ra log máy khách
        logging.error(f"Không thể gửi email báo lỗi: {e}")
        return False


def _global_exception_handler(exc_type, exc_value, exc_tb):
    """
    Hook bắt toàn bộ exception chưa được xử lý trong ứng dụng.
    Tự động gọi send_error_report() khi phần mềm crash.
    """
    # Bỏ qua KeyboardInterrupt (Ctrl+C) - không cần báo lỗi
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    # Định dạng traceback đầy đủ
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    # Ghi vào log local trước
    logging.critical(f"[CRASH] Lỗi nghiêm trọng:\n{tb_text}")

    # Gửi email báo lỗi về cho Thầy Hùng
    send_error_report(tb_text)

    # Vẫn gọi handler gốc để Python in lỗi ra console như bình thường
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def kich_hoat_bao_loi_tu_dong():
    """
    Gọi hàm này 1 lần khi khởi động ứng dụng để kích hoạt
    tính năng tự động gửi email khi phần mềm crash.

    Thêm vào đầu __init__ của MainWindow:
        from utils.error_logger import kich_hoat_bao_loi_tu_dong
        kich_hoat_bao_loi_tu_dong()
    """
    sys.excepthook = _global_exception_handler
    logging.info("[ErrorLogger] ✅ Đã kích hoạt báo lỗi tự động qua email.")


# ── Chạy trực tiếp file này để test gửi email ──
if __name__ == "__main__":
    print("🔧 Đang test gửi email báo lỗi...")
    ket_qua = send_error_report(
        "TEST: Đây là email kiểm tra tính năng báo lỗi tự động.\n"
        "Nếu bạn nhận được email này nghĩa là tính năng hoạt động bình thường."
    )
    if ket_qua:
        print("✅ Gửi thành công! Kiểm tra hộp thư pnhungc3nvt@gmail.com")
    else:
        print("❌ Gửi thất bại. Kiểm tra lại App Password hoặc kết nối mạng.")