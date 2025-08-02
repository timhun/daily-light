# scripts/ocr_image_to_text.py
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import pytesseract
import re
from utils import load_config, get_date_string, ensure_directory, chinese_number_to_digit, log_message

class DailyLightOCR:
    def __init__(self):
        self.config = load_config()
        
    def preprocess_image(self, image_path):
        """圖片預處理"""
        try:
            # 讀取圖片
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            
            # 轉換為PIL格式
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # 自動旋轉檢測
            pil_image = self.auto_rotate_image(pil_image)
            
            # 增強對比度和亮度
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(1.1)
            
            # 轉換為灰度圖
            gray_image = pil_image.convert('L')
            
            # 轉回OpenCV格式進行進一步處理
            cv_image = cv2.cvtColor(np.array(gray_image), cv2.COLOR_GRAY2BGR)
            
            # 高斯模糊去噪
            blurred = cv2.GaussianBlur(cv_image, (1, 1), 0)
            
            # 銳化
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(blurred, -1, kernel)
            
            return Image.fromarray(cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None
    
    def auto_rotate_image(self, image):
        """自動旋轉圖片"""
        try:
            # 嘗試不同角度的旋轉，找到文字識別效果最好的角度
            angles = [0, 90, 180, 270]
            best_angle = 0
            best_confidence = 0
            
            for angle in angles:
                rotated = image.rotate(angle, expand=True)
                
                # 使用 pytesseract 獲取置信度
                try:
                    data = pytesseract.image_to_data(rotated, lang='chi_tra', output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)
                        if avg_confidence > best_confidence:
                            best_confidence = avg_confidence
                            best_angle = angle
                except:
                    continue
            
            if best_angle != 0:
                log_message(f"自動旋轉圖片 {best_angle} 度")
                image = image.rotate(best_angle, expand=True)
            
            return image
            
        except Exception as e:
            log_message(f"自動旋轉失敗: {str(e)}", "WARNING")
            return image
    
    def split_image(self, image):
        """將圖片分割為上下兩部分"""
        width, height = image.size
        
        # 分割為上下兩部分
        upper_half = image.crop((0, 0, width, height // 2))
        lower_half = image.crop((0, height // 2, width, height))
        
        return upper_half, lower_half
    
    def ocr_text(self, image):
        """OCR 文字識別"""
        try:
            # 使用繁體中文識別
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz，。；：！？「」『』（）〈〉《》【】〔〕[]{}一二三四五六七八九十百千萬億零壹貳參肆伍陸柒捌玖拾佰仟萬億兆京垓秭穰溝澗正載極恆河沙阿僧祇那由他不可思議無量大數'
            
            text = pytesseract.image_to_string(image, lang='chi_tra', config=custom_config)
            
            # 清理文字
            text = re.sub(r'\s+', '\n', text.strip())
            text = re.sub(r'\n+', '\n', text)
            
            return text
            
        except Exception as e:
            log_message(f"OCR 識別失敗: {str(e)}", "ERROR")
            return ""
    
    def extract_date_from_text(self, text):
        """從文字中提取日期"""
        # 匹配中文日期格式，如「八月二日」
        pattern = r'([一二三四五六七八九十]+)月([一二三四五六七八九十]+)日'
        matches = re.findall(pattern, text)
        
        if matches:
            month, day = matches[0]
            # 轉換中文數字為阿拉伯數字
            month_num = chinese_number_to_digit(month)
            day_num = chinese_number_to_digit(day)
            
            try:
                month_int = int(month_num)
                day_int = int(day_num)
                return month_int, day_int
            except ValueError:
                pass
        
        return None, None
    
    def identify_segment_type(self, text):
        """識別文本段落類型（晨或晚）"""
        if '晨' in text or '早' in text:
            return 'morning'
        elif '晚' in text or '夜' in text or '晚上' in text:
            return 'evening'
        else:
            # 根據位置判斷，上半部分通常是晨
            return 'unknown'
    
    def process_daily_image(self, date_str=None):
        """處理每日圖片"""
        if date_str is None:
            date_str = get_date_string()
        
        # 圖片路径
        img_path = os.path.join('docs', 'img', f'{date_str}.jpg')
        
        if not os.path.exists(img_path):
            log_message(f"圖片不存在: {img_path}", "ERROR")
            return False
        
        log_message(f"開始處理圖片: {img_path}")
        
        # 預處理圖片
        processed_image = self.preprocess_image(img_path)
        if processed_image is None:
            return False
        
        # 分割圖片
        upper_half, lower_half = self.split_image(processed_image)
        
        # OCR 識別
        upper_text = self.ocr_text(upper_half)
        lower_text = self.ocr_text(lower_half)
        
        if not upper_text and not lower_text:
            log_message("OCR 識別失敗，沒有提取到文字", "ERROR")
            return False
        
        # 確定輸出目錄
        output_dir = os.path.join('docs', 'podcast', date_str)
        ensure_directory(output_dir)
        
        # 判斷文本類型並保存
        success = False
        
        # 處理上半部分（通常是晨）
        if upper_text.strip():
            morning_file = os.path.join(output_dir, 'morning.txt')
            with open(morning_file, 'w', encoding='utf-8') as f:
                f.write(upper_text.strip())
            log_message(f"晨間文本已保存: {morning_file}")
            success = True
        
        # 處理下半部分（通常是晚）
        if lower_text.strip():
            evening_file = os.path.join(output_dir, 'evening.txt')
            with open(evening_file, 'w', encoding='utf-8') as f:
                f.write(lower_text.strip())
            log_message(f"晚間文本已保存: {evening_file}")
            success = True
        
        if not success:
            # 如果都沒有內容，創建默認文件
            default_content = "今日無內容"
            for period in ['morning', 'evening']:
                file_path = os.path.join(output_dir, f'{period}.txt')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(default_content)
            log_message("創建了默認內容文件")
        
        return success

def main():
    """主函數"""
    try:
        ocr_processor = DailyLightOCR()
        date_str = get_date_string()
        
        log_message(f"開始處理 {date_str} 的每日亮光")
        
        success = ocr_processor.process_daily_image(date_str)
        
        if success:
            log_message("OCR 處理完成")
            exit(0)
        else:
            log_message("OCR 處理失敗", "ERROR")
            exit(1)
    
    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    main()
