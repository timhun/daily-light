import os
import re
import sys
from datetime import datetime
from edge_tts import Communicate
from utils import load_config, get_date_string, ensure_directory, get_taiwan_time, log_message

class TextToSpeechEdge:
    def __init__(self):
        self.config = load_config()
        self.tts_config = self.config.get('tts', {})
        self.voice = os.environ.get('TTS_VOICE', self.tts_config.get('voice', 'zh-TW-HsiaoYuNeural'))
        self.rate = self.tts_config.get('rate', '+10%')
        self.volume = self.tts_config.get('volume', '+10%')
        self.podcast_dir = os.path.join('docs', 'podcast', get_date_string())
        ensure_directory(self.podcast_dir)

    def clean_text(self, text):
        """移除所有括弧內的文字，包括半形 ( ) 和全形（ ）"""
        cleaned_text = re.sub(r'\s*\(.*?\)|\s*（.*?）', '', text).strip()
        if not cleaned_text:
            log_message("清理後文本為空，寫入'今日無內容'", "WARNING")
            return "今日無內容"
        return cleaned_text

    async def generate_speech(self, text, output_path):
        """生成語音文件"""
        try:
            log_message(f"原始文本: {text[:50]}...")  # 記錄原始文本
            cleaned_text = self.clean_text(text)  # 清理文本
            log_message(f"清理後文本: {cleaned_text[:50]}...")  # 記錄清理後文本
            if not cleaned_text:
                log_message(f"清理後文本為空，跳過生成: {output_path}", "WARNING")
                return False
            communicate = Communicate(text=cleaned_text, voice=self.voice, rate=self.rate, volume=self.volume)
            await communicate.save(output_path)
            log_message(f"語音文件已生成: {output_path}")
            return True
        except Exception as e:
            log_message(f"語音生成失敗: {str(e)}", "ERROR")
            return False

    async def run(self):
        """主運行邏輯"""
        try:
            log_message("開始語音合成與後續處理...")
            morning_file = os.path.join(self.podcast_dir, 'morning.txt')
            evening_file = os.path.join(self.podcast_dir, 'evening.txt')

            if not os.path.exists(morning_file) or not os.path.exists(evening_file):
                log_message(f"缺少 morning.txt 或 evening.txt，跳過處理", "ERROR")
                return False

            with open(morning_file, 'r', encoding='utf-8') as f:
                morning_text = f.read().strip()
            with open(evening_file, 'r', encoding='utf-8') as f:
                evening_text = f.read().strip()

            # 生成語音文件
            morning_mp3 = os.path.join(self.podcast_dir, 'morning.mp3')
            evening_mp3 = os.path.join(self.podcast_dir, 'evening.mp3')

            success = await self.generate_speech(morning_text, morning_mp3)
            if success:
                log_message("morning 音頻生成成功")
            else:
                log_message("morning 音頻生成失敗，但繼續執行", "WARNING")

            success = await self.generate_speech(evening_text, evening_mp3)
            if success:
                log_message("evening 音頻生成成功")
            else:
                log_message("evening 音頻生成失敗，但繼續執行", "WARNING")

            return True

        except Exception as e:
            log_message(f"主程序執行失敗: {str(e)}", "ERROR")
            return False

async def main():
    """主函數"""
    try:
        tts = TextToSpeechEdge()
        success = await tts.run()

        if success:
            log_message("語音合成與後續處理完成")
            sys.exit(0)
        else:
            log_message("語音合成與後續處理失敗", "ERROR")
            sys.exit(1)

    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())