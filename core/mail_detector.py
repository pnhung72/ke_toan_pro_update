# -*- coding: utf-8 -*-
import imaplib
import email
from email.header import decode_header
import re
import threading
import queue
import tempfile
import os
from pathlib import Path
import logging

class AdminMailScanner:
    def __init__(self, email_user, email_pass, imap_url="imap.gmail.com"):
        self.email_user = email_user
        self.email_pass = email_pass
        self.imap_url = imap_url
        self.update_queue = queue.Queue()
        self.is_running = False

    def start_scanning(self):
        """Kích hoạt Thread chạy ngầm để không gây đơ giao diện chính"""
        if not self.is_running:
            self.is_running = True
            thread = threading.Thread(target=self._scan_process, daemon=True)
            thread.start()

    def _clean_text(self, text):
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='ignore')
        return text

    def _process_attachments(self, msg, mail_id):
        """Xử lý file đính kèm XML hóa đơn (tích hợp trực tiếp)"""
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if not filename:
                continue
            if filename.lower().endswith('.xml') and 'hoadon' in filename.lower():
                logging.info(f"Phát hiện file XML: {filename}")
                try:
                    # Lưu file tạm
                    import tempfile, os, shutil, sqlite3
                    from pathlib import Path
                    with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as tmp:
                        tmp.write(part.get_payload(decode=True))
                        tmp_path = tmp.name
                    logging.info(f"Đã lưu file tạm: {tmp_path}")

                    # Đọc nội dung để kiểm tra (có thể parse sơ qua)
                    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    #print(f"[XML] Nội dung (200 ký tự đầu): {content[:200]}")

                    # Lưu vào database (tạo bảng nếu chưa có)
                    db_path = Path("ke_toan_data/ke_toan.db")
                    conn = sqlite3.connect(str(db_path), timeout=10)
                    conn.execute("PRAGMA journal_mode=WAL")
                    cursor = conn.cursor()
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS invoice_queue (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            xml_path TEXT,
                            invoice_no TEXT,
                            seller_name TEXT,
                            total_amount REAL,
                            status TEXT DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    # Thử lấy số hóa đơn đơn giản (tìm trong nội dung XML)
                    import re
                    match = re.search(r'<InvoiceNo>(.*?)</InvoiceNo>', content, re.IGNORECASE)
                    invoice_no = match.group(1) if match else "UNKNOWN"
                    match2 = re.search(r'<SellerName>(.*?)</SellerName>', content, re.IGNORECASE)
                    seller_name = match2.group(1) if match2 else ""
                    match3 = re.search(r'<TotalAmount>(.*?)</TotalAmount>', content, re.IGNORECASE)
                    total = float(match3.group(1)) if match3 else 0

                    cursor.execute("""
                        INSERT INTO invoice_queue (xml_path, invoice_no, seller_name, total_amount)
                        VALUES (?, ?, ?, ?)
                    """, (tmp_path, invoice_no, seller_name, total))
                    conn.commit()
                    conn.close()
                    logging.info(f"Đã chèn hóa đơn {invoice_no} vào queue")

                    # Backup
                    backup_dir = Path("backup/processed_xml")
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(tmp_path, backup_dir / filename)
                    logging.info("Đã backup file")
                except Exception as e:
                    logging.error(f"Lỗi xử lý XML: {e}")
                    import traceback
                    traceback.print_exc()

    def _scan_process(self):
        #print("[DEBUG] Bắt đầu _scan_process (Bản tối ưu)")
        try:
            #print("[DEBUG] Đang kết nối IMAP...")
            mail = imaplib.IMAP4_SSL(self.imap_url)
            safe_email = self.email_user.encode('ascii', 'ignore').decode('ascii')
            safe_pass = self.email_pass.encode('ascii', 'ignore').decode('ascii')
            mail.login(safe_email, safe_pass)
            mail.select("inbox")

            # 1. CHỈ QUÉT THƯ CHƯA ĐỌC (UNSEEN)
            status, messages = mail.search(None, 'UNSEEN')
            
            if status == "OK":
                mail_ids = messages[0].split()
                # 2. GIỚI HẠN XỬ LÝ: Chỉ lấy 10 thư mới nhất mỗi lần quét để tránh treo máy
                to_process = mail_ids[-10:] if len(mail_ids) > 10 else mail_ids
                
                #print(f"[DEBUG] Số thư mới cần xử lý: {len(to_process)}")
                
                for m_id in to_process:
                    status, data = mail.fetch(m_id, '(RFC822)')
                    if status != "OK": continue
                            
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # 3. XỬ LÝ HÓA ĐƠN VÀ NỘI DUNG (GIỮ NGUYÊN TÍNH NĂNG)
                    self._process_attachments(msg, m_id)
                    
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    # Trích xuất thông tin
                    name_match = re.search(r"Khách hàng:\s*([^\n|]+)", body, re.IGNORECASE)
                    phone_match = re.search(r"SĐT:\s*([^\n|]+)", body, re.IGNORECASE)
                    req_match = re.search(r"Nội dung:\s*([^\n]+)", body, re.IGNORECASE)

                    customer = name_match.group(1).strip() if name_match else msg["From"]
                    phone = phone_match.group(1).strip() if phone_match else "Không có"
                    request_content = req_match.group(1).strip() if req_match else body[:100] + "..."

                    self.update_queue.put({
                        "customer": customer, "phone": phone,
                        "content": request_content, "status": "🔴 Chưa đọc"
                    })
                    
                    # 4. ĐÁNH DẤU LÀ ĐÃ ĐỌC (TRÁNH QUÉT LẠI)
                    mail.store(m_id, '+FLAGS', '\\Seen')
            
            mail.logout()
            #print("[DEBUG] Kết thúc _scan_process thành công")
        except Exception as e:
            logging.error(f"Lỗi quét hòm thư: {e}")
        finally:
            self.is_running = False