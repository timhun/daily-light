# scripts/generate_rss.py
import os
import glob
import datetime
import pytz
import json
from feedgen.feed import FeedGenerator

FEED_TITLE = "幫幫忙說每日亮光"
FEED_AUTHOR = "幫幫忙"
FEED_EMAIL = "tim.oneway@gmail.com"
FEED_LINK = "https://timhun.github.io/daily-light/rss/podcast.xml"
FEED_IMAGE = "https://timhun.github.io/daily-light/img/cover.jpg"
B2_BASE_URL = "https://f005.backblazeb2.com/file/daily-light/"

def get_mp3_files():
    today = datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y%m%d")
    files = sorted(glob.glob(f"docs/audio/{today}_*.mp3"))
    return files

def main():
    fg = FeedGenerator()
    fg.load_extension('podcast')

    fg.title(FEED_TITLE)
    fg.link(href=FEED_LINK, rel='self')
    fg.description("每日早晚讀經默想，幫幫忙為你朗讀每日亮光")
    fg.language('zh-tw')
    fg.image(url=FEED_IMAGE)

    today = datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y%m%d")
    audio_files = get_mp3_files()

    for mp3_path in audio_files:
        filename = os.path.basename(mp3_path)
        pub_time = "06:00:00" if "0600" in filename else "18:00:00"
        pub_datetime = datetime.datetime.strptime(f"{today} {pub_time}", "%Y%m%d %H:%M:%S")
        pub_datetime = pytz.timezone("Asia/Taipei").localize(pub_datetime)

        fe = fg.add_entry()
        fe.id(filename)
        fe.title(f"{today} {'早上' if '0600' in filename else '晚上'}亮光")
        fe.pubDate(pub_datetime)
        fe.enclosure(B2_BASE_URL + filename, 0, 'audio/mpeg')
        fe.description("由幫幫忙播報，朗讀圖片中每日亮光的經文與默想")

    rss_output = "docs/rss/podcast.xml"
    os.makedirs(os.path.dirname(rss_output), exist_ok=True)
    fg.rss_file(rss_output, encoding="utf-8")
    print(f"✅ RSS 產生完成：{rss_output}")

if __name__ == "__main__":
    main()
