import os

# Đường dẫn thư mục
path = r"D:\ke_toan_pro_v3\DATA_XML\HoaDon_DauVao"

# Tạo thư mục nếu chưa có
if not os.path.exists(path):
    os.makedirs(path)

# Nội dung XML mẫu (Cấu trúc rút gọn theo Thông tư 78)
hoa_don_1 = """<?xml version="1.0" encoding="UTF-8"?>
<HDon>
    <inv:shdon xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">0000001</inv:shdon>
    <inv:tdlap xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">2026-05-10</inv:tdlap>
    <inv:nbban xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">
        <inv:ten>Công ty Nước Mắm YaTrang - Chi nhánh Nha Trang</inv:ten>
        <inv:mst>4201234567</inv:mst>
    </inv:nbban>
    <inv:tgtttbso xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">1500000</inv:tgtttbso>
    <inv:tsuat xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">8%</inv:tsuat>
</HDon>
"""

hoa_don_2 = """<?xml version="1.0" encoding="UTF-8"?>
<HDon>
    <inv:shdon xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">0000052</inv:shdon>
    <inv:tdlap xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">2026-05-11</inv:tdlap>
    <inv:nbban xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">
        <inv:ten>Tổng Công Ty Công Nghệ Kế Toán Pro</inv:ten>
        <inv:mst>0101234568</inv:mst>
    </inv:nbban>
    <inv:tgtttbso xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">5600000</inv:tgtttbso>
    <inv:tsuat xmlns:inv="http://laphoadon.gdt.gov.vn/2014/09/invoicexml/v1">10%</inv:tsuat>
</HDon>
"""

# Lưu file
with open(os.path.join(path, "HD_YaTrang_001.xml"), "w", encoding="utf-8") as f:
    f.write(hoa_don_1)
with open(os.path.join(path, "HD_KeToanPro_052.xml"), "w", encoding="utf-8") as f:
    f.write(hoa_don_2)

print(f"--- ĐÃ TẠO 02 HÓA ĐƠN MẪU TẠI: {path} ---")