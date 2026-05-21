# Run2Fully 核心網站與自動化中樞

這個儲存庫（Repository）是 `www.run2fully.com` 的根目錄，同時管理了前端靜態網頁、部落格文章、廣告驗證，以及全站文章連結的自動化同步腳本。

---

## 📂 專案架構與檔案定位

```text
punkdd73.github.io/ (GitHub 專案根目錄，指向 [www.run2fully.com](https://www.run2fully.com))
│
├── .github/
│   └── workflows/
│       └── run_build.yml     # 🤖 GitHub Actions 自動化工作流設定檔 (Node24 環境)
│
├── blog/                     # 💡 部落格文章專區（由主程式以 Streamlit Pages 連回）
│   ├── 0_template.html       # 文章基礎樣板
│   ├── article1.html         # 文章 1（例如：蒙地卡羅波動模擬）
│   └── article2.html         # 文章 2（例如：4% 法則生存指南）  
│
├── assets/
│   ├── preview.jpg           # 首頁專用縮圖（解決 LINE 分享網址時的縮圖問題）
│   ├── banner1.jpg           # 內頁banner社群分享縮圖
│   └── favicon.png           # 瀏覽器icon
│ 
├── index.html                # 首頁（導頁至 app.run2fully.com，執行run2fully.py，由 Render 自動部署）
├── ads.txt                   # Google AdSense 廣告防偽驗證檔
├── build_blog.py             # ⚙️ 核心自動化腳本：全自動掃描並組裝延伸閱讀清單
├── CNAME                     # 轉址
├── requirements.txt          # 加載py套件
├── run2fully.py              # 計算機網站執行腳本
└── README.md                 # 本說明文件
