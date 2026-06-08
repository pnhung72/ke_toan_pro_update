-- ============================================
-- CẬP NHẬT HỆ THỐNG TÀI KHOẢN THEO THÔNG TƯ 99/2025/TT-BTC
-- CHỈ THÊM MỚI, KHÔNG XÓA/SỬA DỮ LIỆU CŨ
-- ============================================

-- Thêm các tài khoản mới (nếu chưa có)
INSERT OR IGNORE INTO accounts (code, name, type) VALUES 
('215', 'Tài sản sinh học', 'TAI_SAN_DAI_HAN'),
('2295', 'Dự phòng tổn thất tài sản sinh học', 'TAI_SAN_DAI_HAN'),
('1383', 'Thuế tiêu thụ đặc biệt hàng nhập khẩu', 'NO_PHAI_TRA'),
('2421', 'Chi phí trả trước dài hạn - Lãi vay', 'TAI_SAN_DAI_HAN'),
('3521', 'Dự phòng bảo hành sản phẩm', 'NO_PHAI_TRA');

-- Kiểm tra kết quả
SELECT code, name, type FROM accounts WHERE code IN ('215', '2295', '1383', '2421', '3521');
