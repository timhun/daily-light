# scripts/upload_to_b2.py
import os
import json
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from utils import load_config, get_date_string, log_message

class B2Uploader:
    def __init__(self):
        self.config = load_config()
        # 優先使用環境變量，否則使用配置文件
        self.key_id = os.environ.get('B2_KEY_ID', self.config['b2'].get('account_id', ''))
        self.application_key = os.environ.get('B2_APPLICATION_KEY', self.config['b2'].get('application_key', ''))
        self.bucket_name = os.environ.get('B2_BUCKET_NAME', self.config['b2'].get('bucket_name', ''))
        self.bucket_url = os.environ.get('B2_BUCKET_URL', self.config['b2'].get('bucket_url', ''))
        self.folder_prefix = os.environ.get('B2_FOLDER_PREFIX', self.config['b2'].get('folder_prefix', ''))

        if not all([self.key_id, self.application_key, self.bucket_name, self.bucket_url]):
            log_message("缺少 B2 認證信息，檢查環境變量或 config/podcast_config.json", "ERROR")
            exit(1)

        # 初始化 B2 API
        info = InMemoryAccountInfo()
        self.b2_api = B2Api(info)
        try:
            self.b2_api.authorize_account("production", self.key_id, self.application_key)
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            log_message(f"B2 認證成功，桶: {self.bucket_name}")
        except Exception as e:
            log_message(f"B2 認證失敗: {str(e)}，請檢查 B2_KEY_ID 和 B2_APPLICATION_KEY", "ERROR")
            exit(1)

    def upload_file(self, local_path, remote_path):
        """上傳文件到 B2"""
        try:
            if not os.path.exists(local_path):
                log_message(f"本地文件不存在: {local_path}", "ERROR")
                return None
            
            # 上傳文件
            file_info = self.bucket.upload_local_file(
                local_file=local_path,
                file_name=remote_path,
                content_type='audio/mpeg'
            )
            
            # 生成公開下載 URL
            download_url = f"{self.bucket_url}/{remote_path}"
            log_message(f"文件已上傳: {download_url}")
            return download_url
            
        except Exception as e:
            log_message(f"上傳失敗 {local_path}: {str(e)}", "ERROR")
            return None
    
    def upload_daily_files(self, date_str=None):
        """上傳每日文件"""
        if date_str is None:
            date_str = get_date_string()
        
        # 確保日期格式為 YYYYMMDD
        if len(date_str) == 4:
            date_str = datetime.datetime.now().strftime('%Y') + date_str
        
        local_dir = os.path.join('docs', 'podcast', date_str)
        
        if not os.path.exists(local_dir):
            log_message(f"本地目錄不存在: {local_dir}", "ERROR")
            return {}
        
        uploaded_files = {}
        
        for period in ['morning', 'evening']:
            audio_file = os.path.join(local_dir, f'{period}.mp3')
            
            if os.path.exists(audio_file):
                remote_path = f"{self.folder_prefix}{date_str}/{period}.mp3" if self.folder_prefix else f"{date_str}/{period}.mp3"
                download_url = self.upload_file(audio_file, remote_path)
                
                if download_url:
                    uploaded_files[period] = {
                        'audio_url': download_url,
                        'local_path': audio_file
                    }
        
        # 保存上傳記錄
        if uploaded_files:
            upload_record_file = os.path.join(local_dir, 'upload_record.json')
            os.makedirs(os.path.dirname(upload_record_file), exist_ok=True)
            with open(upload_record_file, 'w', encoding='utf-8') as f:
                json.dump(uploaded_files, f, ensure_ascii=False, indent=2)
            
            log_message(f"上傳記錄已保存: {upload_record_file}")
        
        return uploaded_files

def main():
    """主函數"""
    try:
        uploader = B2Uploader()
        date_str = get_date_string()
        
        log_message(f"開始上傳 {date_str} 的文件")
        
        uploaded_files = uploader.upload_daily_files(date_str)
        
        if uploaded_files:
            log_message(f"成功上傳 {len(uploaded_files)} 個文件")
            
            # 輸出上傳結果供後續步驟使用
            for period, file_info in uploaded_files.items():
                print(f"{period}_url={file_info['audio_url']}")
            
            exit(0)
        else:
            log_message("沒有文件被上傳", "WARNING")
            exit(1)
    
    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    import datetime
    main()