# scripts/ocr_image_to_text.py
import pytesseract
from PIL import Image
import os
import json
from datetime import datetime

def ocr_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang='chi_tra')
        return text.strip()
    except Exception as e:
        print(f"❌ 無法辨識圖片 {image_path}：{e}")
        return ""

def save_text(date_str, text):
    output_dir = f"docs/podcast/{date_str}"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "script.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ 已儲存逐字稿至 {output_path}")
    return output_path

def main():
    today = datetime.now().strftime("%Y%m%d")
    image_path = f"docs/img/{today}.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ 找不到圖片：{image_path}")
        return

    print(f"📷 開始辨識圖片：{image_path}")
    text = ocr_image(image_path)
    if not text:
        print("⚠️ 無法辨識出文字")
        return

    save_text(today, text)

if __name__ == "__main__":
    main()

