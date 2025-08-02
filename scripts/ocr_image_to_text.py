# scripts/ocr_image_to_text.py

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import re
from paddleocr import PaddleOCR

from utils import load_config, get_date_string, ensure_directory, log_message

# 設定專案路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")
DEBUG_SAVE = True  # 是否儲存分割圖像以便 debug

class DailyLightOCR:
    def __init__(self):
        self.config = load_config()
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)

    def preprocess_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")

            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_image = ImageEnhance.Contrast(pil_image).enhance(1.6)
            pil_image = ImageEnhance.Brightness(pil_image).enhance(1.2)

            return pil_image
        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None

    def split_image(self, image, date_str):
        width, height = image.size
        upper_half = image.crop((0, 0, width, height // 2))
        lower_half = image.crop((0, height // 2, width, height))

        if DEBUG_SAVE:
            debug_dir = os.path.join(OUTPUT_DIR, date_str)
            ensure_directory(debug_dir)
            upper_half.save(os.path.join(debug_dir, "debug_morning.jpg"))
            lower_half.save(os.path.join(debug_dir, "debug_evening.jpg"))

        return upper_half, lower_half

    def ocr_image(self, pil_img):
        try:
            img_np = np.array(pil_img)
            result = self.ocr.ocr(img_np, cls=True)
            lines = []
            for line in result[0]:
                text = line[1][0].strip()
                if len(text) >= 2:
                    lines.append(text)
            return self.clean_and_merge(lines)
        except Exception as e:
            log_message(f"OCR 辨識錯誤: {str(e)}", "ERROR")
            return ""

    def clean_and_merge(self, lines):
        """清理段落並合併為適合語音朗讀的長段落"""
        merged = ''
        for line in lines:
            # 清除亂碼與不明符號
            line = re.sub(r'[^\u4e00-\u9fa5，。、「」！？：；…]', '', line)
            if not line:
                continue
            # 若不是標點結尾，補上句點
            if not re.search(r'[。！？；]$', line):
                line += '。'
            merged += line
        return merged.strip()

    def process_daily_image(self, date_str=None):
        if not date_str:
            date_str = get_date_string()

        image_path = os.path.join(IMG_DIR, f"{date_str}.jpg")
        if not os.path.exists(image_path):
            log_message(f"圖片不存在: {image_path}", "ERROR")
            return False

        log_message(f"開始處理圖片: {image_path}")
        image = self.preprocess_image(image_path)
        if image is None:
            return False

        upper, lower = self.split_image(image, date_str)
        morning_text = self.ocr_image(upper)
        evening_text = self.ocr_image(lower)

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        if morning_text:
            with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(morning_text)
            log_message(f"晨間文本已保存: {output_dir}/morning.txt")

        if evening_text:
            with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(evening_text)
            log_message(f"晚間文本已保存: {output_dir}/evening.txt")

        if not morning_text and not evening_text:
            for period in ["morning", "evening"]:
                with open(os.path.join(output_dir, f"{period}.txt"), "w", encoding="utf-8") as f:
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