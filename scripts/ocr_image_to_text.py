import os
import sys
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from utils import load_config, get_date_string, ensure_directory, log_message

# 設定根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")

class DailyLightOCRPaddle:
    def __init__(self):
        # 使用繁體中文模型，預設使用 CPU
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')

    def preprocess_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            log_message(f"無法讀取圖片: {image_path}", "ERROR")
            return None
        return image

    def split_image(self, image):
        """分割上半部（晨）與下半部（晚）"""
        height = image.shape[0]
        upper_half = image[:height // 2, :]
        lower_half = image[height // 2:, :]
        return upper_half, lower_half

    def ocr_text(self, image_np):
        result = self.ocr.ocr(image_np, cls=True)
        lines = []
        for line in result[0]:
            lines.append(line[1][0])
        return "\n".join(lines).strip()

    def save_text(self, text, date_str, period):
        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)
        file_path = os.path.join(output_dir, f"{period}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        log_message(f"{period} 段文本已儲存至: {file_path}")

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

        upper_half, lower_half = self.split_image(image)

        morning_text = self.ocr_text(upper_half)
        evening_text = self.ocr_text(lower_half)

        if not morning_text and not evening_text:
            log_message("無法辨識晨或晚段內容", "WARNING")
            morning_text = evening_text = "今日無內容"

        self.save_text(morning_text or "今日無內容", date_str, "morning")
        self.save_text(evening_text or "今日無內容", date_str, "evening")

        return True

def main():
    try:
        ocr = DailyLightOCRPaddle()
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