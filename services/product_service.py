from models.product import Product
from utils.logger import get_logger

logger = get_logger(__name__)

class ProductService:
    """Xử lý logic nghiệp vụ liên quan đến sản phẩm"""
    
    @staticmethod
    def get_all_products():
        try:
            return Product.get_all()
        except Exception as e:
            logger.error(f"Lỗi lấy sản phẩm: {e}")
            return []
    
    @staticmethod
    def get_product_by_code(code):
        try:
            return Product.get_by_code(code)
        except Exception as e:
            logger.error(f"Lỗi lấy sản phẩm {code}: {e}")
            return None
    
    @staticmethod
    def create_product(code, name, unit, price_sell, price_buy, stock=0, min_stock=0):
        try:
            existing = Product.get_by_code(code)
            if existing:
                return False, f"Mã sản phẩm '{code}' đã tồn tại"
            
            Product.create(code, name, unit, price_sell, price_buy, stock, min_stock)
            logger.info(f"Đã tạo sản phẩm: {code} - {name}")
            return True, "Thêm sản phẩm thành công"
        except Exception as e:
            logger.error(f"Lỗi tạo sản phẩm: {e}")
            return False, str(e)
    
    @staticmethod
    def update_product(code, **kwargs):
        try:
            Product.update(code, **kwargs)
            logger.info(f"Đã cập nhật sản phẩm: {code}")
            return True, "Cập nhật thành công"
        except Exception as e:
            logger.error(f"Lỗi cập nhật sản phẩm {code}: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_product(code):
        try:
            # Kiểm tra sản phẩm có trong hóa đơn không
            from models.invoice import Invoice
            invoices = Invoice.get_all()
            for inv in invoices:
                if inv.get('product_code') == code:
                    return False, "Sản phẩm đã có trong hóa đơn, không thể xóa"
            
            Product.delete(code)
            logger.info(f"Đã xóa sản phẩm: {code}")
            return True, "Xóa thành công"
        except Exception as e:
            logger.error(f"Lỗi xóa sản phẩm {code}: {e}")
            return False, str(e)
    
    @staticmethod
    def get_low_stock_products(threshold=None):
        """Lấy danh sách sản phẩm tồn kho thấp"""
        try:
            if threshold:
                products = Product.get_all()
                return [p for p in products if p['stock'] <= threshold]
            return Product.get_low_stock()
        except Exception as e:
            logger.error(f"Lỗi lấy sản phẩm tồn kho thấp: {e}")
            return []
    
    @staticmethod
    def update_stock(code, quantity, add=True):
        """Cập nhật tồn kho"""
        try:
            result = Product.update_stock(code, quantity, add)
            action = "nhập" if add else "xuất"
            logger.info(f"Đã {action} {quantity} sản phẩm {code}")
            return result
        except Exception as e:
            logger.error(f"Lỗi cập nhật tồn kho {code}: {e}")
            return False
    
    @staticmethod
    def search_products(keyword):
        """Tìm kiếm sản phẩm theo mã hoặc tên"""
        try:
            products = Product.get_all()
            keyword_lower = keyword.lower().strip()
            return [p for p in products 
                    if keyword_lower in p['code'].lower() 
                    or keyword_lower in p['name'].lower()]
        except Exception as e:
            logger.error(f"Lỗi tìm kiếm sản phẩm: {e}")
            return []