import streamlit as st
import pandas as pd
import numpy as np

# 頁面基本設定
st.set_page_config(page_title="Run2Fully多資產複利計算機", layout="wide")

st.title("Run2Fully多資產複利計算機")
st.markdown("本系統採用長期平均回報率，精確模擬投資在本金與配息再投入下的增長軌跡。")

# ==========================================
# UI 介面設計：側邊欄 (Sidebar) 參數設定
# ==========================================
st.sidebar.header("⚙️ 1. 基礎資金與時間")
init_investment = st.sidebar.number_input("單筆投入金額 (元)", min_value=0, value=100000, step=10000)
monthly_investment = st.sidebar.number_input("每月定期定額 (元)", min_value=0, value=10000, step=1000)
contrib_growth_rate = st.sidebar.number_input("定期定額每年成長率 (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.5)

col_y, col_m = st.sidebar.columns(2)
with col_y:
    years = st.sidebar.number_input("總投入時間 (年)", min_value=0, max_value=100, value=20, step=1)
with col_m:
    months_offset = st.sidebar.number_input("總投入時間 (月)", min_value=0, max_value=11, value=0, step=1)

total_months = (years * 12) + months_offset
st.sidebar.info(f"總計計算月份：**{total_months}** 個月")

is_advanced = False
fee_rate = 0.0
income_tax_rate = 0.0
is_nhi = False
is_tax_fees = False

# 時間防呆
if total_months == 0:
    st.info("💡 **請在左側邊欄設定大於 0 的投入時間！**\n\n設定完畢後，複利模擬大腦將即時啟動，為您演算終局財富曲線，奔向複利。")
    st.stop()

# ==========================================
# UI 介面設計：主畫面 配置模式選擇
# ==========================================
st.markdown("---")
st.subheader("📊 2. 投資標的與回報率設定")
mode = st.radio("請選擇配置模式：", ["單選投資標的", "複選投資組合 (自訂權重)"], horizontal=True)

config_data = []

# 各資產的波動率設定 (進階蒙地卡羅用)
vol_map = {
    "市值型股票 (如 0050/VTI)": 0.15,
    "配息型股票 (如 00878/高股息)": 0.12,
    "債券型資產": 0.05,
    "市值型": 0.15,
    "配息型": 0.12,
    "債券型": 0.05
}

if mode == "單選投資標的":
    asset_type = st.selectbox("選擇資產類型", ["市值型股票 (如 0050/VTI)", "配息型股票 (如 00878/高股息)", "債券型資產"])
    
    # 根據選取類型給予不同的預設長期平均值
    if asset_type == "市值型股票 (如 0050/VTI)":
        def_g, def_y = 8.0, 3.0
    elif asset_type == "配息型股票 (如 00878/高股息)":
        def_g, def_y = 2.0, 6.5
    else:
        def_g, def_y = 0.5, 4.0
        
    col1, col2, col3 = st.columns(3)
    with col1:
        g_rate = st.number_input("長期平均純市值年化增長率 (%)", value=def_g, step=0.1)
    with col2:
        y_rate = st.number_input("長期平均年化配息率 (%)", value=def_y, step=0.1)
    with col3:
        st.markdown("<div style='padding-top: 35px;'></div>", unsafe_allow_html=True)
        is_reinvest = st.checkbox("配息是否再投入", value=True)
        
    config_data.append({
        "type": asset_type, "weight": 100.0, "growth": g_rate / 100, "yield": y_rate / 100, "reinvest": is_reinvest
    })
    st.success("單選標的配置成功 (權重自動為 100%)")

else:
    st.markdown("請設定各資產的長期回報率與權重（總和必須等於 100%）：")
    
    # 建立表頭
    h_type, h_w, h_g, h_y, h_r = st.columns([2, 1.2, 2.5, 2.5, 1])
    h_type.markdown("**資產類型**")
    h_w.markdown("**權重 %**")
    h_g.markdown("**純市值年化增長率 (%)**")
    h_y.markdown("**年化配息率 (%)**")
    h_r.markdown("**再投入**")
    
    # 建立第一列：市值型
    r1_type, r1_w, r1_g, r1_y, r1_r = st.columns([2, 1.2, 2.5, 2.5, 1])
    r1_type.markdown("📈 市值型股票 (如 0050)")
    w_m = r1_w.number_input("權重1", min_value=0, max_value=100, value=40, step=5, label_visibility="collapsed")
    g_m = r1_g.number_input("增長1", value=8.0, step=0.1, label_visibility="collapsed")
    y_m = r1_y.number_input("配息1", value=3.0, step=0.1, label_visibility="collapsed")
    r_m = r1_r.checkbox("再投入1", value=True, label_visibility="collapsed")
    
    # 建立第二列：配息型
    r2_type, r2_w, r2_g, r2_y, r2_r = st.columns([2, 1.2, 2.5, 2.5, 1])
    r2_type.markdown("💰 配息型股票 (如 00878)")
    w_d = r2_w.number_input("權重2", min_value=0, max_value=100, value=40, step=5, label_visibility="collapsed")
    g_d = r2_g.number_input("增長2", value=2.0, step=0.1, label_visibility="collapsed")
    y_d = r2_y.number_input("配息2", value=6.5, step=0.1, label_visibility="collapsed")
    r_d = r2_r.checkbox("再投入2", value=False, label_visibility="collapsed")
    
    # 建立第三列：債券型
    r3_type, r3_w, r3_g, r3_y, r3_r = st.columns([2, 1.2, 2.5, 2.5, 1])
    r3_type.markdown("🛡️ 債券型資產")
    w_b = r3_w.number_input("權重3", min_value=0, max_value=100, value=20, step=5, label_visibility="collapsed")
    g_b = r3_g.number_input("增長3", value=0.5, step=0.1, label_visibility="collapsed")
    y_b = r3_y.number_input("配息3", value=4.0, step=0.1, label_visibility="collapsed")
    r_b = r3_r.checkbox("再投入3", value=True, label_visibility="collapsed")

    total_weight = w_m + w_d + w_b
    if total_weight != 100:
        st.error(f"❌ 目前權重總和為 {total_weight}%。總額必須剛好等於 100% 才能啟動計算。")
        st.stop()
    else:
        st.success("✅ 權重檢查通過 (剛好 100%)")
        
    # 封裝複選數據
    config_data.append({"type": "市值型", "weight": w_m, "growth": g_m/100, "yield": y_m/100, "reinvest": r_m})
    config_data.append({"type": "配息型", "weight": w_d, "growth": g_d/100, "yield": y_d/100, "reinvest": r_d})
    config_data.append({"type": "債券型", "weight": w_b, "growth": g_b/100, "yield": y_b/100, "reinvest": r_b})

# ==========================================
# 核心大腦：計算「加權複利因子」
# ==========================================
final_growth_factor = sum(row["growth"] * (row["weight"] / 100) for row in config_data)
final_reinvest_yield_factor = sum(row["yield"] * (row["weight"] / 100) for row in config_data if row["reinvest"])
final_cashout_yield_factor = sum(row["yield"] * (row["weight"] / 100) for row in config_data if not row["reinvest"])
final_yield_factor = final_reinvest_yield_factor + final_cashout_yield_factor

# ==========================================
# 核心大腦：執行 1 ~ N 個月 確定性滾動運算
# ==========================================
data_rows = []
current_market_value = float(init_investment)
total_cash_withdrawn = 0.0

for m in range(1, total_months + 1):
    years_passed = (m - 1) // 12
    m_contribution = monthly_investment * ((1 + contrib_growth_rate / 100) ** years_passed)
    
    # 手續費與稅費均為 0
    buy_fee = 0.0
    net_contribution = m_contribution
    
    base_value = current_market_value + net_contribution
    m_growth = base_value * (final_growth_factor / 12)
    
    m_div_reinvest_net = base_value * (final_reinvest_yield_factor / 12)
    m_div_cashout_net = base_value * (final_cashout_yield_factor / 12)
    
    tax_deduction = 0.0
    nhi_deduction = 0.0
    reinvest_fee = 0.0
    
    end_market_value = base_value + m_growth + m_div_reinvest_net
    total_cash_withdrawn += m_div_cashout_net
    
    if is_advanced:
        data_rows.append({
            "月份": m,
            "起始市值": round(current_market_value),
            "本月投入": round(m_contribution),
            "市值增長": round(m_growth),
            "配息再投入": round(m_div_reinvest_net),
            "配息提領現金": round(m_div_cashout_net),
            "期末帳戶總市值": round(end_market_value),
            "當月總配息": round(m_div_reinvest_net + m_div_cashout_net),
            "累積提領現金": round(total_cash_withdrawn)
        })
    else:
        data_rows.append({
            "月份": m,
            "帳戶起始金額": round(current_market_value),
            "本月定期定額投入": round(m_contribution),
            "當月市值上漲金額": round(m_growth),
            "配息再投入滾利": round(m_div_reinvest_net),
            "配息提領拿走": round(m_div_cashout_net),
            "期末帳戶總市值": round(end_market_value),
            "當月可領配息(折合月領)": round(m_div_reinvest_net + m_div_cashout_net)
        })
    
    current_market_value = end_market_value

df = pd.DataFrame(data_rows)

# ==========================================
# UI 介面設計：最終累積戰果看板
# ==========================================
st.markdown("---")
st.subheader("🏆 3. 累積期終局戰果看板")

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(label="最終股票帳戶總市值", value=f"${round(current_market_value):,}")

with kpi2:
    st.metric(label="累積純領息提領現金總和", value=f"${round(total_cash_withdrawn):,}")

# 計算投報率 (ROI)
total_capital = float(init_investment) + df["本月投入" if is_advanced else "本月定期定額投入"].sum()
roi = ((current_market_value + total_cash_withdrawn - total_capital) / total_capital * 100) if total_capital > 0 else 0.0

with kpi3:
    st.metric(label="總投資報酬率 (含已拿走現金)", value=f"{roi:.2f}%")

st.info(f"💡 本次計畫總計投入本金總額：**${round(total_capital):,}** 元。")

# ==========================================
# UI 介面設計：蒙地卡羅隨機波動模擬器 (Monte Carlo)
# ==========================================
st.markdown("---")
st.subheader("🎲 4. 隨機波動風險評估 (蒙地卡羅隨機路徑模擬)")
st.markdown("真實市場充斥波動與「順序風險（Sequence of Returns Risk）」。本模組根據資產配置的年化波動度，在背景隨機生成 **250 條** 股市波動路徑，助您評估悲觀、平均及樂觀情境。")

portfolio_annual_return = sum((row["growth"] + row["yield"]) * (row["weight"] / 100) for row in config_data)
portfolio_volatility = sum(vol_map[row["type"]] * (row["weight"] / 100) for row in config_data)

st.markdown(f"💼 當前配置特徵值：預估長期加權年化總回報率 **`{portfolio_annual_return*100:.1f}%`**，預估長期年化波動度 **`{portfolio_volatility*100:.1f}%`**。")

is_mc_real = False

np.random.seed(42)
num_simulations = 250
sim_results = np.zeros((total_months + 1, num_simulations))
sim_results[0, :] = float(init_investment)

mu_m = (portfolio_annual_return - 0.5 * (portfolio_volatility ** 2)) / 12
sigma_m = portfolio_volatility / np.sqrt(12)

random_returns = np.random.normal(loc=mu_m, scale=sigma_m, size=(total_months, num_simulations))
simple_returns = np.exp(random_returns) - 1

total_rate = final_growth_factor + final_reinvest_yield_factor + final_cashout_yield_factor
stay_ratio = (final_growth_factor + final_reinvest_yield_factor) / total_rate if total_rate > 0 else 1.0

for m in range(1, total_months + 1):
    prev_vals = sim_results[m - 1, :]
    years_passed = (m - 1) // 12
    m_contrib = monthly_investment * ((1 + contrib_growth_rate / 100) ** years_passed)
    net_contrib = m_contrib
    
    base_vals = prev_vals + net_contrib
    r = simple_returns[m - 1, :]
    
    account_r = r * stay_ratio
    end_vals = base_vals * (1 + account_r)
    end_vals = np.maximum(end_vals, 0.0)
    sim_results[m, :] = end_vals
    
# Extract nominal percentiles (important for starting capital in retirement phase)
p10_mc_nominal = np.percentile(sim_results, 10, axis=1)
p50_mc_nominal = np.percentile(sim_results, 50, axis=1)
p90_mc_nominal = np.percentile(sim_results, 90, axis=1)

p10_mc = p10_mc_nominal.copy()
p50_mc = p50_mc_nominal.copy()
p90_mc = p90_mc_nominal.copy()

# Add Deterministic Mean to the Monte Carlo comparison
deterministic_path = np.zeros(total_months + 1)
deterministic_path[0] = float(init_investment)
deterministic_path[1:] = df["期末帳戶總市值"]
    
mc_chart_df = pd.DataFrame({
    "月份": list(range(0, total_months + 1)),
    "悲觀情況 (後 10% 分位數)": p10_mc,
    "中位數情況 (50% 分位數)": p50_mc,
    "確定性均值 (理想狀態)": deterministic_path,
    "樂觀情況 (前 10% 分位數)": p90_mc
}).set_index("月份")

st.line_chart(mc_chart_df)

col_mc1, col_mc2, col_mc3, col_mc4 = st.columns(4)
col_mc1.metric("悲觀情況下股票市值 (P10)", f"${round(p10_mc[-1]):,}")
col_mc2.metric("中位數情況下股票市值 (P50)", f"${round(p50_mc[-1]):,}")
col_mc3.metric("確定性均值下股票市值 (理想)", f"${round(deterministic_path[-1]):,}")
col_mc4.metric("樂觀情況下股票市值 (P90)", f"${round(p90_mc[-1]):,}")

# ==========================================
# UI 介面設計：退休提領期模擬 (Withdrawal Phase)
# ==========================================
st.markdown("---")
st.subheader("🍸 5. 退休提領期模擬 (永續提領率測算)")
st.markdown("當累積期結束後，資產即進入**「提領期 (Decumulation Phase)」**。本模組模擬您開始每年提取生活費，資產能否實現「永續活水」，還是會提前坐吃山空？")

# 建立版面區塊
top_col1, top_col2 = st.columns(2)
st.markdown("<br>", unsafe_allow_html=True)
selectors_col1, selectors_col2 = st.columns(2)
st.markdown("<br>", unsafe_allow_html=True)

# 先在右上方 (top_col2) 放通膨開關，因為邏輯需要先取得變數
with top_col2:
    is_inflation = st.toggle("🎈 考慮通貨膨脹", value=False)
    if is_inflation:
        inflation_rate = st.number_input("預估年通貨膨脹率 (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1, key="retirement_inflation_rate")
    else:
        inflation_rate = 0.0

# 2. 提領期始本金來源 | 提領金額設定模式
with selectors_col1:
    retirement_starting_fund_source = st.selectbox(
        "提領期起始本金來源", 
        ["確定性均值 (理想狀態)", "蒙地卡羅 - 悲觀情況 (P10)", "蒙地卡羅 - 中位數情況 (P50)", "蒙地卡羅 - 樂觀情況 (P90)"],
        key="retirement_starting_fund_source_select"
    )

with selectors_col2:
    withdraw_mode = st.radio(
        "提領金額設定模式", 
        ["4% 法則", "自訂金額 (自訂每月金額)"], 
        horizontal=True
    )

# 邏輯計算
if retirement_starting_fund_source == "確定性均值 (理想狀態)":
    retirement_starting_fund_nominal = current_market_value
    retirement_starting_fund_display = deterministic_path[-1]
elif retirement_starting_fund_source == "蒙地卡羅 - 悲觀情況 (P10)":
    retirement_starting_fund_nominal = p10_mc_nominal[-1]
    retirement_starting_fund_display = p10_mc[-1]
elif retirement_starting_fund_source == "蒙地卡羅 - 中位數情況 (P50)":
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
        initial_monthly_withdrawal = st.number_input("自訂退休後第一年每月提領金額 (元)", min_value=0.0, value=default_custom_val, step=1000.0)
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
    max_months = 1200
    w_fund_nominal = retirement_starting_fund
    w_fund_real = retirement_starting_fund
    w_rows = []
    exhaust_month = -1
    total_withdrawn_nominal = 0.0

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
        
        m_growth = w_fund_nominal * (final_growth_factor / 12)
        m_dividend = w_fund_nominal * (final_yield_factor / 12)
        
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
        sim_result_text = f"🚨 **模擬結果 - 警報：您的財務水庫預計可支應：{exhaust_year} 年又 {exhaust_m_rem} 個月 (即模擬第 {exhaust_month} 個月) 乾涸！**\n\n一路上共無情支應了生活費 **{round(total_withdrawn_nominal):,}** 元。"
    else:
        # 當模擬成功時，如果提領率過高，在成功訊息後加上提醒
        ideal_note = ""
        if withdraw_pct > 5.0:
            ideal_note = (
                f"\n\n🚨 **重要提醒：此永續結果是建立在「每年穩定獲利 {portfolio_return_pct:.1f}%、完全無波動」的理想前提下！** "
                f"由於您設定的提領率 ({withdraw_pct:.2f}%) 偏高，在現實市場的真實波動與「順序風險」下，"
                f"資產極可能提早乾涸，此結果僅供理想模型下的對照參考，請勿以此做為唯一的真實退休規劃依據！"
            )
        sim_result_text = (
            f"🎉 **模擬結果 - 恭喜！您的退休提領計畫極其穩健 (資產永續不滅)！**\n\n"
            f"資產可永續支應 **100 年以上**！在模擬第 100 年底，您的股票帳戶名目餘額仍剩餘 **{round(w_fund_nominal):,}** 元 (實質購買力折現後為 **{round(w_fund_real):,}** 元)。\n"
            f"一路上成功且優雅地支應了您高達 **{round(total_withdrawn_nominal):,}** 元 的退休生活開銷！"
            f"{ideal_note}"
        )

    # --- Render integrated box FIRST (directly below buttons, as pointed by arrow) ---
    integrated_msg = f"{withdrawal_desc}\n\n---\n\n{sim_result_text}"
    
    if withdraw_pct <= 5.0:
        st.success(integrated_msg)
    elif withdraw_pct <= 8.0:
        st.warning(integrated_msg)
    else:
        st.error(integrated_msg)

    # --- Render safety assessment warnings SECOND (below integrated box) ---
    # 提領率安全評估與警示系統
    st.markdown("### ⚠️ 提領率安全度評估 (重要警示)")
    if withdraw_pct > 8.0:
        st.error(
            f"🚨 **極高風險警報：自訂年提領率達 {withdraw_pct:.2f}%！**\n\n"
            f"**此為理想狀態的對照值**。目前設定的長期加權年化總回報率為 **{portfolio_return_pct:.1f}%**，因此在數學模擬上顯示為「安全或資產上升」。\n\n"
            f"⚠️ **但請務必注意**：在真實的金融市場中，股市存在劇烈的波動與 **「順序風險 (Sequence of Returns Risk)」**。在提領期，若在退休前幾年不幸遭遇市場下跌，即使長期平均回報率有 {portfolio_return_pct:.1f}%，您的資產也極可能在 10 ~ 15 年內徹底破產（坐吃山空）。學術界與業界公認的安全提領率上限為 **4% ~ 5%**，強烈建議您降低提領率或自訂每月提領金額，以策安全！"
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
        
    st.markdown("📊 **提領期資產餘額與累積提取生活費動態圖**")
    if is_inflation:
        w_chart_data = pd.DataFrame({
            "年": w_df["年"],
            "股票帳戶名目餘額": w_df["帳戶餘額_名目"],
            "股票帳戶實質餘額(折合今日購買力)": w_df["帳戶餘額_實質"],
            "累積已提取名目生活費": w_df["累積提領金額(名目)"]
        }).set_index("年")
    else:
        w_chart_data = pd.DataFrame({
            "年": w_df["年"],
            "股票帳戶總餘額": w_df["帳戶餘額_名目"],
            "累積已提取生活費": w_df["累積提領金額(名目)"]
        }).set_index("年")
    st.line_chart(w_chart_data)

# ==========================================
# UI 介面設計：詳細月份數據表與下載
# ==========================================
st.markdown("---")
st.subheader("📅 詳細月份動態流向大表")
st.dataframe(df, use_container_width=True, hide_index=True)

# 財富成長幾何曲線
st.markdown("---")
st.subheader("📈 累積期財富幾何成長曲線")
if is_advanced:
    chart_data = pd.DataFrame({
        "月份": df["月份"],
        "股票帳戶總市值": df["期末帳戶總市值"],
        "累積提領現金": df["累積提領現金"]
    }).set_index("月份")
else:
    chart_data = pd.DataFrame({
        "月份": df["月份"],
        "股票帳戶總市值": df["期末帳戶總市值"]
    }).set_index("月份")
st.area_chart(chart_data)
