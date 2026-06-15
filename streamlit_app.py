# ============================================================
# MSFT Cloud + AI Buy System - Streamlit App
# 手機版 / App-like dashboard
# ============================================================

import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import msft_cloud_ai_buy_system as core

st.set_page_config(
    page_title="MSFT Cloud AI Buy System",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --bg-card: rgba(17, 24, 39, 0.92);
        --border: rgba(148, 163, 184, 0.18);
        --muted: #94a3b8;
        --text: #e5e7eb;
        --green: #22c55e;
        --yellow: #f59e0b;
        --red: #ef4444;
        --blue: #60a5fa;
    }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1180px; }
    div[data-testid="stMetric"] {
        background: var(--bg-card); border: 1px solid var(--border); padding: 14px 16px;
        border-radius: 18px; box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    }
    div[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: 0.82rem; }
    div[data-testid="stMetricValue"] { font-size: 1.45rem; }
    .hero-card {
        border: 1px solid var(--border); border-radius: 24px; padding: 22px 22px; margin-bottom: 18px;
        background: linear-gradient(135deg, rgba(96,165,250,.20), rgba(34,197,94,.08)), rgba(17,24,39,.96);
        box-shadow: 0 18px 48px rgba(0,0,0,.26);
    }
    .hero-card.hold { background: linear-gradient(135deg, rgba(148,163,184,.18), rgba(96,165,250,.05)), rgba(17,24,39,.96); }
    .hero-card.block { background: linear-gradient(135deg, rgba(239,68,68,.20), rgba(245,158,11,.07)), rgba(17,24,39,.96); }
    .hero-action { font-size: 2.7rem; line-height: 1; font-weight: 900; margin: 0 0 8px 0; letter-spacing: -0.06em; }
    .hero-subtitle { color: var(--muted); font-size: 0.95rem; margin-bottom: 8px; }
    .pill { display: inline-block; padding: 6px 10px; margin: 4px 6px 4px 0; border-radius: 999px; font-size: .82rem; font-weight: 700; border: 1px solid var(--border); color: #e5e7eb; background: rgba(15,23,42,.72); }
    .pill.green { color:#bbf7d0; border-color:rgba(34,197,94,.35); background:rgba(34,197,94,.12); }
    .pill.red { color:#fecaca; border-color:rgba(239,68,68,.38); background:rgba(239,68,68,.12); }
    .pill.yellow { color:#fde68a; border-color:rgba(245,158,11,.38); background:rgba(245,158,11,.12); }
    .mini-note { color: var(--muted); font-size: .86rem; line-height: 1.55; }
    @media (max-width: 760px) {
        .block-container { padding-left: .85rem; padding-right: .85rem; }
        .hero-card { padding: 18px 16px; border-radius: 20px; }
        .hero-action { font-size: 2.2rem; }
        div[data-testid="stMetricValue"] { font-size: 1.15rem; }
        div[data-testid="stMetric"] { padding: 12px 12px; border-radius: 16px; }
        .stTabs [data-baseweb="tab-list"] { gap: 4px; overflow-x: auto; }
        .stTabs [data-baseweb="tab"] { padding-left: 8px; padding-right: 8px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Formatting
# ----------------------------
def safe_float(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else np.nan
    except Exception:
        return np.nan


def usd(x, digits=2):
    x = safe_float(x)
    return "NA" if pd.isna(x) else f"${x:,.{digits}f}"


def usd0(x):
    x = safe_float(x)
    return "NA" if pd.isna(x) else f"${x:,.0f}"


def pct(x, digits=2):
    x = safe_float(x)
    return "NA" if pd.isna(x) else f"{x * 100:.{digits}f}%"


def num(x, digits=2):
    x = safe_float(x)
    return "NA" if pd.isna(x) else f"{x:.{digits}f}"


def shares_fmt(x, fractional=False, dp=3):
    x = safe_float(x)
    if pd.isna(x):
        return "—"
    return f"{x:.{dp}f}" if fractional else f"{int(x)}"


def state_pill(state):
    s = str(state).upper()
    if any(k in s for k in ["BUY", "STRONG", "RISK-ON", "CHEAP", "FAIR", "ACCELERATING"]):
        cls = "green"
    elif any(k in s for k in ["CRISIS", "RISK-OFF", "BAD", "WEAK", "EXTREME"]):
        cls = "red"
    else:
        cls = "yellow"
    return f"<span class='pill {cls}'>{state}</span>"


def clean_for_json(obj):
    if isinstance(obj, dict):
        return {str(k): clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [clean_for_json(v) for v in obj]
    if isinstance(obj, pd.DataFrame):
        return obj.reset_index().to_dict(orient="records")
    if isinstance(obj, pd.Series):
        return obj.dropna().to_dict()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if not np.isfinite(v) else v
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    return obj

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.title("MSFT 系統設定")
st.sidebar.caption("手機版 Streamlit app｜手動執行，不會自動下單")

with st.sidebar.expander("帳戶與持股", expanded=True):
    equity_usd = st.number_input("Equity / 總權益 USD", min_value=0.0, value=float(core.EQUITY_USD), step=100.0)
    free_cash_usd = st.number_input("Free Cash / 可用現金 USD", min_value=0.0, value=float(core.FREE_CASH_USD), step=50.0)
    msft_shares = st.number_input("MSFT shares / 持股", min_value=0.0, value=float(core.MSFT_SHARES), step=1.0)
    msft_avg_cost = st.number_input("MSFT avg cost / 均價", min_value=0.0, value=float(core.MSFT_AVG_COST), step=1.0)
    allow_fractional = st.toggle("允許零股 / Fractional shares", value=bool(core.ALLOW_FRACTIONAL))
    max_daily_cash_use_frac = st.slider("單次最多使用現金比例", 0.0, 1.0, float(core.MAX_DAILY_CASH_USE_FRAC), 0.05)

with st.sidebar.expander("財報後手動輸入", expanded=True):
    st.caption("不知道就留空或 0。Azure / Copilot / AI CapEx efficiency 是 MSFT 關鍵節點。")
    azure_growth_yoy_percent = st.number_input("Azure Growth YoY %", value=None, step=1.0, format="%.2f", placeholder="留空 = 中性")
    cloud_guidance_surprise_percent = st.number_input("Cloud Guidance Surprise %", value=None, step=1.0, format="%.2f", placeholder="留空 = 中性")
    copilot_score = st.slider("Copilot Monetization", -1.0, 1.0, 0.0, 0.05)
    capex_eff_score = st.slider("AI CapEx Efficiency", -1.0, 1.0, 0.0, 0.05)
    enterprise_score = st.slider("Enterprise Durability：Office/Dynamics/LinkedIn", -1.0, 1.0, 0.0, 0.05)
    cloud_margin_score = st.slider("Cloud Margin：AI 折舊/毛利壓力", -1.0, 1.0, 0.0, 0.05)
    platform_risk_score = st.slider("Platform Risk：監管/OpenAI/電力限制", -1.0, 1.0, 0.0, 0.05)
    gaming_pc_score = st.slider("Gaming / PC 補正", -1.0, 1.0, 0.0, 0.05)

with st.sidebar.expander("策略規則", expanded=False):
    trend_mode = st.selectbox("Trend mode", ["BALANCED", "STRICT", "LOOSE"], index=["BALANCED", "STRICT", "LOOSE"].index(core.RISK_RULES.get("BUY_TREND_MODE", "BALANCED")))
    pe_source = st.selectbox("PE source", ["FORWARD", "TRAILING", "BLENDED", "CONSERVATIVE"], index=0)
    valuation_mode = st.selectbox("PE / PEG combine", ["MIN", "AVERAGE", "PRODUCT"], index=0)
    add_enable = st.toggle("回撤加碼", value=bool(core.RISK_RULES.get("ADD_ENABLE", True)))
    macro_hard_block = st.toggle("Macro hard block", value=bool(core.RISK_RULES.get("MACRO_HARD_BLOCK_ENABLE", True)))
    no_buy_below_ma200 = st.toggle("低於 MA200 禁買", value=bool(core.RISK_RULES.get("NO_BUY_BELOW_MA200", False)))

with st.sidebar.expander("資料期間", expanded=False):
    start_date = st.date_input("Start", value=pd.to_datetime(core.DEFAULT_START).date())
    end_date = st.date_input("End", value=datetime.today().date())
    show_debug = st.toggle("顯示 raw debug data", value=False)

run_button = st.sidebar.button("重新計算", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.caption("資料來源主要為 yfinance。FRED/pandas_datareader 已移除，避免 Streamlit Cloud 套件相容性問題。")

@st.cache_data(ttl=900, show_spinner=False)
def run_model_cached(
    equity_usd, free_cash_usd, msft_shares, msft_avg_cost, allow_fractional, max_daily_cash_use_frac,
    azure_growth_yoy_percent, cloud_guidance_surprise_percent, copilot_score, capex_eff_score,
    enterprise_score, cloud_margin_score, platform_risk_score, gaming_pc_score,
    trend_mode, pe_source, valuation_mode, add_enable, macro_hard_block, no_buy_below_ma200,
    start_date_str, end_date_str,
):
    core.EQUITY_USD = float(equity_usd)
    core.FREE_CASH_USD = float(free_cash_usd)
    core.MSFT_SHARES = float(msft_shares)
    core.MSFT_AVG_COST = float(msft_avg_cost)
    core.ALLOW_FRACTIONAL = bool(allow_fractional)
    core.MAX_DAILY_CASH_USE_FRAC = float(max_daily_cash_use_frac)
    core.DEFAULT_START = str(start_date_str)
    core.DEFAULT_END = str(end_date_str)

    core.RISK_RULES["BUY_TREND_MODE"] = str(trend_mode)
    core.RISK_RULES["PE_SOURCE"] = str(pe_source)
    core.RISK_RULES["VALUATION_COMBINE_MODE"] = str(valuation_mode)
    core.RISK_RULES["ADD_ENABLE"] = bool(add_enable)
    core.RISK_RULES["MACRO_HARD_BLOCK_ENABLE"] = bool(macro_hard_block)
    core.RISK_RULES["NO_BUY_BELOW_MA200"] = bool(no_buy_below_ma200)

    core.MSFT_MANUAL.update({
        "AZURE_GROWTH_YOY": np.nan if pd.isna(azure_growth_yoy_percent) else float(azure_growth_yoy_percent) / 100.0,
        "CLOUD_GUIDANCE_SURPRISE": np.nan if pd.isna(cloud_guidance_surprise_percent) else float(cloud_guidance_surprise_percent) / 100.0,
        "COPILOT_MONETIZATION_SCORE": float(copilot_score),
        "AI_CAPEX_EFFICIENCY_SCORE": float(capex_eff_score),
        "ENTERPRISE_DURABILITY_SCORE": float(enterprise_score),
        "CLOUD_MARGIN_SCORE": float(cloud_margin_score),
        "PLATFORM_RISK_SCORE": float(platform_risk_score),
        "GAMING_PC_SCORE": float(gaming_pc_score),
    })

    res_macro = core.build_macro_dashboard(
        start=core.DEFAULT_START, end=core.DEFAULT_END, lookback=core.DEFAULT_LOOKBACK,
        weights=core.DEFAULT_MACRO_WEIGHTS, thresholds=core.DEFAULT_MACRO_THRESHOLDS,
        disloc_thr=core.DEFAULT_DISLOC_THR, ffill_limit=core.DEFAULT_FFILL_LIMIT,
    )
    stock_risk = core.compute_stock_risk(core.CORE_TICKER, end=core.DEFAULT_END, rules=core.RISK_RULES, avg_cost=core.MSFT_AVG_COST)
    holdings = core.compute_holdings(stock_risk["last_price"])
    current_stock_usd = float(holdings.loc[core.CORE_TICKER, "market_value"])
    dd_now = core.drawdown_now(stock_risk["ret"])
    lev_pack = core.leverage_engine(
        sigma_ann=stock_risk["sigma_60"], dd_now=dd_now,
        regime=res_macro["regime"] if res_macro else "DATA-UNSTABLE",
        crisis_on=res_macro["crisis_on"] if res_macro else False,
        limits=res_macro["limits"] if res_macro else {"max_leverage": core.DATA_UNSTABLE_MAX_LEV},
        equity_usd=core.EQUITY_USD, free_cash_usd=core.FREE_CASH_USD, current_stock_usd=current_stock_usd,
    )
    buy_plan, pe_pack, peg_pack, capex_signal, driver_pack, fundamentals = core.build_msft_buy_plan(stock_risk, holdings, lev_pack, res_macro)
    return {"stock_risk": stock_risk, "holdings": holdings, "leverage": lev_pack, "macro": res_macro, "buy_plan": buy_plan, "pe": pe_pack, "peg": peg_pack, "capex": capex_signal, "driver": driver_pack, "fundamentals": fundamentals}

if run_button:
    st.cache_data.clear()

st.title("MSFT Cloud + AI Platform Buy System")
st.caption("Azure/Copilot-adjusted PEG + AI CapEx Efficiency + FCF/Margin Driver Score")

try:
    with st.spinner("計算中：抓取股價、估值、宏觀、CapEx 與 MSFT driver…"):
        result = run_model_cached(
            equity_usd, free_cash_usd, msft_shares, msft_avg_cost, allow_fractional, max_daily_cash_use_frac,
            azure_growth_yoy_percent, cloud_guidance_surprise_percent, copilot_score, capex_eff_score,
            enterprise_score, cloud_margin_score, platform_risk_score, gaming_pc_score,
            trend_mode, pe_source, valuation_mode, add_enable, macro_hard_block, no_buy_below_ma200,
            str(start_date), str(end_date),
        )
except Exception as e:
    st.error("模型執行失敗。常見原因是 yfinance 暫時無法連線，或日期區間太短。")
    st.exception(e)
    st.stop()

buy = result["buy_plan"]
stock = result["stock_risk"]
holdings = result["holdings"]
macro = result["macro"]
capex = result["capex"]
driver = result["driver"]
lev = result["leverage"]
fund = result["fundamentals"]

hero_class = "block" if buy.get("block") else ("hold" if buy["action"] != "BUY" else "")
action_text = buy["action"]
share_text = shares_fmt(buy.get("shares"), allow_fractional, core.FRACTIONAL_DP)
hero_detail = f"建議買進 {share_text} 股，預估使用 {usd0(buy.get('est_buy_usd'))}" if action_text == "BUY" else "目前不買，等待更好的價格 / 趨勢 / 風險條件"
reason_html = "".join([f"<span class='pill red'>{r}</span>" for r in buy.get("reasons", [])]) or "<span class='pill green'>No block</span>"

st.markdown(
    f"""
    <div class='hero-card {hero_class}'>
        <div class='hero-subtitle'>Manual execution only｜系統只給決策，不會自動下單</div>
        <div class='hero-action'>{action_text}</div>
        <div style='font-size:1.08rem;font-weight:700;margin-bottom:10px;'>{hero_detail}</div>
        <div>
            {state_pill('MSFT ' + usd(buy.get('price')))}
            {state_pill('Regime ' + str(buy.get('regime')))}
            {state_pill('Driver ' + str(buy.get('driver_state')))}
            {state_pill('Trend ' + str(buy.get('trend_state')))}
        </div>
        <div style='margin-top:8px'>{reason_html}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("MSFT Price", usd(buy.get("price")), f"DD120 {pct(buy.get('dd_120'))}")
m2.metric("Est Buy", usd0(buy.get("est_buy_usd")), f"Cash left {usd0(buy.get('unused_cash_usd'))}")
m3.metric("Driver Score", num(buy.get("driver_total_score")), buy.get("driver_state"))
m4.metric("Valuation Scale", num(buy.get("valuation_scale")), f"PE {buy.get('pe_state')} / PEG {buy.get('peg_state')}")

m5, m6, m7, m8 = st.columns(4)
m5.metric("Forward PE", num(buy.get("forward_pe")), f"Selected {num(buy.get('selected_pe'))}")
m6.metric("AI PEG", num(buy.get("peg")), f"Growth {num(buy.get('used_growth_pct'))}%")
m7.metric("Margin / FCF", pct(buy.get("operating_margin")), f"FCF {pct(buy.get('fcf_margin'))}")
m8.metric("Macro", buy.get("regime"), f"Risk {num(macro.get('latest', {}).get('TotalScore')) if macro else 'NA'}")

# ----------------------------
# Charts
# ----------------------------
def price_chart(stock_risk):
    close = stock_risk["close"].dropna()
    ma_fast = close.rolling(core.RISK_RULES["MA_FAST"]).mean()
    ma_slow = close.rolling(core.RISK_RULES["MA_SLOW"]).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=close.index, y=close.values, mode="lines", name="MSFT"))
    fig.add_trace(go.Scatter(x=ma_fast.index, y=ma_fast.values, mode="lines", name=f"MA{core.RISK_RULES['MA_FAST']}"))
    fig.add_trace(go.Scatter(x=ma_slow.index, y=ma_slow.values, mode="lines", name=f"MA{core.RISK_RULES['MA_SLOW']}"))
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=35, b=10), template="plotly_dark", title="Price / Trend")
    return fig


def driver_chart(driver_pack):
    df = driver_pack["score_df"].copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["driver"], y=df["score"], text=df["score"].round(2), textposition="outside"))
    fig.add_hline(y=0, line_width=1, line_dash="dash")
    fig.update_layout(height=390, margin=dict(l=10, r=10, t=35, b=90), template="plotly_dark", title="MSFT Core Driver Scores", yaxis=dict(range=[-1.1, 1.1]))
    return fig


def buy_scale_chart(buy_plan):
    labels = ["Trend", "PE", "PEG", "Valuation", "Driver", "Cash Usage"]
    cash_usage = buy_plan["est_buy_usd"] / free_cash_usd if free_cash_usd > 0 else 0.0
    vals = [buy_plan.get("trend_scale"), buy_plan.get("pe_scale"), buy_plan.get("peg_scale"), buy_plan.get("valuation_scale"), buy_plan.get("driver_scale"), cash_usage]
    fig = go.Figure(go.Bar(x=labels, y=vals, text=[num(v) for v in vals], textposition="outside"))
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=35, b=30), template="plotly_dark", title="Buy Scale Components")
    return fig


def capex_chart(capex_pack):
    tbl = capex_pack.get("table", pd.DataFrame())
    fig = go.Figure()
    if tbl is not None and not tbl.empty:
        fig.add_trace(go.Scatter(x=tbl.index, y=tbl["capex"], mode="lines+markers", name="Quarterly CapEx"))
        if "capex_ttm" in tbl.columns:
            fig.add_trace(go.Scatter(x=tbl.index, y=tbl["capex_ttm"], mode="lines+markers", name="TTM CapEx"))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=35, b=10), template="plotly_dark", title="MSFT AI CapEx Commitment")
    return fig


def macro_chart(macro_pack):
    factors = macro_pack.get("factors", pd.DataFrame()) if macro_pack else pd.DataFrame()
    fig = go.Figure()
    if not factors.empty:
        for col in ["Liquidity", "Credit", "Volatility", "Growth", "Rate", "Geo", "TotalScore"]:
            if col in factors.columns:
                fig.add_trace(go.Scatter(x=factors.index, y=factors[col], mode="lines", name=col))
    fig.add_hline(y=0, line_width=1, line_dash="dash")
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=35, b=10), template="plotly_dark", title="Macro Dashboard")
    return fig

# ----------------------------
# Tabs
# ----------------------------
tab_decision, tab_drivers, tab_valuation, tab_risk, tab_capex, tab_data = st.tabs(["決策", "驅動因子", "估值", "風險/宏觀", "MSFT CapEx", "資料"])

with tab_decision:
    c1, c2 = st.columns([1.4, 1.0])
    with c1:
        st.plotly_chart(price_chart(stock), use_container_width=True)
    with c2:
        st.plotly_chart(buy_scale_chart(buy), use_container_width=True)
        st.markdown("#### 決策原因")
        st.write(buy.get("reasons", []) or ["No block. 但仍需手動判斷與下單。"])

with tab_drivers:
    c1, c2 = st.columns([1.2, 1.0])
    with c1:
        st.plotly_chart(driver_chart(driver), use_container_width=True)
    with c2:
        st.markdown("#### Driver Notes")
        for k, v in driver.get("notes", {}).items():
            st.markdown(f"**{k}**  ")
            st.caption(v)
    st.dataframe(driver["score_df"], use_container_width=True)

with tab_valuation:
    c1, c2, c3 = st.columns(3)
    c1.metric("Selected PE", num(result["pe"].get("selected_pe")), result["pe"].get("pe_state"))
    c2.metric("PEG", num(result["peg"].get("peg")), result["peg"].get("peg_state"))
    c3.metric("Used Growth", f"{num(result['peg'].get('used_growth_pct'))}%", result["peg"].get("growth_quality"))
    st.markdown("#### PE Pack")
    st.json(clean_for_json(result["pe"]), expanded=False)
    st.markdown("#### PEG Pack")
    st.json(clean_for_json(result["peg"]), expanded=False)

with tab_risk:
    st.plotly_chart(macro_chart(macro), use_container_width=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ATR %", pct(buy.get("atr_pct")))
    c2.metric("Sigma 60D", pct(buy.get("sigma_60")))
    c3.metric("L Final", num(lev.get("L_final")))
    c4.metric("Dislocation", num(macro.get("latest", {}).get("Dislocation") if macro else np.nan))
    st.markdown("#### Macro Latest")
    st.json(clean_for_json(macro.get("latest", {}) if macro else {}), expanded=False)

with tab_capex:
    st.plotly_chart(capex_chart(capex), use_container_width=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CapEx Quality", capex.get("quality"))
    c2.metric("CapEx QoQ", pct(capex.get("qoq")))
    c3.metric("CapEx YoY", pct(capex.get("yoy")))
    c4.metric("CapEx Score", num(capex.get("score")))
    st.caption(capex.get("note"))
    tbl = capex.get("table", pd.DataFrame())
    if tbl is not None and not tbl.empty:
        st.dataframe(tbl, use_container_width=True)

with tab_data:
    st.markdown("#### Holdings")
    st.dataframe(holdings, use_container_width=True)
    st.markdown("#### Fundamentals")
    st.json(clean_for_json(fund), expanded=False)
    st.markdown("#### Download")
    clean_result = clean_for_json(result)
    st.download_button("下載 JSON", data=json.dumps(clean_result, ensure_ascii=False, indent=2), file_name="msft_buy_system_result.json", mime="application/json", use_container_width=True)
    try:
        csv_df = pd.DataFrame([buy])
        st.download_button("下載 Buy Plan CSV", data=csv_df.to_csv(index=False).encode("utf-8-sig"), file_name="msft_buy_plan.csv", mime="text/csv", use_container_width=True)
    except Exception:
        pass
    if show_debug:
        st.markdown("#### Raw Debug")
        st.json(clean_result, expanded=False)
