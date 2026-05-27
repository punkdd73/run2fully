import os
import re

BLOG_DIR = "blog"

if not os.path.exists(BLOG_DIR):
    print(f"錯誤：找不到【{BLOG_DIR}】資料夾")
    exit()

# ==========================================
# 1. 核心大改造：改為動態過濾「當前文章」
# ==========================================
updated_count = 0

# 先掃描一次，把全站所有可用的文章資訊（檔名與標題）儲存成一個清單
all_articles = []
for filename in os.listdir(BLOG_DIR):
    if filename.endswith(".html"):
        if filename == "0_template.html":
            continue            
        filepath = os.path.join(BLOG_DIR, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            title = title_match.group(1).split("-")[0].strip() if title_match else filename
            all_articles.append({"filename": filename, "title": title})
        except Exception as e:
            print(f"讀取 {filename} 失敗: {e}")

# 開始逐一處理每個 HTML 檔案的寫入
for filename in os.listdir(BLOG_DIR):
    if filename.endswith(".html"):
        # 💡 關鍵修正：後半段的寫入迴圈，也必須把樣板檔排除！
        if filename == "0_template.html":
            continue

        filepath = os.path.join(BLOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # ====== 新增：自動在 </h1> 後方加上日期 ======
            import datetime
            original_content = content
            if "</h1>" in content:
                # 檢查 </h1> 後方是否已經有 <p>YYYY-MM-DD</p> 格式，避免重複加入
                if not re.search(r'</h1>\s*<p>\d{4}-\d{2}-\d{2}</p>', content):
                    # 取檔案的建立時間作為文章日期 (即使是舊文章也能抓到正確時間)
                    file_ctime = os.path.getctime(filepath)
                    date_str = datetime.datetime.fromtimestamp(file_ctime).strftime("%Y-%m-%d")
                    content = content.replace("</h1>", f"</h1>\n<p>{date_str}</p>", 1)
            
            # ====== 新增：自動替換 canonical 與 og:url 為正確檔名 ======
            content = re.sub(r'<link\s+rel="canonical"\s+href="[^"]*"\s*/>', f'<link rel="canonical" href="https://www.run2fully.com/blog/{filename}" />', content)
            content = re.sub(r'<meta\s+property="og:url"\s+content="[^"]*"\s*/>', f'<meta property="og:url" content="https://www.run2fully.com/blog/{filename}" />', content)
            # ============================================
            # ============================================

            
            # 💡 精確對齊你縮短後的隱形暗號
            start_tag = "<!--AUTO_LINKS_START-->"
            end_tag = "<!--AUTO_LINKS_END-->"
            
            if start_tag in content and end_tag in content:
                front_part = content.split(start_tag)[0]
                back_part = content.split(end_tag)[-1]
                
                # 💡 關鍵優化：組裝延伸閱讀時，如果「清單中的檔名」等於「目前正在處理的檔名」，就直接跳過不放入！
                filtered_links = []
                for article in all_articles:
                    if article["filename"] != filename:
                        filtered_links.append(f'<li>• <a href="/blog/{article["filename"]}">{article["title"]}</a></li>')
                
                # 組裝要塞入的最新延伸閱讀內容
                inside_content = "\n    <h3 style='margin-top: 30px;'>🧭 延伸觀念解析</h3>\n"
                inside_content += "    <ul style='list-style: none; padding-left: 10px; line-height: 1.8;'>\n"
                inside_content += "\n".join(filtered_links)
                inside_content += "\n    </ul>\n"
                
                # 重新組裝檔案內容
                new_content = f"{front_part}{start_tag}{inside_content}{end_tag}{back_part}"
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated_count += 1
            else:
                # 如果找不到暗號，但是有更新日期，也要儲存檔案
                if content != original_content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    updated_count += 1
                else:
                    print(f"【注意】{filename} 找不到暗號標籤，略過不處理。")
        except Exception as e:
            print(f"寫入 {filename} 失敗: {e}")

print(f"【大功告成】已成功更新 {updated_count} 個 HTML 檔案（已完美排除當前文章連結與樣板檔）！")

# ==========================================
# 2. 更新首頁 (index.html) 的文章列表
# ==========================================
index_filepath = "index.html"
if os.path.exists(index_filepath):
    try:
        with open(index_filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        start_tag = "<!--AUTO_LINKS_START-->"
        end_tag = "<!--AUTO_LINKS_END-->"
        
        if start_tag in content and end_tag in content:
            front_part = content.split(start_tag)[0]
            back_part = content.split(end_tag)[-1]
            
            # 組裝首頁的連結 (顯示所有文章)
            index_links = []
            for article in all_articles:
                index_links.append(f'<li><a href="/blog/{article["filename"]}">{article["title"]}</a></li>')
            
            inside_content = "\n        <ul style='line-height: 1.8; font-size: 1.1em;'>\n"
            inside_content += "\n".join(f"            {link}" for link in index_links)
            inside_content += "\n        </ul>\n        "
            
            new_content = f"{front_part}{start_tag}{inside_content}{end_tag}{back_part}"
            
            with open(index_filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"【系統】已成功更新 {index_filepath} 的文章列表！")
        else:
            print(f"【注意】{index_filepath} 找不到暗號標籤，略過不處理。")
    except Exception as e:
        print(f"寫入 {index_filepath} 失敗: {e}")

# ==========================================
# 3. sitemap 同步更新
# ==========================================
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap_content += '  <url><loc>https://www.run2fully.com/</loc><priority>1.0</priority></url>\n'

for article in all_articles:
    sitemap_content += f'  <url><loc>https://www.run2fully.com/blog/{article["filename"]}</loc><priority>0.8</priority></url>\n'

sitemap_content += '</urlset>'

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_content)
print("【系統】已自動更新 sitemap.xml")
