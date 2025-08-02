import os
import json
from datetime import datetime, timedelta
import pytz

def load_config():
    """載入配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'podcast_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_taiwan_time():
    """獲取台灣時間"""
    tw_tz = pytz.timezone('Asia/Taipei')
    return datetime.now(tw_tz)

def get_date_string(date_obj=None):
    """獲取日期字符串 YYYYMMDD"""
    if date_obj is None:
        date_obj = get_taiwan_time()
    return date_obj.strftime('%Y%m%d')

def ensure_directory(path):
    """確保目錄存在"""
    os.makedirs(path, exist_ok=True)

def chinese_number_to_digit(chinese_num):
    """中文數字轉阿拉伯數字"""
    chinese_digits = {
        '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
        '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
        '零': '0'
    }
    
    result = chinese_num
    for chinese, digit in chinese_digits.items():
        result = result.replace(chinese, digit)
    
    return result

def log_message(message, level="INFO"):
    """記錄日誌"""
    timestamp = get_taiwan_time().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")
