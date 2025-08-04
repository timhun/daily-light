#utils.py
import os
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
    return date_obj.strftime('%Y%m%d')

def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def chinese_number_to_digit(chinese_num):
    digits = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
              '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
              '零': '0'}
    result = chinese_num
    for zh, num in digits.items():
        result = result.replace(zh, num)
    return result

def log_message(message, level="INFO"):
    timestamp = get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")