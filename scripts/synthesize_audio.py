# scripts/synthesize_audio.py
import os
import subprocess
from datetime import datetime
import pytz
import logging
import shutil
import sys

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 環境變數與路徑
BASE_DIR = os.getenv("BASE_DIR", "docs")
PODCAST_DIR = os.path.join(BASE_DIR, "podcast")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
VOICE = "zh-TW-YunJheNeural"
RATE = "+15%"

def check_edge_tts():
    """檢查 edge-tts 是否可用"""
    if not shutil.which("edge-tts"):
        logger.error("edge-tts 未安裝，請執行 pip install edge-tts")
        sys.exit(1)

def synthesize(text_path, output_path):
    """執行語音合成"""
    try:
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            logger.warning("文字稿為空，生成預設音訊")
            text = "今日無內容，請明日再收聽。"
        command = [
            "edge-tts",
            "--voice", VOICE,
            "--rate", RATE,
            "--text", text,
            "--write-media", output_path
        ]
        logger.info(f"執行命令：{' '.join(command)}")
        if os.path.exists(output_path):
            shutil.copy(output_path, f"{output_path}.bak")
        subprocess.run(command, check=True, capture_output=True, text=True)
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error("音訊檔案生成失敗")
            return False
        logger.info(f"語音合成完成：{output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"edge-tts 執行失敗：{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"語音合成錯誤：{e}")
        return False

def main():
    check_edge_tts()
    tz = pytz.timezone("Asia/Taipei")
    today = datetime.now(tz).strftime("%Y%m%d")
    script_path = os.path.join(PODCAST_DIR, today, "script.txt")
    audio_path = os.path.join(AUDIO_DIR, f"{today}.mp3")

    if not os.path.exists(script_path):
        logger.error(f"找不到 script.txt：{script_path}")
        sys.exit(1)

    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    if not synthesize(script_path, audio_path):
        logger.error("語音合成失敗，退出")
        sys.exit(1)

if __name__ == "__main__":
    main()
