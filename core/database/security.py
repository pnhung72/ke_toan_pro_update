import sys
import os
import traceback
import logging

def bat_tat_ca_lenh_thoat():
    def dummy_exit(*args, **kwargs):
        #print("\n" + "!"*80)
        logging.critical("THỦ PHẠM GÂY THOÁT ĐÃ BỊ BẮT!")
        traceback.print_stack() # In ra con đường dẫn đến lệnh thoát
        #print("!"*80 + "\n")
        # Không cho thoát, giữ giao diện lại
    
    sys.exit = dummy_exit
    os._exit = dummy_exit
    logging.info("Đã thiết lập bẫy thoát cấp cao nhất.")

# Chạy nó ngay khi import
bat_tat_ca_lenh_thoat()