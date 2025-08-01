# scripts/ocr_image_to_text.py
import pytesseract
from PIL import Image
import os
from datetime import datetime
import pytz
import sys

# 確保 TESSDATA_PREFIX 環境變數存在，避免 chi_tra 無法載入
os.environ["TESSDATA_PREFIX"] = os.environ.get("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/5/tessdata")

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
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"❌ 建立資料夾失敗：{e}")
        return ""
    
    output_path = os.path.join(output_dir, "script.txt")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ 已儲存逐字稿至 {output_path}")
    except Exception as e:
        print(f"❌ 無法寫入文字檔：{e}")
    return output_path if os.path.exists(output_path) else ""

def main():
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    image_path = f"docs/img/{today}.jpg"

    print(f"📷 開始辨識圖片：{image_path}")

    if not os.path.exists("docs/img"):
        print("❌ 圖片資料夾 docs/img 不存在！")
    else:
        print(f"📂 目前 docs/img 內檔案有：{os.listdir('docs/img')}")

    if not os.path.exists(image_path):
        print(f"❌ 找不到圖片：{image_path}，將建立空白逐字稿")
        save_text(today, "")
        sys.exit(0)

    text = ocr_image(image_path)
    if not text:
        print("⚠️ 無法辨識出文字，將建立空白逐字稿")
        save_text(today, "")
        sys.exit(0)

    print(f"📝 OCR 辨識結果（前100字）：{text[:100]}")

    save_text(today, text)

if __name__ == "__main__":
    main()
