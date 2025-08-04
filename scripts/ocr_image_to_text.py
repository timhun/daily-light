import os
import sys
import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageOps
from datetime import datetime
import pytz

# ===== 🧠 初始化 PaddleOCR =====
ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 繁中直式適用

# ===== 🗂️ 圖片路徑與輸出設定 =====
today = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y%m%d")
image_path = os.path.abspath(f"docs/img/{today}.jpg")
output_dir = os.path.abspath(f"docs/podcast/{today}")
os.makedirs(output_dir, exist_ok=True)

# ===== 🧹 前處理函式 =====
def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_eq = cv2.equalizeHist(gray)
    blurred = cv2.GaussianBlur(img_eq, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

# ===== 🌀 自動旋轉矯正 =====
def auto_rotate(img):
    try:
        import imutils
        return imutils.rotate_bound(img, angle=0)  # 預留旋轉介面
    except:
        return img

# ===== ✂️ 圖片上下分段 =====
def split_image(img):
    h = img.shape[0]
    top = img[:h // 2, :]
    bottom = img[h // 2:, :]
    return top, bottom

# ===== 🔍 辨識文字段落清理 =====
def ocr_text_clean(results):
    paragraphs = []
    for line in results:
        text = line[1][0]
        if len(text.strip()) > 3:
            paragraphs.append(text.strip())
    return "\n".join(paragraphs)

# ===== 🧪 OCR 主程式 =====
def run_ocr(image_path, debug=False):
    img = cv2.imread(image_path)
    img = auto_rotate(img)
    img = preprocess_image(img)
    top_img, bottom_img = split_image(img)

    # 儲存 debug 圖片
    if debug:
        cv2.imwrite(os.path.join(output_dir, "morning_debug.jpg"), top_img)
        cv2.imwrite(os.path.join(output_dir, "evening_debug.jpg"), bottom_img)

    # OCR
    morning_result = ocr.ocr(top_img, cls=True)
    evening_result = ocr.ocr(bottom_img, cls=True)

    # 整理
    morning_text = ocr_text_clean(morning_result[0]) if morning_result else "今日無內容"
    evening_text = ocr_text_clean(evening_result[0]) if evening_result else "今日無內容"

    with open(os.path.join(output_dir, "morning.txt"), "w", encoding="utf-8") as f:
        f.write(morning_text)
    with open(os.path.join(output_dir, "evening.txt"), "w", encoding="utf-8") as f:
        f.write(evening_text)

    print("✅ OCR 完成")
    print("晨：", morning_text[:50], "...")
    print("晚：", evening_text[:50], "...")

# ===== 🚀 執行 =====
if __name__ == "__main__":
    if not os.path.exists(image_path):
        print(f"❌ 找不到圖片: {image_path}")
        sys.exit(1)
    run_ocr(image_path, debug=True)