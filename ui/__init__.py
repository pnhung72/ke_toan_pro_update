# ui/__init__.py
from .main_window import MainWindow
from .product_tab import ProductTab
from .transaction_tab import TransactionTab
from .invoice_tab import InvoiceTab
from .debt_tab import DebtTab
from .report_tab import ReportTab

__all__ = [
    'MainWindow',
    'ProductTab',
    'TransactionTab',
    'InvoiceTab',
    'DebtTab',
    'ReportTab'
]