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
            local_audio_path = os.path.join('
