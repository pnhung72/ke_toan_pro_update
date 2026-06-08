import xml.etree.ElementTree as ET
import os
import sqlite3
import re

class XMLService:
    def __init__(self, mst_owner="4201140371"):
        self.mst_owner = str(mst_owner).strip()
        from data_config import DB_PATH
        self.db_path = DB_PATH

    def parse_invoice(self, xml_path):
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Bóc MST: Tìm tất cả chuỗi 10-13 số nằm trong các thẻ XML
            msts = re.findall(r'<[^>]*mst[^>]*>(\d{10}|\d{13})</', content, re.IGNORECASE)
            # Nếu không tìm thấy trong thẻ MST, tìm diện rộng các chuỗi số 10-13 chữ số
            if not msts:
                msts = re.findall(r'(\d{10}|\d{13})', content)
            
            # Loại bỏ trùng lặp và giữ nguyên thứ tự xuất hiện
            unique_msts = []
            for m in msts:
                if m not in unique_msts:
                    unique_msts.append(m)

            # 2. Tìm Số tiền: Ưu tiên thẻ đặc thù của Thầy (tgtttbso) và các thẻ chuẩn
            money_match = re.search(r'<[^>]*tgtttbso[^>]*>([\d\.,]+)</', content, re.IGNORECASE) or \
                          re.search(r'<(?:TgTThanh|TotalPayment|TToan|SumVatAmount)>([\d\.,]+)</', content, re.IGNORECASE)
            
            # 3. Tìm Ngày (YYYY-MM-DD)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
            
            # Xử lý số tiền (chuyển đổi dấu phẩy nếu có)
            sotien_str = money_match.group(1).replace(',', '') if money_match else "0"
            sotien = float(sotien_str)

            # Logic xác định MST đối tác thông minh:
            # Lọc bỏ MST của Thầy ra khỏi danh sách tìm được
            partners = [m for m in unique_msts if m != self.mst_owner]
            
            if partners:
                # Nếu có MST khác mình, đó chắc chắn là đối tác
                mst_doi_tac = partners[0]
            elif unique_msts:
                # Nếu chỉ thấy 1 MST và nó là của mình, có thể file thiếu MST kia
                mst_doi_tac = ""
            else:
                mst_doi_tac = ""

            return {
                "tax_code": mst_doi_tac,
                "total_payment": sotien,
                "created_date": date_match.group(1) if date_match else "2026-05-11",
                "buyer_name": f"Đối tác {mst_doi_tac}" if mst_doi_tac else "Khách hàng vãng lai",
                "sale_source": "XML_Import"
            }
        except Exception as e:
            logging.error(f"Lỗi khi xử lý file {xml_path}: {e}")
            return None

    def save_to_db(self, folder_path):
        # Tự động dọn dẹp để nạp mới hoàn toàn
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM invoices WHERE sale_source = 'XML_Import'")
        
        results = []
        for f in os.listdir(folder_path):
            if f.lower().endswith('.xml'):
                data = self.parse_invoice(os.path.join(folder_path, f))
                if data: results.append(data)
        
        cursor = conn.cursor()
        for item in results:
            cursor.execute('''INSERT INTO invoices (tax_code, total_payment, created_date, buyer_name, sale_source)
                              VALUES (?, ?, ?, ?, ?)''', 
                           (item['tax_code'], item['total_payment'], item['created_date'], item['buyer_name'], item['sale_source']))
        conn.commit()
        count = len(results)
        conn.close()
        return f"Đã dọn dẹp và nạp lại thành công {count} hóa đơn."