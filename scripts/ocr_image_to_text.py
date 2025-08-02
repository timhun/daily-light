import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import re
from paddleocr import PaddleOCR
from utils import load_config, get_date_string, ensure_directory, log_message

# 設定專案根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")


class DailyLightOCR:
    def __init__(self):
        self.config = load_config()
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 使用中文與角度分類

    def preprocess_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")

            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_image = ImageEnhance.Contrast(pil_image).enhance(1.2)
            pil_image = ImageEnhance.Brightness(pil_image).enhance(1.1)
            gray_image = pil_image.convert('L')

            cv_image = cv2.cvtColor(np.array(gray_image), cv2.COLOR_GRAY2BGR)
            blurred = cv2.GaussianBlur(cv_image, (1, 1), 0)
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(blurred, -1, kernel)

            return Image.fromarray(cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB))
        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None

    def split_image(self, image):
        width, height = image.size
        upper_half = image.crop((0, 0, width, height // 2))
        lower_half = image.crop((0, height // 2, width, height))
        return upper_half, lower_half

    def ocr_text(self, image):
        try:
            image_np = np.array(image)
            result = self.ocr.ocr(image_np)

            # 擷取文字
            lines = []
            for line in result[0]:
                lines.append(line[1][0])
            return '\n'.join(lines).strip()
        except Exception as e:
            log_message(f"OCR 識別失敗: {str(e)}", "ERROR")
            return ""

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

        upper, lower = self.split_image(image)
        upper_text = self.ocr_text(upper)
        log_message(f"晨段 OCR 結果:\n{upper_text}")
        lower_text = self.ocr_text(lower)
        log_message(f"晚段 OCR 結果:\n{lower_text}")

        if not upper_text and not lower_text:
            log_message("OCR 識別失敗，沒有提取到文字", "ERROR")
            return False

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        if upper_text.strip():
            with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(upper_text.strip())
            log_message(f"晨間文本已保存: {output_dir}/morning.txt")

        if lower_text.strip():
            with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(lower_text.strip())
            log_message(f"晚間文本已保存: {output_dir}/evening.txt")

        if not upper_text.strip() and not lower_text.strip():
            for period in ["morning", "evening"]:
                with open(os.path.join(output_dir, f"{period}.txt"), "w", encoding="utf-8") as f:
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