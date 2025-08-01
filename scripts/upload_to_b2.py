# scripts/upload_to_b2.py
import os
import sys
import boto3
from datetime import datetime
import pytz
import logging
import shutil
from botocore.exceptions import ClientError

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 環境變數與路徑
BASE_DIR = os.getenv("BASE_DIR", "docs")
PODCAST_DIR = os.path.join(BASE_DIR, "podcast")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
BUCKET_NAME = os.getenv("B2_BUCKET_NAME", "daily-light")
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
B2_URL = os.getenv("B2_URL", "https://f005.backblazeb2.com")
B2_ENDPOINT_URL = os.getenv("B2_ENDPOINT_URL", "https://s3.us-west-004.backblazeb2.com")

def upload_to_b2(local_path, b2_path):
    """上傳檔案至 Backblaze B2"""
    if not B2_KEY_ID or not B2_APPLICATION_KEY:
        logger.error("B2_KEY_ID 或 B2_APPLICATION_KEY 未設置")
        sys.exit(1)
    try:
        session = boto3.session.Session()
        b2 = session.client(
            service_name="s3",
            endpoint_url=B2_ENDPOINT_URL,
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APPLICATION_KEY,
        )
        logger.info(f"上傳至 B2：{b2_path}")
        b2.upload_file(local_path, BUCKET_NAME, b2_path)
        url = f"{B2_URL}/file/{BUCKET_NAME}/{b2_path}"
        b2.head_object(Bucket=BUCKET_NAME, Key=b2_path)
        logger.info(f"上傳完成：{url}")
        return url
    except ClientError as e:
        logger.error(f"B2 上傳失敗：{e}")
        return None
    except Exception as e:
        logger.error(f"上傳錯誤：{e}")
        return None

def main():
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    local_audio_path = os.path.join(AUDIO_DIR, f"{today}.mp3")
    archive_path = os.path.join(PODCAST_DIR, today, "archive_audio_url.txt")

    if not os.path.exists(local_audio_path):
        logger.error(f"找不到音檔：{local_audio_path}")
        sys.exit(1)

    b2_filename = f"audio/{today}.mp3"
    url = upload_to_b2(local_audio_path, b2_filename)
    if not url:
        logger.error("上傳失敗，退出")
        sys.exit(1)

    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    if os.path.exists(archive_path):
        shutil.copy(archive_path, f"{archive_path}.bak")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(url)
    logger.info(f"已儲存音檔連結：{archive_path}")

if __name__ == "__main__":
    main()
