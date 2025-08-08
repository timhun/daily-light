# utils.py
import os
import re
import json
from datetime import datetime
import pytz

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'podcast_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_taiwan_time():
    tz = pytz.timezone('Asia/Taipei')
    return datetime.now(tz)

def get_date_string(date_obj=None):
    if not date_obj:
        date_obj = get_taiwan_time()
    return date_obj.strftime('%m%d')

def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def ensure_dir(path):
    """ensure_directory 的別名，用於OCR腳本兼容性"""
    return ensure_directory(path)

def extract_date_from_filename(filename):
    """從文件名提取日期"""
    name_without_ext = os.path.splitext(filename)[0]

    patterns = [
        r'(\d{2}\d{2})',       # MMDD
        r'(\d{2}-\d{2})',      # MM-DD
        r'(\d{2}_\d{2})',      # MM_DD
    ]

    for pattern in patterns:
        match = re.search(pattern, name_without_ext)
        if match:
            date_str = match.group(1)
            if len(date_str) == 4 and '-' not in date_str and '_' not in date_str:
                date_str = f"{date_str[:2]}-{date_str[2:4]}"
            elif '_' in date_str:
                date_str = date_str.replace('_', '-')
            try:
                datetime.strptime(f"{get_taiwan_time().year}-{date_str}", '%Y-%m-%d')
                return date_str
            except ValueError:
                continue

    chinese_date_pattern = r'(\d{1,2})月(\d{1,2})日'
    match = re.search(chinese_date_pattern, name_without_ext)
    if match:
        month, day = match.groups()
        return f"{month.zfill(2)}-{day.zfill(2)}"

    return None

def chinese_number_to_digit(chinese_num):
    digits = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
              '六': '6', '七': '7', '八': '8', '九': '9', '十': '10', '零': '0'}
    result = chinese_num
    for zh, num in digits.items():
        result = result.replace(zh, num)
    return result

def log_message(message, level="INFO"):
    timestamp = get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")

def format_date_for_output(date_str):
    """將日期字符串格式化為輸出目錄名稱"""
    try:
        date_obj = datetime.strptime(f"{get_taiwan_time().year}-{date_str}", '%Y-%m-%d')
        return date_obj.strftime('%m%d')
    except ValueError:
        return date_str

def validate_date_string(date_str):
    try:
        datetime.strptime(f"{get_taiwan_time().year}-{date_str}", '%Y-%m-%d')
        return True
    except ValueError:
        return False

def get_file_info(filepath):
    if not os.path.exists(filepath):
        return None
    stat = os.stat(filepath)
    return {
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'created': datetime.fromtimestamp(stat.st_ctime)
    }
