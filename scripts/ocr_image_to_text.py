# scripts/ocr_image_to_text.py

import os
import re
import cv2
import numpy as np
from datetime import datetime
from paddleocr import PaddleOCR
from utils import ensure_dir, extract_date_from_filename, log_message

# Initialize OCR
ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False, show_log=False)

def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Shadow/background compensation
    blurred = cv2.medianBlur(enhanced, 11)
    blurred = np.where(blurred == 0, 1, blurred)  # Prevent divide-by-zero
    norm = cv2.divide(enhanced, blurred, scale=255)

    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(
        norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 15
    )
    return binary

def crop_sections(image):
    height = image.shape[0]
    top_half = image[:height // 2, :]
    bottom_half = image[height // 2:, :]
    return top_half, bottom_half

def ocr_image_section(img, debug_path=None):
    try:
        result = ocr.ocr(img, cls=True)
        if not result or not result[0]:
            return ""

        lines = []
        for line in result[0]:
            if line and len(line) >= 2 and line[1]:
                text = line[1][0].strip()
                confidence = line[1][1]
                if text and confidence > 0.5:
                    lines.append(text)

        joined = "\n".join(lines)
        joined = re.sub(r"\s+", " ", joined).strip()  # Clean and compact
        return joined
    except Exception as e:
        log_message("OCR processing error: {}".format(str(e)), "ERROR")
        return ""

def save_debug_images(base_dir, img_name, orig, proc, top, bot):
    ensure_dir(base_dir)
    try:
        cv2.imwrite(os.path.join(base_dir, f"{img_name}_original.jpg"), orig)
        cv2.imwrite(os.path.join(base_dir, f"{img_name}_processed.jpg"), proc)
        cv2.imwrite(os.path.join(base_dir, f"{img_name}_morning.jpg"), top)
        cv2.imwrite(os.path.join(base_dir, f"{img_name}_evening.jpg"), bot)
    except Exception as e:
        log_message("Failed to save debug images: {}".format(str(e)), "ERROR")

def main():
    input_dir = "docs/img"
    output_dir = "docs/podcast"
    debug_dir = "debug"

    supported_formats = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")

    for fname in sorted(os.listdir(input_dir)):
        if not fname.lower().endswith(supported_formats):
            continue

        date_str = extract_date_from_filename(fname)
        if not date_str:
            log_message(f"Cannot extract date from filename: {fname}", "WARNING")
            continue

        img_path = os.path.join(input_dir, fname)
        image = cv2.imread(img_path)

        if image is None:
            log_message(f"Failed to read image: {img_path}", "ERROR")
            continue

        try:
            processed = preprocess_image(image)
            top_half, bottom_half = crop_sections(processed)

            save_debug_images(debug_dir, fname.replace(".jpg", ""), image, processed, top_half, bottom_half)

            morning_text = ocr_image_section(top_half)
            evening_text = ocr_image_section(bottom_half)

            out_path = os.path.join(output_dir, date_str)
            ensure_dir(out_path)

            with open(os.path.join(out_path, "morning.txt"), "w", encoding="utf-8") as f:
                f.write(morning_text if morning_text.strip() else "今日無內容")

            with open(os.path.join(out_path, "evening.txt"), "w", encoding="utf-8") as f:
                f.write(evening_text if evening_text.strip() else "今日無內容")

            log_message(f"Completed: {fname}", "SUCCESS")
        except Exception as e:
            log_message(f"Processing failed: {fname}, Error: {str(e)}", "ERROR")

if __name__ == "__main__":
    main()