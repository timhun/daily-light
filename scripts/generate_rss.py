import os
import sys
from datetime import datetime
from feedgen.feed import FeedGenerator
from feedgen.ext import itunes as itunes_ext  # 明確導入 iTunes 擴展
from utils import load_config, get_date_string, ensure_directory, get_taiwan_time, log_message

class RSSGenerator:
    def __init__(self):
        self.config = load_config()
        self.rss_config = self.config.get('rss', {})
        self.podcast_config = self.config.get('podcast', {})
        self.feed_title = self.rss_config.get('title', 'Default Podcast Title')
        self.feed_author = self.rss_config.get('author', 'Default Author')
        self.feed_email = self.rss_config.get('email', 'tim.oneway@gmail.com')
        self.feed_description = self.rss_config.get('description', 'Default description')
        self.podcast_dir = os.path.join('docs', 'podcast', get_date_string())
        self.output_path = os.path.join('docs', 'rss', 'podcast_light.xml')

        ensure_directory(os.path.dirname(self.output_path))

    def generate_feed(self):
        """生成 RSS Feed"""
        try:
            log_message("開始生成 RSS Feed")

            # 初始化 FeedGenerator
            fg = FeedGenerator()
            fg.id(self.podcast_config.get('image_url', ''))
            fg.title(self.feed_title)
            fg.author({'name': self.feed_author, 'email': self.feed_email})
            fg.description(self.feed_description)
            fg.link(href=self.podcast_config.get('image_url', ''), rel='self')
            fg.language(self.podcast_config.get('language', 'zh-TW'))

            # 添加 iTunes 擴展
            itunes = fg.load_extension('itunes')
            itunes.itunes_author(self.feed_author)
            itunes.itunes_category(self.podcast_config.get('category', 'Religion & Spirituality'))
            itunes.itunes_explicit(self.podcast_config.get('explicit', 'no'))
            itunes.itunes_image(self.podcast_config.get('image_url', ''))

            # 檢查並添加當日項目
            if not os.path.exists(self.podcast_dir):
                log_message(f"目錄 {self.podcast_dir} 不存在，跳過項目添加", "WARNING")
                return False

            files = [f for f in os.listdir(self.podcast_dir) if f.endswith('.mp3')]
            if not files:
                log_message(f"目錄 {self.podcast_dir} 中無 MP3 文件", "WARNING")
                return False

            for mp3_file in files:
                if 'morning' in mp3_file.lower():
                    title = f"{get_date_string()} 晨間"
                elif 'evening' in mp3_file.lower():
                    title = f"{get_date_string()} 晚間"
                else:
                    continue

                fe = fg.add_entry()
                fe.id(f"https://{self.podcast_config.get('image_url', '')}/{mp3_file}")
                fe.title(title)
                fe.description(self.feed_description)
                fe.link(href=f"https://{self.podcast_config.get('image_url', '')}/{mp3_file}", rel='enclosure')
                fe.enclosure(f"https://{self.podcast_config.get('image_url', '')}/{mp3_file}", 0, 'audio/mpeg')  # 需更新文件大小
                fe.published(get_taiwan_time().isoformat())
                itunes_entry = fe.load_extension('itunes')
                itunes_entry.itunes_duration("00:05:00")  # 需動態計算

            # 寫入 RSS 文件
            fg.rss_file(self.output_path)
            log_message(f"RSS Feed 已生成: {self.output_path}")
            return True

        except Exception as e:
            log_message(f"RSS 生成失敗: {str(e)}", "ERROR")
            return False

    def run(self):
        """主運行邏輯"""
        try:
            success = self.generate_feed()
            if success:
                log_message("RSS Feed 生成成功")
            else:
                log_message("RSS Feed 生成失敗", "ERROR")
            return success

        except Exception as e:
            log_message(f"主程序執行失敗: {str(e)}", "ERROR")
            return False

def main():
    """主函數"""
    try:
        rss_gen = RSSGenerator()
        success = rss_gen.run()

        if success:
            log_message("生成 RSS Feed 完成")
            sys.exit(0)
        else:
            log_message("RSS 生成失敗，但繼續執行", "WARNING")
            sys.exit(1)

    except Exception as e:
        log_message(f"主程序執行失敗: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()