import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import base64
import json

# 頁面基本設定
st.set_page_config(
    page_title="Run2Fully ETF複利計算機",
    page_icon="https://www.run2fully.com/assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 解析網址參數
if hasattr(st, "query_params"):
    query_params = st.query_params
else:
    query_params = st.experimental_get_query_params()

import zlib

default_state = {}
if "data" in query_params:
    try:
        data_val = query_params["data"]
        if isinstance(data_val, list):
            data_val = data_val[0]
        decoded = base64.urlsafe_b64decode(data_val)
        try:
            decompressed = zlib.decompress(decoded)
            data_str = decompressed.decode('utf-8')
        except zlib.error:
            data_str = decoded.decode('utf-8')
        default_state = json.loads(data_str)
    except Exception as e:
        pass

def get_default(key, fallback):
    val = default_state.get(key, fallback)
    if isinstance(fallback, int):
        return int(val)
    elif isinstance(fallback, float):
        return float(val)
    return val

st.title("Run2Fully ETF複利計算機")
st.markdown("採用長期平均回報率，模擬多種投資配置及風險情境，計算資產的增長軌跡，並提供退休提領試算。\n\n*網站內容僅為數據推導，不構成投資建議。")
st.image("assets/banner.jpg")
st.markdown(
    """
    <style>
    /* 隱藏圖表工具列 */
    [data-testid="stElementToolbar"] {
        display: none !important;
    }
    
    /* 調整側邊選單寬度，減少頂部間距 */
    [data-testid="stSidebar"] {
        width: 280px;
        min-width: 280px;
        max-width: 280px;
    }
    .stSidebar [data-testid="stVerticalBlock"] {
        padding-top: 1rem !important;
    }

    /* 💡 新增：縮小圖片下方的區塊間距 */
    [data-testid="stImage"] {
        margin-bottom: -15px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# UI 介面設計：1. 基礎資金與時間 (主畫面)
# ==========================================
st.markdown("---")
st.subheader("⚙️ 1. 總投資年限")

col_y, col_m = st.columns(2)
with col_y:
    years = st.number_input("總投入時間 (年)", value=get_default('years', 20), step=1)
with col_m:
    months_offset = st.number_input("總投入時間 (月)", value=get_default('months_offset', 0), step=1)

total_months = int((years * 12) + months_offset)
st.info(f"總計計算月份：**{total_months}** 個月")

is_advanced = False
fee_rate = 0.0
income_tax_rate = 0.0
is_nhi = False
is_tax_fees = False

if total_months == 0:
    st.info("💡 **請在上方設定大於 0 的投入時間！**\n\n設定完畢後，複利模擬將即時啟動，為您演算終局財富曲線。")
    st.stop()

# ==========================================
# UI 介面設計：主畫面 配置模式選擇
# ==========================================
st.markdown("---")
st.subheader("📊 2. 投資標的與投入設定")
mode_options = ["單選投資標的", "複選投資組合"]
mode_idx = mode_options.index(get_default('mode', "單選投資標的")) if get_default('mode', "單選投資標的") in mode_options else 0
mode = st.radio("請選擇配置模式：", mode_options, index=mode_idx, horizontal=True)

config_data = []

# 各資產的波動率設定 (蒙地卡羅模擬)
vol_map = {
    "市值型ETF (如0050/VTI)": 0.15,
    "配息型ETF (如00878/SCHD)": 0.12,
    "債券型ETF (如00679B/BND)": 0.05,
    "市值型": 0.15,
    "配息型": 0.12,
    "債券型": 0.05
}

if mode == "單選投資標的":
    asset_type_options = ["市值型ETF (如0050/VTI)", "配息型ETF (如00878/SCHD)", "債券型ETF (如00679B/BND)"]
    asset_type_idx = asset_type_options.index(get_default('asset_type', asset_type_options[0])) if get_default('asset_type', asset_type_options[0]) in asset_type_options else 0
    asset_type = st.selectbox("選擇資產類型", asset_type_options, index=asset_type_idx)
    
    if asset_type == "市值型ETF (如0050/VTI)":
        def_g, def_y = 8.0, 3.0
    elif asset_type == "配息型ETF (如00878/SCHD)":
        def_g, def_y = 2.0, 6.5
    else:
        def_g, def_y = 0.5, 4.0
        
    col1, col2, col3 = st.columns(3)
    with col1:
        init_inv = st.number_input("單筆投入(元)", value=get_default('init_inv', 0), step=10000)
    with col2:
        monthly_inv = st.number_input("每月定額(元)", value=get_default('monthly_inv', 0), step=1000)
    with col3:
        monthly_g = st.number_input("逐年增加定額(元)；例如每年增加$500/月", value=get_default('monthly_g', 0), step=100)
        
    col4, col5, col6 = st.columns(3)
    with col4:
        g_rate = st.number_input("市值年增率(%)", value=get_default('g_rate', def_g), step=0.1)
    with col5:
        y_rate = st.number_input("年化配息率(%)", value=get_default('y_rate', def_y), step=0.1)
    with col6:
        st.markdown("<div style='padding-top: 35px;'></div>", unsafe_allow_html=True)
        is_reinvest = st.checkbox("配息再投入", value=get_default('is_reinvest', True))
        
    config_data.append({
        "type": asset_type, "init_inv": max(0.0, float(init_inv)), "monthly_inv": max(0.0, float(monthly_inv)), 
        "monthly_growth_rate": float(monthly_g), "growth": float(g_rate) / 100, "yield": float(y_rate) / 100, "reinvest": is_reinvest
    })

else:
    st.markdown("請分別設定各資產的投入金額與回報率（各資產獨立計算）：")
    
    assets_config = [
        {"name": "📈 市值型ETF (如0050/VTI)", "type": "市值型", "def_g": 8.0, "def_y": 3.0, "def_r": True},
        {"name": "💰 配息型ETF (如00878/SCHD)", "type": "配息型", "def_g": 2.0, "def_y": 6.5, "def_r": False},
        {"name": "🛡️ 債券型ETF (如00679B/BND)", "type": "債券型", "def_g": 0.5, "def_y": 4.0, "def_r": True}
    ]
    
    for i, ast in enumerate(assets_config):
        st.markdown(f"#### {ast['name']}")
        c1, c2, c3 = st.columns(3)
        with c1:
            i_inv = st.number_input("單筆投入(元)", value=get_default(f'i_inv_{i}', 0), step=10000, key=f"i_inv_{i}")
        with c2:
            m_inv = st.number_input("每月定額(元)", value=get_default(f'm_inv_{i}', 0), step=1000, key=f"m_inv_{i}")
        with c3:
            m_g = st.number_input("逐年增加定額(元)；例如每年增加$500/月", value=get_default(f'm_g_{i}', 0), step=100, key=f"m_g_{i}")
            
        c4, c5, c6 = st.columns(3)
        with c4:
            g_rate = st.number_input("市值年增率(%)", value=get_default(f'g_rate_{i}', ast['def_g']), step=0.1, key=f"g_{i}")
        with c5:
            y_rate = st.number_input("年化配息率(%)", value=get_default(f'y_rate_{i}', ast['def_y']), step=0.1, key=f"y_{i}")
        with c6:
            st.markdown("<div style='padding-top: 35px;'></div>", unsafe_allow_html=True)
            r_inv = st.checkbox("配息再投入", value=get_default(f'r_inv_{i}', ast['def_r']), key=f"r_{i}")
            
        config_data.append({
            "type": ast['type'], 
            "init_inv": max(0.0, float(i_inv)), 
            "monthly_inv": max(0.0, float(m_inv)), 
            "monthly_growth_rate": float(m_g), 
            "growth": float(g_rate) / 100, 
            "yield": float(y_rate) / 100, 
            "reinvest": r_inv
        })

# ==========================================
# 核心大腦：執行 1 ~ N 個月 確定性滾動運算
# ==========================================
total_init_investment = sum(cfg["init_inv"] for cfg in config_data)
total_capital_added = total_init_investment

assets_state = []
for cfg in config_data:
    assets_state.append({
        "current_market_value": cfg["init_inv"],
        "total_cash_withdrawn": 0.0,
        "cfg": cfg
    })

data_rows = []
global_total_cash_withdrawn = 0.0
global_current_market_value = total_init_investment

for m in range(1, total_months + 1):
    years_passed = (m - 1) // 12
    
    m_total_contrib = 0.0
    m_total_growth = 0.0
    m_total_reinvest = 0.0
    m_total_cashout = 0.0
    m_total_end_value = 0.0
    
    for ast in assets_state:
        cfg = ast["cfg"]
        m_contrib = max(0.0, cfg["monthly_inv"] + (cfg["monthly_growth_rate"] * years_passed))
        base_value = ast["current_market_value"] + m_contrib
        
        m_growth = base_value * (cfg["growth"] / 12)
        if cfg["reinvest"]:
            m_reinvest = base_value * (cfg["yield"] / 12)
            m_cashout = 0.0
        else:
            m_reinvest = 0.0
            m_cashout = base_value * (cfg["yield"] / 12)
            
        end_value = base_value + m_growth + m_reinvest
        
        ast["current_market_value"] = end_value
        ast["total_cash_withdrawn"] += m_cashout
        
        m_total_contrib += m_contrib
        m_total_growth += m_growth
        m_total_reinvest += m_reinvest
        m_total_cashout += m_cashout
        m_total_end_value += end_value
        
    total_capital_added += m_total_contrib
    global_total_cash_withdrawn += m_total_cashout
    global_current_market_value = m_total_end_value
    
    data_rows.append({
        "月份": m,
        "年": round(m / 12, 2),
        "帳戶起始金額": round(m_total_end_value - m_total_growth - m_total_reinvest - m_total_contrib),
        "本月定投金額": round(m_total_contrib),
        "當月市值上漲金額": round(m_total_growth),
        "期末帳戶總市值": round(m_total_end_value),
        "配息再投入": round(m_total_reinvest),
        "配息提領": round(m_total_cashout),
        "當月總配息": round(m_total_reinvest + m_total_cashout),
        "累積提領配息": round(global_total_cash_withdrawn)
    })

df = pd.DataFrame(data_rows)

# ==========================================
# UI 介面設計：最終累積戰果看板
# ==========================================
st.markdown("---")
st.subheader("🏆 3. 累積期終局戰果看板")

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(label="最終股票帳戶總市值", value=f"${round(global_current_market_value):,}")

with kpi2:
    st.metric(label="累積純領息提領現金總和", value=f"${round(global_total_cash_withdrawn):,}")

# 計算投報率 (ROI)
roi = ((global_current_market_value + global_total_cash_withdrawn - total_capital_added) / total_capital_added * 100) if total_capital_added > 0 else 0.0

with kpi3:
    st.metric(label="總投資報酬率 (含已領配息現金)", value=f"{roi:.2f}%")

st.info(f"💡 本次計畫總計投入本金總額：**${round(total_capital_added):,}** 元。")

# ==========================================
# UI 介面設計：蒙地卡羅隨機波動模擬器 (Monte Carlo)
# ==========================================
st.markdown("---")
st.subheader("🎲 4. 波動風險評估 (蒙地卡羅隨機路徑模擬)")
st.markdown("真實市場充斥波動與「順序風險」。本模組根據資產配置的年化波動度，在背景隨機生成250條股市波動路徑，助您評估悲觀、平均及樂觀情境。")

total_inv_per_asset = [cfg["init_inv"] + cfg["monthly_inv"] * total_months for cfg in config_data]
total_inv_sum = sum(total_inv_per_asset)

if total_inv_sum > 0:
    weights = [w / total_inv_sum for w in total_inv_per_asset]
else:
    weights = [1.0 / len(config_data)] * len(config_data)

portfolio_annual_return = sum((cfg["growth"] + cfg["yield"]) * w for cfg, w in zip(config_data, weights))
portfolio_volatility = sum(vol_map.get(cfg["type"], 0.1) * w for cfg, w in zip(config_data, weights))

st.markdown(f"💼 當前配置特徵值：預估長期加權年化總回報率 **`{portfolio_annual_return*100:.1f}%`**，預估長期年化波動度 **`{portfolio_volatility*100:.1f}%`**。")

np.random.seed(42)
num_simulations = 250
sim_results = np.zeros((total_months + 1, num_simulations))

for cfg in config_data:
    asset_sim_results = np.zeros((total_months + 1, num_simulations))
    asset_sim_results[0, :] = float(cfg["init_inv"])
    
    vol = vol_map.get(cfg["type"], 0.1)
    asset_return = cfg["growth"] + (cfg["yield"] if cfg["reinvest"] else 0.0)
    
    mu_m = (asset_return - 0.5 * (vol ** 2)) / 12
    sigma_m = vol / np.sqrt(12)
    
    random_returns = np.random.normal(loc=mu_m, scale=sigma_m, size=(total_months, num_simulations))
    simple_returns = np.exp(random_returns) - 1
    
    for m in range(1, total_months + 1):
        prev_vals = asset_sim_results[m - 1, :]
        years_passed = (m - 1) // 12
        m_contrib = max(0.0, cfg["monthly_inv"] + (cfg["monthly_growth_rate"] * years_passed))
        
        base_vals = prev_vals + m_contrib
        r = simple_returns[m - 1, :]
        
        end_vals = base_vals * (1 + r)
        end_vals = np.maximum(end_vals, 0.0)
        asset_sim_results[m, :] = end_vals
        
    sim_results += asset_sim_results
    
p10_mc_nominal = np.percentile(sim_results, 10, axis=1)
p50_mc_nominal = np.percentile(sim_results, 50, axis=1)
p90_mc_nominal = np.percentile(sim_results, 90, axis=1)

p10_mc = p10_mc_nominal.copy()
p50_mc = p50_mc_nominal.copy()
p90_mc = p90_mc_nominal.copy()

deterministic_path = np.zeros(total_months + 1)
deterministic_path[0] = float(total_init_investment)
deterministic_path[1:] = df["期末帳戶總市值"]
    
mc_chart_df = pd.DataFrame({
    "月份": list(range(0, total_months + 1)),
    "悲觀": p10_mc,
    "平均": p50_mc,
    "理想": deterministic_path,
    "樂觀": p90_mc
})
mc_chart_df["年"] = mc_chart_df["月份"] / 12
mc_melt = mc_chart_df.melt(id_vars=["年", "月份"], value_vars=["悲觀", "平均", "理想", "樂觀"], var_name="情境", value_name="市值")

mc_altair = alt.Chart(mc_melt).mark_line().encode(
    x=alt.X("年:Q", title="年", axis=alt.Axis(format="d")),
    y=alt.Y("市值:Q", title="市值", axis=alt.Axis(format=",d")),
    color=alt.Color("情境:N", sort=["悲觀", "平均", "理想", "樂觀"], legend=alt.Legend(title=None, orient="bottom")),
    tooltip=[alt.Tooltip("年:Q", title="年", format=".1f"), alt.Tooltip("情境:N", title="情境"), alt.Tooltip("市值:Q", title="市值", format=",.0f")]
).properties(height=400)
st.altair_chart(mc_altair, use_container_width=True)

col_mc1, col_mc2, col_mc3, col_mc4 = st.columns(4)
col_mc1.metric("悲觀市值 (10%最差情況)", f"${round(p10_mc[-1]):,}")
col_mc2.metric("中位數市值 (50%平均情況)", f"${round(p50_mc[-1]):,}")
col_mc3.metric("確定性均值 (理想情況)", f"${round(deterministic_path[-1]):,}")
col_mc4.metric("樂觀市值 (10%最好情況)", f"${round(p90_mc[-1]):,}")

# ==========================================
# UI 介面設計：退休提領期模擬 (Withdrawal Phase)
# ==========================================
st.markdown("---")
st.subheader("🍸 5. 退休提領期模擬 (永續提領率測算)")
st.markdown("當累積期結束後，資產即進入「提領期」。本模組負責模擬您開始每年提取生活費後，資產能否實現「永續活水」，還是會提前坐吃山空？\n\n*註：在提領期階段，資產的配息與資本利得已合併計算為總報酬。總報酬在扣除您設定的提領金額後，剩餘部分將自動滾入本金繼續計算。提領資金不分本金與配息，皆視為從總資產中提撥。*")

# 建立版面區塊
top_col1, top_col2 = st.columns(2)
st.markdown("<br>", unsafe_allow_html=True)
selectors_col1, selectors_col2 = st.columns(2)
st.markdown("<br>", unsafe_allow_html=True)

# 先在右上方 (top_col2) 放通膨開關，因為邏輯需要先取得變數
with top_col2:
    is_inflation = st.toggle("🎈 考慮通貨膨脹", value=get_default('is_inflation', False))
    if is_inflation:
        inflation_rate = st.number_input("預估年通貨膨脹率 (%)", min_value=0.0, max_value=10.0, value=get_default('inflation_rate', 2.0), step=0.1, key="retirement_inflation_rate")
    else:
        inflation_rate = 0.0

# 2. 提領期始本金來源 | 提領金額設定模式
with selectors_col1:
    rsf_options = ["確定性均值 (理想情況)", "悲觀市值 (10%最差情況)", "中位數市值 (50%平均情況)", "樂觀市值 (10%最好情況)"]
    rsf_idx = rsf_options.index(get_default('retirement_starting_fund_source', rsf_options[0])) if get_default('retirement_starting_fund_source', rsf_options[0]) in rsf_options else 0
    retirement_starting_fund_source = st.selectbox(
        "提領期起始本金來源", 
        rsf_options,
        index=rsf_idx,
        key="retirement_starting_fund_source_select"
    )

with selectors_col2:
    wm_options = ["4% 法則", "自訂金額 (自訂每月金額)"]
    wm_idx = wm_options.index(get_default('withdraw_mode', wm_options[0])) if get_default('withdraw_mode', wm_options[0]) in wm_options else 0
    withdraw_mode = st.radio(
        "提領金額設定模式", 
        wm_options, 
        index=wm_idx,
        horizontal=True
    )

# 邏輯計算
if retirement_starting_fund_source == "確定性均值 (理想情況)":
    retirement_starting_fund_nominal = global_current_market_value
    retirement_starting_fund_display = deterministic_path[-1]
elif retirement_starting_fund_source == "悲觀市值 (10%最差情況)":
    retirement_starting_fund_nominal = p10_mc_nominal[-1]
    retirement_starting_fund_display = p10_mc[-1]
elif retirement_starting_fund_source == "中位數市值 (50%平均情況)":
    retirement_starting_fund_nominal = p50_mc_nominal[-1]
    retirement_starting_fund_display = p50_mc[-1]
else:
    retirement_starting_fund_nominal = p90_mc_nominal[-1]
    retirement_starting_fund_display = p90_mc[-1]

retirement_starting_fund = retirement_starting_fund_nominal
real_starting = retirement_starting_fund_display / ((1 + inflation_rate/100)**(total_months/12)) if is_inflation else retirement_starting_fund_display

# 1. 提領起始本金 呈現 (放在左上方 top_col1)
with top_col1:
    if is_inflation:
        st.metric(
            label="提領期起始本金 (名目)", 
            value=f"${round(retirement_starting_fund_display):,}", 
            delta=f"折合今日購買力: ${round(real_starting):,}", 
            delta_color="off"
        )
    else:
        st.metric(label="提領期起始本金", value=f"${round(retirement_starting_fund_display):,}")

# 自訂提領金額輸入 (依賴於前面的本金計算)
with selectors_col2:
    if withdraw_mode == "4% 法則":
        withdraw_pct = 4.0
        initial_annual_withdrawal = retirement_starting_fund * 0.04
        initial_monthly_withdrawal = initial_annual_withdrawal / 12
        real_monthly = initial_monthly_withdrawal / ((1 + inflation_rate/100)**(total_months/12))
        real_annual = initial_annual_withdrawal / ((1 + inflation_rate/100)**(total_months/12))
        if is_inflation:
            withdrawal_desc = f"💡 **4% 法則預估：第一年每月名目提領 {round(initial_monthly_withdrawal):,} 元（折合今日購買力 {round(real_monthly):,} 元），全年名目提領 {round(initial_annual_withdrawal):,} 元。**"
        else:
            withdrawal_desc = f"💡 **4% 法則預估：第一年每月提領 {round(initial_monthly_withdrawal):,} 元，全年提領 {round(initial_annual_withdrawal):,} 元。**"
    else:
        default_custom_val = float(round((retirement_starting_fund * 0.04) / 12)) if retirement_starting_fund > 0 else 30000.0
        initial_monthly_withdrawal = st.number_input("自訂退休後第一年每月提領金額 (元)", min_value=0.0, value=get_default('initial_monthly_withdrawal', default_custom_val), step=1000.0)
        initial_annual_withdrawal = initial_monthly_withdrawal * 12
        withdraw_pct = (initial_annual_withdrawal / retirement_starting_fund * 100) if retirement_starting_fund > 0 else 0.0
        
        real_monthly = initial_monthly_withdrawal / ((1 + inflation_rate/100)**(total_months/12))
        
        if is_inflation:
            withdrawal_desc = f"💡 **自訂金額預估：第一年每月名目提領 {round(initial_monthly_withdrawal):,} 元（折合今日購買力 {round(real_monthly):,} 元），全年名目提領 {round(initial_annual_withdrawal):,} 元（名目年提領率為 {withdraw_pct:.2f}%）。**"
        else:
            withdrawal_desc = f"💡 **自訂金額預估：第一年每月提領 {round(initial_monthly_withdrawal):,} 元，全年提領 {round(initial_annual_withdrawal):,} 元（年提領率為 {withdraw_pct:.2f}%）。**"

is_withdraw_inflation = is_inflation

if retirement_starting_fund <= 0:
    st.warning("⚠️ **提領期起始本金為 0 元，無法進行退休提領模擬。**")
else:
    # --- Background Simulation (non-visual) ---
    max_months = 480  # 40年
    w_fund_nominal = retirement_starting_fund
    w_fund_real = retirement_starting_fund
    w_rows = []
    exhaust_month = -1
    total_withdrawn_nominal = 0.0
    
    final_balances = [ast["current_market_value"] for ast in assets_state]
    final_balances_sum = sum(final_balances)
    ret_weights = [b / final_balances_sum for b in final_balances] if final_balances_sum > 0 else weights
    blended_growth = sum(cfg["growth"] * w for cfg, w in zip(config_data, ret_weights))
    blended_yield = sum(cfg["yield"] * w for cfg, w in zip(config_data, ret_weights))

    is_mc_mode = retirement_starting_fund_source != "確定性均值 (理想情況)"

    if is_mc_mode:
        np.random.seed(42)
        blended_volatility = sum(vol_map.get(cfg["type"], 0.1) * w for cfg, w in zip(config_data, ret_weights))
        blended_return = blended_growth + blended_yield
        mu_m = (blended_return - 0.5 * (blended_volatility ** 2)) / 12
        sigma_m = blended_volatility / np.sqrt(12)
        random_returns = np.random.normal(loc=mu_m, scale=sigma_m, size=(max_months, num_simulations))
        simple_returns = np.exp(random_returns) - 1
        
        sim_w_results = np.zeros((max_months + 1, num_simulations))
        sim_w_results[0, :] = retirement_starting_fund
        sim_w_cum_withdrawals = np.zeros((max_months + 1, num_simulations))
        
        monthly_withdrawals = np.zeros(max_months)
        for wm in range(1, max_months + 1):
            w_year = (wm - 1) // 12
            if is_withdraw_inflation:
                monthly_withdrawals[wm-1] = initial_monthly_withdrawal * ((1 + inflation_rate / 100) ** w_year)
            else:
                monthly_withdrawals[wm-1] = initial_monthly_withdrawal

        for wm in range(1, max_months + 1):
            prev_vals = sim_w_results[wm - 1, :]
            current_w = monthly_withdrawals[wm-1]
            actual_w = np.minimum(prev_vals, current_w)
            after_w = prev_vals - actual_w
            
            r = simple_returns[wm - 1, :]
            end_vals = after_w * (1 + r)
            end_vals = np.maximum(end_vals, 0.0)
            
            sim_w_results[wm, :] = end_vals
            sim_w_cum_withdrawals[wm, :] = sim_w_cum_withdrawals[wm - 1, :] + actual_w
            
        if retirement_starting_fund_source == "悲觀市值 (10%最差情況)":
            chosen_path = np.percentile(sim_w_results, 10, axis=1)
            chosen_cum_w = np.percentile(sim_w_cum_withdrawals, 10, axis=1)
        elif retirement_starting_fund_source == "中位數市值 (50%平均情況)":
            chosen_path = np.percentile(sim_w_results, 50, axis=1)
            chosen_cum_w = np.percentile(sim_w_cum_withdrawals, 50, axis=1)
        else:
            chosen_path = np.percentile(sim_w_results, 90, axis=1)
            chosen_cum_w = np.percentile(sim_w_cum_withdrawals, 90, axis=1)
            
        for wm in range(1, max_months + 1):
            w_fund_nominal_end = chosen_path[wm]
            cum_w = chosen_cum_w[wm]
            actual_w = cum_w - chosen_cum_w[wm-1]
            
            if chosen_path[wm-1] <= 0.01 and actual_w <= 0.01:
                if exhaust_month == -1:
                    exhaust_month = wm - 1
                break
            
            discount_factor = (1 + inflation_rate / 100) ** (wm / 12) if is_inflation else 1.0
            w_fund_real_end = w_fund_nominal_end / discount_factor
            
            w_rows.append({
                "月份": wm,
                "年": round(wm / 12, 2),
                "帳戶餘額_名目": round(w_fund_nominal_end),
                "帳戶餘額_實質": round(w_fund_real_end),
                "當月實際提取生活費": round(actual_w),
                "累積提領金額(名目)": round(cum_w),
                "累積提領金額(實質購買力)": round(cum_w / discount_factor)
            })
            
        w_fund_nominal = w_rows[-1]["帳戶餘額_名目"] if w_rows else 0.0
        w_fund_real = w_rows[-1]["帳戶餘額_實質"] if w_rows else 0.0
        total_withdrawn_nominal = w_rows[-1]["累積提領金額(名目)"] if w_rows else 0.0
        
    else:
        for wm in range(1, max_months + 1):
            w_year = (wm - 1) // 12
            if is_withdraw_inflation:
                current_monthly_withdrawal = initial_monthly_withdrawal * ((1 + inflation_rate / 100) ** w_year)
            else:
                current_monthly_withdrawal = initial_monthly_withdrawal
                
            if w_fund_nominal <= 0:
                exhaust_month = wm - 1
                break
                
            current_monthly_withdrawal_actual = min(w_fund_nominal, current_monthly_withdrawal)
            total_withdrawn_nominal += current_monthly_withdrawal_actual
            
            m_growth = w_fund_nominal * (blended_growth / 12)
            m_dividend = w_fund_nominal * (blended_yield / 12)
            
            excess_dividend = m_dividend - current_monthly_withdrawal_actual
            net_change = m_growth + excess_dividend
            
            w_fund_nominal_end = max(0.0, w_fund_nominal + net_change)
            
            discount_factor = (1 + inflation_rate / 100) ** (wm / 12) if is_inflation else 1.0
            w_fund_real_end = w_fund_nominal_end / discount_factor
            
            w_rows.append({
                "月份": wm,
                "年": round(wm / 12, 2),
                "帳戶餘額_名目": round(w_fund_nominal_end),
                "帳戶餘額_實質": round(w_fund_real_end),
                "當月實際提取生活費": round(current_monthly_withdrawal_actual),
                "累積提領金額(名目)": round(total_withdrawn_nominal),
                "累積提領金額(實質購買力)": round(total_withdrawn_nominal / discount_factor)
            })
            
            w_fund_nominal = w_fund_nominal_end
            w_fund_real = w_fund_real_end
            
    w_df = pd.DataFrame(w_rows)
    
    # Calculate simulation result text
    portfolio_return_pct = portfolio_annual_return * 100
    if exhaust_month != -1:
        exhaust_year = exhaust_month // 12
        exhaust_m_rem = exhaust_month % 12
        if withdraw_mode == "4% 法則":
            sim_result_text = f"🚨 **退休提領模擬分析 (警示)：**\n\n您的帳戶資金預計在第 **{exhaust_year} 年又 {exhaust_m_rem} 個月** (第 {exhaust_month} 個月) 宣告枯竭。\n\n期間累計提取生活費總額：**{round(total_withdrawn_nominal):,}** 元。"
        else:
            sim_result_text = f"🚨 **模擬結果 - 警報：您的自訂提領計畫將會乾涸！**\n\n財務水庫預計僅可支應 **{exhaust_year} 年又 {exhaust_m_rem} 個月** (即模擬第 {exhaust_month} 個月) 即告乾涸！\n\n期間共支應了生活費 **{round(total_withdrawn_nominal):,}** 元。"
    else:
        # 當模擬成功時，如果提領率過高，在成功訊息後加上提醒
        ideal_note = ""
        if withdraw_pct > 5.0:
            ideal_note = (
                f"\n\n🚨 **重要提醒：此永續結果是建立在「每年穩定獲利 {portfolio_return_pct:.1f}%、完全無波動」的理想前提下！** "
                f"由於您設定的提領率 ({withdraw_pct:.2f}%) 偏高，在現實市場的真實波動與「順序風險」下，"
                f"資產極可能提早乾涸，此結果僅供理想模型下的對照參考，請勿以此做為唯一的真實退休規劃依據！"
            )
        if is_inflation:
            balance_desc = f"您的股票帳戶名目餘額仍剩餘 **{round(w_fund_nominal):,}** 元 (實質購買力折現後為 **{round(w_fund_real):,}** 元)"
        else:
            balance_desc = f"您的股票帳戶餘額仍剩餘 **{round(w_fund_nominal):,}** 元 (不考慮通膨影響)"
            
        if withdraw_mode == "4% 法則":
            sim_result_text = (
                f"🟢 **退休提領模擬分析：**\n\n"
                f"在當前設定下，資產可永續支應 **40 年以上**（未出現乾涸狀況）。\n"
                f"在模擬第 40 年底，{balance_desc}。\n"
                f"模擬期間累計提取生活費總額：**{round(total_withdrawn_nominal):,}** 元。"
                f"{ideal_note}"
            )
        else:
            sim_result_text = (
                f"🎉 **模擬結果 - 恭喜！您的自訂退休提領計畫極其穩健！**\n\n"
                f"您的自訂生活費支應計畫可永續支應 **40 年以上**！在模擬第 40 年底，{balance_desc}。\n"
                f"一路上成功支應了您設定的退休生活開銷，累計提領：**{round(total_withdrawn_nominal):,}** 元！"
                f"{ideal_note}"
            )

    # --- Render integrated box FIRST (directly below buttons, as pointed by arrow) ---
    integrated_msg = f"{withdrawal_desc}\n\n---\n\n{sim_result_text}"
    
    if exhaust_month != -1:
        st.error(integrated_msg)
    elif withdraw_pct <= 5.0:
        st.success(integrated_msg)
    elif withdraw_pct <= 8.0:
        st.warning(integrated_msg)
    else:
        st.error(integrated_msg)

    # --- Render safety assessment warnings SECOND (below integrated box) ---
    # 提領率安全評估與警示系統
    st.markdown("### ⚠️ 提領率安全度評估示警")
    if withdraw_pct > 8.0:
        st.error(
            f"🚨 **極高風險警報：自訂年提領率達 {withdraw_pct:.2f}%！**\n\n"
            f"**此為理想狀態的對照值**。目前設定的長期加權年化總回報率為 **{portfolio_return_pct:.1f}%**，因此在數學模擬上顯示為「安全或資產上升」。\n\n"
            f"⚠️ **但請務必注意**：在真實的金融市場中，股市存在劇烈的波動與 **「順序風險」**。在提領期，若在退休前幾年不幸遭遇市場下跌，即使長期平均回報率有 {portfolio_return_pct:.1f}%，您的資產也極可能在 10 ~ 15 年內徹底破產（坐吃山空）。學術界與業界公認的安全提領率上限為 **4% ~ 5%**，強烈建議您降低提領率或自訂每月提領金額，以策安全！"
        )
    elif withdraw_pct > 5.0:
        st.warning(
            f"⚠️ **高風險警示：自訂年提領率為 {withdraw_pct:.2f}% (已超越安全警戒線)！**\n\n"
            f"此提領率在固定回報率 **{portfolio_return_pct:.1f}%** 的理想模擬下表現穩定，但這**並未計入真實市場的波動性**。\n\n"
            f"在現實中，若退休初期遇到市場熊市，即使長期平均回報率再高，也可能因為「前期提領過多、本金迅速萎縮」而導致資產無法翻身，最終提早耗盡。業界黃金法則通常為 **4%**，建議您審慎評估，或準備動態提領應變計畫。"
        )
    elif withdraw_pct > 4.0:
        st.info(
            f"💡 **溫馨提示：年提領率為 {withdraw_pct:.2f}%，處於中等風險區間。**\n\n"
            f"此比例接近經典的 **4% 法則**。在無波動的 `{portfolio_return_pct:.1f}%` 固定回報理想模式下非常安全，但在真實市場波動下，若遭遇極端熊市，仍存在約 10% ~ 20% 的機率在 30 年內耗盡資產。現實操作中，建議視市場行情動態調整提領金額。"
        )
    else:
        st.success(
            f"🟢 **安全區間：年提領率為 {withdraw_pct:.2f}%，符合安全提領標準！**\n\n"
            f"此提領率低於或等於經典的 **4% 法則**。歷史實證數據顯示，即使計入真實市場的百年歷史劇烈波動與多次金融危機，此提領率依然能保障 95% 以上的退休組合在 30 ~ 50 年內永不乾涸。這是一個非常穩健且極具參考意義的規劃！"
        )
        
    st.markdown("---")
    st.markdown("### 🔗 分享您的專屬試算參數")
    
    current_state = {
        'years': years,
        'months_offset': months_offset,
        'mode': mode,
        'is_inflation': is_inflation,
        'inflation_rate': inflation_rate,
        'retirement_starting_fund_source': retirement_starting_fund_source,
        'withdraw_mode': withdraw_mode,
    }
    if withdraw_mode != "4% 法則":
        current_state['initial_monthly_withdrawal'] = initial_monthly_withdrawal

    if mode == "單選投資標的":
        current_state.update({
            'asset_type': asset_type,
            'init_inv': init_inv,
            'monthly_inv': monthly_inv,
            'monthly_g': monthly_g,
            'g_rate': g_rate,
            'y_rate': y_rate,
            'is_reinvest': is_reinvest
        })
    else:
        for i in range(len(config_data)):
            current_state.update({
                f'i_inv_{i}': config_data[i]['init_inv'],
                f'm_inv_{i}': config_data[i]['monthly_inv'],
                f'm_g_{i}': config_data[i]['monthly_growth_rate'],
                f'g_rate_{i}': config_data[i]['growth'] * 100,
                f'y_rate_{i}': config_data[i]['yield'] * 100,
                f'r_inv_{i}': config_data[i]['reinvest']
            })

    json_str = json.dumps(current_state, separators=(',', ':'))
    compressed = zlib.compress(json_str.encode('utf-8'))
    b64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    if hasattr(st, "query_params"):
        st.query_params["data"] = b64_str
    else:
        st.experimental_set_query_params(data=b64_str)
        
    share_url = f"https://app.run2fully.com/?data={b64_str}"
    
    @st.cache_data(show_spinner=False)
    def get_short_url(long_url):
        import urllib.request
        import urllib.parse
        try:
            api_url = "https://tinyurl.com/api-create.php?url=" + urllib.parse.quote(long_url)
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.read().decode('utf-8')
        except Exception:
            return long_url

    short_url = get_short_url(share_url)
    
    html_code = f"""
    <script>
    function copyToClipboard() {{
        var dummy = document.createElement('input'), text = "{short_url}";
        document.body.appendChild(dummy);
        dummy.value = text;
        dummy.select();
        document.execCommand('copy');
        document.body.removeChild(dummy);
        
        var msg = document.getElementById('copy-msg');
        msg.style.display = 'inline';
        setTimeout(function() {{ msg.style.display = 'none'; }}, 2000);
    }}
    </script>
    <button onclick="copyToClipboard()" style="padding: 10px 20px; font-size: 16px; background-color: #0068c9; color: white; border: none; border-radius: 5px; cursor: pointer; transition: 0.3s;" onmouseover="this.style.backgroundColor='#0054a3'" onmouseout="this.style.backgroundColor='#0068c9'">
        📋 點擊複製分享網址
    </button>
    <span id="copy-msg" style="display: none; color: #0068c9; margin-left: 10px; font-weight: bold;">✅ 網址已複製！</span>
    """
    st.components.v1.html(html_code, height=60)

# ==========================================
# UI 介面設計：詳細月份數據表與下載
# ==========================================
st.markdown("---")
st.subheader("📅 詳細月份動態流向大表")
st.dataframe(df.drop(columns=["年"]), use_container_width=True, hide_index=True)

# 財富成長幾何曲線
st.markdown("---")
st.subheader("📈 累積期財富幾何成長曲線")
area_chart_df = df.copy()
area_chart_df = area_chart_df.rename(columns={
    "期末帳戶總市值": "總市值",
    "累積提領現金": "累積提領"
})
if "累積提領" in area_chart_df.columns:
    area_melt = area_chart_df.melt(id_vars=["年"], value_vars=["總市值", "累積提領"], var_name="項目", value_name="金額")
else:
    area_melt = area_chart_df.melt(id_vars=["年"], value_vars=["總市值"], var_name="項目", value_name="金額")

area_altair = alt.Chart(area_melt).mark_area(opacity=0.5).encode(
    x=alt.X("年:Q", title="年", axis=alt.Axis(format="d")),
    y=alt.Y("金額:Q", title="金額", axis=alt.Axis(format=",d")),
    color=alt.Color("項目:N", sort=["總市值", "累積提領"], legend=alt.Legend(title=None, orient="bottom")),
    tooltip=[alt.Tooltip("年:Q", title="年", format=".1f"), alt.Tooltip("項目:N", title="項目"), alt.Tooltip("金額:Q", title="金額", format=",.0f")]
).properties(height=400)
st.altair_chart(area_altair, use_container_width=True)


# --- 側邊欄導航 ---
with st.sidebar:
     st.markdown("<h3 style='margin-top: -20px;'><strong>📚 Run2Fully 投資雜談</strong></h3>", unsafe_allow_html=True)
     st.markdown("---")
    
    # 這是連結到您已準備好的靜態 HTML 文章
     st.page_link("https://www.run2fully.com/blog/compound.html", label="**寫在開始追尋複利之前...**", icon="☝️")
     st.page_link("https://www.run2fully.com/blog/turnzero.html", label="**炒股！等著「賠光光」？**", icon="☝️")
     st.page_link("https://www.run2fully.com/blog/four_percent.html", label="**規劃你的4%永續提領**", icon="🔥")
     st.page_link("https://www.run2fully.com/blog/active_race.html", label="**少年不知「被動」好？**", icon="☝️")
     st.page_link("https://www.run2fully.com/blog/why_high_div.html", label="**到底該不該買高股息？**", icon="🔥")




st.markdown("---")
st.caption("© 2026 [Run2Fully](mailto:butw.ec@gmail.com) | All rights reserved.")
