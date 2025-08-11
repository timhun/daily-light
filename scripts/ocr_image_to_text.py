import os
import re
import sys
from utils import load_config, get_date_string, ensure_directory, get_taiwan_time, log_message

class OCRImageToText:
    def __init__(self):
        self.config = load_config()
        self.output_dir = os.path.join('docs', 'podcast', get_date_string())
        ensure_directory(self.output_dir)
        self.input_text_path = os.path.join('docs', 'img', f'{get_date_string()}.txt')

    def process_text(self):
        """處理校正稿並分割為晨間和晚間內容，基於空行"""
        try:
            log_message(f"開始處理校正稿: {self.input_text_path}")
            if not os.path.exists(self.input_text_path):
                log_message(f"校正稿 {self.input_text_path} 不存在", "ERROR")
                return False

            with open(self.input_text_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()

            if not text:
                log_message("校正稿內容為空，寫入'今日無內容'", "WARNING")
                return False

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
            log_message(f"處理校正稿失敗: {str(e)}", "ERROR")
            return False

    def run(self):
        """主運行邏輯"""
        try:
            log_message("開始處理校正稿...")
            success = self.process_text()
            if success:
                log_message("校正稿處理完成")
            else:
                log_message("校正稿處理失敗，但繼續執行", "WARNING")
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
            log_message("校正稿處理完成")
            sys.exit(0)
        else:
            log_message("校正稿處理失敗", "ERROR")
            sys.exit(1)

    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()