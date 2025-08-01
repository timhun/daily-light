# scripts/ocr_image_to_text.py
import pytesseract
from PIL import Image
import os
from datetime import datetime
import pytz
import logging
import sys
import glob

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 環境變數與路徑
BASE_DIR = os.getenv("BASE_DIR", "docs")
IMAGE_DIR = os.path.join(BASE_DIR, "img")  # 與儲存庫結構一致
OUTPUT_DIR = os.path.join(BASE_DIR, "podcast")
TESSDATA_PREFIX = os.environ.get("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/5/tessdata")

if not os.path.exists(TESSDATA_PREFIX):
    logger.error("TESSDATA_PREFIX 路徑無效，請檢查 Tesseract 語言資料")
    sys.exit(1)
os.environ["TESSDATA_PREFIX"] = TESSDATA_PREFIX

def get_image_path(date_str):
    """動態查找圖片路徑，支援多種格式"""
    for ext in ["jpg", "png", "jpeg"]:
        path = os.path.join(IMAGE_DIR, f"{date_str}.{ext}")
        if os.path.exists(path):
            return path
    return None

def ocr_image(image_path):
    """執行 OCR 並驗證圖片"""
    try:
        img = Image.open(image_path)
        img.verify()  # 驗證圖片
        img = Image.open(image_path)  # 重新打開
        text = pytesseract.image_to_string(img, lang='chi_tra')
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        logger.error("找不到 Tesseract，可透過 sudo apt install tesseract-ocr 安裝")
    except pytesseract.TesseractError as e:
        logger.error(f"Tesseract 執行錯誤：{e}")
    except Exception as e:
        logger.error(f"圖片處理失敗：{e}")
    return ""

def save_text(date_str, text):
    """儲存逐字稿並備份舊檔案"""
    output_dir = os.path.join(OUTPUT_DIR, date_str)
    output_path = os.path.join(output_dir, "script.txt")
    try:
        if os.path.exists(output_path):
            shutil.copy(output_path, f"{output_path}.bak")
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"已儲存逐字稿至 {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"儲存逐字稿失敗：{e}")
        return ""

def main():
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    image_path = get_image_path(today)

    logger.info(f"開始辨識圖片：{image_path}")
    if not image_path:
        logger.warning(f"找不到圖片：{today}，將建立空白逐字稿")
        save_text(today, "今日無內容")
        sys.exit(0)

    text = ocr_image(image_path)
    if not text:
        logger.warning("無法辨識出文字，建立預設逐字稿")
        save_text(today, "今日無內容")
    else:
        logger.info(f"辨識內容（前100字）：{text[:100]}")
        save_text(today, text)

if __name__ == "__main__":
    main()
