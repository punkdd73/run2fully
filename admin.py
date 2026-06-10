import streamlit as st
from github import Github
import markdown
import os
import re

st.set_page_config(page_title="Run2Fully 後台管理", layout="wide")

# ==========================================
# 1. 密碼保護機制
# ==========================================
def check_password():
    """驗證密碼是否正確，並使用 Session State 記住登入狀態"""
    def password_entered():
        # 如果使用者沒有設定 Secrets，就給一個預設密碼方便本地測試
        correct_password = st.secrets.get("ADMIN_PASSWORD", "run2fully")
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 不要把密碼留在記憶體
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 尚未登入，顯示輸入框
        st.text_input("請輸入管理員密碼", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # 密碼錯誤
        st.text_input("請輸入管理員密碼", type="password", on_change=password_entered, key="password")
        st.error("😕 密碼錯誤！")
        return False
    else:
        # 已登入
        return True

if not check_password():
    st.stop()  # 密碼不正確就停止執行後面的程式

# ==========================================
# 2. 建立 GitHub 連線
# ==========================================
@st.cache_resource
def get_repo():
    # 讀取 Secrets 中的 Token
    token = st.secrets.get("GITHUB_TOKEN", "")
    if not token:
        st.error("未設定 GITHUB_TOKEN，無法連線至 GitHub API。")
        st.stop()
    g = Github(token)
    repo = g.get_repo("punkdd73/run2fully")
    return repo

try:
    repo = get_repo()
except Exception as e:
    st.error(f"無法連線到 GitHub: {e}")
    st.info("請確認您的 GITHUB_TOKEN 是否正確且具有 repo 權限。")
    st.stop()

st.title("Run2Fully 後台管理系統 ☁️")
st.write("此後台會直接透過 API 將變更同步至 GitHub。")

tab1, tab3, tab2 = st.tabs(["✍️ 發布新文章", "📂 文章管理", "🔗 側邊欄連結管理"])

# ==========================================
# 3. 發布新文章 (Markdown -> HTML)
# ==========================================
with tab1:
    st.subheader("撰寫並發布新文章")
    
    col1, col2 = st.columns(2)
    with col1:
        filename = st.text_input("檔案名稱 (英數字，不需加 .html)", placeholder="e.g., compound_interest")
    with col2:
        title = st.text_input("文章標題", placeholder="文章的顯示標題 (如：複利的威力)")
        
    og_desc = st.text_input("文章簡介 (og:description)", placeholder="這段文字會顯示在分享連結的預覽中")
    
    md_content = st.text_area("文章內文 (Markdown 格式)", height=400, placeholder="在這裡輸入 Markdown...")
    
    st.markdown("---")
    st.markdown("### 即時預覽")
    if md_content:
        with st.container(border=True):
            st.markdown(md_content)
            
    st.markdown("---")
    if st.button("🚀 生成 HTML 並發布到 GitHub", type="primary"):
        if not filename or not title or not md_content or not og_desc:
            st.warning("檔名、標題、簡介與內文皆為必填！")
        else:
            with st.spinner("正在轉換並上傳至 GitHub..."):
                try:
                    # 1. 取得樣板
                    template_file = repo.get_contents("blog/0_template.html")
                    template_html = template_file.decoded_content.decode("utf-8")
                    
                    # 2. 轉換 markdown 為 HTML
                    html_body = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
                    
                    # 3. 替換樣板內容
                    new_html = template_html
                    
                    # 替換 <title>
                    new_html = re.sub(r'<title>.*?</title>', f'<title>{title} - Run2Fully 深度理財</title>', new_html, flags=re.IGNORECASE | re.DOTALL)
                    # 替換 og:title
                    new_html = re.sub(r'<meta\s+property=["\']og:title["\']\s+content=["\'].*?["\']\s*/?>', f'<meta property="og:title" content="{title}" />', new_html, flags=re.IGNORECASE | re.DOTALL)
                    # 替換 og:description
                    new_html = re.sub(r'<meta\s+property=["\']og:description["\']\s+content=["\'].*?["\']\s*/?>', f'<meta property="og:description" content="{og_desc}" />', new_html, flags=re.IGNORECASE | re.DOTALL)
                    # 替換 {{FILENAME}}
                    new_html = new_html.replace('{{FILENAME}}', f'{filename}.html')
                    # 替換 <h1>
                    from datetime import datetime
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    new_html = re.sub(r'<h1>.*?</h1>', f'<h1>{title}</h1>\n<p>{today_str}</p>', new_html, count=1)
                    
                    # 替換內文區塊
                    # 依據 template，內文介於 <img src="/assets/banner.jpg"> 與 下方的 <BR><BR><a href... 之間
                    start_marker = '<img src="/assets/banner.jpg">'
                    end_marker = '<BR><BR><a href="https://app.run2fully.com" class="back-btn">前往Run2Fully ETF複利計算機</a><BR><BR><a href="https://www.run2fully.com" class="back-btn">返回首頁</a><BR><BR>'
                    
                    if start_marker in new_html and end_marker in new_html:
                        front = new_html.split(start_marker)[0]
                        back = new_html.split(end_marker)[1]
                        new_html = front + start_marker + "\n\n" + html_body + "\n\n  " + end_marker + back
                    else:
                        st.error("樣板格式錯誤，找不到插入內文的定位點！(請確認 0_template.html 是否被修改過)")
                        st.stop()
                    
                    # 4. 上傳到 GitHub
                    file_path = f"blog/{filename}.html"
                    try:
                        # 檢查檔案是否已存在
                        repo.get_contents(file_path)
                        st.error(f"檔案 `blog/{filename}.html` 已經存在！請更換檔名。")
                    except:
                        # 檔案不存在，建立新檔案
                        repo.create_file(file_path, f"Add blog post: {title}", new_html)
                        st.success(f"✅ 成功發布文章！檔案已建立：`blog/{filename}.html`")
                        
                except Exception as e:
                    st.error(f"發布失敗: {e}")

# ==========================================
# 4. 文章管理 (修改與刪除)
# ==========================================
with tab3:
    st.subheader("文章管理 (修改與刪除)")
    st.write("此處列出 `/blog` 底下的所有文章。您可直接以 HTML 原始碼進行修改或刪除。")
    
    if st.session_state.get("article_updated"):
        st.success("✅ 文章更新成功！")
        st.session_state["article_updated"] = False
        
    if st.session_state.get("article_deleted"):
        st.success("✅ 文章已成功刪除！")
        st.session_state["article_deleted"] = False
    
    if st.button("🔄 重新載入文章列表"):
        st.rerun()
        
    try:
        blog_files = repo.get_contents("blog")
        articles = [f for f in blog_files if f.name.endswith('.html') and f.name != '0_template.html']
        
        if not articles:
            st.info("目前沒有找到任何文章。")
        else:
            for article in articles:
                with st.expander(f"📄 {article.name}", expanded=False):
                    col_edit, col_del = st.columns([8, 2])
                    
                    with col_edit:
                        st.write(f"**檔案路徑：** `{article.path}`")
                    
                    with col_del:
                        if st.button("🗑️ 刪除文章", key=f"del_{article.name}"):
                            try:
                                repo.delete_file(article.path, f"Delete blog post: {article.name}", article.sha)
                                st.session_state["article_deleted"] = True
                                st.rerun()
                            except Exception as e:
                                st.error(f"刪除失敗: {e}")
                                
                    st.write("#### 編輯 HTML 原始碼")
                    file_content = article.decoded_content.decode("utf-8")
                    new_content = st.text_area("HTML 內容", value=file_content, height=400, key=f"edit_{article.name}")
                    
                    if st.button("💾 儲存變更", key=f"save_{article.name}"):
                        if new_content != file_content:
                            try:
                                repo.update_file(article.path, f"Update blog post: {article.name}", new_content, article.sha)
                                st.session_state["article_updated"] = True
                                st.rerun()
                            except Exception as e:
                                st.error(f"儲存失敗: {e}")
                        else:
                            st.info("內容沒有變動，無須儲存。")
                            
    except Exception as e:
        st.error(f"讀取 `/blog` 資料夾失敗: {e}")

# ==========================================
# 5. 管理側邊欄連結 (修改 run2fully.py)
# ==========================================
with tab2:
    st.subheader("首頁側邊欄連結管理")
    st.write("在這裡修改，會直接改寫 GitHub 上 `run2fully.py` 的程式碼。")
    
    if st.session_state.get("sidebar_updated"):
        st.success("✅ 側邊欄更新成功！")
        st.session_state["sidebar_updated"] = False
        
    if st.button("🔄 讀取最新連結列表"):
        st.rerun()
        
    try:
        run2fully_file = repo.get_contents("run2fully.py")
        run2fully_code = run2fully_file.decoded_content.decode("utf-8")
        
        # 尋找側邊欄的連結區塊：st.page_link("網址", label="標題", icon="圖示")
        pattern = r'st\.page_link\(\s*"(.*?)",\s*label="(.*?)",\s*icon="(.*?)"\s*\)'
        links = re.findall(pattern, run2fully_code)
        
        updated_links = []
        
        if links:
            st.write("**目前的連結：**")
            for i, link in enumerate(links):
                with st.expander(f"📌 {link[1].replace('**', '')} ({link[0].split('/')[-1]})", expanded=False):
                    c1, c2, c3 = st.columns([4, 3, 1])
                    with c1:
                        new_url = st.text_input(f"網址", value=link[0], key=f"url_{i}")
                    with c2:
                        new_label = st.text_input(f"標題", value=link[1], key=f"label_{i}")
                    with c3:
                        new_icon = st.text_input(f"Icon", value=link[2], key=f"icon_{i}")
                    
                    delete = st.checkbox(f"❌ 刪除此連結", key=f"del_{i}")
                    
                    if not delete:
                        updated_links.append((new_url, new_label, new_icon))
        else:
            st.info("目前沒有找到任何連結。")
            
        st.markdown("---")
        st.write("**➕ 新增連結：**")
        c1, c2, c3 = st.columns([4, 3, 1])
        with c1:
            add_url = st.text_input("新網址", placeholder="https://www.run2fully.com/blog/xxx.html", key="add_url")
        with c2:
            add_label = st.text_input("新標題", placeholder="**我是標題**", key="add_label")
        with c3:
            add_icon = st.text_input("新 Icon", placeholder="☝️", key="add_icon")
            
        if add_url and add_label:
            if not add_icon:
                add_icon = "📄"
            updated_links.append((add_url, add_label, add_icon))
            st.success("上方已暫存您的新連結！請點擊下方儲存按鈕將其寫入 GitHub。")
            
        if st.button("💾 儲存並更新至 GitHub", type="primary"):
            with st.spinner("正在更新 run2fully.py..."):
                # 建立新的程式碼區段
                new_code_lines = []
                for url, label, icon in updated_links:
                    new_code_lines.append(f'     st.page_link("{url}", label="{label}", icon="{icon}")')
                new_lines_str = "\n".join(new_code_lines)
                
                # 尋找替換插入點
                start_marker = "# 這是連結到您已準備好的靜態 HTML 文章\n"
                
                if start_marker in run2fully_code:
                    parts = run2fully_code.split(start_marker)
                    front = parts[0] + start_marker
                    back_part = parts[1]
                    
                    # 過濾掉原本的 st.page_link，直到遇到非 st.page_link 或空行為止
                    back_lines = back_part.split("\n")
                    filtered_back_lines = []
                    for line in back_lines:
                        if "st.page_link" in line and 'icon=' in line:
                            continue
                        filtered_back_lines.append(line)
                        
                    new_run2fully_code = front + new_lines_str + "\n" + "\n".join(filtered_back_lines)
                    
                    try:
                        repo.update_file("run2fully.py", "Admin: Update sidebar links", new_run2fully_code, run2fully_file.sha)
                        # 清空輸入框狀態
                        for k in ["add_url", "add_label", "add_icon"]:
                            if k in st.session_state:
                                st.session_state[k] = ""
                        st.session_state["sidebar_updated"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新失敗: {e}")
                else:
                    st.error("更新失敗：在程式碼中找不到插入點註解 `# 這是連結到您已準備好的靜態 HTML 文章`")
            
    except Exception as e:
        st.error(f"讀取 `run2fully.py` 失敗: {e}")
