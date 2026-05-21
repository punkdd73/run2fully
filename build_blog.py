import os
import re

BLOG_DIR = "blog"
articles = []

if not os.path.exists(BLOG_DIR):
    print(f"錯誤：找不到【{BLOG_DIR}】資料夾")
    exit()

# 1. 蒐集所有最新文章連結（已排除樣板檔）
for filename in os.listdir(BLOG_DIR):
    if filename.endswith(".html") and filename != "0_template.html":
        filepath = os.path.join(BLOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            title = title_match.group(1).split("-")[0].strip() if title_match else filename
            articles.append(f'<li>• <a href="/blog/{filename}">{title}</a></li>')
        except Exception as e:
            print(f"讀取 {filename} 失敗: {e}")

# 2. 組裝要塞入的最新延伸閱讀內容
inside_content = "\n    <h3 style='margin-top: 30px;'>🧭 延伸觀念解析</h3>\n"
inside_content += "    <ul style='list-style: none; padding-left: 10px; line-height: 1.8;'>\n"
inside_content += "\n".join(articles)
inside_content += "\n    </ul>\n"

# 3. 掃描並用純文字暗號進行安全拆解
updated_count = 0
for filename in os.listdir(BLOG_DIR):
    if filename.endswith(".html"):
        filepath = os.path.join(BLOG_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 💡 終極調整：直接用純文字當暗號牆，絕對不會打錯，也不會被過濾
            start_tag = "<!--AUTO_LINKS_START-->"
            end_tag = "<!--AUTO_LINKS_END-->"
            
            if start_tag in content and end_tag in content:
                front_part = content.split(start_tag)[0]
                back_part = content.split(end_tag)[-1]
                
                # 重新組裝
                new_content = f"{front_part}{start_tag}{inside_content}{end_tag}{back_part}"
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated_count += 1
            else:
                print(f"【注意】{filename} 找不到暗號 {start_tag} 或 {end_tag}，略過不處理。")
        except Exception as e:
            print(f"寫入 {filename} 失敗: {e}")

print(f"【成功】已全自動覆蓋更新 {updated_count} 個 HTML 檔案的延伸閱讀選單！")
