# scripts/synthesize_audio.py
import os
from datetime import datetime
import subprocess

VOICE = "zh-TW-YunJheNeural"
RATE = "+15%"  # 較自然的語速

def synthesize(text_path, output_path):
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read()

    if not text.strip():
        print("❌ 文字稿為空，跳過合成")
        return

    command = [
        "edge-tts",
        "--voice", VOICE,
        "--rate", RATE,
        "--text", text,
        "--write-media", output_path
    ]
    print(f"🎙️ 開始語音合成：{output_path}")
    subprocess.run(command, check=True)
    print(f"✅ 語音合成完成：{output_path}")

def main():
    today = datetime.now().strftime("%Y%m%d")
    script_path = f"docs/podcast/{today}/script.txt"
    audio_path = f"docs/podcast/{today}/audio.mp3"

    if not os.path.exists(script_path):
        print(f"❌ 找不到 script.txt：{script_path}")
        return

    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    synthesize(script_path, audio_path)

if __name__ == "__main__":
    main()
