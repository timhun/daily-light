import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR
from utils import (
    load_config,
    get_date_string,
    ensure_directory,
    chinese_number_to_digit,
    log_message,
    get_taiwan_time
)

# 設定專案根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")

class DailyLightOCR:
    def __init__(self, debug=False):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        self.config = load_config()
        self.debug = debug

    def preprocess_image(self, image_path):
        """強化圖片處理"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 調整亮度與對比
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # 二值化
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 去除雜點
            kernel = np.ones((1, 1), np.uint8)
            opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

            return opened
        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None

    def split_image(self, image_np, date_str):
        """分割圖片上下兩半"""
        h, w = image_np.shape
        upper = image_np[0:h // 2, :]
        lower = image_np[h // 2:, :]

        if self.debug:
            debug_dir = os.path.join(OUTPUT_DIR, date_str)
            ensure_directory(debug_dir)
            cv2.imwrite(os.path.join(debug_dir, "upper_half.jpg"), upper)
            cv2.imwrite(os.path.join(debug_dir, "lower_half.jpg"), lower)

        return upper, lower

    def ocr_text(self, image_np):
        """OCR 認字"""
        try:
            result = self.ocr.ocr(image_np, cls=True)
            texts = []
            for line in result[0]:
                line_text = line[1][0].strip()
                if line_text:
                    texts.append(line_text)
            return "\n".join(texts)
        except Exception as e:
            log_message(f"OCR 識別失敗: {str(e)}", "ERROR")
            return ""

    def format_text_for_speech(self, raw_text):
        """將辨識後的文字整理為段落，適合朗讀"""
        lines = raw_text.splitlines()
        cleaned = []
        buffer = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if len(line) < 10 and not line.endswith("。"):
                buffer += line
            else:
                if buffer:
                    line = buffer + line
                    buffer = ""
                cleaned.append(line)

        if buffer:
            cleaned.append(buffer)

        return "\n\n".join(cleaned)

    def process_daily_image(self, date_str=None):
        if not date_str:
            date_str = get_date_string()

        img_path = os.path.join(IMG_DIR, f"{date_str}.jpg")
        if not os.path.exists(img_path):
            log_message(f"圖片不存在: {img_path}", "ERROR")
            return False

        log_message(f"開始處理圖片: {img_path}")
        image_np = self.preprocess_image(img_path)
        if image_np is None:
            return False

        upper, lower = self.split_image(image_np, date_str)
        upper_text = self.ocr_text(upper)
        lower_text = self.ocr_text(lower)

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        success = False

        if upper_text.strip():
            formatted = self.format_text_for_speech(upper_text)
            with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(formatted)
            log_message(f"晨間文本已保存: {output_dir}/morning.txt")
            success = True

        if lower_text.strip():
            formatted = self.format_text_for_speech(lower_text)
            with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(formatted)
            log_message(f"晚間文本已保存: {output_dir}/evening.txt")
            success = True

        if not success:
            for period in ["morning", "evening"]:
                with open(os.path.join(output_dir, f"{period}.txt"), "w", encoding="utf-8") as f:
                    f.write("今日無內容")
            log_message("創建了默認內容文件")

        return success


def main():
    try:
        ocr = DailyLightOCR(debug=True)
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