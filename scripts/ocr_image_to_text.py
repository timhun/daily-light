# scripts/ocr_image_to_text.py
import os
import sys
from datetime import datetime
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

# 設定 TESSDATA_PREFIX 環境變數 (在 GitHub Actions 中可能需要)
# os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/4.00/tessdata'

def process_image(image_path):
    """
    對圖片進行增強處理以提高 OCR 辨識率。
    """
    try:
        img = Image.open(image_path)
        # 轉換為灰度
        img = img.convert('L')
        # 增加對比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        # 銳化
        img = img.filter(ImageFilter.SHARPEN)
        return img
    except FileNotFoundError:
        print(f"Error: 圖片檔案未找到 {image_path}")
        return None

def read_correction_text(correction_path):
    """
    讀取校正文字稿。
    """
    try:
        with open(correction_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            # 清理文字，統一換行符號和移除多餘空白
            text = re.sub(r'\r\n|\r', '\n', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    except FileNotFoundError:
        print(f"校正文字稿未找到: {correction_path}")
        return None
    except Exception as e:
        print(f"讀取校正文字稿失敗: {str(e)}")
        return None

def split_text(full_text, date_str):
    """
    分割文字為晨、晚兩部分，改進正則表達式以提高匹配靈活性。
    """
    # 改進正則表達式，支援更多分隔符號和格式
    morning_pattern = r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*[•．]\s*晨'
    evening_pattern = r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*[•．]\s*晚'
    
    morning_match = re.search(r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*[．。]\s*晨', full_text)
    evening_match = re.search(r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*[．。]\s*晚', full_text)
    
    morning_text = ""
    evening_text = ""

    if morning_match and evening_match:
        print("偵測到'晨'與'晚'的關鍵字。")
        morning_start_index = morning_match.end()
        evening_start_index = evening_match.start()
        morning_text = full_text[morning_start_index:evening_start_index].strip()
        evening_text = full_text[evening_match.end():].strip()
        
    elif morning_match:
        print("只偵測到'晨'的關鍵字。")
        morning_text = full_text[morning_match.end():].strip()
    
    elif evening_match:
        print("只偵測到'晚'的關鍵字。")
        evening_text = full_text[evening_match.end():].strip()

    else:
        print(f"未偵測到'晨'或'晚'的關鍵字，完整文字: {full_text}")
        return None, None

    # 清理文字，移除不必要的換行和空白
    morning_text = re.sub(r'\s+', ' ', morning_text).strip()
    evening_text = re.sub(r'\s+', ' ', evening_text).strip()
    
    return morning_text, evening_text

def ocr_and_split(date_str):
    """
    主函數，執行 OCR 並將內容分割成晨、晚兩部分，並與校正文字稿比對。
    """
    # 將日期格式從 YYYYMMDD 轉為 MMDD
    if len(date_str) == 8:
        date_str = date_str[4:]
    base_path = os.path.join('docs', 'podcast', date_str)
    img_path = os.path.join('docs', 'img', f"{date_str}.jpg")
    correction_path = os.path.join('docs', 'img', f"{date_str}.txt")
    
    print(f"正在處理圖片: {img_path}")
    print(f"檢查校正文字稿: {correction_path}")

    # 建立輸出目錄
    os.makedirs(base_path, exist_ok=True)
    
    # 讀取校正文字稿
    correction_text = read_correction_text(correction_path)
    
    if correction_text:
        print("使用校正文字稿進行處理。")
        morning_text, evening_text = split_text(correction_text, date_str)
    else:
        print("未找到校正文字稿，使用 OCR 進行處理。")
        # 處理圖片
        processed_img = process_image(img_path)
        if processed_img is None:
            sys.exit(1)

        # OCR 辨識
        full_text = pytesseract.image_to_string(processed_img, lang='chi_tra')
        morning_text, evening_text = split_text(full_text, date_str)

    if morning_text is None and evening_text is None:
        print("文字分割失敗，OCR 或校正文字稿可能有誤。")
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write("今日無內容")
        with open(os.path.join(base_path, 'evening.txt'), 'w', encoding='utf-8') as f:
            f.write("今日無內容")
        print("已寫入'今日無內容'。")
        return

    # 寫入晨間內容
    if morning_text:
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write(morning_text)
        print(f"成功寫入 morning.txt，內容長度: {len(morning_text)}")
    else:
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write("今日晨間無內容")
        print("晨間內容為空。")

    # 寫入晚間內容
    if evening_text:
        with open(os.path.join(base_path, 'evening.txt'), 'w', encoding='utf-8') as f:
            f.write(evening_text)
        print(f"成功寫入 evening.txt，內容長度: {len(evening_text)}")
    else:
        with open(os.path.join(base_path, 'evening.txt'), 'w', encoding='utf-8') as f:
            f.write("今日晚間無內容")
        print("晚間內容為空。")


if __name__ == "__main__":
    # 如果從命令行傳入日期，則使用該日期，否則使用當前日期
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        # 假設在台灣時區執行
        from datetime import datetime
        import pytz
        tz = pytz.timezone('Asia/Taipei')
        target_date = datetime.now(tz).strftime('%m%d')

    ocr_and_split(target_date)
