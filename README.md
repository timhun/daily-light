# daily-light
daily-light/
├── .github/
│   └── workflows/
│       └── podcast_light.yml          👈 GitHub Actions 自動執行流程
├── docs/
│   ├── images/
│   │   └── 20250731.jpg               👈 每日圖片（早上或下午放一張）
│   ├── audio/
│   │   └── 20250731.mp3               👈 合成後音訊（每日 1 集）
│   ├── rss/
│   │   └── podcast_light.xml          👈 自動產生 RSS Feed
│   └── img/
│       └── cover.jpg                  👈 Podcast 封面圖
├── scripts/
│   ├── ocr_image_to_text.py          👈 OCR 辨識每日圖片 → 文字稿
│   ├── synthesize_audio.py           👈 將文字稿轉成語音 MP3
│   ├── upload_to_b2.py               👈 上傳 MP3 至 Backblaze B2
│   └── generate_rss.py               👈 自動產出 RSS feed
├── requirements.txt                  👈 依賴套件（包含 TTS 與 OCR）
