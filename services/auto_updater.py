# services/auto_updater.py
# ============================================================
# HỆ THỐNG CẬP NHẬT TỰ ĐỘNG - KẾ TOÁN PRO  (v2)
# Nguồn sự thật duy nhất: version.json
# Cải tiến:
#   • Progress bar có phần trăm thực (không indeterminate)
#   • Kiểm tra hash MD5 để đảm bảo file tải đúng
#   • Retry tự động tối đa 3 lần khi mạng chập chờn
#   • Ghi log chi tiết ra file update.log
#   • Tự dọn file backup cũ (giữ tối đa 5 bản)
# ============================================================
import os
import sys
import json
import time
import shutil
import hashlib
import logging
import requests
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

# ── Cấu hình ─────────────────────────────────────────────────
VERSION_URL = (
    "https://raw.githubusercontent.com/pnhung72/"
    "ke_toan_pro_update/main/version.json"
)
CHECK_INTERVAL_HOURS = 6
MAX_RETRIES           = 3
RETRY_DELAY_SECONDS   = 5
MAX_BACKUP_FILES      = 5
# ─────────────────────────────────────────────────────────────


def _setup_logging(base_dir: str):
    """Ghi log ra file update.log trong thư mục gốc app"""
    log_path = os.path.join(base_dir, "update.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _base_dir() -> str:
    """Trả về thư mục gốc: cạnh exe (frozen) hoặc gốc project"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _doc_phien_ban_hien_tai() -> str:
    """
    Đọc phiên bản hiện tại.
    Nguồn ưu tiên: version.json → version.txt → '0.0.0'
    """
    base = _base_dir()
    # 1. Thử version.json (nguồn sự thật)
    vj = os.path.join(base, "version.json")
    if os.path.exists(vj):
        try:
            with open(vj, encoding="utf-8") as f:
                data = json.load(f)
            v = data.get("phien_ban_moi_nhat", "").strip()
            if v:
                return v
        except Exception:
            pass
    # 2. Fallback: version.txt (tương thích ngược)
    vt = os.path.join(base, "version.txt")
    if os.path.exists(vt):
        try:
            return open(vt, encoding="utf-8").readline().strip()
        except Exception:
            pass
    return "0.0.0"


def _so_sanh_version(v1: str, v2: str) -> int:
    """So sánh 2 version chuỗi dạng x.y.z
    Trả về: 1 nếu v1 > v2 | -1 nếu v1 < v2 | 0 nếu bằng"""
    try:
        a = [int(x) for x in v1.strip().split(".")]
        b = [int(x) for x in v2.strip().split(".")]
        while len(a) < len(b): a.append(0)
        while len(b) < len(a): b.append(0)
        for x, y in zip(a, b):
            if x > y: return 1
            if x < y: return -1
        return 0
    except Exception:
        return 0


def _kiem_tra_server() -> dict | None:
    """Lấy version.json từ GitHub với retry. Trả về dict hoặc None."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(VERSION_URL, timeout=8)
            if r.status_code == 200:
                return r.json()
            logging.warning(f"[Updater] Server trả về HTTP {r.status_code} (lần {attempt})")
        except Exception as e:
            logging.warning(f"[Updater] Kết nối thất bại (lần {attempt}): {e}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)
    return None


def _tinh_md5(file_path: str) -> str:
    """Tính MD5 của file"""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _backup_database(base_dir: str) -> str | None:
    """
    Backup ke_toan.db → backups/ke_toan_backup_YYYYMMDD_HHMMSS.db
    Giữ tối đa MAX_BACKUP_FILES bản cũ nhất.
    """
    db_candidates = [
        os.path.join(base_dir, "ke_toan_data", "ke_toan.db"),
        os.path.join(base_dir, "data", "ke_toan.db"),
    ]
    for db_path in db_candidates:
        if not os.path.exists(db_path):
            continue
        try:
            backup_dir = os.path.join(base_dir, "ke_toan_data", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"ke_toan_backup_{ts}.db")
            shutil.copy2(db_path, backup_path)
            logging.info(f"[Updater] ✅ Backup DB: {backup_path}")

            # Dọn bản cũ — giữ lại MAX_BACKUP_FILES bản mới nhất
            all_backups = sorted(
                Path(backup_dir).glob("ke_toan_backup_*.db"),
                key=lambda p: p.stat().st_mtime,
            )
            for old in all_backups[:-MAX_BACKUP_FILES]:
                old.unlink()
                logging.info(f"[Updater] 🗑️  Đã xoá backup cũ: {old.name}")

            return backup_path
        except Exception as e:
            logging.error(f"[Updater] Lỗi backup: {e}")
    return None


# ─────────────────────────────────────────────────────────────
class CuaSoCapNhat(tk.Toplevel):
    """Cửa sổ thông báo cập nhật với progress bar có phần trăm thực"""

    def __init__(self, parent, server_info: dict, pv_hien_tai: str):
        super().__init__(parent)
        self.server_info   = server_info
        self.pv_hien_tai   = pv_hien_tai

        self.title("🔔 Có phiên bản mới!")
        self.geometry("520x440")
        self.resizable(False, False)
        self.grab_set()

        # Căn giữa màn hình
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 520) // 2
        y = (self.winfo_screenheight() - 440) // 2
        self.geometry(f"520x440+{x}+{y}")

        self._tao_giao_dien()

    # ── Giao diện ────────────────────────────────────────────
    def _tao_giao_dien(self):
        pv_moi  = self.server_info.get("phien_ban_moi_nhat", "?")
        ngay    = self.server_info.get("ngay_phat_hanh", "")
        ghi_chu = self.server_info.get("ghi_chu_phien_ban", [])
        bat_buoc = self.server_info.get("canh_bao_bat_buoc", False)
        mb      = self.server_info.get("kich_thuoc_mb", "?")

        # Header
        frame_hdr = tk.Frame(self, bg="#1565C0", pady=15)
        frame_hdr.pack(fill=tk.X)
        tk.Label(
            frame_hdr,
            text="🎉 Phần Mềm Kế Toán Pro — Bản cập nhật mới!",
            bg="#1565C0", fg="white", font=("Arial", 12, "bold"),
        ).pack()

        # Thông tin version
        fv = tk.Frame(self, pady=8)
        fv.pack(fill=tk.X, padx=20)
        tk.Label(fv, text=f"Phiên bản hiện tại:  {self.pv_hien_tai}",
                 font=("Arial", 10), fg="#666").pack(anchor="w")
        tk.Label(fv, text=f"Phiên bản mới:        {pv_moi}  ({ngay})  —  ~{mb} MB",
                 font=("Arial", 10, "bold"), fg="#1565C0").pack(anchor="w")

        # Changelog
        tk.Label(self, text="📋 Nội dung cập nhật:",
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
        frame_log = tk.Frame(self, bg="#F5F5F5", relief="sunken", bd=1)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=20, pady=4)
        for item in ghi_chu:
            tk.Label(frame_log, text=f"  {item}", bg="#F5F5F5",
                     font=("Arial", 9), anchor="w", justify="left").pack(fill=tk.X, pady=1)

        # Progress khu vực
        self.frame_pg = tk.Frame(self)
        self.frame_pg.pack(fill=tk.X, padx=20, pady=4)
        self.lbl_status = tk.Label(self.frame_pg, text="", font=("Arial", 9), fg="#555")
        self.lbl_status.pack(anchor="w")
        self.var_pg = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(
            self.frame_pg, variable=self.var_pg,
            maximum=100, mode="determinate", length=480,
        )
        # (ẩn cho đến khi bắt đầu tải)

        # Cảnh báo bắt buộc
        if bat_buoc:
            tk.Label(self, text="⚠️  Đây là bản cập nhật bắt buộc — không thể bỏ qua!",
                     fg="red", font=("Arial", 9, "bold")).pack()

        # Nút
        frame_btn = tk.Frame(self, pady=8)
        frame_btn.pack()
        if not bat_buoc:
            tk.Button(frame_btn, text="Để sau", width=12, font=("Arial", 10),
                      command=self.destroy).pack(side=tk.LEFT, padx=10)
        self.btn = tk.Button(
            frame_btn, text="✅ Cập nhật ngay",
            width=16, bg="#1565C0", fg="white", font=("Arial", 10, "bold"),
            command=self._bat_dau_cap_nhat,
        )
        self.btn.pack(side=tk.LEFT, padx=10)

    # ── Điều phối cập nhật ────────────────────────────────────
    def _bat_dau_cap_nhat(self):
        self.btn.config(state="disabled", text="Đang xử lý...")
        self.progress.pack(fill=tk.X)
        threading.Thread(target=self._thuc_hien_cap_nhat, daemon=True).start()

    def _set_status(self, msg: str):
        self.after(0, lambda: self.lbl_status.config(text=msg))

    def _set_progress(self, pct: int):
        self.after(0, lambda: self.var_pg.set(pct))

    def _thuc_hien_cap_nhat(self):
        try:
            base_dir = _base_dir()
            exe_path = (
                sys.executable if getattr(sys, "frozen", False)
                else os.path.join(base_dir, "PhanMemKeToan.exe")
            )

            # ── 1. Backup DB (0–10%) ──────────────────────────
            self._set_status("🔒 Đang sao lưu cơ sở dữ liệu...")
            self._set_progress(5)
            backup = _backup_database(base_dir)
            if not backup:
                self._set_status("⚠️  Không tìm thấy database, tiếp tục cập nhật...")
            self._set_progress(10)

            # ── 2. Tải exe mới (10–85%) ───────────────────────
            self._set_status("📥 Đang tải phiên bản mới...")
            link     = self.server_info.get("link_tai_exe", "")
            ten_file = self.server_info.get("ten_file_exe", "PhanMemKeToan.exe")
            exe_moi  = os.path.join(base_dir, f"_update_{ten_file}")

            r = requests.get(link, stream=True, timeout=120)
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code} khi tải file")

            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(exe_moi, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = 10 + int(downloaded / total * 75)
                            self._set_progress(pct)
                            mb_dl = downloaded / 1_048_576
                            mb_tt = total     / 1_048_576
                            self._set_status(
                                f"📥 Đang tải...  {mb_dl:.1f} / {mb_tt:.1f} MB"
                            )
            self._set_progress(85)

            # ── 3. Kiểm tra hash MD5 (nếu server cung cấp) ───
            md5_server = self.server_info.get("md5_exe", "")
            if md5_server:
                self._set_status("🔍 Kiểm tra tính toàn vẹn file...")
                md5_local = _tinh_md5(exe_moi)
                if md5_local.lower() != md5_server.lower():
                    os.remove(exe_moi)
                    raise Exception(
                        f"File bị hỏng (MD5 sai)!\n"
                        f"Server: {md5_server}\nLocal:  {md5_local}"
                    )
                logging.info("[Updater] ✅ MD5 khớp")
            self._set_progress(90)

            # ── 4. Cập nhật version.json cục bộ ──────────────
            self._set_status("📝 Cập nhật thông tin phiên bản...")
            vj_path = os.path.join(base_dir, "version.json")
            if os.path.exists(vj_path):
                try:
                    with open(vj_path, encoding="utf-8") as f:
                        local_vj = json.load(f)
                    local_vj["phien_ban_moi_nhat"] = self.server_info.get(
                        "phien_ban_moi_nhat", local_vj.get("phien_ban_moi_nhat")
                    )
                    with open(vj_path, "w", encoding="utf-8") as f:
                        json.dump(local_vj, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logging.warning(f"[Updater] Không cập nhật version.json cục bộ: {e}")
            self._set_progress(95)

            # ── 5. Tạo batch thay thế và khởi động lại ───────
            self._set_status("⚙️  Đang cài đặt...")
            bat_path = os.path.join(base_dir, "_do_update.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("timeout /t 2 /nobreak > nul\n")
                f.write(f'move /y "{exe_moi}" "{exe_path}"\n')
                f.write(f'start "" "{exe_path}"\n')
                f.write('del "%~f0"\n')

            self._set_progress(100)
            self._set_status("✅ Hoàn tất! Đang khởi động lại...")
            self.after(1500, lambda: self._khoi_dong_lai(bat_path))

        except Exception as e:
            logging.error(f"[Updater] Lỗi: {e}")
            self.after(0, lambda: self._bao_loi(str(e)))

    def _khoi_dong_lai(self, bat_path: str):
        subprocess.Popen(bat_path, shell=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        self.after(500, lambda: sys.exit(0))

    def _bao_loi(self, loi: str):
        self.var_pg.set(0)
        self.btn.config(state="normal", text="↩️ Thử lại")
        self.lbl_status.config(text=f"❌ Lỗi: {loi[:120]}", fg="red")
        messagebox.showerror(
            "Lỗi cập nhật",
            f"Không thể cập nhật:\n\n{loi}\n\nVui lòng thử lại sau.",
            parent=self,
        )


# ─────────────────────────────────────────────────────────────
class AutoUpdater:
    """
    Dùng trong main.py:
        updater = AutoUpdater(root)
        updater.kich_hoat()          # chạy ngầm, kiểm tra mỗi 6 giờ
        updater.kiem_tra_ngay(root)  # kiểm tra ngay khi khởi động (tuỳ chọn)
    """

    def __init__(self, parent_window: tk.Tk):
        self.parent    = parent_window
        self._dang_chay = False

    def kich_hoat(self):
        """Kích hoạt kiểm tra định kỳ trong luồng nền"""
        if self._dang_chay:
            return
        self._dang_chay = True
        _setup_logging(_base_dir())
        threading.Thread(target=self._vong_kiem_tra, daemon=True).start()
        logging.info("[Updater] ✅ Kích hoạt hệ thống cập nhật tự động.")

    def kiem_tra_ngay(self):
        """Kiểm tra 1 lần ngay lập tức (gọi sau khi UI đã sẵn sàng)"""
        threading.Thread(target=self._kiem_tra_mot_lan, daemon=True).start()

    # ── Vòng lặp nền ─────────────────────────────────────────
    def _vong_kiem_tra(self):
        while True:
            try:
                self._kiem_tra_mot_lan()
            except Exception as e:
                logging.error(f"[Updater] Lỗi vòng kiểm tra: {e}")
            time.sleep(CHECK_INTERVAL_HOURS * 3600)

    def _kiem_tra_mot_lan(self):
        """Lấy version.json từ server, so sánh, hiện popup nếu có bản mới"""
        server_info = _kiem_tra_server()
        if not server_info:
            return

        pv_hien_tai = _doc_phien_ban_hien_tai()
        pv_server   = server_info.get("phien_ban_moi_nhat", "0.0.0")

        ket_qua = _so_sanh_version(pv_server, pv_hien_tai)
        if ket_qua > 0:
            logging.info(f"[Updater] 🆕 Bản mới: {pv_server}  (hiện tại: {pv_hien_tai})")
            self.parent.after(
                0, lambda: self._hien_thong_bao(server_info, pv_hien_tai)
            )
        elif ket_qua == 0:
            logging.info(f"[Updater] ✅ Đang dùng bản mới nhất ({pv_hien_tai}).")
        else:
            # Trường hợp hiếm: local > server (dev build)
            logging.info(
                f"[Updater] ℹ️  Bản local ({pv_hien_tai}) mới hơn server ({pv_server})."
            )

    def _hien_thong_bao(self, server_info: dict, pv_hien_tai: str):
        try:
            win = CuaSoCapNhat(self.parent, server_info, pv_hien_tai)
            self.parent.wait_window(win)
        except Exception as e:
            logging.error(f"[Updater] Lỗi hiện thông báo: {e}")