import pytesseract
from PIL import Image
import os
from datetime import datetime
import pytz
import sys

def ocr_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang='chi_tra')
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("❌ 找不到 Tesseract，可透過 sudo apt install tesseract-ocr 安裝")
    except pytesseract.TesseractError as e:
        print(f"❌ Tesseract 執行錯誤：{e}")
    except Exception as e:
        print(f"❌ 其他錯誤：{e}")
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
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    image_path = f"docs/img/{today}.jpg"

    print(f"📷 開始辨識圖片：{image_path}")

    if not os.path.exists(image_path):
        print(f"❌ 找不到圖片：{image_path}")
        save_text(today, "")  # 寫入空稿以避免 GitHub Action 中斷
        sys.exit(0)

    text = ocr_image(image_path)
    if not text:
        print("⚠️ 無法辨識出文字，將建立空的逐字稿")
        save_text(today, "")
        sys.exit(0)

    save_text(today, text)

if __name__ == "__main__":
    main()