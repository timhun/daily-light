# text_to_speech_edge.py
import os
import re
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

    async def generate_speech(self, text, output_path):
        """生成語音文件"""
        try:
            log_message(f"開始為文本生成語音: {output_path}")
            communicate = Communicate(text=text, voice=self.voice, rate=self.rate, volume=self.volume)
            await communicate.save(output_path)
            log_message(f"語音文件已生成: {output_path}")
            return True
        except Exception as e:
            log_message(f"語音生成失敗: {str(e)}", "ERROR")
            return False

    def process_text(self, input_path):
        """處理文字稿並分割為晨間和晚間內容"""
        try:
            if not os.path.exists(input_path):
                log_message(f"文字稿 {input_path} 不存在", "ERROR")
                return None, None

            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                log_message("文字稿內容為空，寫入'今日無內容'", "WARNING")
                return "今日無內容", "今日無內容"

            # 偵測 '晨' 和 '晚' 關鍵字並分割
            morning_match = re.search(r'八月十日\s*晨(?:.*?(?=八月十日\s*晚|$))', content, re.DOTALL)
            evening_match = re.search(r'八月十日\s*晚(?:.*$)', content, re.DOTALL)

            morning_text = morning_match.group(0).replace('八月十日 晨', '').strip() if morning_match else None
            evening_text = evening_match.group(0).replace('八月十日 晚', '').strip() if evening_match else None

            if not morning_text and not evening_text:
                log_message("未偵測到'晨'或'晚'的關鍵字", "ERROR")
                return "今日無內容", "今日無內容"

            if morning_text:
                log_message(f"晨間內容: {morning_text[:50]}...")
            else:
                log_message("未找到晨間內容，寫入'今日無內容'", "WARNING")
                morning_text = "今日無內容"

            if evening_text:
                log_message(f"晚間內容: {evening_text[:50]}...")
            else:
                log_message("未找到晚間內容，寫入'今日無內容'", "WARNING")
                evening_text = "今日無內容"

            # 將文本保存為獨立文件
            morning_file = os.path.join(self.podcast_dir, 'morning.txt')
            evening_file = os.path.join(self.podcast_dir, 'evening.txt')
            with open(morning_file, 'w', encoding='utf-8') as f:
                f.write(morning_text)
            with open(evening_file, 'w', encoding='utf-8') as f:
                f.write(evening_text)

            return morning_text, evening_text

        except Exception as e:
            log_message(f"處理文字稿失敗: {str(e)}", "ERROR")
            return None, None

    async def run(self, input_path):
        """主運行邏輯"""
        try:
            log_message("開始語音合成與後續處理...")
            morning_text, evening_text = self.process_text(input_path)

            if morning_text is None or evening_text is None:
                log_message("文字處理失敗，跳過語音生成", "ERROR")
                return False

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
        input_path = os.path.join('docs', 'img', f'{get_date_string()}.txt')
        success = await tts.run(input_path)

        if success:
            log_message("語音合成與後續處理完成")
            exit(0)
        else:
            log_message("語音合成與後續處理失敗", "ERROR")
            exit(1)

    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
