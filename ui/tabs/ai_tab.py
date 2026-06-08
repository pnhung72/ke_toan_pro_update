import tkinter as tk
from tkinter import ttk, messagebox
from theme import get_font
from ai.engine.forecaster import forecaster
from ai.engine.anomaly_detector import anomaly_detector
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import sqlite3

class AITab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.update_status()
        self.load_feedback_stats()
        self.show_forecast()
        self.load_anomaly_alerts()

    def create_widgets(self):
        # Khung trạng thái
        status_frame = ttk.LabelFrame(self, text="🤖 Trạng thái AI", padding=5)
        status_frame.pack(fill="x", padx=10, pady=5)
        self.status_label = ttk.Label(status_frame, text="Đang khởi tạo...", font=get_font("label"))
        self.status_label.pack(side="left", padx=10)

        # Nút retrain
        self.retrain_btn = ttk.Button(status_frame, text="🔄 Retrain Model", command=self.retrain_model)
        self.retrain_btn.pack(side="right", padx=10)

        # Khung thống kê phản hồi
        stats_frame = ttk.LabelFrame(self, text="📊 Thống kê phản hồi", padding=5)
        stats_frame.pack(fill="x", padx=10, pady=5)
        self.feedback_label = ttk.Label(stats_frame, text="Đúng: 0 | Sai (đã sửa): 0", font=get_font("label"))
        self.feedback_label.pack(side="left", padx=10)

        # Nút làm mới thống kê
        self.refresh_stats_btn = ttk.Button(stats_frame, text="🔄 Làm mới", command=self.load_feedback_stats)
        self.refresh_stats_btn.pack(side="right", padx=10)

        # Khung cảnh báo bất thường
        alert_frame = ttk.LabelFrame(self, text="⚠️ Cảnh báo giao dịch bất thường", padding=5)
        alert_frame.pack(fill="x", padx=10, pady=5)
        self.alert_text = tk.Text(alert_frame, height=6, font=get_font("small"), wrap="word")
        self.alert_text.pack(fill="x", padx=5, pady=5)

        # Khung dự báo
        forecast_frame = ttk.LabelFrame(self, text="📈 Dự báo dòng tiền 30 ngày tới", padding=5)
        forecast_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.figure = plt.Figure(figsize=(6,4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=forecast_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def load_feedback_stats(self):
        try:
            conn = sqlite3.connect("ke_toan_data/ke_toan.db")
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM transaction_metadata WHERE ai_feedback = 'correct'")
            correct = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM transaction_metadata WHERE ai_feedback = 'wrong_correction'")
            wrong = cur.fetchone()[0]
            conn.close()
            self.feedback_label.config(text=f"✅ Đúng: {correct} | ❌ Sai (đã sửa): {wrong}")
        except Exception as e:
            self.feedback_label.config(text=f"Lỗi tải thống kê: {e}")

    def load_anomaly_alerts(self):
        self.alert_text.delete(1.0, tk.END)
        try:
            anomalies = anomaly_detector.get_recent_anomalies(days=30)
            if anomalies.empty:
                self.alert_text.insert(tk.END, "✅ Không phát hiện giao dịch bất thường nào trong 30 ngày qua.\n")
                return
            for idx, row in anomalies.iterrows():
                date = row['date']
                amount = row['amount']
                account = row['account_code']
                desc = row.get('description', '')[:50]
                self.alert_text.insert(tk.END, f"• {date} | {account} | {amount:,.0f} VND | {desc}\n")
        except Exception as e:
            self.alert_text.insert(tk.END, f"❌ Không thể tải cảnh báo: {e}\n")

    def update_status(self):
        if forecaster._model is not None:
            self.status_label.config(text="✅ AI đã sẵn sàng (Offline, chạy trên máy của bạn)")
        else:
            threading.Thread(target=forecaster.train, daemon=True).start()
            self.status_label.config(text="🔄 Đang khởi tạo AI (lần đầu có thể lâu hơn)...")
        self.after(5000, self.update_status)

    def retrain_model(self):
        self.retrain_btn.config(state="disabled", text="🔄 Đang retrain...")
        def do_retrain():
            try:
                from ai.feedback.retrain_script import retrain_model
                retrain_model()
                self.after(0, self.load_feedback_stats)
                self.after(0, self.load_anomaly_alerts)
                self.after(0, self.show_forecast)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi", f"Retrain thất bại: {e}"))
            finally:
                self.after(0, lambda: self.retrain_btn.config(state="normal", text="🔄 Retrain Model"))
        threading.Thread(target=do_retrain, daemon=True).start()

    def show_forecast(self):
        try:
            pred = forecaster.forecast(30)
            if pred.empty:
                self.ax.clear()
                self.ax.text(0.5, 0.5, "Chưa đủ dữ liệu để dự báo (cần ít nhất 14 ngày)",
                             transform=self.ax.transAxes, ha='center')
                self.ax.set_title("Dự báo dòng tiền")
                self.canvas.draw()
                return
            self.ax.clear()
            self.ax.plot(pred.index, pred.values, marker='o', linestyle='-', color='green')
            self.ax.set_title("Dự báo dòng tiền 30 ngày tới")
            self.ax.set_xlabel("Ngày")
            self.ax.set_ylabel("Doanh thu (VNĐ)")
            self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
            self.canvas.draw()
        except Exception as e:
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"Lỗi: {str(e)}", transform=self.ax.transAxes, ha='center')
            self.canvas.draw()