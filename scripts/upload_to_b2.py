# scripts/upload_to_b2.py
import os
import sys
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from datetime import datetime
from utils import load_config, get_date_string, ensure_directory, get_taiwan_time, log_message

class B2Uploader:
    def __init__(self):
        self.config = load_config()
        self.key_id = os.environ.get('B2_KEY_ID', self.config['b2'].get('account_id', ''))
        self.application_key = os.environ.get('B2_APPLICATION_KEY', self.config['b2'].get('application_key', ''))
        self.bucket_name = os.environ.get('B2_BUCKET_NAME', self.config['b2'].get('bucket_name', ''))
        self.bucket_url = os.environ.get('B2_BUCKET_URL', self.config['b2'].get('bucket_url', ''))
        self.folder_prefix = os.environ.get('B2_FOLDER_PREFIX', self.config['b2'].get('folder_prefix', ''))

        if not all([self.key_id, self.application_key, self.bucket_name, self.bucket_url]):
            log_message("缺少 B2 認證信息，檢查環境變量或 config/podcast_config.json", "ERROR")
            sys.exit(1)

        self.info = InMemoryAccountInfo()
        self.b2_api = B2Api(self.info)
        try:
            self.b2_api.authorize_account("production", self.key_id, self.application_key)
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            log_message(f"B2 認證成功，桶: {self.bucket_name}")
        except Exception as e:
            log_message(f"B2 認證失敗: {str(e)}，請檢查 B2_KEY_ID 和 B2_APPLICATION_KEY", "ERROR")
            sys.exit(1)

        self.podcast_dir = os.path.join('docs', 'podcast', get_date_string())
        if not os.path.exists(self.podcast_dir):
            log_message(f"目錄 {self.podcast_dir} 不存在，跳過上傳", "WARNING")
            sys.exit(0)

    def upload_file(self, file_path, file_name):
        """上傳單個文件到 B2"""
        try:
            full_path = os.path.join(self.podcast_dir, file_path)
            if not os.path.exists(full_path):
                log_message(f"文件 {full_path} 不存在，跳過上傳", "WARNING")
                return False

            remote_path = os.path.join(self.folder_prefix, get_date_string(), file_name).replace('\\', '/')
            self.bucket.upload_local_file(
                local_file=full_path,
                file_name=remote_path,
                file_infos={'source': 'podcast_generator'}
            )
            log_message(f"文件已上傳: {remote_path}")
            return True
        except Exception as e:
            log_message(f"文件 {file_path} 上傳失敗: {str(e)}", "ERROR")
            return False

    def run(self):
        """主運行邏輯"""
        try:
            log_message("開始上傳到 B2...")
            files_to_upload = [
                ('morning.mp3', 'morning.mp3'),
                ('evening.mp3', 'evening.mp3'),
                ('morning.txt', 'morning.txt'),
                ('evening.txt', 'evening.txt')
            ]

            success = False
            for file_path, file_name in files_to_upload:
                if self.upload_file(file_path, file_name):
                    success = True

            if success:
                log_message("B2 上傳至少一個文件成功")
            else:
                log_message("B2 上傳所有文件失敗", "WARNING")

            return success

        except Exception as e:
            log_message(f"主程序執行失敗: {str(e)}", "ERROR")
            return False

def main():
    """主函數"""
    try:
        uploader = B2Uploader()
        success = uploader.run()

        if success:
            log_message("上傳到 B2 完成")
            sys.exit(0)
        else:
            log_message("上傳失敗，但繼續執行", "WARNING")
            sys.exit(1)

    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()