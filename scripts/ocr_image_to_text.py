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
logging.basicConfig(level=os.getenv("PYTHON_LOG_LEVEL", "INFO"), format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 環境變數與路徑
BASE_DIR = os.getenv("BASE_DIR", "docs")
IMAGE_DIR = os.path.join(BASE_DIR, "img")  # Match log path
OUTPUT_DIR = os.path.join(BASE_DIR, "podcast")
TESSDATA_PREFIX = os.environ.get("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/5/tessdata")

# 檢查 Tesseract 語言資料
for lang in ["chi_tra", "chi_sim"]:
    if not os.path.exists(os.path.join(TESSDATA_PREFIX, f"{lang}.traineddata")):
        logger.error(f"缺少 {lang}.traineddata，請安裝 tesseract-ocr-{lang}")
        sys.exit(1)
os.environ["TESSDATA_PREFIX"] = TESSDATA_PREFIX

def get_image_path(date_str):
    for ext in ["jpg", "png", "jpeg"]:
        path = os.path.join(IMAGE_DIR, f"{date_str}.{ext}")
        logger.debug(f"檢查圖片路徑：{path}")
        if os.path.exists(path):
            logger.info(f"找到圖片：{path}")
            return path
    logger.warning(f"未找到任何圖片：{date_str}.{{jpg,png,jpeg}}")
    return None

def preprocess_image(img):
    img = img.rotate(-90, expand=True)  # Rotate 90 degrees clockwise for vertical text
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
    return img

def split_image(image_path):
    try:
        img = Image.open(image_path)
        height = img.height
        mid = height // 2
        upper_half = img.crop((0, 0, img.width, mid))  # Morning
        lower_half = img.crop((0, mid, img.width, height))  # Evening
        return upper_half, lower_half
    except Exception as e:
        logger.error(f"圖片分割失敗：{e}")
        return None, None

def is_valid_text(text):
    if not text or len(text) < 10:
        return False
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = len([c for c in text if c.isprintable()])
    return chinese_chars / total_chars > 0.3

def ocr_image(image_path):
    upper_img, lower_img = split_image(image_path)
    if not upper_img or not lower_img:
        return None, None
    texts = []
    for img, label in [(upper_img, "morning"), (lower_img, "evening")]:
        try:
            img = preprocess_image(img)
            for lang in ['chi_tra', 'chi_sim']:
                logger.info(f"嘗試語言 {label}：{lang}")
                text = pytesseract.image_to_string(img, lang=lang, config='--psm 6 --oem 3 --dpi 300')
                if is_valid_text(text):
                    # Validate marker (e.g., "八月一日．晨" or "八月一日．晚")
                    if label == "morning" and re.search(r'[\u516d\u6708-\u5341\u6708]\u6708[\u4e00-\u4e5d\u5341\u4e8c]\u65e5[\u3002]\u6668', text):
                        texts.append((f"[{label.upper()}] {text.strip()}", label))
                        break
                    elif label == "evening" and re.search(r'[\u516d\u6708-\u5341\u6708]\u6708[\u4e00-\u4e5d\u5341\u4e8c]\u65e5[\u3002]\u665a', text):
                        texts.append((f"[{label.upper()}] {text.strip()}", label))
                        break
            else:
                logger.warning(f"無法辨識 {label} 有效文字")
        except Exception as e:
            logger.error(f"{label} 圖片處理失敗：{e}")
    return texts[0] if len(texts) > 0 else (None, None), texts[1] if len(texts) > 1 else (None, None)

def save_text(date_str, text, time_of_day):
    output_dir = os.path.join(OUTPUT_DIR, date_str)
    output_path = os.path.join(output_dir, f"{time_of_day}.txt")
    try:
        if os.path.exists(output_path):
            shutil.copy(output_path, f"{output_path}.bak")
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"已儲存 {time_of_day} 逐字稿至 {output_path}，內容：{text[:200]}...")
        return output_path
    except Exception as e:
        logger.error(f"儲存 {time_of_day} 逐字稿失敗：{e}")
        return ""

def main():
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    image_path = get_image_path(today)

    logger.info(f"開始辨識圖片：{image_path}")
    if not image_path:
        logger.warning(f"找不到圖片：{today}，將建立預設逐字稿")
        save_text(today, "今日無內容", "morning")
        save_text(today, "今日無內容", "evening")
        sys.exit(1)

    morning_text, evening_text = ocr_image(image_path)
    if not morning_text[0] or not evening_text[0]:
        logger.warning("無有效文字，生成預設逐字稿")
        save_text(today, "今日無內容", "morning")
        save_text(today, "今日無內容", "evening")
        sys.exit(1)
    else:
        save_text(today, morning_text[0], "morning")
        save_text(today, evening_text[0], "evening")

if __name__ == "__main__":
    main()
