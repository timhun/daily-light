# 《幫幫忙說每日亮光》Podcast 自動化專案

[![Daily Light Podcast Generator](https://github.com/timhun/daily-light/actions/workflows/podcast_light.yml/badge.svg)](https://github.com/timhun/daily-light/actions/workflows/podcast_light.yml)

## 專案概述

這是一個全自動化的 Podcast 生成系統，每日自動將《每日亮光》的圖片內容轉換為語音節目。

功能特色
🔄 全自動化: 每日自動執行，無需人工干預
📱 OCR 識別: 自動識別圖片中的中文文字
🎙️ 語音合成: 使用 Microsoft Edge TTS 生成自然語音
☁️ 雲端存儲: 音檔上傳至 Backblaze B2 (bucket_name: "daily-light")
📡 RSS 發布: 自動生成並更新 RSS Feed
🌐 多平台: 支援 Apple Podcasts、Spotify 等平台
執行時間
晨間: 每日 06:00 (台灣時間)
晚間: 每日 18:00 (台灣時間)
創建儲存庫: https://github.com/timhun/daily-light 設置 B2 帳號並獲取 API 金鑰 在 GitHub 設置 Secrets:

B2_KEY_ID B2_APPLICATION_KEY

手動上傳按日期的圖片檔 (docs/img/MMDD.jpg)以供辨識，內容分為上半段為"晨"，下半段為"晚"

特殊功能：

(1)智能圖片處理: 增強對比度 中文日期識別: 支援「八月二日」格式 錯誤處理: 完整的異常處理和日誌記錄 手動觸發: 支援 workflow_dispatch 文件驗證: 檢查文件存在性和完整性
(2)doc/img/MMDD.jpg 辨識直式繁體中文，生成"晨"與"晚"二份文字稿，再轉成"晨"與"晚"的mp3
(3)有提供doc/img/MMDD.txt 目錄下當天日期正確的文字稿以供比對校正，若與校正稿的不一致，請改用校正稿內對應的文字生成"晨"與"晚"的文字稿
(4)早上6點上傳當日"晨"的mp3播報檔，晚上6點上傳當日"晚的mp3, 語音播報內容不讀出文字稿內()之內的文字

🎯 使用方式

每日上傳圖片到 docs/img/MMDD.jpg 系統自動在 06:00 和 18:00 執行 生成的 Podcast 會自動發布到 RSS Feed 用戶可透過 RSS 訂閱: https://timhun.github.io/daily-light/rss/podcast_light.xml

daily-light/
├── docs/                    # 主要數據和輸出目錄
│   ├── img/                # 儲存待處理的圖片檔案
│   │   ├── 20250807.jpg    # 當前日期的圖片（例如 OCR 來源）
│   │   ├── 20250807.txt    # 校正稿（可選）
│   │   └── ...             # 其他日期的圖片和校正稿
│   ├── podcast/            # Podcast 相關內容
│   │   ├── 20250807/       # 當前日期的 Podcast 內容
│   │   │   ├── morning.txt # 晨間文本
│   │   │   ├── evening.txt # 晚間文本
│   │   │   ├── morning.mp3 # 晨間音頻
│   │   │   └── evening.mp3 # 晚間音頻
│   │   └── ...             # 其他日期的 Podcast 內容
│   └── rss/                # RSS feed 儲存目錄
│       └── podcast.xml     # 生成的 RSS feed 文件
├── scripts/                # 腳本目錄
│   ├── ocr_image_to_text.py  # OCR 處理腳本
│   ├── text_to_speech_edge.py  # 語音合成與後續處理腳本
│   └── upload_to_b2.py      # (可選) 獨立上傳腳本
├── config/                 # 配置文件目錄
│   └── podcast_config.json # 儲存 API 密鑰、配置等
├── requirements.txt        # Python 依賴文件
├── .github/                # GitHub Actions 配置文件
│   └── workflows/
│       └── daily_light_podcast_generator.yml  # 工作流文件
└── README.md               # 專案說明文件
