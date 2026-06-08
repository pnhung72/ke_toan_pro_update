import base64

# Đọc file icon.ico
with open("icon.ico", "rb") as f:
    icon_b64 = base64.b64encode(f.read()).decode('utf-8')
print("ICON_BASE64 =", repr(icon_b64))
print("\n" + "="*50 + "\n")

# Đọc file ACB.jpeg
with open("ACB.jpeg", "rb") as f:
    qr_b64 = base64.b64encode(f.read()).decode('utf-8')
print("QR_BASE64 =", repr(qr_b64))

# Lưu vào file để dùng
with open("images_base64.py", "w", encoding="utf-8") as f:
    f.write("ICON_BASE64 = " + repr(icon_b64) + "\n")
    f.write("QR_BASE64 = " + repr(qr_b64) + "\n")
print("\nĐã tạo file images_base64.py")