生成一個github《幫幫忙說每日亮光》Podcast 專案的完整專案架構與工作流程（整合 OCR、晨晚分段、語音合成、B2 上傳、RSS 產出）：
專案目錄結構
.
├── docs/
│   ├── img/                      # 每日圖片來源（格式：YYYYMMDD.jpg）
│   │   └── 20250801.jpg
│   ├── podcast/
│   │   └── 20250801/
│   │       ├── morning.txt       # 晨的逐字稿
│   │       ├── evening.txt       # 晚的逐字稿
│   │       ├── morning.mp3       # 晨的音檔
│   │       ├── evening.mp3       # 晚的音檔
│   └── rss/
│       └── podcast.xml           # 合併後的 RSS feed
│
├── scripts/
│   ├── ocr_image_to_text.py      # OCR 辨識並分成晨/晚
│   ├── text_to_speech_edge.py    # 語音合成（使用 edge-tts）
│   ├── upload_to_b2.py           # 上傳至 B2
│   ├── generate_rss.py           # 產生 RSS feed
│
├── .github/
│   └── workflows/
│       └── podcast_light.yml     # GitHub Actions 自動化流程
│
├── requirements.txt              # Python 套件依賴
└── README.md

運作流程摘要
每天 06:00 與 18:00（台灣時間）自動觸發 GitHub Actions

GitHub Actions 使用 podcast_light.yml 自動啟動流程

OCR 辨識圖片（ocr_image_to_text.py）

每天只有一張圖：docs/img/YYYYMMDD.jpg

自動旋轉、增強、分成上下兩段

若偵測出「●月●日．晨」和「●月●日．晚」關鍵字，就輸出為：

docs/podcast/YYYYMMDD/morning.txt

docs/podcast/YYYYMMDD/evening.txt

若辨識失敗，輸出為 今日無內容

語音合成（text_to_speech_edge.py）

分別將 morning.txt 和 evening.txt 生成二個 MP3（使用 edge-tts 語音 zh-TW-YunJheNeural）

產出：

morning.mp3

evening.mp3

上傳至 B2（upload_to_b2.py）(B2_BUCKET_NAME: daily-light)

上傳生成的 mp3 檔案至 B2 Bucket

回傳公開下載網址

生成 RSS（generate_rss.py）

將 morning 和 evening 的音檔與文字稿合併為單一 RSS feed（podcast.xml）

RSS commit 並推送至 GitHub Pages

commit 更新後的 docs/rss/podcast.xml

自動同步至 Apple Podcast、Spotify 等平台

email: tim.oneway@gmail.com
主持人:幫幫忙
