# -*- coding: utf-8 -*-
"""
Unit tests for TaxCompliance service
"""

import unittest
import sys
import os

# Thêm đường dẫn dự án
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from services.tax_compliance import TaxCompliance


class TestTaxCompliance(unittest.TestCase):
    """Test cases for TaxCompliance"""
    
    def setUp(self):
        """Chuẩn bị trước mỗi test"""
        self.tax = TaxCompliance()
    
    def test_revenue_threshold_below_500m(self):
        """Test doanh thu dưới 500 triệu"""
        revenue = 400_000_000
        result = TaxCompliance.check_revenue_threshold(revenue)
        
        self.assertFalse(result["exceeded"])
        self.assertEqual(result["required_form"], "S1a-HKD")
        self.assertIn("duoi nguong", result["message"])
    
    def test_revenue_threshold_above_500m(self):
        """Test doanh thu trên 500 triệu"""
        revenue = 600_000_000
        result = TaxCompliance.check_revenue_threshold(revenue)
        
        self.assertTrue(result["exceeded"])
        self.assertEqual(result["required_form"], "01/CNKD")
        self.assertIn("vuot nguong", result["message"])
    
    def test_revenue_threshold_equal_500m(self):
        """Test doanh thu bằng 500 triệu"""
        revenue = 500_000_000
        result = TaxCompliance.check_revenue_threshold(revenue)
        
        self.assertTrue(result["exceeded"])
        self.assertEqual(result["required_form"], "01/CNKD")
    
    def test_get_deadline(self):
        """Test lấy hạn nộp"""
        deadline = TaxCompliance.get_deadline("01/BK-STK")
        self.assertEqual(deadline, "20/04/2026")
        
        deadline = TaxCompliance.get_deadline("UNKNOWN")
        self.assertEqual(deadline, "Chua xac dinh")
    
    def test_check_deadline(self):
        """Test kiểm tra hạn nộp"""
        result = TaxCompliance.check_deadline("01/BK-STK")
        self.assertIn(result["status"], ["pending", "overdue", "unknown"])
    
    def test_get_required_forms_below_threshold(self):
        """Test lấy danh sách mẫu biểu khi dưới ngưỡng"""
        forms = TaxCompliance.get_required_forms(400_000_000)
        
        form_codes = [f["code"] for f in forms]
        self.assertIn("01/BK-STK", form_codes)
        self.assertIn("S1a-HKD", form_codes)
        self.assertIn("01/TKN-CNKD", form_codes)
        self.assertNotIn("01/CNKD", form_codes)
    
    def test_get_required_forms_above_threshold(self):
        """Test lấy danh sách mẫu biểu khi trên ngưỡng"""
        forms = TaxCompliance.get_required_forms(600_000_000)
        
        form_codes = [f["code"] for f in forms]
        self.assertIn("01/BK-STK", form_codes)
        self.assertIn("01/CNKD", form_codes)
        self.assertIn("01/TKN-CNKD", form_codes)


if __name__ == "__main__":
    unittest.main()