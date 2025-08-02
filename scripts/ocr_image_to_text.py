# scripts/ocr_image_to_text.py
import os
import sys
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from utils import load_config, get_date_string, ensure_directory, log_message

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")

class DailyLightOCR:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        self.debug = True

    def preprocess_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return Image.fromarray(binary)
        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None

    def split_image(self, image):
        width, height = image.size
        upper = image.crop((0, 0, width, height // 2))
        lower = image.crop((0, height // 2, width, height))
        if self.debug:
            upper.save(os.path.join(OUTPUT_DIR, "debug_upper.jpg"))
            lower.save(os.path.join(OUTPUT_DIR, "debug_lower.jpg"))
        return upper, lower

    def ocr_text(self, image):
        image_np = np.array(image)
        result = self.ocr.ocr(image_np)
        lines = []
        for line in result[0]:
            text = line[1][0].strip()
            if text:
                lines.append(text)
        return self.organize_paragraphs(lines)

    def organize_paragraphs(self, lines):
        """將文字行整理成段落"""
        paragraph = ""
        for line in lines:
            if line.endswith("。") or line.endswith("！") or line.endswith("？"):
                paragraph += line + "\n"
            else:
                paragraph += line
        return paragraph.strip()

    def process_daily_image(self, date_str=None):
        if not date_str:
            date_str = get_date_string()

        img_path = os.path.join(IMG_DIR, f"{date_str}.jpg")
        if not os.path.exists(img_path):
            log_message(f"圖片不存在: {img_path}", "ERROR")
            return False

        log_message(f"開始處理圖片: {img_path}")
        image = self.preprocess_image(img_path)
        if image is None:
            return False

        upper_img, lower_img = self.split_image(image)
        upper_text = self.ocr_text(upper_img)
        lower_text = self.ocr_text(lower_img)

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        if upper_text:
            with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(upper_text)
            log_message(f"晨間文本已保存: {output_dir}/morning.txt")

        if lower_text:
            with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(lower_text)
            log_message(f"晚間文本已保存: {output_dir}/evening.txt")

        if not upper_text and not lower_text:
            for p in ['morning', 'evening']:
                with open(os.path.join(output_dir, f"{p}.txt"), "w", encoding="utf-8") as f:
                    f.write("今日無內容")
            log_message("創建了默認內容文件")

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