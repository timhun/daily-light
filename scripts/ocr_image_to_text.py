# scripts/ocr_image_to_text.py
import os
import sys
from datetime import datetime
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

# 設定 TESSDATA_PREFIX 環境變數（在 GitHub Actions 中可能需要）
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
        print(f"錯誤: 圖片檔案未找到 {image_path}")
        return None

def ocr_and_split(date_str):
    """
    主函數，執行 OCR 並將內容分割成晨、晚兩部分。
    """
    base_path = os.path.join('docs', 'podcast', date_str)
    img_path = os.path.join('docs', 'img', f"{date_str}.jpg")
    
    print(f"正在處理圖片: {img_path}")

    # 建立輸出目錄
    os.makedirs(base_path, exist_ok=True)
    
    # 處理圖片
    processed_img = process_image(img_path)
    if processed_img is None:
        sys.exit(1)

    # OCR 辨識
    # 使用繁體中文語言包 chi_tra
    full_text = pytesseract.image_to_string(processed_img, lang='chi_tra')

    # 使用更靈活的正則表達式，同時辨識阿拉伯數字與中文數字
    morning_match = re.search(r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*．\s*晨', full_text)
    evening_match = re.search(r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*．\s*晚', full_text)

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
        print("未偵測到'晨'或'晚'的關鍵字，OCR 辨識可能失敗。")
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write("今日無內容")
        with open(os.path.join(base_path, 'evening.txt'), 'w', encoding='utf-8') as f:
            f.write("今日無內容")
        print("已寫入'今日無內容'。")
        return

    # 清理文字，移除不必要的換行和空白
    morning_text = re.sub(r'\s+', ' ', morning_text).strip()
    evening_text = re.sub(r'\s+', ' ', evening_text).strip()

    if morning_text:
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write(morning_text)
        print(f"成功寫入 morning.txt，內容長度: {len(morning_text)}")
    else:
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding 市='utf-8') as f:
            f.write("今日晨間無內容")
        print("晨間內容為空。")

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
        target_date = datetime.now(tz).strftime('%Y%m%d')

    ocr_and_split(target_date)
