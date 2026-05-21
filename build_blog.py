import os
import re

# 定義文章資料夾（因為腳本在根目錄，文章在 blog 資料夾）
BLOG_DIR = "blog"

articles = []

if not os.path.exists(BLOG_DIR):
    print(f"錯誤：找不到【{BLOG_DIR}】資料夾，請確認位置。")
    exit()

# 1. 掃描所有文章，抓取標題與檔名
for filename in os.listdir(BLOG_DIR):
    if filename.endswith(".html") and filename != "0_template.html":
        filepath = os.path.join(BLOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            title = title_match.group(1).split("-")[0].strip() if title_match else filename
            # 組裝成網頁超連結
            articles.append(f'<li>• <a href="/blog/{filename}">{title}</a></li>')
        except Exception as e:
            print(f"讀取 {filename} 失敗: {e}")

# 2. 組裝要塞入的 HTML 目錄
links_html = "\n"
links_html += "    <h3 style='margin-top: 30px;'>🧭 延伸觀念解析</h3>\n"
links_html += "    <ul style='list-style: none; padding-left: 10px; line-height: 1.8;'>\n"
links_html += "\n".join(articles)
links_html += "\n    </ul>\n"
links_html += "    "

# 3. 把全站所有 HTML 檔案（包含樣板）的暗號區塊全部替換
updated_count = 0
for filename in os.listdir(BLOG_DIR):
    if filename.endswith(".html"):
        filepath = os.path.join(BLOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "" in content and "" in content:
                new_content = re.sub(
                    r".*?", 
                    links_html, 
                    content, 
                    flags=re.DOTALL
                )
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated_count += 1
        except Exception as e:
            print(f"寫入 {filename} 失敗: {e}")

print(f"【成功】已自動同步 {updated_count} 個 HTML 檔案的延伸閱讀選單！")
