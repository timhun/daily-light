# scripts/upload_to_b2.py
import os
import sys
from b2sdk.v2 import *

def upload_to_b2(bucket_name, file_path, file_name):
    """
    上傳檔案到 Backblaze B2。
    """
    key_id = os.environ.get('B2_KEY_ID')
    app_key = os.environ.get('B2_APP_KEY')

    if not all([key_id, app_key, bucket_name]):
        print("錯誤：B2_KEY_ID, B2_APP_KEY 或 B2_BUCKET_NAME 環境變數未設定。")
        sys.exit(1)
        
    if not os.path.exists(file_path):
        print(f"錯誤：檔案 {file_path} 不存在，跳過上傳。")
        return None

    print(f"正在授權 B2...")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", key_id, app_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)

    print(f"正在上傳 {file_path} 到 B2 Bucket '{bucket_name}' 並命名為 '{file_name}'...")
    uploaded_file = bucket.upload_local_file(
        local_file=file_path,
        file_name=file_name
    )

    download_url = b2_api.get_download_url_for_file_name(bucket_name, file_name)
    print(f"上傳成功！公開下載網址: {download_url}")
    return download_url


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python upload_to_b2.py <local_file_path> <remote_file_name>")
        sys.exit(1)

    local_path = sys.argv[1]
    remote_name = sys.argv[2]
    bucket = os.environ.get('B2_BUCKET_NAME')

    upload_to_b2(bucket, local_path, remote_name)
