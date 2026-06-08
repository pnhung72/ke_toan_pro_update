# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import sys
import webbrowser
from theme import get_font, apply_theme
import importlib
import logging

def force_get_version():
    """Đọc trực tiếp từ file version.txt, không qua cache"""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        # Đường dẫn từ ui/about_tab.py ra thư mục gốc
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    v_path = os.path.join(base_dir, "version.txt")
    try:
        if os.path.exists(v_path):
            with open(v_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return "5.2.3" # Giá trị dự phòng nếu không thấy file

VERSION = force_get_version()
try:
    import config
    # Buộc Python nạp lại file config để lấy phiên bản mới nhất vừa build
    importlib.reload(config)
    VERSION = getattr(config, "VERSION", "n++5.0.8")
except ImportError:
    VERSION = "n++5.0.8"


class AboutTab(ttk.Frame):
    def __init__(self, parent, notebook, root): # Thêm 'root' vào đây
        self.root = root  # <--- BẮT BUỘC THÊM DÒNG NÀY ĐỂ KHAI BÁO
        self.parent = parent
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="✨ Giới thiệu")
        self.bg_color = self.frame.cget("bg")
        apply_theme()
        self.create_widgets()

    def _get_icon_path(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, 'icon.ico')

    def _get_qr_path(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(__file__))
        possible_names = ['ACB.jpeg', 'ACB.jpg', 'qr_code.jpeg', 'qr_code.jpg', 'qr.png']
        for name in possible_names:
            path = os.path.join(base_dir, name)
            if os.path.exists(path):
                return path
        return None

    def _share_facebook(self):
        webbrowser.open("https://www.facebook.com/sharer/sharer.php?u=https://keotoanpro.com")

    def _share_zalo(self):
        messagebox.showinfo("Chia sẻ Zalo", "Mã QR Zalo: 0982493474\n\nHoặc quét mã QR để liên hệ")

    def _share_messenger(self):
        webbrowser.open("https://m.me/0982493474")

    def _copy_link(self):
        self.parent.clipboard_clear()
        self.parent.clipboard_append("https://keotoanpro.com")
        messagebox.showinfo("Đã sao chép", "Link giới thiệu đã được sao chép!")

    def create_widgets(self):
        main_frame = tk.Frame(self.frame, bg=self.bg_color, padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)

        # Cấu trúc Canvas để cuộn trang
        canvas = tk.Canvas(main_frame, highlightthickness=0, bg=self.bg_color)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.bg_color)

        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def _on_canvas_configure(event):
            canvas.itemconfig(self.canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.container = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        self.container.pack(pady=20, padx=20, anchor="center")

        # === HEADER GỌN GÀNG: LOGO + TÊN PHẦN MỀM CÙNG 1 DÒNG ===
        top_frame = tk.Frame(self.container, bg=self.bg_color)
        top_frame.pack(pady=10)
        
        # 1. Logo (để trống, chờ nạp)
        self.logo_label = tk.Label(top_frame, bg=self.bg_color)
        self.logo_label.grid(row=0, column=0, padx=(0, 15), pady=0)
        
        # 2. Tiêu đề duy nhất
        title_label = tk.Label(top_frame, text=f"PHẦN MỀM KẾ TOÁN PRO v{VERSION}", 
                               font=get_font("title"), fg="#1A237E", bg=self.bg_color)
        title_label.grid(row=0, column=1, pady=0)
        
        # 3. Phiên bản và trạng thái nằm ngay dưới header
        tk.Label(self.container, text=f"Phiên bản Doanh nghiệp {VERSION}",
                 font=get_font("subtitle"), fg="#2E7D32", bg=self.bg_color).pack(pady=2)
        
        tk.Label(self.container, 
            text="✓ Đã kích hoạt hệ thống báo lỗi tự động (Smart Error Reporting)", 
            font=get_font("label", bold=True), fg="#2e7d32", bg=self.bg_color).pack(pady=2)

        ttk.Separator(self.container, orient="horizontal").pack(fill="x", pady=10)
        
        # Gọi lệnh nạp ảnh sau 500ms
        self.container.after(500, self.load_images_delayed)
        
        def _on_canvas_configure(event):
            # Ép chiều rộng của frame nội dung bằng với chiều rộng của canvas
            canvas.itemconfig(self.canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Thêm một frame đệm để gom nội dung vào giữa
        self.container = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        self.container.pack(pady=20, padx=20, anchor="center")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", on_mousewheel) # Thêm self. vào trước

        # === PHẦN GIỚI THIỆU ĐỘT PHÁ TỰ ĐỘNG ===
        intro_text = (
            f"Cột mốc v{VERSION} đánh dấu bước nhảy vọt công nghệ: Quy hoạch Hệ sinh thái ERP Số "
            "phân tầng chuẩn hóa toàn diện, giải phóng hiệu năng lõi (Clean Core), tích hợp "
            "Trung tâm Điều hành Admin Core chuyên nghiệp và hệ thống tự động hóa thông minh, "
            "giúp ứng dụng luôn vận hành ở trạng thái tối ưu và mượt mà nhất."
        )
        
        tk.Label(self.container, text=intro_text, font=get_font("label"), 
                 fg="#2E7D32", bg=self.bg_color, wraplength=700, justify="center").pack(pady=10)
                 
        new_features_frame = tk.LabelFrame(self.container, text=f"🚀 ĐỘT PHÁ CÔNG NGHỆ PHIÊN BẢN {VERSION}",
                                           font=get_font("label", bold=True), bg=self.bg_color, 
                                           fg="#1A237E", padx=40, pady=12)
        
        new_features_frame.pack(pady=8, anchor="center")
        
        # Danh sách tính năng mới - Ngắn gọn, nổi bật, ấn tượng mạnh
        new_features = [
            ("🤖", " AI thông minh chạy 100% offline", "Gợi ý danh mục giao dịch theo ngữ cảnh, dự báo dòng tiền, phát hiện bất thường – bảo mật tuyệt đối, không gửi dữ liệu ra ngoài."),
            ("📸", " nhập hóa đơn bằng OCR (Local)", "Quét ảnh/PDF, tự động nhận diện và điền thông tin hóa đơn vào form, hỗ trợ EasyOCR tiếng Việt."),
            ("🧠", " học từ người dùng (Active Learning)", "Mô hình phân loại tự cải thiện dựa trên phản hồi 'đúng/sai', retrain khi đủ dữ liệu."),
            ("📈", " dự báo dòng tiền & cảnh báo bất thường", "Sử dụng Exponential Smoothing và Isolation Forest, hiển thị đồ thị trực quan trong tab AI."),
            ("🧱", " kiến trúc cắm ghép động plug-and-play", "Tự động điều hướng và nạp phân hệ ngành nghề chuyên sâu qua ModuleRegistry."),
            ("📧", " tự động hóa hóa đơn đầu vào (Email XML)", "Quét email, tải file XML, phân tích và lưu vào hàng đợi duyệt – hỗ trợ nhiều định dạng (Viettel, VNPT, Misa).")
        ]
        
        for icon, title_text, desc in new_features:
            item_frame = tk.Frame(new_features_frame, bg=self.bg_color)
            item_frame.pack(fill="x", pady=4)
            
            # Khung con chứa nội dung cũng được neo vào giữa
            content_sub = tk.Frame(item_frame, bg=self.bg_color)
            content_sub.pack(anchor="center")
            
            tk.Label(content_sub, text=f"{icon} {title_text}:", 
                     font=get_font("label", bold=True), bg=self.bg_color).pack(side="left")
            tk.Label(content_sub, text=f" {desc}", 
                     font=get_font("label"), fg="#333", bg=self.bg_color).pack(side="left")

        # === PHẦN 2: NỖI ĐAU KHÁCH HÀNG (CĂN GIỮA) ===
        pain_frame = tk.LabelFrame(self.container, text="😫 NỖI ĐAU CỦA DOANH NGHIỆP?",
                                    font=get_font("label", bold=True), bg=self.bg_color, fg="#C62828", padx=15, pady=12)
        pain_frame.pack(pady=8, anchor="center")
        # === PHẦN NỖI ĐAU THỊ TRƯỜNG - ĐÁNH TRÚNG TÂM LÝ KHÁCH HÀNG ===
        pains = [
            "❌ phí thuê bao đắt đỏ, ép buộc trả tiền gia hạn và nâng cấp hàng năm.",
            "❌ dữ liệu lưu trữ tập trung trên cloud bên thứ ba, nguy cơ rò rỉ thông tin mật.",
            "❌ lệ thuộc hoàn toàn vào internet, mất kết nối mạng là hệ thống đóng băng."
        ]
        for pain in pains:
            tk.Label(pain_frame, text=pain, font=get_font("label"), bg=self.bg_color, anchor="center").pack(fill="x", pady=3)

        # === PHẦN 3: GIẢI PHÁP TỐI ƯU (CĂN GIỮA) ===
        solution_frame = tk.LabelFrame(self.container, text="🔥 GIẢI PHÁP TỐI ƯU TỪ KẾ TOÁN PRO",
                                       font=get_font("label", bold=True), bg=self.bg_color, fg="#2E7D32", padx=15, pady=12)
        solution_frame.pack(pady=8, anchor="center")
        # === PHẦN GIẢI PHÁP ĐỘT PHÁ - ĐÁP ỨNG TRỰC DIỆN NỖI ĐAU ===
        solutions = [
            (
                "☁️", 
                "hệ sinh thái đám mây lai độc bản:", 
                "Đồng bộ ngầm đa luồng (Multi-Threading) về két sắt Drive riêng của khách hàng, bảo mật dữ liệu tuyệt đối."
            ),
            (
                "🧱", 
                "kiến trúc cắm ghép động đa ngành:", 
                "Kích hoạt mở rộng tức thì phân hệ Xăng dầu, Nước mắm YaTrang Nha Trang từ xa qua chuỗi License Key thông minh."
            ),
            (
                "📋", 
                "đón đầu pháp lý chuẩn hóa mới:", 
                "Tự động hóa kiểm soát biểu mẫu, tuân thủ trọn vẹn Thông tư 18/2026 & 99/2025, tối ưu hóa quyết toán thuế."
            ),
            (
                "🧩", 
                "tùy biến theo yêu cầu (add‑on đặt riêng):", 
                "Doanh nghiệp có thể yêu cầu xây dựng thêm module nghiệp vụ đặc thù (quản lý hạn sử dụng, lô hàng, báo giá tự động...), kích hoạt từ xa qua License Key."
            ),
            (
                "🧠", 
                "trí tuệ nhân tạo local (AI Offline):", 
                "Gợi ý thông minh, dự báo, phát hiện bất thường, học từ người dùng – tất cả chạy trên máy tính của bạn, không cần Internet, bảo mật tuyệt đối."
            ),
        ]
        
        for icon, s_title, s_desc in solutions:
            s_item = tk.Frame(solution_frame, bg=self.bg_color)
            s_item.pack(fill="x", pady=6)
            
            s_content = tk.Frame(s_item, bg=self.bg_color)
            s_content.pack(anchor="w", fill="x", padx=10)
            
            # Tách nhãn Icon ra riêng, ép khuôn width=3 để triệt tiêu lỗi khoảng cách rộng
            lbl_icon = tk.Label(s_content, text=icon, font=("Segoe UI Emoji", 12), bg=self.bg_color, width=3, anchor="center")
            lbl_icon.pack(side="left", padx=(0, 5))
            
            # Gom Tiêu đề và Mô tả vào 1 nhãn, đặt wraplength=600 để tự động xuống hàng, chống lỗi đè/cắt chữ
            full_text = f"{s_title}: {s_desc}"
            lbl_text = tk.Label(
                s_content, 
                text=full_text, 
                font=get_font("label"), 
                fg="#333", 
                bg=self.bg_color,
                justify="left",
                anchor="w",
                wraplength=600
            )
            lbl_text.pack(side="left", fill="x", expand=True)

        # === PHẦN 4: BẢNG GIÁ ĐẦU TƯ (CĂN GIỮA ĐỦ 3 GÓI KHỚP LICENSE KÈM THEO) ===
        price_frame = tk.LabelFrame(self.container, text="💰 GIÁ TRỊ ĐẦU TƯ TRỌN ĐỜI",
                                    font=get_font("label", bold=True), bg=self.bg_color, fg="black", padx=15, pady=12)
        price_frame.pack(pady=8, anchor="center")
        price_grid = tk.Frame(price_frame, bg=self.bg_color)
        price_grid.pack(anchor="center")
        
        # Danh sách bổ sung trọn vẹn 3 gói bản quyền theo đúng hệ thống sinh mã
        # === PHẦN GIÁ TRỊ ĐẦU TƯ TRỌN ĐỜI - BẢNG GIÁ 3 GÓI PHÂN TẦNG ===
        prices = [
            ("gói basic", "1.200.000đ", "Dành cho cá nhân & Hộ kinh doanh.\nĐầy đủ nghiệp vụ hạch toán thuế cốt lõi."),
            ("gói pro", "2.500.000đ", "Dành cho DN & Kế toán dịch vụ.\nGồm Bank-Connect, Audit, và khả năng mua thêm add‑on tự động hóa hóa đơn đầu vào."),
            ("gói enterprise", "5.000.000đ", "Đặc quyền tối cao hệ sinh thái số ERP.\nEmail Intelligence, Admin Core, Phân tích AI, và ưu tiên hỗ trợ. Có thể tùy chỉnh thêm add‑on theo yêu cầu."),
        ]
        for i, (p_name, p_val, p_desc) in enumerate(prices):
            card = tk.Frame(price_grid, relief="ridge", borderwidth=2, bg="white", padx=12, pady=12)
            card.grid(row=0, column=i, padx=8, pady=8, sticky="n")
            tk.Label(card, text=p_name, font=get_font("label", bold=True), bg="white").pack()
            tk.Label(card, text=p_val, font=get_font("title"), fg="#D32F2F", bg="white").pack(pady=6)
            tk.Label(card, text=p_desc, font=get_font("small"), fg="#666", bg="white", wraplength=170).pack()

        # === PHẦN 5: CAM KẾT (CĂN GIỮA) ===
        support_frame = tk.LabelFrame(self.container, text="🎯 CAM KẾT TỪ NGOCPHAN",
                                      font=get_font("label", bold=True), bg=self.bg_color, fg="black", padx=15, pady=15)
        support_frame.pack(pady=10, anchor="center")
        # === PHẦN CAM KẾT HỖ TRỢ - ĐẬP TAN MỌI DO DỰ CỦA KHÁCH HÀNG ===
        supports = [
            "✅ bảo hành nền tảng lõi và hỗ trợ kỹ thuật trọn đời từ chính Tác giả.",
            "✅ miễn phí cấp quyền, kích hoạt phân hệ ngành nghề từ xa qua License Key.",
            "✅ tự động đồng bộ, cập nhật mẫu biểu thuế mới nhất (Thông tư 18/2026 & 99/2025).",
            "✅ hỗ trợ vận hành, tối ưu cấu hình bảo mật qua UltraViewer/Zalo chuyên sâu 24/7.",
            "✅ **tích hợp và hướng dẫn sử dụng tính năng tự động quét hóa đơn XML từ email.**",
            "✅ **Dùng thử miễn phí 30 ngày, trải nghiệm toàn bộ tính năng trước khi quyết định mua.**"   # Thêm dòng này
        ]
        for sup in supports:
            tk.Label(support_frame, text=sup, font=get_font("label"), bg=self.bg_color, anchor="center").pack(fill="x", pady=4)
        # === PHẦN 6: LIÊN HỆ & QR ===
        contact_frame = tk.LabelFrame(self.container, text="📞 LIÊN HỆ NGAY",
                                      font=get_font("label", bold=True), bg=self.bg_color, fg="black", padx=15, pady=15)
        contact_frame.pack(pady=10, anchor="center")
        contact_grid = tk.Frame(contact_frame, bg=self.bg_color)
        contact_grid.pack(anchor="center")
        info_col = tk.Frame(contact_grid, bg=self.bg_color)
        info_col.grid(row=0, column=0, padx=20, sticky="n")
        for text in ["👨‍💻 Tác giả: Phan Ngọc Hùng", "📧 Email: pnhungc3nvt@gmail.com", "📱 Zalo: 0982493474", "🏦 ACB: 24205887 - PHAN NGOC HUNG", "🌐 Website: https://keotoanpro.com", "🔧 Hỗ trợ cài đặt add-on: 0982493474"]:
            tk.Label(info_col, text=text, font=get_font("label"), bg=self.bg_color, anchor="w").pack(anchor="w", pady=6)

        # === PHẦN 6: LIÊN HỆ & QR (Thay thế đoạn load QR cũ) ===
        # === PHẦN 6: LIÊN HỆ & QR (KHỞI TẠO TRỐNG) ===
        qr_col = tk.Frame(contact_grid, bg=self.bg_color)
        qr_col.grid(row=0, column=1, padx=20, sticky="n")
        
        # Tạo Label QR trống ngay từ đầu
        self.qr_label = tk.Label(qr_col, bg=self.bg_color)
        self.qr_label.pack()
        
        # Nhãn hướng dẫn luôn hiển thị
        tk.Label(qr_col, text="Quét mã QR để thanh toán", font=get_font("label"), bg=self.bg_color).pack()

        # === PHẦN 7: CHUYỂN KHOẢN ===
        transfer_frame = tk.Frame(contact_frame, bg=self.bg_color)
        transfer_frame.pack(pady=10)
        tk.Label(transfer_frame, text="⚠️ NỘI DUNG CHUYỂN KHOẢN BẮT BUỘC:",
                 font=get_font("label", bold=True), fg="#F44336", bg=self.bg_color).pack()
        tk.Label(transfer_frame, text="MUA PHẦN MỀM + TÊN + SĐT + EMAIL",
                 font=get_font("label", bold=True), fg="#2196F3", bg=self.bg_color).pack()

        # === PHẦN 8: CHIA SẺ ===
        share_frame = tk.LabelFrame(self.container, text="📢 CHIA SẺ - NHẬN NGAY ƯU ĐÃI",
                                    font=get_font("label", bold=True), bg=self.bg_color, fg="black", padx=15, pady=15)
        share_frame.pack(pady=10, anchor="center")
        share_buttons = tk.Frame(share_frame, bg=self.bg_color)
        share_buttons.pack(anchor="center")
        
        btn_fb = tk.Button(share_buttons, text="📘 Chia sẻ Facebook", command=self._share_facebook,
                           font=get_font("button"), bg="#1877F2", fg="black", padx=15, pady=5)
        btn_fb.pack(side="left", padx=15, pady=8)
        btn_zalo = tk.Button(share_buttons, text="💬 Chia sẻ Zalo", command=self._share_zalo,
                             font=get_font("button"), bg="lightgray", fg="black", padx=15, pady=5)
        btn_zalo.pack(side="left", padx=15, pady=8)
        btn_msg = tk.Button(share_buttons, text="✉️ Chia sẻ Messenger", command=self._share_messenger,
                            font=get_font("button"), bg="lightgray", fg="black", padx=15, pady=5)
        btn_msg.pack(side="left", padx=15, pady=8)
        btn_copy = tk.Button(share_buttons, text="🔗 Sao chép link", command=self._copy_link,
                             font=get_font("button"), bg="lightgray", fg="black", padx=15, pady=5)
        btn_copy.pack(side="left", padx=15, pady=8)

        tk.Label(share_frame, text="🎁 Chia sẻ ngay để nhận mã giảm giá 10%!",
                 font=get_font("label"), fg="#4CAF50", bg=self.bg_color).pack(pady=10)

        # === BẢN QUYỀN (Tự động cập nhật theo VERSION) ===
        tk.Label(self.container,
                 text=f"© 2026 Phan Ngọc Hùng - Bảo lưu mọi quyền | Phiên bản {VERSION}",
                 font=get_font("label"), fg="gray", bg=self.bg_color).pack(pady=15)
                 
    # THÊM HÀM MỚI NÀY VÀO DƯỚI ĐÂY
    def load_images_delayed(self):
        """Hàm này chạy sau 500ms để đảm bảo Tkinter đã ổn định"""
        # 1. Load Logo
        try:
            icon_path = self._get_icon_path()
            if os.path.exists(icon_path):
                img = Image.open(icon_path).resize((80, 80), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img, master=self.root) # Giữ tham chiếu và gắn chủ sở hữu
                self.logo_label.config(image=self.logo_img)
                self.logo_label.image = self.logo_img # <--- THÊM DÒNG NÀY (Đây là chốt chặn cuối cùng)
        except Exception as e:
            logging.error(f"Lỗi load logo muộn: {e}")

        # 2. Load QR
        try:
            qr_path = self._get_qr_path()
            if qr_path and os.path.exists(qr_path):
                qr_img = Image.open(qr_path).resize((180, 180), Image.Resampling.LANCZOS)
                self.qr_img = ImageTk.PhotoImage(qr_img, master=self.root) # Giữ tham chiếu
                self.qr_label.config(image=self.qr_img)
            else:
                self.qr_label.config(text="📱 QR Code", font=get_font("label"))
        except Exception as e:
            logging.error(f"Lỗi load QR muộn: {e}")
            self.qr_label.config(text="[QR LỖI]")
