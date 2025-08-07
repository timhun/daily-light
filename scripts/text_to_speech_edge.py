# text_to_speech_edge.py
import os
import asyncio
import edge_tts
import re
from utils import load_config, get_date_string, log_message
from b2sdk.v1 import InMemoryAccountInfo, B2Api
from feedgen.feed import FeedGenerator
import mutagen  # 用於獲取音頻時長

class DailyLightTTS:
    def __init__(self):
        self.config = load_config()
        # 初始化 Backblaze B2
        info = InMemoryAccountInfo()
        self.b2_api = B2Api(info)
        self.b2_api.authorize_account(
            "production",
            self.config['b2']['account_id'],
            self.config['b2']['application_key']
        )
        self.bucket = self.b2_api.get_bucket_by_name(self.config['b2']['bucket_name'])
        self.bucket_url = self.config['b2']['bucket_url']

    async def generate_speech(self, text, output_path):
        """生成語音文件"""
        try:
            if not text.strip():
                log_message("文本為空，跳過語音生成")
                return False
            
            voice = self.config['tts']['voice']
            rate = self.config['tts']['rate']
            volume = self.config['tts']['volume']
            
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
            await communicate.save(output_path)
            
            log_message(f"語音文件已生成: {output_path}")
            return True
            
        except Exception as e:
            log_message(f"語音生成失敗: {str(e)}", "ERROR")
            return False
    
    def add_intro_outro(self, text, period):
        """添加開場和結尾，移除括號內文字"""
        intro_texts = {
            'morning': "早安！讓我們一起來分享今天晨間的靈修內容。",
            'evening': "晚安！讓我們一起來分享今天晚間的靈修內容。"
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
            
            remote_path = f"{date_str}/{period}.mp3"
            self.bucket.upload_local_file(
                content_type='audio/mpeg',
                file_name=remote_path,
                file=open(file_path, 'rb')
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
            fg.title(self.config['rss']['title'])
            fg.author({'name': self.config['rss']['author'], 'email': self.config['rss']['email']})
            fg.link(href='https://timhun.github.io/daily-light/', rel='alternate')
            fg.description(self.config['rss']['description'])
            fg.language('zh-TW')

            # 晨間內容
            if morning_url:
                fe = fg.add_entry()
                fe.id(morning_url)
                fe.title(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} 晨")
                fe.link(href=morning_url)
                audio = mutagen.File(f"docs/podcast/{date_str}/morning.mp3")
                duration = int(audio.info.length) if audio else 300
                fe.enclosure(url=morning_url, length=os.path.getsize(f"docs/podcast/{date_str}/morning.mp3"), type="audio/mpeg")
                fe.pubDate(datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800"))
                fe.podcast.itunes_duration(duration)

            # 晚間內容
            if evening_url:
                fe = fg.add_entry()
                fe.id(evening_url)
                fe.title(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} 晚")
                fe.link(href=evening_url)
                audio = mutagen.File(f"docs/podcast/{date_str}/evening.mp3")
                duration = int(audio.info.length) if audio else 300
                fe.enclosure(url=evening_url, length=os.path.getsize(f"docs/podcast/{date_str}/evening.mp3"), type="audio/mpeg")
                fe.pubDate(datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800"))
                fe.podcast.itunes_duration(duration)

            rss_output = os.path.join('docs', 'rss', 'podcast.xml')
            os.makedirs(os.path.dirname(rss_output), exist_ok=True)
            fg.rss_file(rss_output)
            log_message(f"RSS feed 已生成: {rss_output}")
        except Exception as e:
            log_message(f"生成 RSS feed 失敗: {str(e)}", "ERROR")

    async def process_daily_audio(self, date_str=None):
        """處理每日音頻生成並上傳"""
        if date_str is None:
            date_str = get_date_string()
        
        input_dir = os.path.join('docs', 'podcast', date_str)
        
        if not os.path.exists(input_dir):
            log_message(f"文本目錄不存在: {input_dir}", "ERROR")
            return False
        
        success_count = 0
        morning_url = None
        evening_url = None
        
        for period in ['morning', 'evening']:
            text_file = os.path.join(input_dir, f'{period}.txt')
            audio_file = os.path.join(input_dir, f'{period}.mp3')
            
            if not os.path.exists(text_file):
                log_message(f"文本文件不存在: {text_file}", "WARNING")
                continue
            
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                
                full_text = self.add_intro_outro(text, period)
                success = await self.generate_speech(full_text, audio_file)
                
                if success:
                    success_count += 1
                    log_message(f"{period} 音頻生成成功")
                    url = await self.upload_to_b2(audio_file, date_str, period)
                    if url:
                        if period == 'morning':
                            morning_url = url
                        else:
                            evening_url = url
                else:
                    log_message(f"{period} 音頻生成失敗", "ERROR")
                    
            except Exception as e:
                log_message(f"處理 {period} 文件時出錯: {str(e)}", "ERROR")
        
        # 生成 RSS feed
        if success_count > 0:
            self.generate_rss(date_str, morning_url, evening_url)
        
        return success_count > 0

async def main():
    """主函數"""
    try:
        tts_processor = DailyLightTTS()
        date_str = get_date_string()
        
        log_message(f"開始生成 {date_str} 的語音文件")
        
        success = await tts_processor.process_daily_audio(date_str)
        
        if success:
            log_message("語音生成與後續處理完成")
            exit(0)
        else:
            log_message("語音生成或後續處理失敗", "ERROR")
            exit(1)
    
    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
