# utils/sync_lock.py
import threading
import logging

_ocr_running = False
_ocr_event = threading.Event()
_ocr_event.set()  # Mặc định: OCR không chạy, sync được phép

def ocr_started():
    """Gọi khi OCR bắt đầu - chặn sync"""
    global _ocr_running
    _ocr_running = True
    _ocr_event.clear()
    logging.info("OCR bắt đầu - tạm dừng đồng bộ rclone")

def ocr_finished():
    """Gọi khi OCR kết thúc - cho phép sync tiếp"""
    global _ocr_running
    _ocr_running = False
    _ocr_event.set()
    logging.info("OCR kết thúc - đồng bộ rclone tiếp tục")

def can_sync():
    """Kiểm tra nhanh (non-blocking)"""
    return not _ocr_running

def wait_for_ocr_to_finish(timeout=300):
    """Chờ OCR xong rồi mới cho sync chạy (blocking, tối đa 5 phút)"""
    result = _ocr_event.wait(timeout=timeout)
    if not result:
        logging.warning("Timeout chờ OCR - tiếp tục sync")
    return result