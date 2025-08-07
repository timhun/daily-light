# scripts/text_to_speech_edge.py
import os
import asyncio
import edge_tts
import re
from utils import load_config, get_date_string, log_message
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from feedgen.feed import FeedGenerator
import mutagen
import datetime

class DailyLightTTS:
    def __init__(self):
        self.config = load_config()
        self.tz = datetime.timezone(datetime.timedelta(hours=8))
        info = InMemoryAccountInfo()
        self.b2_api = B2Api(info)
        # 優先使用環境變量，否則使用配置文件
        key_id = os.environ.get('B2_KEY_ID', self.config['b2'].get('account_id'))
        app_key = os.environ.get('B2_APPLICATION_KEY', self.config['b2'].get('application_key'))
        bucket_name = os.environ.get('B2_BUCKET_NAME', self.config['b2'].get('bucket_name'))
        bucket_url = os.environ.get('B2_BUCKET_URL', self.config['b2'].get('bucket_url'))

        if not all([key_id, app_key, bucket_name, bucket_url]):
            log_message("缺少 B2 認證信息，檢查環境變量或 config/podcast_config.json", "ERROR")
            exit(1)

        try:
            self.b2_api.authorize_account("production", key_id, app_key)
            self.bucket = self.b2_api.get_bucket_by_name(bucket_name)
            self.bucket_url = bucket_url
            log_message(f"B2 認證成功，桶: {bucket_name}")
        except Exception as e:
            log_message(f"B2 認證失敗: {str(e)}，請檢查 B2_KEY_ID 和 B2_APPLICATION_KEY", "ERROR")
            exit(1)

        self.tts_config = {
            'voice': os.environ.get('TTS_VOICE', self.config['tts'].get('voice', 'zh-CN-Xiaoxiao')),
            'rate': os.environ.get('TTS_RATE', self.config['tts'].get('rate', '+0%')),
            'volume': os.environ.get('TTS_VOLUME', self.config['tts'].get('volume', '+0%'))
        }
        self.rss_config = {
            'title': os.environ.get('RSS_TITLE', self.config['rss'].get('title', '幫幫忙說每日亮光')),
            'author': os.environ.get('RSS_AUTHOR', self.config['rss'].get('author', '幫幫忙')),
            'email': os.environ.get('RSS_EMAIL', self.config['rss'].get('email', 'contact@example.com')),
            'description': os.environ.get('RSS_DESCRIPTION', self.config['rss'].get('description', '每日靈修內容，晨間與晚間分享'))
        }

    async def generate_speech(self, text, output_path):
        """生成語音文件"""
        try:
            if not text.strip():
                log_message("文本為空，跳過語音生成")
                return False
            
            communicate = edge_tts.Communicate(
                text, self.tts_config['voice'], rate=self.tts_config['rate'], volume=self.tts_config['volume']
            )
            await communicate.save(output_path)
            log_message(f"語音文件已生成: {output_path}")
            return True
        except Exception as e:
            log_message(f"語音生成失敗: {str(e)}", "ERROR")
            return False

    def add_intro_outro(self, text, period):
        """添加開場和結尾，移除括號內文字"""
        intro_texts = {
            'morning': "親愛的朋友，早安！歡迎收聽《幫幫忙說每日亮光》。我是幫幫忙，讓我們一起來分享今天晨間的靈修內容。",
            'evening': "親愛的朋友，晚安！歡迎收聽《幫幫忙說每日亮光》。我是幫幫忙，讓我們一起來分享今天晚間的靈修內容。"
        }
        outro_text = "感謝您的收聽，願神祝福您的每一天。我們明天再見！"
        intro = intro_texts.get(period, intro_texts['morning'])
        text_without_brackets = re.sub(r'\s*\([^()]*\)', '', text)
        if text.strip() == "今日無內容":
            full_text = f"{intro} 很抱歉，今天的內容暫時無法提供。{outro_text}"
        else:
            full_text = f"{intro} {text_without_brackets} {outro_text}"
        return full_text

    async def upload_to_b2(self, file_path, date_str, period):
        """上傳 MP3 到 Backblaze B2"""
        try:
            if not os.path.exists(file_path):
                log_message(f"本地文件不存在: {file_path}", "ERROR")
                return None
            identifier = f"daily-light-{date_str}-{period}"
            remote_path = f"{identifier}.mp3"
            self.bucket.upload_local_file(
                local_file=file_path,
                file_name=remote_path,
                content_type="audio/mpeg"
            )
            download_url = f"{self.bucket_url}/{remote_path}"
            log_message(f"文件已上傳: {download_url}")
            return download_url
        except Exception as e:
            log_message(f"上傳 {period}.mp3 到 Backblaze B2 失敗: {str(e)}", "ERROR")
            return None

    def generate_rss(self, date_str, morning_url, evening_url):
        """生成或更新 RSS feed"""
        try:
            fg = FeedGenerator()
            fg.id('https://timhun.github.io/daily-light/')
            fg.title(self.rss_config['title'])
            fg.author({'name': self.rss_config['author'], 'email': self.rss_config['email']})
            fg.link(href='https://timhun.github.io/daily-light/', rel='alternate')
            fg.description(self.rss_config['description'])
            fg.language('zh-TW')

            if morning_url:
                fe = fg.add_entry()
                fe.id(morning_url)
                fe.title(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} 晨")
                fe.link(href=morning_url)
                audio = mutagen.File(f"docs/podcast/{date_str}/morning.mp3")
                duration = int(audio.info.length) if audio else 300
                fe.enclosure(url=morning_url, length=os.path.getsize(f"docs/podcast/{date_str}/morning.mp3"), type="audio/mpeg")
                fe.pubDate(datetime.datetime.now(self.tz).strftime("%a, %d %b %Y %H:%M:%S +0800"))
                fe.podcast.itunes_duration(duration)

            if evening_url:
                fe = fg.add_entry()
                fe.id(evening_url)
                fe.title(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} 晚")
                fe.link(href=evening_url)
                audio = mutagen.File(f"docs/podcast/{date_str}/evening.mp3")
                duration = int(audio.info.length) if audio else 300
                fe.enclosure(url=evening_url, length=os.path.getsize(f"docs/podcast/{date_str}/evening.mp3"), type="audio/mpeg")
                fe.pubDate(datetime.datetime.now(self.tz).strftime("%a, %d %b %Y %H:%M:%S +0800"))
                fe.podcast.itunes_duration(duration)

            rss_output = os.path.join('docs', 'rss', 'podcast.xml')
            os.makedirs(os.path.dirname(rss_output), exist_ok=True)
            fg.rss_file(rss_output)
            log_message(f"RSS feed 已生成: {rss_output}")
        except Exception as e:
            log_message(f"生成 RSS feed 失敗: {str(e)}", "ERROR")

    async def process_daily_audio(self, date_str=None):
        """處理每日音頻