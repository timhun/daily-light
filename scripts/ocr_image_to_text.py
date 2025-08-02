import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import pytesseract
import re
from utils import load_config, get_date_string, ensure_directory, chinese_number_to_digit, log_message

# 設定根目錄與路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")

class DailyLightOCR:
    def __init__(self):
        self.config = load_config()

    def preprocess_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")

            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_image = self.auto_rotate_image(pil_image)
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

    def auto_rotate_image(self, image):
        try:
            angles = [0, 90, 180, 270]
            best_angle = 0
            best_confidence = 0
            for angle in angles:
                rotated = image.rotate(angle, expand=True)
                try:
                    data = pytesseract.image_to_data(rotated, lang='chi_tra', output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if conf.isdigit()]
                    if confidences:
                        avg_conf = sum(confidences) / len(confidences)
                        if avg_conf > best_confidence:
                            best_confidence = avg_conf
                            best_angle = angle
                except:
                    continue
            if best_angle != 0:
                log_message(f"自動旋轉圖片 {best_angle} 度")
                return image.rotate(best_angle, expand=True)
            return image
        except Exception as e:
            log_message(f"自動旋轉失敗: {str(e)}", "WARNING")
            return image

    def split_image(self, image):
        width, height = image.size
        upper_half = image.crop((0, 0, width, height // 2))
        lower_half = image.crop((0, height // 2, width, height))
        return upper_half, lower_half

    def ocr_text(self, image):
        try:
            config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz，。；：！？「」『』（）〈〉《》【】〔〕[]{}一二三四五六七八九十百千萬億零壹貳參肆伍陸柒捌玖拾佰仟萬億兆京垓秭穰溝澗正載極恆河沙阿僧祇那由他不可思議無量大數'
            text = pytesseract.image_to_string(image, lang='chi_tra', config=config)
            text = re.sub(r'\s+', '\n', text.strip())
            return re.sub(r'\n+', '\n', text)
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
        lower_text = self.ocr_text(lower)

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        if upper_text.strip():
            with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(upper_text.strip())
            log_message(f"晨間文本已保存: {output_dir}/morning.txt")
        else:
            with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write("今日無內容")

        if lower_text.strip():
            with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(lower_text.strip())
            log_message(f"晚間文本已保存: {output_dir}/evening.txt")
        else:
            with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write("今日無內容")

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