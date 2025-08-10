# scripts/synthesize_audio.py
import os
import edge_tts
import asyncio
import platform
from datetime import datetime
import logging
import sys

logging.basicConfig(level=os.getenv("PYTHON_LOG_LEVEL", "INFO"), format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.getenv("BASE_DIR", "docs")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
VOICE = os.getenv("TTS_VOICE", "zh-TW-YunJheNeural")

async def synthesize_text(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        text = "今日無內容，請明日再收聽。"
    communicate = edge_tts.Communicate(text, VOICE)
    logger.info(f"合成語音：{output_path}")
    await communicate.save(output_path)

def main():
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    audio_dir = os.path.join(AUDIO_DIR, today)
    os.makedirs(audio_dir, exist_ok=True)

    for time_of_day in ["morning", "evening"]:
        input_path = os.path.join(BASE_DIR, "podcast", today, f"{time_of_day}.txt")
        output_path = os.path.join(audio_dir, f"{time_of_day}.mp3")
        if os.path.exists(input_path):
            asyncio.run(synthesize_text(input_path, output_path))
        else:
            logger.warning(f"找不到 {time_of_day} 逐字稿，跳過語音合成")

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
