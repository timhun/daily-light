import os
import re
import cv2
import numpy as np
from datetime import datetime
from paddleocr import PaddleOCR
from utils import ensure_dir, extract_date_from_filename

# === 初始化 OCR ===

ocr = PaddleOCR(use_angle_cls=True, lang=‘ch’, use_gpu=False, show_log=False)

def preprocess_image(image):
# 灰階
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

```
# CLAHE 增強對比
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(gray)

# 陰影/背景補償
blurred = cv2.medianBlur(enhanced, 11)
# 防止除零錯誤
blurred = np.where(blurred == 0, 1, blurred)
norm = cv2.divide(enhanced, blurred, scale=255)

# 自適應二值化
binary = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 35, 15)
return binary
```

def crop_sections(image):
height = image.shape[0]
top_half = image[:height // 2, :]
bottom_half = image[height // 2:, :]
return top_half, bottom_half

def ocr_image_section(img, debug_path=None):
try:
result = ocr.ocr(img, cls=True)

```
    if not result or not result[0]:
        return ""
        
    lines = []
    for line in result[0]:
        if line and len(line) >= 2 and line[1]:
            text = line[1][0].strip()
            confidence = line[1][1]
            
            # 只保留信心度較高的結果
            if text and confidence > 0.5:
                lines.append(text)

    joined = '\n'.join(lines)
    
    # 原始圖片已經是繁體中文，不需要簡繁轉換
    # 只做基本的文本清理
    joined = re.sub(r'\s+', ' ', joined)  # 合併多餘空格
    joined = joined.strip()
    
    return joined
    
except Exception as e:
    print(f"OCR處理錯誤: {e}")
    return ""
```

def save_debug_images(base_dir, img_name, orig, proc, top, bot):
ensure_dir(base_dir)
try:
cv2.imwrite(os.path.join(base_dir, f”{img_name}_original.jpg”), orig)
cv2.imwrite(os.path.join(base_dir, f”{img_name}_processed.jpg”), proc)
cv2.imwrite(os.path.join(base_dir, f”{img_name}_morning.jpg”), top)
cv2.imwrite(os.path.join(base_dir, f”{img_name}_evening.jpg”), bot)
except Exception as e:
print(f”保存調試圖像失敗: {e}”)

def main():
input_dir = “docs/img”
output_dir = “docs/podcast”
debug_dir = “debug”

```
# 支持多種圖像格式
supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

for fname in sorted(os.listdir(input_dir)):
    if not fname.lower().endswith(supported_formats):
        continue

    date_str = extract_date_from_filename(fname)
    if not date_str:
        print(f"❌ 無法從檔名擷取日期：{fname}")
        continue

    img_path = os.path.join(input_dir, fname)
    image = cv2.imread(img_path)

    if image is None:
        print(f"❌ 圖片讀取失敗：{img_path}")
        continue

    try:
        processed = preprocess_image(image)
        top_half, bottom_half = crop_sections(processed)

        save_debug_images(debug_dir, fname.replace(".jpg", ""), image, processed, top_half, bottom_half)

        # 辨識上下段
        morning_text = ocr_image_section(top_half)
        evening_text = ocr_image_section(bottom_half)

        # 儲存
        out_path = os.path.join(output_dir, date_str)
        ensure_dir(out_path)

        morning_file = os.path.join(out_path, "morning.txt")
        evening_file = os.path.join(out_path, "evening.txt")

        with open(morning_file, "w", encoding="utf-8") as f:
            f.write(morning_text if morning_text.strip() else "今日無內容")

        with open(evening_file, "w", encoding="utf-8") as f:
            f.write(evening_text if evening_text.strip() else "今日無內容")

        print(f"✅ 已完成：{fname}")
        
    except Exception as e:
        print(f"❌ 處理失敗：{fname}, 錯誤：{e}")
```

if **name** == “**main**”:
main()