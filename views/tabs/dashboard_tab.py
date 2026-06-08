# -*- coding: utf-8 -*-
"""
DashboardTab - Trang tong quan
"""

import tkinter as tk
from tkinter import ttk
import math
from views.tabs.base_tab import BaseTab
from services.dashboard_service import DashboardService
from theme import get_font
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
#print("⚠️ Matplotlib chưa được cài đặt. Cài đặt bằng: pip install matplotlib")


def safe_value(value, default=0):
    """Chuyển đổi giá trị an toàn, xử lý NaN"""
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    try:
        return float(value) if not math.isnan(float(value)) else default
    except (ValueError, TypeError):
        return default


class DashboardTab(BaseTab):
    """Tab dashboard tong quan"""
    
    def __init__(self, parent, notebook, controller=None):
        from core.database.connection_pool import get_connection_pool
        from config import DB_PATH
        self.dashboard_service = DashboardService(get_connection_pool(DB_PATH))
        super().__init__(parent, notebook, controller)
    
    def setup_ui(self):
        """Tao giao dien dashboard"""
        # === STYLE CHO FONT LỚN ===
        style = ttk.Style()
        style.configure("Dashboard.TLabelframe.Label", font=get_font("bold"))
        style.configure("Dashboard.TButton", font=get_font("label"), padding=8)
        style.configure("Dashboard.TLabel", font=get_font("label"))
        style.configure("Dashboard.Treeview", font=get_font("small"), rowheight=28)
        style.configure("Dashboard.Treeview.Heading", font=get_font("bold"))
        
        # Notebook con cho dashboard
        self.inner_notebook = ttk.Notebook(self.frame)
        self.inner_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 1: Tong quan
        self.overview_frame = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(self.overview_frame, text="📊 Tổng quan")
        self._setup_overview_tab()
        
        # Tab 2: Bieu do
        self.chart_frame = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(self.chart_frame, text="📈 Biểu đồ")
        self._setup_chart_tab()
        
        # Tab 3: Cong no
        self.debt_frame = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(self.debt_frame, text="💰 Công nợ")
        self._setup_debt_tab()
        
        # Tab 4: Du bao
        self.forecast_frame = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(self.forecast_frame, text="🔮 Dự báo")
        self._setup_forecast_tab()
    
    def _setup_overview_tab(self):
        """Tab tổng quan - Bố cục 2 cột cân đối, dùng dữ liệu thật từ service"""
        # Frame cuộn
        canvas = tk.Canvas(self.overview_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.overview_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        
        # Frame chính với padding
        content_frame = ttk.Frame(scrollable_frame, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Cấu hình 2 cột cân đối
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # ========== CỘT TRÁI: CÁC CARD ==========
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10)
        left_frame.columnconfigure(0, weight=1)
        
        # Lấy dữ liệu thật từ service (không fallback về dữ liệu cứng)
        try:
            revenue_data = self.dashboard_service.get_revenue_stats()
            revenue_value = safe_value(revenue_data.get('monthly_revenue', 0) if revenue_data else 0)
            revenue_change = safe_value(revenue_data.get('change_percent', 0) if revenue_data else 0)
        except Exception as e:
            print(f"Lỗi lấy doanh thu: {e}")
            revenue_value = 0
            revenue_change = 0
        
        # Card doanh thu
        card1 = ttk.LabelFrame(left_frame, text="📅 DOANH THU THÁNG", style="Dashboard.TLabelframe")
        card1.pack(fill="x", pady=10, ipady=15, ipadx=10)
        
        change_color = "green" if revenue_change >= 0 else "red"
        change_sign = "+" if revenue_change >= 0 else ""
        
        ttk.Label(card1, text=f"{revenue_value:,.0f} VNĐ".replace(",", "."),
                  font=get_font("title"), foreground="#2196F3").pack(pady=(10, 5))
        ttk.Label(card1, text=f"{change_sign}{revenue_change:.1f}% so với tháng trước",
                  font=get_font("label"), foreground=change_color).pack(pady=(0, 10))
        
        # Card công nợ
        try:
            debt_data = self.dashboard_service.get_debt_summary()
            total_debt = safe_value(debt_data.get('total_debt', 0) if debt_data else 0)
            overdue = safe_value(debt_data.get('overdue', 0) if debt_data else 0)
        except Exception as e:
            print(f"Lỗi lấy công nợ: {e}")
            total_debt = 0
            overdue = 0
        
        card2 = ttk.LabelFrame(left_frame, text="💰 CÔNG NỢ", style="Dashboard.TLabelframe")
        card2.pack(fill="x", pady=10, ipady=15, ipadx=10)
        
        ttk.Label(card2, text=f"{total_debt:,.0f} VNĐ".replace(",", "."),
                  font=get_font("title"), foreground="#FF9800").pack(pady=(10, 5))
        ttk.Label(card2, text=f"Quá hạn: {overdue:,.0f} VNĐ".replace(",", "."),
                  font=get_font("label"), foreground="red").pack(pady=(0, 10))
        
        # Card thuế
        try:
            tax_data = self.dashboard_service.get_tax_summary()
            pending = safe_value(tax_data.get('pending', 0) if tax_data else 0)
            paid = safe_value(tax_data.get('paid', 0) if tax_data else 0)
        except Exception as e:
            print(f"Lỗi lấy thuế: {e}")
            pending = 0
            paid = 0
        
        card3 = ttk.LabelFrame(left_frame, text="📋 THUẾ PHẢI NỘP", style="Dashboard.TLabelframe")
        card3.pack(fill="x", pady=10, ipady=15, ipadx=10)
        
        ttk.Label(card3, text=f"{pending:,.0f} VNĐ".replace(",", "."),
                  font=get_font("title"), foreground="#4CAF50").pack(pady=(10, 5))
        ttk.Label(card3, text=f"Đã nộp: {paid:,.0f} VNĐ".replace(",", "."),
                  font=get_font("label")).pack(pady=(0, 10))
        
        # ========== CỘT PHẢI: DANH SÁCH ==========
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        right_frame.columnconfigure(0, weight=1)
        
        # Sản phẩm bán chạy
        try:
            products = self.dashboard_service.get_top_products()
        except Exception as e:
            print(f"Lỗi lấy top sản phẩm: {e}")
            products = []
        
        products_frame = ttk.LabelFrame(right_frame, text="🏆 TOP SẢN PHẨM BÁN CHẠY",
                                        style="Dashboard.TLabelframe", padding=15)
        products_frame.pack(fill="x", pady=10)
        
        if products:
            for i, p in enumerate(products, 1):
                item_frame = ttk.Frame(products_frame)
                item_frame.pack(fill="x", pady=8)
                
                # SỬA TẠI ĐÂY: Dùng 'product_name' thay vì 'name'
                ten_hien_thi = p.get('product_name', 'Không xác định')
                ttk.Label(item_frame, text=f"{i}. {ten_hien_thi}",
                          font=get_font("label")).pack(side="left")
                
                # SỬA TẠI ĐÂY: Dùng 'qty' thay vì 'quantity'
                so_luong = p.get('qty', 0)
                # Lấy đơn vị tính 'unit' đã được Service gửi sang
                dvt = p.get('unit', 'lít')
                
                # Hiển thị số lượng và đơn vị tính tự động
                ttk.Label(item_frame, text=f"{so_luong} {dvt}",
                          font=get_font("label"), foreground="blue").pack(side="right")
        else:
            ttk.Label(products_frame, text="Chưa có dữ liệu",
                      font=get_font("label"), foreground="gray").pack(pady=20)
        
        # Giao dịch gần đây
        try:
            transactions = self.dashboard_service.get_recent_transactions()
        except Exception as e:
            print(f"Lỗi lấy giao dịch: {e}")
            transactions = []
        
        trans_frame = ttk.LabelFrame(right_frame, text="📝 GIAO DỊCH GẦN ĐÂY",
                                     style="Dashboard.TLabelframe", padding=15)
        trans_frame.pack(fill="both", expand=True, pady=10)
        
        if transactions:
            for t in transactions:
                color = "#4CAF50" if t.get('type') == "Thu" else "#F44336"
                item_frame = ttk.Frame(trans_frame)
                item_frame.pack(fill="x", pady=8)
                ttk.Label(item_frame, text=t.get('date', ''), font=get_font("label")).pack(side="left", padx=10)
                ttk.Label(item_frame, text=t.get('type', ''), font=get_font("label"), foreground=color).pack(side="left", padx=15)
                amount = safe_value(t.get('amount', 0))
                ttk.Label(item_frame, text=f"{amount:,.0f} VNĐ".replace(",", "."),
                          font=get_font("label")).pack(side="right", padx=10)
        else:
            ttk.Label(trans_frame, text="Chưa có giao dịch",
                      font=get_font("label"), foreground="gray").pack(pady=20)
    
    def _setup_chart_tab(self):
        """Tab bieu do - ĐÃ SỬA LỖI FONT VÀ NaN"""
        try:
            # 1. Lazy Loading: Chỉ import khi mở tab để bảo vệ font hệ thống
            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Buộc matplotlib không xâm lấn vào giao diện chính
            matplotlib.use('Agg') 
            # Đảm bảo font trong biểu đồ không gây xung đột với font hệ thống
            plt.rcParams['font.family'] = 'sans-serif'
        except ImportError:
            ttk.Label(self.chart_frame, 
                      text="⚠️ Matplotlib chưa được cài đặt.\nChạy lệnh: pip install matplotlib",
                      font=get_font("label"), foreground="red").pack(pady=50)
            return
        
        try:
            # 2. Bieu do doanh thu (Giữ nguyên logic của Thầy)
            data = self.dashboard_service.get_revenue_by_month()
            
            # Xử lý dữ liệu an toàn
            months = data.get("months", [])
            revenues = [safe_value(r) for r in data.get("revenues", [])]
            
            # Đảm bảo months và revenues có cùng độ dài
            if len(months) == 0:
                months = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]
            if len(revenues) < len(months):
                revenues.extend([0] * (len(months) - len(revenues)))
            
            # Sử dụng plt từ nội bộ hàm
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Bieu do cot
            ax1.bar(months, revenues, color='skyblue')
            ax1.set_title('Doanh thu theo tháng', fontsize=14)
            ax1.set_xlabel('Tháng', fontsize=12)
            ax1.set_ylabel('Doanh thu (VND)', fontsize=12)
            ax1.tick_params(axis='x', rotation=45, labelsize=11)
            ax1.tick_params(axis='y', labelsize=11)
            
            # 3. Bieu do tron - cong no (Xử lý dữ liệu an toàn)
            debt_data = self.dashboard_service.get_debt_summary()
            total_debt = safe_value(debt_data.get('total_debt', 0) if debt_data else 0)
            paid = safe_value(debt_data.get('paid', 0) if debt_data else 0)
            overdue = safe_value(debt_data.get('overdue', 0) if debt_data else 0)
            
            unpaid = total_debt - paid - overdue
            if unpaid < 0:
                unpaid = 0
            
            # Sửa lại nhãn cho gọn và thêm khoảng cách để không bị đè nhau
            labels = ['Đã thu', 'Chưa thu', 'Quá hạn']
            sizes = [paid, unpaid, overdue]
            sizes = [max(0, s) for s in sizes] # Đảm bảo không có giá trị âm
             
            # Vẽ biểu đồ tròn thông minh: Chỉ hiện nhãn nếu có dữ liệu > 0
            if sum(sizes) > 0:
                colors = ['#4CAF50', '#FF9800', '#F44336']
                full_labels = ['Đã thu', 'Chưa thu', 'Quá hạn']
                
                # Tạo danh sách nhãn lọc: nếu giá trị bằng 0 thì để trống ""
                display_labels = [l if s > 0 else "" for l, s in zip(full_labels, sizes)]
                
                ax2.pie(sizes, labels=display_labels, colors=colors, autopct=lambda p: '{:.1f}%'.format(p) if p > 0 else '', 
                        textprops={'fontsize': 11}, 
                        labeldistance=1.2)
            else:
                ax2.text(0.5, 0.5, 'Chưa có dữ liệu', ha='center', va='center', fontsize=14)
            ax2.set_title('Tình trạng công nợ', fontsize=14)
            
            plt.tight_layout()
            
            # Nhúng biểu đồ vào frame mà không ảnh hưởng font toàn cục
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            ttk.Label(self.chart_frame, text=f"Lỗi hiển thị biểu đồ: {str(e)}", 
                      font=get_font("label"), foreground="red").pack(pady=50)
    
    def _setup_debt_tab(self):
        """Tab cong no"""
        try:
            debt_data = self.dashboard_service.get_debt_summary()
            total_debt = safe_value(debt_data.get('total_debt', 0) if debt_data else 0)
            paid = safe_value(debt_data.get('paid', 0) if debt_data else 0)
            overdue = safe_value(debt_data.get('overdue', 0) if debt_data else 0)
            customers_count = safe_value(debt_data.get('customers_count', 0) if debt_data else 0)
        except Exception:
            total_debt = 0
            paid = 0
            overdue = 0
            customers_count = 0
        
        info_frame = ttk.Frame(self.debt_frame, padding=20)
        info_frame.pack(fill="both", expand=True)
        
        # Tong cong no
        total_frame = ttk.LabelFrame(info_frame, text="TỔNG CÔNG NỢ", 
                                     style="Dashboard.TLabelframe", padding=15)
        total_frame.pack(fill="x", pady=10)
        ttk.Label(total_frame, text=f"{total_debt:,.0f} VNĐ".replace(",", "."), 
                  font=get_font("title"), foreground="#2196F3").pack(pady=10)
        
        # Chi tiet
        detail_frame = ttk.Frame(info_frame)
        detail_frame.pack(fill="x", pady=15)
        
        ttk.Label(detail_frame, text=f"✅ Đã thanh toán: {paid:,.0f} VNĐ".replace(",", "."), 
                  font=get_font("label"), foreground="#4CAF50").pack(anchor="w", pady=5)
        ttk.Label(detail_frame, text=f"⚠️ Quá hạn: {overdue:,.0f} VNĐ".replace(",", "."), 
                  font=get_font("label"), foreground="#F44336").pack(anchor="w", pady=5)
        ttk.Label(detail_frame, text=f"👥 Số khách hàng: {customers_count}", 
                  font=get_font("label"), foreground="#2196F3").pack(anchor="w", pady=5)
        
        # Danh sach khach hang cong no
        list_frame = ttk.LabelFrame(info_frame, text="📋 KHÁCH HÀNG CÔNG NỢ", 
                                    style="Dashboard.TLabelframe", padding=10)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("customer", "debt", "due_date", "status")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15, style="Dashboard.Treeview")
        tree.heading("customer", text="Khách hàng")
        tree.heading("debt", text="Công nợ (VNĐ)")
        tree.heading("due_date", text="Hạn trả")
        tree.heading("status", text="Trạng thái")
        
        tree.column("customer", width=280, anchor="w")
        tree.column("debt", width=180, anchor="e")
        tree.column("due_date", width=120, anchor="center")
        tree.column("status", width=120, anchor="center")
        
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Thêm dữ liệu
        self._load_debt_list(tree)
    
    def _load_debt_list(self, tree):
        """Tải danh sách công nợ"""
        try:
            customers = self.dashboard_service.get_debt_customers()
            if customers:
                for c in customers:
                    debt_val = safe_value(c.get('debt', 0))
                    status_color = "🔴 Quá hạn" if c.get('is_overdue') else "🟢 Đang hạn"
                    tree.insert("", "end", values=(
                        c.get('customer_name', ''),
                        f"{debt_val:,.0f}".replace(",", "."),
                        c.get('due_date', ''),
                        status_color
                    ))
            else:
                tree.insert("", "end", values=("Chưa có dữ liệu", "", "", ""))
        except Exception:
            tree.insert("", "end", values=("Chưa có dữ liệu công nợ", "", "", ""))
    
    def _setup_forecast_tab(self):
        """Tab du bao"""
        try:
            forecast = self.dashboard_service.get_cash_flow_forecast(30)
        except Exception:
            forecast = []
        
        main_frame = ttk.Frame(self.forecast_frame, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Summary
        summary_frame = ttk.LabelFrame(main_frame, text="🔮 DỰ BÁO 30 NGÀY", 
                                       style="Dashboard.TLabelframe", padding=15)
        summary_frame.pack(fill="x", pady=10)
        
        if forecast:
            total_inflow = sum(safe_value(f.get("inflow", 0)) for f in forecast)
            total_outflow = sum(safe_value(f.get("outflow", 0)) for f in forecast)
            final_balance = total_inflow - total_outflow
            balance_color = "#4CAF50" if final_balance >= 0 else "#F44336"
            
            ttk.Label(summary_frame, text=f"💰 Tổng thu dự kiến: {total_inflow:,.0f} VNĐ".replace(",", "."), 
                      font=get_font("label"), foreground="#4CAF50").pack(anchor="w", pady=5)
            ttk.Label(summary_frame, text=f"💸 Tổng chi dự kiến: {total_outflow:,.0f} VNĐ".replace(",", "."), 
                      font=get_font("label"), foreground="#F44336").pack(anchor="w", pady=5)
            ttk.Label(summary_frame, text=f"📊 Cân đối: {final_balance:,.0f} VNĐ".replace(",", "."), 
                      font=get_font("bold"), foreground=balance_color).pack(anchor="w", pady=10)
        else:
            ttk.Label(summary_frame, text="Chưa có dữ liệu dự báo", 
                      font=get_font("label"), foreground="gray").pack(pady=20)
        
        # Bang du bao
        table_frame = ttk.LabelFrame(main_frame, text="📅 CHI TIẾT THEO NGÀY", 
                                     style="Dashboard.TLabelframe", padding=10)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("date", "inflow", "outflow", "balance")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18, style="Dashboard.Treeview")
        tree.heading("date", text="Ngày")
        tree.heading("inflow", text="Thu (VNĐ)")
        tree.heading("outflow", text="Chi (VNĐ)")
        tree.heading("balance", text="Cân đối (VNĐ)")
        
        tree.column("date", width=120, anchor="center")
        tree.column("inflow", width=180, anchor="e")
        tree.column("outflow", width=180, anchor="e")
        tree.column("balance", width=180, anchor="e")
        
        if forecast:
            for f in forecast[:30]:
                inflow = safe_value(f.get("inflow", 0))
                outflow = safe_value(f.get("outflow", 0))
                balance = safe_value(f.get("balance", 0))
                tree.insert("", "end", values=(
                    f.get("date", ""),
                    f"{inflow:,.0f}".replace(",", "."),
                    f"{outflow:,.0f}".replace(",", "."),
                    f"{balance:,.0f}".replace(",", ".")
                ))
        else:
            tree.insert("", "end", values=("Chưa có dữ liệu", "", "", ""))
        
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def _create_card(self, parent, title, value, subtitle):
        """Tao card thong ke"""
        frame = ttk.LabelFrame(parent, text=title, padding=12)
        ttk.Label(frame, text=value, font=get_font("title")).pack(anchor="w")
        ttk.Label(frame, text=subtitle, font=get_font("label")).pack(anchor="w")
        return frame
    
    def bind_events(self):
        pass
    
    def load_data(self):
        """Tai du lieu cho dashboard"""
        self.show_message("✅ Dashboard đã sẵn sàng", is_error=False)