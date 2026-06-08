"""
Module phân tích XML hóa đơn điện tử
Hỗ trợ nhiều định dạng (Viettel, VNPT, Misa, ...)
"""

import xml.etree.ElementTree as ET
import re
from datetime import datetime
from .logger import get_logger

logger = get_logger()


class BaseInvoiceParser:
    """Parser cơ sở"""

    def parse(self, root, content_str):
        raise NotImplementedError


class ViettelParser(BaseInvoiceParser):
    """Parser cho hóa đơn Viettel (thường có namespace)"""

    def parse(self, root, content_str):
        # Tìm namespace thường dùng của Viettel
        ns = {'inv': 'http://www.viettel.com.vn/invoice'}
        try:
            seller_tax = self._get_text(root, './/inv:SellerTaxCode', ns)
            seller_name = self._get_text(root, './/inv:SellerName', ns)
            invoice_no = self._get_text(root, './/inv:InvoiceNo', ns)
            issue_date = self._get_text(root, './/inv:IssueDate', ns)
            total_wo_tax = self._get_float(root, './/inv:TotalAmountWithoutTax', ns)
            tax_amount = self._get_float(root, './/inv:TaxAmount', ns)
            total = self._get_float(root, './/inv:TotalAmount', ns)

            return {
                'seller_tax_code': seller_tax,
                'seller_name': seller_name,
                'invoice_no': invoice_no,
                'issue_date': self._normalize_date(issue_date),
                'total_amount_wo_tax': total_wo_tax,
                'tax_amount': tax_amount,
                'total_amount': total,
            }
        except Exception as e:
            logger.error(f"ViettelParser lỗi: {e}")
            return None

    def _get_text(self, root, xpath, ns):
        elem = root.find(xpath, ns)
        return elem.text.strip() if elem is not None and elem.text else ''

    def _get_float(self, root, xpath, ns):
        elem = root.find(xpath, ns)
        if elem is not None and elem.text:
            try:
                return float(elem.text.replace(',', ''))
            except (ValueError, AttributeError):
                return 0.0
        return 0.0

    def _normalize_date(self, date_str):
        if not date_str:
            return ''
        # Xử lý nhiều định dạng ngày
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y%m%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                continue
        return date_str


class GenericXMLParser(BaseInvoiceParser):
    """Parser chung cho XML không namespace, dùng tên thẻ phổ biến"""

    COMMON_TAGS = {
        'seller_tax_code': ['SellerTaxCode', 'MSTNguoiBan', 'maSoThue', 'taxCode'],
        'seller_name': ['SellerName', 'TenNguoiBan', 'tenNguoiBan', 'supplierName'],
        'invoice_no': ['InvoiceNo', 'SoHoaDon', 'soHoaDon', 'invoiceNumber'],
        'issue_date': ['IssueDate', 'NgayLap', 'ngayLapHoaDon', 'invoiceDate'],
        'total_amount_wo_tax': ['TotalAmountWithoutTax', 'TongTienHang', 'totalBeforeTax'],
        'tax_amount': ['TaxAmount', 'TienThue', 'taxAmount'],
        'total_amount': ['TotalAmount', 'TongThanhToan', 'totalAmount'],
    }

    def parse(self, root, content_str):
        try:
            result = {}
            for field, possible_tags in self.COMMON_TAGS.items():
                value = ''
                for tag in possible_tags:
                    elem = root.find(f'.//{tag}')
                    if elem is not None and elem.text:
                        value = elem.text.strip()
                        break
                    # Thử tìm không phân biệt hoa thường
                    for child in root.iter():
                        if child.tag.lower() == tag.lower() and child.text:
                            value = child.text.strip()
                            break
                    if value:
                        break
                if field in ['total_amount_wo_tax', 'tax_amount', 'total_amount']:
                    value = self._to_float(value)
                elif field == 'issue_date':
                    value = self._normalize_date(value)
                result[field] = value
            return result
        except Exception as e:
            logger.error(f"GenericXMLParser lỗi: {e}")
            return None

    def _to_float(self, val):
        if not val:
            return 0.0
        try:
            return float(val.replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0

    def _normalize_date(self, date_str):
        if not date_str:
            return ''
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y%m%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                continue
        return date_str


def parse_xml(file_path):
    """
    Hàm chính: nhận đường dẫn file XML, trả về dict các trường hóa đơn.
    Nếu không parse được, trả về None và ghi log lỗi.
    """
    logger.info(f"Đang parse file: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        # Thử parse với encoding UTF-8, fallback
        try:
            xml_str = content.decode('utf-8')
        except UnicodeDecodeError:
            xml_str = content.decode('utf-8', errors='replace')
        root = ET.fromstring(xml_str)

        # Phát hiện parser phù hợp (Viettel có namespace đặc trưng)
        if 'viettel' in xml_str.lower() or 'Viettel' in xml_str:
            parser = ViettelParser()
        else:
            parser = GenericXMLParser()

        result = parser.parse(root, xml_str)
        if result and result.get('invoice_no'):
            logger.info(f"Parse thành công: Số hóa đơn {result['invoice_no']}")
            return result
        else:
            logger.error(f"Parse thất bại: không tìm thấy số hóa đơn trong {file_path}")
            return None

    except ET.ParseError as e:
        logger.error(f"Lỗi cú pháp XML {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Lỗi không xác định khi parse {file_path}: {e}")
        return None