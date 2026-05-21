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
    if filename.endswith(".html") and filename != "0_template.html":
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
        filepath = os.path.join(BLOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
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
                print(f"【注意】{filename} 找不到暗號標籤，略過不處理。")
        except Exception as e:
            print(f"寫入 {filename} 失敗: {e}")

print(f"【大功告成】已成功更新 {updated_count} 個 HTML 檔案（已完美排除當前文章連結）！")
