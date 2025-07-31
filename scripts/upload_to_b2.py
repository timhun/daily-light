# scripts/upload_to_b2.py
import os
import sys
import boto3
from datetime import datetime

BUCKET_NAME = "daily-light"
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
B2_URL = "https://f005.backblazeb2.com/file"

def upload_to_b2(local_path, b2_path):
    session = boto3.session.Session()
    b2 = session.client(
        service_name="s3",
        endpoint_url="https://s3.us-west-004.backblazeb2.com",
        aws_access_key_id=B2_KEY_ID,
        aws_secret_access_key=B2_APPLICATION_KEY,
    )

    print(f"🚀 上傳至 B2：{b2_path}")
    b2.upload_file(local_path, BUCKET_NAME, b2_path)
    url = f"{B2_URL}/{BUCKET_NAME}/{b2_path}"
    print(f"✅ 上傳完成：{url}")
    return url

def main():
    today = datetime.now().strftime("%Y%m%d")
    local_audio_path = f"docs/podcast/{today}/audio.mp3"
    if not os.path.exists(local_audio_path):
        print(f"❌ 找不到音檔：{local_audio_path}")
        sys.exit(1)

    b2_filename = f"{today}.mp3"
    url = upload_to_b2(local_audio_path, b2_filename)

    archive_path = f"docs/podcast/{today}/archive_audio_url.txt"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(url)
    print(f"✅ 已儲存音檔連結：{archive_path}")

if __name__ == "__main__":
    main()
