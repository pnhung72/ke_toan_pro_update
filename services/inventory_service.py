from models.product import Product
from models.purchase_order import PurchaseOrder
from models.journal_entry import JournalEntry
from datetime import datetime

class InventoryService:
    @staticmethod
    def import_product(product_code, quantity, unit_price, supplier, date=None):
        if not date:
            date = datetime.now().strftime("%d/%m/%Y")
        
        # Cập nhật tồn kho
        Product.update_stock(product_code, quantity, add=True)
        # Cập nhật giá nhập (có thể lưu giá nhập mới nhất)
        Product.update(product_code, price_buy=unit_price)
        # Lưu phiếu nhập
        from models.purchase_order import PurchaseOrder
        PurchaseOrder.create(date, product_code, quantity, unit_price, supplier)
        # Ghi nhận bút toán kép
        product = Product.get_by_code(product_code)
        total = quantity * unit_price
        JournalEntry.create(
            date=date,
            description=f"Nhập kho {product['name']} từ {supplier}",
            entries=[
                {"account": "156", "debit": total, "credit": 0},
                {"account": "331", "debit": 0, "credit": total}
            ]
        )
        return True