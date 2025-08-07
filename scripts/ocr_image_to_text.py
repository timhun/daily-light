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
        if not os.path.exists(image_path):
            print(f"錯誤: 圖片檔案未找到 {image_path}")
            return None
        img = Image.open(image_path)
        # 轉換為灰度
        img = img.convert('L')
        # 增加對比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        # 銳化
        img = img.filter(ImageFilter.SHARPEN)
        return img
    except Exception as e:
        print(f"錯誤: 處理圖片 {image_path} 失敗 - {str(e)}")
        return None

def ocr_and_split(date_str):
    """
    主函數，執行 OCR 並將內容分割成晨、晚兩部分，優先採用校正稿內容。
    """
    base_path = os.path.join('docs', 'podcast', date_str)
    img_path = os.path.join('docs', 'img', f"{date_str}.jpg")
    correction_path = os.path.join('docs', 'img', f"{date_str}.txt")
    
    print(f"正在處理圖片: {img_path}")

    # 強制創建輸出目錄
    os.makedirs(base_path, exist_ok=True)
    print(f"輸出目錄已創建: {base_path}")

    # 檢查並處理圖片
    processed_img = process_image(img_path)
    if processed_img is None:
        print(f"圖片處理失敗，跳過 {date_str} 的處理。")
        return

    # OCR 辨識
    print(f"開始執行 OCR 辨識...")
    full_text_ocr = pytesseract.image_to_string(processed_img, lang='chi_tra')
    print(f"OCR 辨識完成，提取文字長度: {len(full_text_ocr.strip())}")

    # 檢查校正稿是否存在，優先使用校正稿內容
    full_text = full_text_ocr
    if os.path.exists(correction_path):
        with open(correction_path, 'r', encoding='utf-8') as f:
            full_text_correction = f.read().strip()
        if full_text_correction:
            print(f"找到校正稿: {correction_path}，優先採用校正稿內容。")
            full_text = full_text_correction
        else:
            print(f"校正稿 {correction_path} 內容為空，使用 OCR 結果。")
    else:
        print("未找到校正稿，使用 OCR 結果。")

    # 更新正則表達式，支援逗號和句號作為分隔符號，並處理多餘空格
    morning_match = re.search(r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*[，\.]\s*晨', full_text)
    evening_match = re.search(r'八月\s*[\d一二三四五六七八九十百]+\s*日\s*[，\.]\s*晚', full_text)

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
        print("未偵測到'晨'或'晚'的關鍵字，OCR 或校正稿可能失敗。")
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write("今日無內容")
        with open(os.path.join(base_path, 'evening.txt'), 'w', encoding='utf-8') as f:
            f.write("今日無內容")
        print(f"已寫入'今日無內容'至 {base_path}/morning.txt 和 {base_path}/evening.txt")
        return

    # 清理文字，移除不必要的換行和空白
    morning_text = re.sub(r'\s+', ' ', morning_text).strip()
    evening_text = re.sub(r'\s+', ' ', evening_text).strip()

    if morning_text:
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write(morning_text)
        print(f"成功寫入 {base_path}/morning.txt，內容長度: {len(morning_text)}")
    else:
        with open(os.path.join(base_path, 'morning.txt'), 'w', encoding='utf-8') as f:
            f.write("今日晨間無內容")
        print(f"晨間內容為空，已寫入 {base_path}/morning.txt")

    if evening_text:
        with open(os.path.join(base_path, 'evening.txt'), 'w', encoding='utf-8') as f:
            f.write(evening_text)
        print(f"成功寫入 {base_path}/evening.txt，內容長度: {len(evening_text)}")
    else:
        with open(os.path.join(base_path, 'evening.txt'), 'w', encoding='utf-8') as f:
            f.write("今日晚間無內容")
        print(f"晚間內容為空，已寫入 {base_path}/evening.txt")

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
        print(f"使用當前日期: {target_date}")

    ocr_and_split(target_date)