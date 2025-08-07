# text_to_speech_edge.py
import os
import asyncio
import edge_tts
import re
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
        """添加開場和結尾，移除括號內文字"""
        intro_texts = {
            'morning': "親愛的朋友，早安！歡迎收聽《幫幫忙說每日亮光》。我是幫幫忙，讓我們一起來分享今天晨間的靈修內容。",
            'evening': "親愛的朋友，晚安！歡迎收聽《幫幫忙說每日亮光》。我是幫幫忙，讓我們一起來分享今天晚間的靈修內容。"
        }
        
        outro_text = "感謝您的收聽，願神祝福您的每一天。我們明天再見！"
        
        intro = intro_texts.get(period, intro_texts['morning'])
        
        # 移除括號內的文字（例如 (約十四26)）
        text_without_brackets = re.sub(r'\s*\([^()]*\)', '', text)
        
        # 組合完整文本
        if text.strip() == "今日無內容
