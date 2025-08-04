import os
import re
import json
from datetime import datetime
import pytz

def load_config():
config_path = os.path.join(os.path.dirname(os.path.dirname(**file**)), ‘config’, ‘podcast_config.json’)
with open(config_path, ‘r’, encoding=‘utf-8’) as f:
return json.load(f)

def get_taiwan_time():
tz = pytz.timezone(‘Asia/Taipei’)
return datetime.now(tz)

def get_date_string(date_obj=None):
if not date_obj:
date_obj = get_taiwan_time()
return date_obj.strftime(’%Y%m%d’)

def ensure_directory(path):
os.makedirs(path, exist_ok=True)

# OCR腳本兼容性函數（別名）

def ensure_dir(path):
“”“ensure_directory 的別名，用於OCR腳本兼容性”””
return ensure_directory(path)

def extract_date_from_filename(filename):
“”“從文件名提取日期”””
# 移除文件擴展名
name_without_ext = os.path.splitext(filename)[0]

```
# 匹配多種日期格式
patterns = [
    r'(\d{4}-\d{2}-\d{2})',     # YYYY-MM-DD
    r'(\d{4}_\d{2}_\d{2})',     # YYYY_MM_DD
    r'(\d{4}\d{2}\d{2})',       # YYYYMMDD
    r'(\d{2}-\d{2}-\d{4})',     # DD-MM-YYYY
    r'(\d{2}_\d{2}_\d{4})',     # DD_MM_YYYY
    r'(\d{2}\d{2}\d{4})',       # DDMMYYYY
]

for pattern in patterns:
    match = re.search(pattern, name_without_ext)
    if match:
        date_str = match.group(1)
        
        # 統一轉換為 YYYY-MM-DD 格式
        if len(date_str) == 8 and '-' not in date_str and '_' not in date_str:
            # YYYYMMDD 或 DDMMYYYY 格式
            if date_str[:4].startswith('20') or date_str[:4].startswith('19'):
                # YYYYMMDD
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                # DDMMYYYY
                date_str = f"{date_str[4:8]}-{date_str[2:4]}-{date_str[:2]}"
        elif '_' in date_str:
            date_str = date_str.replace('_', '-')
        elif len(date_str) == 10 and date_str[2] == '-':
            # DD-MM-YYYY 轉換為 YYYY-MM-DD
            parts = date_str.split('-')
            if len(parts) == 3:
                date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
        
        # 驗證日期格式
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            continue

# 如果沒有找到標準日期格式，嘗試從中文日期提取
chinese_date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
match = re.search(chinese_date_pattern, name_without_ext)
if match:
    year, month, day = match.groups()
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

# 嘗試匹配月日格式（假設是當前年份）
month_day_pattern = r'(\d{1,2})月(\d{1,2})日'
match = re.search(month_day_pattern, name_without_ext)
if match:
    current_year = get_taiwan_time().year
    month, day = match.groups()
    return f"{current_year}-{month.zfill(2)}-{day.zfill(2)}"

return None
```

def chinese_number_to_digit(chinese_num):
digits = {‘一’: ‘1’, ‘二’: ‘2’, ‘三’: ‘3’, ‘四’: ‘4’, ‘五’: ‘5’,
‘六’: ‘6’, ‘七’: ‘7’, ‘八’: ‘8’, ‘九’: ‘9’, ‘十’: ‘10’,
‘零’: ‘0’}
result = chinese_num
for zh, num in digits.items():
result = result.replace(zh, num)
return result

def log_message(message, level=“INFO”):
timestamp = get_taiwan_time().strftime(’%Y-%m-%d %H:%M:%S’)
print(f”[{timestamp}] {level}: {message}”)

def format_date_for_output(date_str):
“”“將日期字符串格式化為輸出目錄名稱”””
try:
# 嘗試解析日期
date_obj = datetime.strptime(date_str, ‘%Y-%m-%d’)
# 返回 YYYY-MM-DD 格式
return date_obj.strftime(’%Y-%m-%d’)
except ValueError:
# 如果解析失敗，返回原字符串
return date_str

def validate_date_string(date_str):
“”“驗證日期字符串是否有效”””
try:
datetime.strptime(date_str, ‘%Y-%m-%d’)
return True
except ValueError:
return False

def get_file_info(filepath):
“”“獲取文件信息”””
if not os.path.exists(filepath):
return None

```
stat = os.stat(filepath)
return {
    'size': stat.st_size,
    'modified': datetime.fromtimestamp(stat.st_mtime),
    'created': datetime.fromtimestamp(stat.st_ctime)
}
```