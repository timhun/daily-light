import os
import sys
import asyncio
from datetime import datetime
import pytz
import edge_tts

async def text_to_speech(text_path, output_path, voice):
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print(f"⚠️ 檔案為空：{text_path}，跳過語音合成")
        return

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    print(f"✅ 已儲存音檔至：{output_path}")

def main():
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    base_dir = f"docs/podcast/{today}"
    text_path = os.path.join(base_dir, "script.txt")
    output_path = os.path.join(base_dir, "audio.mp3")
    voice = os.getenv("VOICE_NAME", "zh-TW-YunJheNeural")

    if not os.path.exists(text_path):
        print(f"❌ 找不到逐字稿：{text_path}")
        sys.exit(0)

    asyncio.run(text_to_speech(text_path, output_path, voice))

if __name__ == "__main__":
    main()
