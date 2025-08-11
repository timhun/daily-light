import os
import re
from PIL import Image
import pytesseract
from utils import load_config, get_date_string, ensure_directory, get_taiwan_time, log_message

class OCRImageToText:
    def __init__(self):
        self.config = load_config()
        self.ocr_config = self.config.get('ocr', {})
        self.image_dir = os.path.join('docs', 'img')
        self.output_dir = os.path.join('docs', 'podcast', get_date_string())
        ensure_directory(self.output_dir)
        self.output_text_path = os.path.join(self.image_dir, f'{get_date_string()}.txt')

    def process_image(self, image_path):
        """處理圖片並提取文字，基於段落分隔生成 morning.txt 和 evening.txt"""
        try:
            log_message(f"開始處理圖片: {image_path}")
            # 打開圖片並進行 OCR
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='chi_tra', config='--oem 3 --psm 6')
            log_message(f"OCR 提取的原始文字: {text[:50]}...")

            if not text.strip():
                log_message("OCR 提取的文字為空", "WARNING")
                return False

            # 將文字保存到臨時文件
            with open(self.output_text_path, 'w', encoding='utf-8') as f:
                f.write(text.strip())
            log_message(f"文字已保存至: {self.output_text_path}")

            # 分割晨間和晚間內容，基於空行
            lines = text.strip().split('\n')
            morning_text = []
            evening_text = []
            state = 'morning'  # 預設狀態為晨間

            for line in lines:
                line = line.strip()
                if not line:  # 空行，切換到晚間
                    state = 'evening'
                    continue
                if state == 'morning':
                    morning_text.append(line)
                elif state == 'evening':
                    evening_text.append(line)

            morning_text = '\n'.join(morning_text).strip()
            evening_text = '\n'.join(evening_text).strip()

            if not morning_text:
                log_message("未找到晨間內容，寫入'今日無內容'", "WARNING")
                morning_text = "今日無內容"
            else:
                log_message(f"晨間內容: {morning_text[:50]}...")

            if not evening_text:
                log_message("未找到晚間內容，寫入'今日無內容'", "WARNING")
                evening_text = "今日無內容"
            else:
                log_message(f"晚間內容: {evening_text[:50]}...")

            # 保存分段文件
            morning_file = os.path.join(self.output_dir, 'morning.txt')
            evening_file = os.path.join(self.output_dir, 'evening.txt')
            with open(morning_file, 'w', encoding='utf-8') as f:
                f.write(morning_text)
            with open(evening_file, 'w', encoding='utf-8') as f:
                f.write(evening_text)

            return True

        except Exception as e:
            log_message(f"OCR 處理失敗: {str(e)}", "ERROR")
            return False

    def run(self):
        """主運行邏輯"""
        try:
            log_message("開始 OCR 處理...")
            image_path = os.path.join(self.image_dir, f'{get_date_string()}.jpg')
            if not os.path.exists(image_path):
                log_message(f"圖片 {image_path} 不存在", "ERROR")
                return False

            success = self.process_image(image_path)
            if success:
                log_message("OCR 處理完成")
            else:
                log_message("OCR 處理失敗，但繼續執行", "WARNING")
            return success

        except Exception as e:
            log_message(f"主程序執行失敗: {str(e)}", "ERROR")
            return False

def main():
    """主函數"""
    try:
        ocr = OCRImageToText()
        success = ocr.run()

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