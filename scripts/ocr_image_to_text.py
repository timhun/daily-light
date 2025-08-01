# scripts/ocr_image_to_text.py
import pytesseract
from PIL import Image, ImageEnhance
import os
import pytz
from datetime import datetime
import logging
import sys
import glob
import shutil

# 設定日誌
logging.basicConfig(level=os.getenv("PYTHON_LOG_LEVEL", "INFO"), format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 環境變數與路徑
BASE_DIR = os.getenv("BASE_DIR", "docs")
IMAGE_DIR = os.path.join(BASE_DIR, "img")  # Updated to match log
OUTPUT_DIR = os.path.join(BASE_DIR, "podcast")
TESSDATA_PREFIX = os.environ.get("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/5/tessdata")

# 檢查 Tesseract 語言資料
for lang in ["chi_tra", "chi_sim"]:
    if not os.path.exists(os.path.join(TESSDATA_PREFIX, f"{lang}.traineddata")):
        logger.error(f"缺少 {lang}.traineddata，請安裝 tesseract-ocr-{lang}")
        sys.exit(1)
os.environ["TESSDATA_PREFIX"] = TESSDATA_PREFIX

def get_image_path(date_str):
    """動態查找圖片路徑，支援多種格式"""
    for ext in ["jpg", "png", "jpeg"]:
        path = os.path.join(IMAGE_DIR, f"{date_str}.{ext}")
        logger.debug(f"檢查圖片路徑：{path}")
        if os.path.exists(path):
            logger.info(f"找到圖片：{path}")
            return path
    logger.warning(f"未找到任何圖片：{date_str}.{{jpg,png,jpeg}}")
    return None

def preprocess_image(image_path):
    """預處理圖片以提高 OCR 準確度"""
    try:
        img = Image.open(image_path).convert("L")  # Grayscale
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)  # Increase contrast
        img = img.resize((img.width * 2, img.height * 2))  # Increase resolution
        return img
    except Exception as e:
        logger.error(f"圖片預處理失敗：{e}")
        return None

def is_valid_text(text):
    """檢查文字是否有效（至少50%為中文字符）"""
    if not text:
        return False
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese_chars / len(text) > 0.5

def ocr_image(image_path):
    """執行 OCR，嘗試多種語言"""
    img = preprocess_image(image_path)
    if not img:
        return ""
    try:
        for lang in ['chi_tra', 'chi_sim']:
            logger.info(f"嘗試語言：{lang}")
            text = pytesseract.image_to_string(img, lang=lang, config='--psm 6 --oem 3')
            if is_valid_text(text):
                logger.info(f"成功辨識文字（語言：{lang}）")
                return text.strip()
        logger.warning("無法辨識有效文字")
        return ""
    except pytesseract.TesseractNotFoundError:
        logger.error("找不到 Tesseract，可透過 sudo apt install tesseract-ocr 安裝")
        return ""
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
        logger.warning(f"找不到圖片：{today}，將建立預設逐字稿")
        save_text(today, "今日無內容")
        sys.exit(1)  # Exit with error to alert workflow

    text = ocr_image(image_path)
    if not text or not is_valid_text(text):
        logger.warning("無有效文字，生成預設逐字稿")
        save_text(today, "今日無內容")
        sys.exit(1)  # Exit with error
    else:
        logger.info(f"辨識內容（前100字）：{text[:100]}")
        save_text(today, text)

if __name__ == "__main__":
    main()
