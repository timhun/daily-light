# scripts/generate_rss.py
import os
import json
from datetime import datetime, timedelta
from feedgen.feed import FeedGenerator
from utils import load_config, get_date_string, ensure_directory, get_taiwan_time, log_message

class RSSGenerator:
    def __init__(self):
        self.config = load_config()
        self.podcast_config = self.config['podcast']
    
    def create_feed_generator(self):
        """創建 RSS Feed 生成器"""
        fg = FeedGenerator()
        
        # 基本信息
        fg.id('https://timhun.github.io/daily-light/')
        fg.title(self.podcast_config['title'])
        fg.subtitle(self.podcast_config['subtitle'])
        fg.author({'name': self.podcast_config['author'], 'email': self.podcast_config['email']})
        fg.description(self.podcast_config['description'])
        fg.language(self.podcast_config['language'])
        fg.link(href='https://timhun.github.io/daily-light/', rel='alternate')
        fg.link(href='https://timhun.github.io/daily-light/rss/podcast.xml', rel='self')
        fg.image(self.podcast_config['image_url'])
        
        # Podcast 特定設置
        fg.podcast.itunes_category(self.podcast_config['category'])
        fg.podcast.itunes_explicit(self.podcast_config['explicit'])
        fg.podcast.itunes_author(self.podcast_config['author'])
        fg.podcast.itunes_owner(self.podcast_config['author'], self.podcast_config['email'])
        fg.podcast.itunes_summary(self.podcast_config['description'])
        fg.podcast.itunes_image(self.podcast_config['image_url'])
        
        return fg
    
    def get_file_size(self, file_path):
        """獲取文件大小"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
        except:
            pass
        return 0
    
    def get_audio_duration(self, file_path):
        """獲取音頻時長（簡化版本）"""
        # 這裡簡化處理，實際應用中可以使用 mutagen 等庫
        # 根據文件大小估算時長（假設 1MB ≈ 1分鐘）
        try:
            file_size_mb = self.get_file_size(file_path) / (1024 * 1024)
            duration_seconds = int(file_size_mb * 60)  # 簡化估算
            return duration_seconds
        except:
            return 300  # 默認5分鐘
    
    def add_episode(self, fg, date_str, period, audio_url, text_content):
        """添加節目集數"""
        try:
            # 讀取文本內容
            episode_text = text_content.strip()
            if not episode_text or episode_text == "今日無內容":
                episode_text = f"今日{period}時段暫無內容"
            
            # 創建集數
            fe = fg.add_entry()
            
            # 基本信息
            episode_title = f"{self.podcast_config['title']} - {date_str[:4]}年{date_str[4:6]}月{date_str[6:8]}日{'晨間' if period == 'morning' else '晚間'}"
            episode_id = f"daily-light-{date_str}-{period}"
            
            fe.id(f"https://timhun.github.io/daily-light/podcast/{date_str}/{period}")
            fe.title(episode_title)
            fe.description(f"今日{'晨間' if period == 'morning' else '晚間'}靈修分享\n\n{episode_text[:200]}...")
            fe.author({'name': self.podcast_config['author'], 'email': self.podcast_config['email']})
            
            # 時間設置
            pub_date = datetime.strptime(date_str, '%Y%m%d')
            if period == 'morning':
                pub_date = pub_date.replace(hour=6, minute=0)
            else:
                pub_date = pub_date.replace(hour=18, minute=0)
            
            fe.pubDate(pub_date)
            
            # 音頻信息
            local_audio_path = os.path.join('docs', 'podcast', date_str, f'{period}.mp3')
            file_size = self.get_file_size(local_audio_path)
            duration = self.get_audio_duration(local_audio_path)
            
            fe.enclosure(audio_url, str(file_size), 'audio/mpeg')
            fe.podcast.itunes_duration(duration)
            fe.podcast.itunes_explicit(False)
            fe.podcast.itunes_subtitle(f"{'晨間' if period == 'morning' else '晚間'}靈修分享")
            fe.podcast.itunes_summary(episode_text[:500])
            
            log_message(f"已添加集數: {episode_title}")
            
        except Exception as e:
            log_message(f"添加集數失敗: {str(e)}", "ERROR")
    
    def generate_rss(self, days_back=30):
        """生成 RSS Feed"""
        try:
            fg = self.create_feed_generator()
            current_date = get_taiwan_time()
            
            # 處理最近 days_back 天的內容
            for i in range(days_back):
                check_date = current_date - timedelta(days=i)
                date_str = check_date.strftime('%Y%m%d')
                
                podcast_dir = os.path.join('docs', 'podcast', date_str)
                
                if not os.path.exists(podcast_dir):
                    continue
                
                # 檢查上傳記錄
                upload_record_file = os.path.join(podcast_dir, 'upload_record.json')
                if not os.path.exists(upload_record_file):
                    continue
                
                try:
                    with open(upload_record_file, 'r', encoding='utf-8') as f:
                        upload_records = json.load(f)
                    
                    # 添加每個時段的集數
                    for period in ['morning', 'evening']:
                        if period in upload_records:
                            audio_url = upload_records[period]['audio_url']
                            
                            # 讀取文本內容
                            text_file = os.path.join(podcast_dir, f'{period}.txt')
                            text_content = ""
                            if os.path.exists(text_file):
                                with open(text_file, 'r', encoding='utf-8') as f:
                                    text_content = f.read()
                            
                            self.add_episode(fg, date_str, period, audio_url, text_content)
                
                except Exception as e:
                    log_message(f"處理 {date_str} 數據時出錯: {str(e)}", "WARNING")
                    continue
            
            # 生成 RSS 文件
            rss_dir = os.path.join('docs', 'rss')
            ensure_directory(rss_dir)
            
            rss_file = os.path.join(rss_dir, 'podcast.xml')
            fg.rss_file(rss_file)
            
            log_message(f"RSS Feed 已生成: {rss_file}")
            return True
            
        except Exception as e:
            log_message(f"RSS 生成失敗: {str(e)}", "ERROR")
            return False

def main():
    """主函數"""
    try:
        rss_generator = RSSGenerator()
        
        log_message("開始生成 RSS Feed")
        
        success = rss_generator.generate_rss()
        
        if success:
            log_message("RSS Feed 生成完成")
            exit(0)
        else:
            log_message("RSS Feed 生成失敗", "ERROR")
            exit(1)
    
    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    main()
