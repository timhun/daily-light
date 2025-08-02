import os
import sys
import re
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from utils import (
    load_config,
    get_date_string,
    ensure_directory,
    log_message,
)

# 專案路徑設定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")
DEBUG_DIR = os.path.join(BASE_DIR, "debug", "splits")

class DailyLightOCR:
    def __init__(self):
        self.config = load_config()
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', det_db_box_thresh=0.4, rec_algorithm='CRNN', use_space_char=True)

    def preprocess_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            # 灰階、亮度、對比增強、銳化、去噪
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            enhanced = cv2.convertScaleAbs(gray, alpha=1.3, beta=10)
            blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
            sharpen_kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
            sharpened = cv2.filter2D(blurred, -1, sharpen_kernel)
            return sharpened
        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None

    def split_image(self, image, save_debug=False, date_str=""):
        h = image.shape[0]
        upper = image[:h // 2]
        lower = image[h // 2:]
        if save_debug:
            ensure_directory(DEBUG_DIR)
            cv2.imwrite(os.path.join(DEBUG_DIR, f"{date_str}_morning.jpg"), upper)
            cv2.imwrite(os.path.join(DEBUG_DIR, f"{date_str}_evening.jpg"), lower)
        return upper, lower

    def ocr_text(self, image):
        try:
            result = self.ocr.ocr(image, cls=True)
            lines = []
            for line in result[0]:
                txt = line[1][0]
                if txt.strip():
                    lines.append(txt.strip())
            return self.postprocess_text(lines)
        except Exception as e:
            log_message(f"OCR 識別失敗: {str(e)}", "ERROR")
            return ""

    def postprocess_text(self, lines):
        if not lines:
            return ""
        # 嘗試依據標點斷句、合併為自然段
        paragraph = ""
        for line in lines:
            paragraph += line
            if line[-1:] in "。！？；":
                paragraph += "\n"
            else:
                paragraph += " "
        return re.sub(r'\n+', '\n', paragraph.strip())

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

        upper_img, lower_img = self.split_image(image, save_debug=True, date_str=date_str)
        upper_text = self.ocr_text(upper_img)
        lower_text = self.ocr_text(lower_img)

        if not upper_text and not lower_text:
            log_message("OCR 識別失敗，沒有提取到文字", "ERROR")
            return False

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        if upper_text.strip():
            morning_file = os.path.join(output_dir, "morning.txt")
            with open(morning_file, "w", encoding="utf-8") as f:
                f.write(upper_text.strip())
            log_message(f"晨間文本已保存: {morning_file}")

        if lower_text.strip():
            evening_file = os.path.join(output_dir, "evening.txt")
            with open(evening_file, "w", encoding="utf-8") as f:
                f.write(lower_text.strip())
            log_message(f"晚間文本已保存: {evening_file}")

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