# Run2Fully 核心網站與自動化中樞

這個儲存庫（Repository）是 `www.run2fully.com` 的根目錄，同時管理了前端靜態網頁、部落格文章、廣告驗證，以及全站文章連結的自動化同步腳本，並包含了最新的 Streamlit 後台管理系統。

---

## 🌟 主要功能

1. **靜態首頁與部落格系統**：透過 GitHub Pages 託管 `www.run2fully.com`，提供高效的靜態頁面讀取體驗。
2. **自動化文章建置 (`build_blog.py`)**：自動掃描並組裝延伸閱讀清單，並生成 `sitemap.xml` 以利 SEO。
3. **Streamlit 後台管理系統 (`admin.py`)**：
   - 提供密碼保護的視覺化後台。
   - 支援 Markdown 撰寫文章，自動套用樣板 (`0_template.html`) 轉換為 HTML 並推送到 GitHub 儲存庫。
   - 直接在介面上管理與修改現有文章。
   - 動態更新 `run2fully.py` 中的側邊欄文章連結。
4. **Run2Fully 計算機 (`run2fully.py`)**：由 Render 自動部署至 `app.run2fully.com` 的主應用程式。

---

## 📂 專案架構與檔案定位

```text
punkdd73.github.io/ (GitHub 專案根目錄，指向 www.run2fully.com)
│
├── .github/
│   └── workflows/
│       └── run_build.yml     # 🤖 GitHub Actions 自動化工作流設定檔 (Node24 環境)
│       └── build_blog.yml    # 🤖 自動建置 Blog 相關檔案的 Actions
│
├── blog/                     # 💡 部落格文章專區
│   ├── 0_template.html       # 文章基礎樣板，供 admin.py 轉換時套用
│   └── (其他 .html 文章)      # 透過後台生成的靜態 HTML 文章
│
├── assets/
│   ├── preview.jpg           # 首頁專用縮圖（解決 LINE 分享網址時的縮圖問題）
│   ├── banner1.jpg           # 內頁 banner 社群分享縮圖
│   └── favicon.png           # 瀏覽器 icon
│ 
├── index.html                # 首頁 Landing Page
├── ads.txt                   # Google AdSense 廣告防偽驗證檔
├── build_blog.py             # ⚙️ Blog自動化腳本：全自動掃描並組裝延伸閱讀清單 + 生成 sitemap.xml
├── sitemap.xml               # 自動生成的網站地圖
├── CNAME                     # 網域轉址設定
├── requirements.txt          # Python 依賴套件清單
├── admin.py                  # 🔐 Streamlit 後台管理系統（文章發布、編輯、側邊欄管理）
├── run2fully.py              # 🧮 計算機網站執行腳本（部署於 Render: app.run2fully.com）
├── robots.txt                # 搜尋引擎爬蟲指引
└── README.md                 # 本說明文件
```

---

## 🚀 本地端執行與開發

### 1. 安裝依賴套件
請確保已經安裝 Python 環境，然後執行：
```bash
pip install -r requirements.txt
```

### 2. 執行後台管理系統
後台系統使用 Streamlit 建立，您可以在本地端啟動：
```bash
streamlit run admin.py
```
> **注意**：本地端測試時，需在 `.streamlit/secrets.toml` 中設定 `ADMIN_PASSWORD`（後台登入密碼）與 `GITHUB_TOKEN`（用於 API 推送變更），否則將無法正常使用上傳與修改功能。

### 3. 執行主應用程式（計算機）
若需測試計算機功能，執行：
```bash
streamlit run run2fully.py
```

### 4. 手動建置 Blog 與 Sitemap
如果您不依賴 GitHub Actions，可以手動執行腳本更新 sitemap 與延伸閱讀：
```bash
python build_blog.py
```
