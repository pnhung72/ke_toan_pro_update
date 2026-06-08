# core/registry.py
import logging

class ModuleRegistry:
    """Bộ quản lý và điều hướng các module ngành nghề trong hệ sinh thái Kế Toán Pro"""
    _modules = {}

    @classmethod
    def register_module(cls, name, display_name, description, tabs=None):
        """Hàm để một module ngành nghề tự đăng ký thông tin và giao diện của nó"""
        cls._modules[name] = {
            "display_name": display_name,
            "description": description,
            "tabs": tabs or [],
            "is_active": False
        }
        # Xử lý in ra console an toàn (bỏ qua lỗi encoding)
        try:
            logging.info(f"Đã nạp cấu trúc Module: {display_name}")
        except UnicodeEncodeError:
            # Nếu không in được (do console không hỗ trợ Unicode), bỏ qua
            pass

    @classmethod
    def activate_module(cls, name):
        """Kích hoạt module được chọn để sử dụng"""
        if name in cls._modules:
            for k in cls._modules:
                cls._modules[k]["is_active"] = False  # Tắt các module khác
            cls._modules[name]["is_active"] = True
            try:
                logging.info(f"Kích hoạt thành công hệ sinh thái ngành: {cls._modules[name]['display_name']}")
            except UnicodeEncodeError:
                pass
            return True
        return False

    @classmethod
    def get_active_tabs(cls):
        """Lấy danh sách các Tab giao diện đặc thù của ngành đang kích hoạt"""
        for name, info in cls._modules.items():
            if info["is_active"]:
                return info["tabs"]
        return []

# --- KHỞI TẠO ĐĂNG KÝ MẪU (Thử nghiệm hệ sinh thái) ---
# Ví dụ ta có 2 module ngành nghề đặc thù cấu hình sẵn:
ModuleRegistry.register_module(
    name="thuong_mai",
    display_name="Ngành Thương mại & Dịch vụ",
    description="Quản lý kho hàng hóa, doanh thu bán sỉ/lẻ",
    tabs=["Tab_BanHang", "Tab_Kho_ThuongMai"]
)

ModuleRegistry.register_module(
    name="san_xuat_dac_thu",
    display_name="Ngành Sản xuất Truyền thống",
    description="Quản lý định mức nguyên vật liệu, tính giá thành chai/thùng",
    tabs=["Tab_DinhMuc_GiaThanh", "Tab_QuanLy_LoSanXuat"]
)