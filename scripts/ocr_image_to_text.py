#ocr_image_to_text_enhanced.py
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import re
from paddleocr import PaddleOCR
from utils import load_config, get_date_string, ensure_directory, log_message

# 設定專案根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "img")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "podcast")
DEBUG_SAVE = True  # 儲存分割圖片與前處理圖片供 debug

class DailyLightOCR:
    def __init__(self):
        self.config = load_config()
        # 使用更高精度的模型配置
        self.ocr = PaddleOCR(
            use_angle_cls=True, 
            lang='ch', 
            use_gpu=False,
            det_model_dir=None,  # 使用預設最新模型
            rec_model_dir=None,
            cls_model_dir=None,
            det_limit_side_len=1280,  # 增加檢測圖片邊長限制
            det_limit_type='max',
            rec_batch_num=6,  # 批次處理數量
            max_text_length=50,  # 最大文字長度
            rec_image_shape="3, 48, 320",  # 識別圖片尺寸
            drop_score=0.3  # 降低置信度閾值，保留更多結果
        )

    def enhance_image_quality(self, image):
        """進階圖片品質提升"""
        # 轉換為 PIL Image 進行更細緻的處理
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # 1. 銳化濾鏡
        sharpening_filter = ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)
        image = image.filter(sharpening_filter)
        
        # 2. 對比度增強
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
        
        # 3. 亮度調整
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        
        # 4. 清晰度增強
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        return image

    def preprocess_image(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")

            # 自動旋轉（若有 EXIF 或非正向圖片）
            if image.shape[0] < image.shape[1]:
                image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

            # 降噪處理
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
            
            # 灰階處理
            gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

            # 形態學操作去除雜訊
            kernel = np.ones((2,2), np.uint8)
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # 高斯模糊然後銳化
            blur = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0)
            sharpened = cv2.addWeighted(gray, 2.0, blur, -1.0, 0)

            # 自適應直方圖均衡化
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            contrast = clahe.apply(sharpened)

            # 進階圖片品質提升
            enhanced = self.enhance_image_quality(contrast)
            
            # 轉回 numpy 進行二值化
            enhanced_np = np.array(enhanced)
            
            # 多種二值化方法組合
            # 1. Otsu's 二值化
            _, binary1 = cv2.threshold(enhanced_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 2. 自適應二值化
            binary2 = cv2.adaptiveThreshold(enhanced_np, 255,
                                           cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 21, 10)
            
            # 3. 組合兩種方法
            binary = cv2.bitwise_and(binary1, binary2)
            
            # 形態學後處理
            kernel = np.ones((1,1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

            # 儲存前處理圖片供 debug
            if DEBUG_SAVE:
                debug_dir = os.path.join(OUTPUT_DIR, get_date_string())
                ensure_directory(debug_dir)
                cv2.imwrite(os.path.join(debug_dir, "debug_preprocessed.jpg"), binary)
                cv2.imwrite(os.path.join(debug_dir, "debug_enhanced.jpg"), enhanced_np)

            # 回傳 PIL 物件
            return Image.fromarray(binary)
        except Exception as e:
            log_message(f"圖片預處理失敗: {str(e)}", "ERROR")
            return None

    def split_image_smart(self, image, date_str):
        """智能分割圖片，偵測文字區域"""
        width, height = image.size
        
        # 轉換為 OpenCV 格式進行分析
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # 尋找文字區域
        contours, _ = cv2.findContours(255 - gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 根據輪廓計算更精確的分割點
        y_coords = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > width * 0.1 and h > 10:  # 過濾太小的區域
                y_coords.extend([y, y + h])
        
        if y_coords:
            y_coords.sort()
            mid_point = y_coords[len(y_coords) // 2]
            # 確保分割點在合理範圍內
            split_point = max(height // 3, min(height * 2 // 3, mid_point))
        else:
            split_point = height // 2
        
        upper_half = image.crop((0, 0, width, split_point))
        lower_half = image.crop((0, split_point, width, height))

        if DEBUG_SAVE:
            debug_dir = os.path.join(OUTPUT_DIR, date_str)
            ensure_directory(debug_dir)
            upper_half.save(os.path.join(debug_dir, "debug_morning.jpg"))
            lower_half.save(os.path.join(debug_dir, "debug_evening.jpg"))
            # 儲存分割線位置資訊
            with open(os.path.join(debug_dir, "split_info.txt"), "w") as f:
                f.write(f"分割點: {split_point}, 圖片高度: {height}")

        return upper_half, lower_half

    def ocr_image_multi_attempt(self, pil_img):
        """多次嘗試 OCR 辨識，取最佳結果"""
        attempts = []
        
        # 原圖辨識
        try:
            img_np = np.array(pil_img)
            result = self.ocr.ocr(img_np, cls=True)
            if result and result[0]:
                text = self.extract_text_from_result(result)
                attempts.append(("original", text, len(text)))
        except Exception as e:
            log_message(f"原圖 OCR 失敗: {str(e)}", "WARNING")
        
        # 放大圖片辨識
        try:
            enlarged = pil_img.resize((pil_img.width * 2, pil_img.height * 2), Image.LANCZOS)
            img_np = np.array(enlarged)
            result = self.ocr.ocr(img_np, cls=True)
            if result and result[0]:
                text = self.extract_text_from_result(result)
                attempts.append(("enlarged", text, len(text)))
        except Exception as e:
            log_message(f"放大圖片 OCR 失敗: {str(e)}", "WARNING")
        
        # 反色辨識（適用於深色背景）
        try:
            inverted = Image.eval(pil_img, lambda x: 255 - x)
            img_np = np.array(inverted)
            result = self.ocr.ocr(img_np, cls=True)
            if result and result[0]:
                text = self.extract_text_from_result(result)
                attempts.append(("inverted", text, len(text)))
        except Exception as e:
            log_message(f"反色圖片 OCR 失敗: {str(e)}", "WARNING")
        
        if not attempts:
            return ""
        
        # 選擇辨識出最多文字的結果
        best_attempt = max(attempts, key=lambda x: x[2])
        log_message(f"最佳辨識方法: {best_attempt[0]}, 字數: {best_attempt[2]}")
        
        return self.clean_text(best_attempt[1])

    def extract_text_from_result(self, result):
        """從 OCR 結果中提取文字"""
        lines = []
        for line in result[0]:
            if line and len(line) > 1:
                text = line[1][0]
                confidence = line[1][1]
                # 只保留置信度較高的結果
                if confidence > 0.3:
                    lines.append(text.strip())
        return '\n'.join(lines)

    def clean_text(self, raw_text):
        """改進的文字清理功能"""
        lines = raw_text.splitlines()
        cleaned = []
        prev_line = ""
        
        for line in lines:
            line = line.strip()
            
            # 跳過太短或只有符號的行
            if len(line) < 2 or re.match(r'^[\W\d_]+$', line):
                continue
            
            # 跳過重複行
            if line == prev_line:
                continue
            
            # 修正常見的 OCR 錯誤
            line = self.fix_common_ocr_errors(line)
            
            cleaned.append(line)
            prev_line = line
        
        return '\n'.join(cleaned)

    def fix_common_ocr_errors(self, text):
        """修正常見的 OCR 辨識錯誤"""
        # 常見的中文 OCR 錯誤對應表
        error_corrections = {
            '0': '○',  # 數字0常被誤認為圓圈
            '1': 'l',  # 數字1常被誤認為小寫L
            '｜': '丨',  # 全形豎線
            '—': '一',  # 破折號誤認為一
            '．': '。',  # 全形句號
            '；': ';',  # 分號
        }
        
        for wrong, correct in error_corrections.items():
            # 只在中文語境下進行替換
            if re.search(r'[\u4e00-\u9fff]', text):
                text = text.replace(wrong, correct)
        
        return text

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

        upper, lower = self.split_image_smart(image, date_str)
        
        log_message("開始晨間文本辨識...")
        morning_text = self.ocr_image_multi_attempt(upper)
        
        log_message("開始晚間文本辨識...")
        evening_text = self.ocr_image_multi_attempt(lower)

        output_dir = os.path.join(OUTPUT_DIR, date_str)
        ensure_directory(output_dir)

        if morning_text.strip():
            with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(morning_text.strip())
            log_message(f"晨間文本已保存: {output_dir}/morning.txt (字數: {len(morning_text)})")

        if evening_text.strip():
            with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(evening_text.strip())
            log_message(f"晚間文本已保存: {output_dir}/evening.txt (字數: {len(evening_text)})")

        if not morning_text.strip() and not evening_text.strip():
            for period in ["morning", "evening"]:
                with open(os.path.join(output_dir, f"{period}.txt"), "w", encoding="utf-8") as f:
                    f.write("今日無內容")
            log_message("未辨識出內容，已建立預設空白內容")
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
