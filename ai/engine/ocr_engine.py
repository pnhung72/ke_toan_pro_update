import easyocr
import cv2
import numpy as np
import re
import os
from pathlib import Path

class OCREngine:
    _instance = None
    _reader = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_reader(self):
        if self._reader is None:
            # Chỉ load một lần (lazy)
            self._reader = easyocr.Reader(['vi', 'en'], gpu=False)
        return self._reader

    def preprocess_image(self, image_path):
        """Tiền xử lý ảnh: grayscale, contrast, deskew (an toàn)"""
        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Tăng contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Deskew (xoay ảnh) an toàn – dùng contours
        try:
            # Tìm vùng có chữ
            thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) > 100:  # chỉ xoay nếu có đủ điểm
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                (h, w) = enhanced.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(enhanced, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return rotated
            else:
                return enhanced
        except Exception as e:
            print(f"Lỗi deskew: {e}")
            return enhanced

    def extract_info(self, text):
        """Trích xuất số hóa đơn, ngày, tiền, thuế từ text OCR"""
        lines = text.split('\n')
        result = {
            'so_hoa_don': '',
            'ngay': '',
            'tien': 0,
            'thue': 0,
            'tong': 0
        }
        # Tìm số hóa đơn (mẫu đơn giản)
        for line in lines:
            if re.search(r'\b(No|Số|HĐ|HD|Invoice)[:\s]*(\d+)', line, re.I):
                match = re.search(r'(\d+)', line)
                if match:
                    result['so_hoa_don'] = match.group(1)
                    break
        # Tìm ngày (dd/mm/yyyy, dd-mm-yyyy)
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', text)
        if date_match:
            result['ngay'] = date_match.group(1)
        # Tìm tổng tiền (cộng hoặc tổng cộng)
        amounts = re.findall(r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)', text)
        if amounts:
            # Lấy số lớn nhất (giả định là tổng tiền)
            try:
                numeric = [float(a.replace('.', '').replace(',', '.')) for a in amounts if a.replace('.', '').replace(',', '').isdigit()]
                if numeric:
                    result['tong'] = max(numeric)
            except:
                pass
        return result

    def process_image(self, image_path, progress_callback=None):
        """OCR ảnh, trả về text và thông tin đã parse"""
        if progress_callback:
            progress_callback(10)
        img_processed = self.preprocess_image(image_path)
        if img_processed is None:
            return None, None
        if progress_callback:
            progress_callback(30)
        reader = self._get_reader()
        if progress_callback:
            progress_callback(50)
        # OCR
        results = reader.readtext(img_processed, detail=0, paragraph=True)
        full_text = '\n'.join(results)
        if progress_callback:
            progress_callback(80)
        parsed = self.extract_info(full_text)
        if progress_callback:
            progress_callback(100)
        return full_text, parsed

ocr_engine = OCREngine()