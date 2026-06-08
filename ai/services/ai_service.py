# ai/services/ai_service.py
from ai.engine.classifier import classifier
import logging
import os
import sys

# Cấu hình log để debug trong file debug_ai_service.log
logging.basicConfig(
    filename='debug_ai_service.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AIService:
    def __init__(self):
        # Lazy load classifier model
        self.classifier = classifier
        logging.info("AIService initialized.")
        
        # Kiểm tra đường dẫn khi chạy từ file .exe (frozen)
        if getattr(sys, 'frozen', False):
            logging.info(f"Running as bundled exe. MEIPASS: {sys._MEIPASS}")
        else:
            logging.info("Running as python script.")

    def suggest_account(self, description):
        """Trả về danh sách gợi ý tài khoản dạng [(account_name, confidence), ...]"""
        try:
            logging.info(f"Attempting to predict for: {description}")
            if self.classifier is None:
                logging.error("Classifier is None!")
                return []
            
            results = self.classifier.predict(description, top_k=3)
            logging.info(f"Prediction successful: {results}")
            return results
        except Exception as e:
            error_msg = f"AI Service error: {str(e)}"
            logging.error(error_msg)
            print(error_msg)
            return []