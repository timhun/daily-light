import os
import sys
import datetime
import pytz
from mutagen.mp3 import MP3
from feedgen.feed import FeedGenerator
from utils import load_config, get_date_string, ensure_directory, get_taiwan_time, log_message

# ===== 基本常數設定 =====
SITE_URL = "https://timhun.github.io/daily-light"
B2_BASE = "https://f005.backblazeb2.com/file/daily-light"
COVER_URL = f"{SITE_URL}/docs/img/cover.jpg"
RSS_FILE = os.path.join('docs', 'rss', 'podcast_light.xml')

FIXED_DESCRIPTION = """每日一則靈修亮光，用聲音溫柔照亮新的一天。
\n\n🔔 訂閱以接收每日晨間與晚間更新，探索經文與反思。
\n\n📮 主持人：幫幫便，聯繫：tim.oneway@gmail.com"""

# ===== 初始化 Feed =====
fg = FeedGenerator()
fg.load_extension("podcast")
fg.id(SITE_URL)
fg.title("幫幫便說每日亮光")
fg.author({"name": "幫幫便", "email": "tim.oneway@gmail.com"})
fg.link(href=SITE_URL, rel="alternate")
fg.language("zh-TW")
fg.description(FIXED_DESCRIPTION)
fg.logo(COVER_URL)
fg.link(href=f"{SITE_URL}/rss/podcast_light.xml", rel="self")
fg.podcast.itunes_category("Religion & Spirituality", "Christianity")
fg.podcast.itunes_image(COVER_URL)
fg.podcast.itunes_explicit("no")
fg.podcast.itunes_author("幫幫便")
fg.podcast.itunes_owner(name="幫幫便", email="tim.oneway@gmail.com")

# ===== 找出最新資料夾 =====
episodes_dir = os.path.join('docs', 'podcast')
matching_folders = sorted([
    f for f in os.listdir(episodes_dir)
    if os.path.isdir(os.path.join(episodes_dir, f)) and f == get_date_string()
], reverse=True)

if not matching_folders:
    log_message(f"⚠️ 找不到當日 podcast 資料夾 {get_date_string()}，RSS 未產生", "WARNING")
    sys.exit(0)

latest_folder = matching_folders[0]
base_path = os.path.join(episodes_dir, latest_folder)

# ===== 處理 morning 和 evening 項目 =====
audio_files = [('morning.mp3', '晨間'), ('evening.mp3', '晚間')]
for audio_file, session in audio_files:
    audio_path = os.path.join(base_path, audio_file)
    archive_url_file = os.path.join(base_path, f"{session.lower()}_url.txt")

    if os.path.exists(audio_path) and os.path.exists(archive_url_file):
        with open(archive_url_file, "r") as f:
            audio_url = f.read().strip()

        try:
            mp3 = MP3(audio_path)
            duration = int(mp3.info.length)
        except Exception as e:
            log_message(f"⚠️ 讀取 {audio_file} 時長失敗：{e}", "WARNING")
            duration = None

        tz = pytz.timezone("Asia/Taipei")
        pub_date = tz.localize(datetime.datetime.now()).strftime("%a, %d %b %Y %H:%M:%S GMT")  # 使用當前日期
        title = f"每日亮光 - {get_date_string()} {session}"

        # 摘要處理 (假設 summary.txt 存在)
        summary_path = os.path.join(base_path, f"{session.lower()}_summary.txt")
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_text = f.read().strip()
            full_description = f"{FIXED_DESCRIPTION}\n\n🎯 今日{session}摘要：{summary_text}"
        else:
            full_description = FIXED_DESCRIPTION

        # === Feed Entry ===
        fe = fg.add_entry()
        fe.id(audio_url)
        fe.title(title)
        fe.description(full_description)
        fe.content(full_description, type="CDATA")
        fe.enclosure(audio_url, str(os.path.getsize(audio_path)), "audio/mpeg")
        fe.pubDate(pub_date)
        if duration:
            fe.podcast.itunes_duration(str(datetime.timedelta(seconds=duration)))

# ===== 輸出 RSS =====
ensure_directory(os.path.dirname(RSS_FILE))
try:
    fg.rss_file(RSS_FILE)
    log_message(f"✅ 已產生 RSS Feed：{RSS_FILE}")
except Exception as e:
    log_message(f"❌ RSS 寫入失敗: {str(e)}", "ERROR")
    sys.exit(1)

def main():
    """主函數"""
    try:
        log_message("生成 RSS Feed 完成")
        sys.exit(0)
    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()