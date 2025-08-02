# scripts/upload_to_b2.py
import os
import json
from b2sdk.v1 import InMemoryAccountInfo, B2Api, B2RawApi
from utils import load_config, get_date_string, log_message

class B2Uploader:
    def __init__(self):
        self.config = load_config()
        self.bucket_name = self.config['b2']['bucket_name']
        self.folder_prefix = self.config['b2']['folder_prefix']
        
        # 從環境變量獲取 B2 認證信息
        self.key_id = os.environ.get('B2_KEY_ID')
        self.application_key = os.environ.get('B2_APPLICATION_KEY')
        
        if not self.key_id or not self.application_key:
            raise ValueError("B2 認證信息未設置")
        
        # 初始化 B2 API
        info = InMemoryAccountInfo()
        self.b2_api = B2Api(info)
        self.b2_api.authorize_account("production", self.key_id, self.application_key)
        
        # 獲取存儲桶
        self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
    
    def upload_file(self, local_path, remote_path):
        """上傳文件到 B2"""
        try:
            if not os.path.exists(local_path):
                log_message(f"本地文件不存在: {local_path}", "ERROR")
                return None
            
            # 上傳文件
            file_info = self.bucket.upload_file(
                content_type='audio/mpeg',
                filename=remote_path,
                local_file=open(local_path, 'rb')
            )
            
            # 生成公開下載 URL
            download_url = f"https://f002.backblazeb2.com/file/{self.bucket_name}/{remote_path}"
            
            log_message(f"文件已上傳: {download_url}")
            return download_url
            
        except Exception as e:
            log_message(f"上傳失敗 {local_path}: {str(e)}", "ERROR")
            return None
    
    def upload_daily_files(self, date_str=None):
        """上傳每日文件"""
        if date_str is None:
            date_str = get_date_string()
        
        local_dir = os.path.join('docs', 'podcast', date_str)
        
        if not os.path.exists(local_dir):
            log_message(f"本地目錄不存在: {local_dir}", "ERROR")
            return {}
        
        uploaded_files = {}
        
        for period in ['morning', 'evening']:
            audio_file = os.path.join(local_dir, f'{period}.mp3')
            
            if os.path.exists(audio_file):
                remote_path = f"{self.folder_prefix}{date_str}/{period}.mp3"
                download_url = self.upload_file(audio_file, remote_path)
                
                if download_url:
                    uploaded_files[period] = {
                        'audio_url': download_url,
                        'local_path': audio_file
                    }
        
        # 保存上傳記錄
        if uploaded_files:
            upload_record_file = os.path.join(local_dir, 'upload_record.json')
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
    main()
