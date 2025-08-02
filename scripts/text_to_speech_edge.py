import os
import asyncio
import edge_tts
from utils import load_config, get_date_string, log_message

class DailyLightTTS:
    def __init__(self):
        self.config = load_config()
    
    async def generate_speech(self, text, output_path):
        """生成語音文件"""
        try:
            if not text.strip():
                log_message("文本為空，跳過語音生成")
                return False
            
            # 配置語音參數
            voice = self.config['tts']['voice']
            rate = self.config['tts']['rate']
            volume = self.config['tts']['volume']
            
            # 創建 TTS 通信實例
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
            
            # 生成音頻文件
            await communicate.save(output_path)
            
            log_message(f"語音文件已生成: {output_path}")
            return True
            
        except Exception as e:
            log_message(f"語音生成失敗: {str(e)}", "ERROR")
            return False
    
    def add_intro_outro(self, text, period):
        """添加開場和結尾"""
        intro_texts = {
            'morning': "親愛的朋友，早安！歡迎收聽《幫幫忙說每日亮光》。我是幫幫忙，讓我們一起來分享今天晨間的靈修內容。",
            'evening': "親愛的朋友，晚安！歡迎收聽《幫幫忙說每日亮光》。我是幫幫忙，讓我們一起來分享今天晚間的靈修內容。"
        }
        
        outro_text = "感謝您的收聽，願神祝福您的每一天。我們明天再見！"
        
        intro = intro_texts.get(period, intro_texts['morning'])
        
        # 組合完整文本
        if text.strip() == "今日無內容":
            full_text = f"{intro} 很抱歉，今天的內容暫時無法提供。{outro_text}"
        else:
            full_text = f"{intro} {text} {outro_text}"
        
        return full_text
    
    async def process_daily_audio(self, date_str=None):
        """處理每日音頻生成"""
        if date_str is None:
            date_str = get_date_string()
        
        input_dir = os.path.join('docs', 'podcast', date_str)
        
        if not os.path.exists(input_dir):
            log_message(f"文本目錄不存在: {input_dir}", "ERROR")
            return False
        
        success_count = 0
        
        for period in ['morning', 'evening']:
            text_file = os.path.join(input_dir, f'{period}.txt')
            audio_file = os.path.join(input_dir, f'{period}.mp3')
            
            if not os.path.exists(text_file):
                log_message(f"文本文件不存在: {text_file}", "WARNING")
                continue
            
            # 讀取文本
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                
                # 添加開場和結尾
                full_text = self.add_intro_outro(text, period)
                
                # 生成語音
                success = await self.generate_speech(full_text, audio_file)
                
                if success:
                    success_count += 1
                    log_message(f"{period} 音頻生成成功")
                else:
                    log_message(f"{period} 音頻生成失敗", "ERROR")
                    
            except Exception as e:
                log_message(f"處理 {period} 文件時出錯: {str(e)}", "ERROR")
        
        return success_count > 0

async def main():
    """主函數"""
    try:
        tts_processor = DailyLightTTS()
        date_str = get_date_string()
        
        log_message(f"開始生成 {date_str} 的語音文件")
        
        success = await tts_processor.process_daily_audio(date_str)
        
        if success:
            log_message("語音生成完成")
            exit(0)
        else:
            log_message("語音生成失敗", "ERROR")
            exit(1)
    
    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
