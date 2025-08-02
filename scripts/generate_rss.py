# scripts/generate_rss.py
import os
import re
from datetime import datetime
from feedgen.feed import FeedGenerator
from dateutil import tz

# --- 基本設定 (請根據您的需求修改) ---
PODCAST_TITLE = "幫幫忙說每日亮光"
# 重要！請將此 URL 替換為您的 GitHub Pages 網址
# 範例: https://tim-oneway.github.io/daily-light-podcast/
BASE_URL = "https://timhun.github.io/<your-repo-name>" 
PODCAST_DESCRIPTION = "每日靈修，以馬內利。透過自動化技術，將《每日亮光》轉換為語音，陪伴您的每一天。"
PODCAST_AUTHOR = {'name': '幫幫忙', 'email': 'tim.oneway@gmail.com'}
# 重要！請將此 URL 替換為您的封面圖的完整路徑
# 範例: f"{BASE_URL}/img/cover.jpg"
PODCAST_COVER_URL = f"{BASE_URL}/img/cover.jpg"
B2_PUBLIC_URL_BASE = f"https://f005.backblazeb2.com/file/{os.environ.get('B2_BUCKET_NAME')}"


def get_file_info(file_path):
    """
    獲取檔案大小和類型。
    """
    if not os.path.exists(file_path):
        return 0, 'audio/mpeg'
    size = os.path.getsize(file_path)
    return str(size), 'audio/mpeg'

def generate_rss():
    """
    掃描 podcast 目錄並生成 RSS feed。
    """
    fg = FeedGenerator()
    fg.load_extension('podcast')

    # --- Podcast 整體資訊 ---
    fg.title(PODCAST_TITLE)
    fg.link(href=BASE_URL, rel='alternate')
    fg.description(PODCAST_DESCRIPTION)
    fg.language('zh-TW')
    fg.author(PODCAST_AUTHOR)
    fg.image(url=PODCAST_COVER_URL, title=PODCAST_TITLE, link=BASE_URL)
    
    # --- iTunes 特定標籤 ---
    fg.podcast.itunes_author(PODCAST_AUTHOR['name'])
    fg.podcast.itunes_owner(name=PODCAST_AUTHOR['name'], email=PODCAST_AUTHOR['email'])
    fg.podcast.itunes_category('Religion & Spirituality', 'Christianity')
    fg.podcast.itunes_explicit('no')
    fg.podcast.itunes_image(PODCAST_COVER_URL)

    # --- 掃描所有集數並加入到 Feed ---
    podcast_dir = 'docs/podcast'
    date_folders = sorted([d for d in os.listdir(podcast_dir) if os.path.isdir(os.path.join(podcast_dir, d))], reverse=True)

    for date_str in date_folders:
        match = re.match(r'(\d{4})(\d{2})(\d{2})', date_str)
        if not match:
            continue
        
        year, month, day = map(int, match.groups())
        episode_date = datetime(year, month, day, tzinfo=tz.gettz('Asia/Taipei'))

        day_path = os.path.join(podcast_dir, date_str)
        
        # 處理晚間內容
        evening_txt_path = os.path.join(day_path, 'evening.txt')
        evening_mp3_path = os.path.join(day_path, 'evening.mp3')
        if os.path.exists(evening_txt_path) and os.path.exists(evening_mp3_path):
            with open(evening_txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fe = fg.add_entry()
            title = f"{year}年{month}月{day}日 (晚)"
            fe.title(title)
            fe.id(f"{date_str}-evening")
            fe.pubDate(episode_date.replace(hour=18)) # 假設晚間在 18:00 發佈
            fe.description(f"晚間靈修：\n{content}")
            fe.link(href=f"{BASE_URL}/podcast/{date_str}/")
            
            mp3_filename = f"{date_str}_evening.mp3"
            mp3_url = f"{B2_PUBLIC_URL_BASE}/{mp3_filename}"
            size, mime = get_file_info(evening_mp3_path)
            fe.enclosure(url=mp3_url, length=size, type=mime)

        # 處理晨間內容
        morning_txt_path = os.path.join(day_path, 'morning.txt')
        morning_mp3_path = os.path.join(day_path, 'morning.mp3')
        if os.path.exists(morning_txt_path) and os.path.exists(morning_mp3_path):
            with open(morning_txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fe = fg.add_entry()
            title = f"{year}年{month}月{day}日 (晨)"
            fe.title(title)
            fe.id(f"{date_str}-morning")
            fe.pubDate(episode_date.replace(hour=6)) # 假設晨間在 06:00 發佈
            fe.description(f"晨間靈修：\n{content}")
            fe.link(href=f"{BASE_URL}/podcast/{date_str}/")

            mp3_filename = f"{date_str}_morning.mp3"
            mp3_url = f"{B2_PUBLIC_URL_BASE}/{mp3_filename}"
            size, mime = get_file_info(morning_mp3_path)
            fe.enclosure(url=mp3_url, length=size, type=mime)

    # 產生 RSS XML 檔案
    rss_path = os.path.join('docs', 'rss', 'podcast.xml')
    os.makedirs(os.path.dirname(rss_path), exist_ok=True)
    fg.rss_file(rss_path, pretty=True)
    print(f"RSS Feed 已成功生成於: {rss_path}")


if __name__ == "__main__":
    generate_rss()
