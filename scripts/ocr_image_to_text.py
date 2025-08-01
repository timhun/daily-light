# scripts/ocr_image_to_text.py

import pytesseract
from PIL import Image, ImageEnhance
import os
import pytz
from datetime import datetime
import logging
import sys
import shutil
import re

# 設定日誌
logging.basicConfig(level=os.getenv("PYTHON_LOG_LEVEL", "INFO"),
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 環境變數與路徑
BASE_DIR = os.getenv("BASE_DIR", "docs")
IMAGE_DIR = os.path.join(BASE_DIR, "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "podcast")
TESSDATA_PREFIX = os.environ.get("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/5/tessdata")

# 檢查 Tesseract 語言資料
for lang in ["chi_tra", "chi_sim"]:
    trained_path = os.path.join(TESSDATA_PREFIX, f"{lang}.traineddata")
    if not os.path.exists(trained_path):
        logger.error(f"❌ 缺少 {lang}.traineddata，請安裝 tesseract-ocr-{lang}")
        sys.exit(1)
os.environ["TESSDATA_PREFIX"] = TESSDATA_PREFIX

def get_image_path(date_str):
    for ext in ["jpg", "png", "jpeg"]:
        path = os.path.join(IMAGE_DIR, f"{date_str}.{ext}")
        if os.path.exists(path):
            logger.info(f"找到圖片：{path}")
            return path
    logger.warning(f"未找到圖片：{date_str}.{{jpg,png,jpeg}}")
    return None

def preprocess_image(img):
    img = img.rotate(-90, expand=True)  # 旋轉 90 度，適應直式文字
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
    return img

def split_image(image_path):
    try:
        img = Image.open(image_path)
        height = img.height
        mid = height // 2
        upper = img.crop((0, 0, img.width, mid))
        lower = img.crop((0, mid, img.width, height))
        return upper, lower
    except Exception as e:
        logger.error(f"圖片分割失敗：{e}")
        return None, None

def is_valid_text(text):
    if not text or len(text) < 10:
        return False
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese_chars > 10

def ocr_image(image_path):
    upper_img, lower_img = split_image(image_path)
    if not upper_img or not lower_img:
        return (None, None), (None, None)

    texts = []
    for img, label in [(upper_img, "morning"), (lower_img, "evening")]:
        try:
            img = preprocess_image(img)
            for lang in ['chi_tra', 'chi_sim']:
                logger.info(f"嘗試語言 {label}：{lang}")
                text = pytesseract.image_to_string(img, lang=lang, config='--psm 6 --oem 3 --dpi 300')
                if is_valid_text(text):
                    if label == "morning" and re.search(r'(一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)[一二三四五六七八九十]{1,3}日．晨', text):
                        texts.append((f"[{label.upper()}] {text.strip()}", label))
                        break
                    elif label == "evening" and re.search(r'(一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)[一二三四五六七八九十]{1,3}日．晚', text):
                        texts.append((f"[{label.upper()}] {text.strip()}", label))
                        break
            else:
                logger.warning(f"無法辨識 {label} 有效文字")
                texts.append((None, label))
        except Exception as e:
            logger.error(f"{label} 圖片處理失敗：{e}")
            texts.append((None, label))

    return texts[0], texts[1]

def save_text(date_str, text, time_of_day):
    output_dir = os.path.join(OUTPUT_DIR, date_str)
    output_path = os.path.join(output_dir, f"{time_of_day}.txt")
    try:
        os.makedirs(output_dir, exist_ok=True)
        if os.path.exists(output_path):
            shutil.copy(output_path, f"{output_path}.bak")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"✅ 已儲存 {time_of_day} 逐字稿至 {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"❌ 儲存 {time_of_day} 逐字稿失敗：{e}")
        return ""

def main():
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    image_path = get_image_path(today)

    logger.info(f"開始辨識圖片：{image_path}")
    if not image_path:
        logger.warning("找不到圖片，將建立空白逐字稿")
        save_text(today, "今日無內容", "morning")
        save_text(today, "今日無內容", "evening")
        sys.exit(0)

    (morning_text, _), (evening_text, _) = ocr_image(image_path)

    if not morning_text:
        logger.warning("無法辨識晨間內容")
        morning_text = "今日無內容"
    if not evening_text:
        logger.warning("無法辨識晚間內容")
        evening_text = "今日無內容"

    save_text(today, morning_text, "morning")
    save_text(today, evening_text, "evening")

if __name__ == "__main__":
    main()