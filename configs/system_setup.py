import requests
import os
import sys

class SystemSetup:
    def __init__(self):
        # Xác định thư mục gốc tuyệt đối
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Lùi 1 cấp từ config/system_setup.py ra thư mục gốc
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.version_path = os.path.join(self.base_dir, "version.txt")
        self.invoice_dir = os.path.join(self.base_dir, "hoa_don")

    def get_version(self):
        """Hàm đọc phiên bản an toàn"""
        try:
            if os.path.exists(self.version_path):
                with open(self.version_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return "Unknown"
        except:
            return "Error"

    def get_business_info(self, mst):
        # ... (Giữ nguyên mã tra cứu MST của bạn ở đây)
        try:
            api_url = f"https://api.vietqr.io/v2/business/{mst}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json().get("data")
                if data:
                    return {
                        "mst_chu_quan": mst,
                        "ten_don_vi": data.get("name"),
                        "dia_chi": data.get("address")
                    }
            return None
        except Exception as e:
            print(f"[!] Lỗi kết nối: {e}")
            return None