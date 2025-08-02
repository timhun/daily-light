import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR
from utils import load_config, get_date_string, ensure_directory, log_message

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")
DEBUG_SAVE = True

class DailyLightOCR:
    def __init__(self):
        self.config = load_config()
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)

    def preprocess_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"無法讀取圖片: {image_path}")
        pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        pil = ImageEnhance.Contrast(pil).enhance(1.5)
        pil = ImageEnhance.Brightness(pil).enhance(1.2)
        return pil

    def split_image(self, image, date_str):
        w, h = image.size
        upper = image.crop((0, 0, w, h // 2))
        lower = image.crop((0, h // 2, w, h))
        if DEBUG_SAVE:
            debug_dir = os.path.join(OUTPUT_DIR, date_str)
            ensure_directory(debug_dir)
            upper.save(os.path.join(debug_dir, "debug_morning.jpg"))
            lower.save(os.path.join(debug_dir, "debug_evening.jpg"))
        return upper, lower

    def ocr_image(self, pil_img):
        np_img = np.array(pil_img)
        result = self.ocr.ocr(np_img, cls=True)
        lines = []
        for line in result[0]:
            text = line[1][0]
            lines.append(text.strip())
        return self.clean_text('\n'.join(lines))

    def clean_text(self, raw_text):
        lines = raw_text.splitlines()
        cleaned = []
        for line in lines:
            line = line.strip()
            if len(line) < 2:
                continue
            cleaned.append(line)
        return '\n'.join(cleaned)

    def process_daily_image(self, date_str=None):
        if not date_str:
            date_str = get_date_string()
        image_path = os.path.join(IMG_DIR, f"{date_str}.jpg")
        if not os.path.exists(image_path):
            log_message(f"圖片不存在: {image_path}", "ERROR")
            return False

        log_message(f"開始處理圖片: {image_path}")
        image = self.preprocess_image(image_path)
        upper, lower = self.split_image(image, date_str)

        morning = self.ocr_image(upper)
        evening = self.ocr_image(lower)

        out_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(out_dir)

        if morning.strip():
            with open(os.path.join(out_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(morning)
            log_message(f"晨間文本已保存: {out_dir}/morning.txt")
        if evening.strip():
            with open(os.path.join(out_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(evening)
            log_message(f"晚間文本已保存: {out_dir}/evening.txt")

        if not morning.strip() and not evening.strip():
            for period in ["morning", "evening"]:
                with open(os.path.join(out_dir, f"{period}.txt"), "w", encoding="utf-8") as f:
                    f.write("今日無內容")
            log_message("未辨識出內容，已建立預設空白內容")
        return True

def main():
    try:
        ocr = DailyLightOCR()
        date_str = get_date_string()
        log_message(f"開始處理 {date_str} 的每日亮光")
        success = ocr.process_daily_image(date_str)
        if success:
            log_message("OCR 處理完成")
            sys.exit(0)
        else:
            log_message("OCR 處理失敗", "ERROR")
            sys.exit(1)
    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()