# scripts/ocr_image_to_text.py

import os
import sys
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from utils import get_date_string, ensure_directory, log_message

# 設定專案根目錄與資料路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")


class DailyLightOCR:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")

    def preprocess_image(self, image_path):
        """強化影像前處理：旋轉、對比、去噪"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")

            # 轉為灰階
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 自動對比與亮度調整（CLAHE）
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # 中值濾波降噪
            denoised = cv2.medianBlur(enhanced, 3)

            # 回轉為 BGR（PaddleOCR 接收彩色圖）
            processed = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)

            return processed

        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None

    def split_image(self, image):
        """將圖片垂直分成上下兩半"""
        h, w = image.shape[:2]
        upper = image[:h//2, :]
        lower = image[h//2:, :]
        return upper, lower

    def ocr_text(self, image):
        """使用 PaddleOCR 辨識文字"""
        try:
            result = self.ocr.ocr(image, cls=True)
            lines = []
            for line in result[0]:
                lines.append(line[1][0])
            return '\n'.join(lines)
        except Exception as e:
            log_message(f"OCR 辨識失敗: {str(e)}", "ERROR")
            return ""

    def process_daily_image(self, date_str=None):
        if date_str is None:
            date_str = get_date_string()

        img_path = os.path.join(IMG_DIR, f"{date_str}.jpg")
        if not os.path.exists(img_path):
            log_message(f"圖片不存在: {img_path}", "ERROR")
            return False

        log_message(f"開始處理圖片: {img_path}")
        image = self.preprocess_image(img_path)
        if image is None:
            return False

        upper, lower = self.split_image(image)
        upper_text = self.ocr_text(upper)
        lower_text = self.ocr_text(lower)

        if not upper_text.strip() and not lower_text.strip():
            log_message("OCR 無辨識結果", "ERROR")
            return False

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        if upper_text.strip():
            morning_path = os.path.join(output_dir, "morning.txt")
            with open(morning_path, "w", encoding="utf-8") as f:
                f.write(upper_text.strip())
            log_message(f"晨間文本已保存: {morning_path}")

        if lower_text.strip():
            evening_path = os.path.join(output_dir, "evening.txt")
            with open(evening_path, "w", encoding="utf-8") as f:
                f.write(lower_text.strip())
            log_message(f"晚間文本已保存: {evening_path}")

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