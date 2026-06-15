# ============================================================
# MSFT-ONLY CLOUD + AI PLATFORM BUY SYSTEM
# Version: Azure/Copilot-adjusted PEG + AI CapEx Efficiency + FCF/Margin Driver Score
#
# - Only holding: MSFT
# - Cash buy only by default
# - No stock pool / No hedge / No auto order
# - MA50 + MA200 balanced trend system
# - PE valuation scale tuned for MSFT quality-growth profile
# - Azure/Copilot-adjusted normalized PEG valuation scale
# - MSFT AI CapEx commitment + efficiency signal
# - Driver score: Azure, Copilot, margin/FCF, CapEx efficiency, enterprise durability, risk, valuation/macro
# - Macro dashboard via yfinance only: no pandas_datareader / no FRED dependency
# - Output only BUY / HOLD
# ============================================================

from __future__ import annotations

import warnings
from datetime import datetime
from typing import Any, Dict, Tuple

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

pd.set_option("display.max_columns", 120)
pd.set_option("display.width", 180)

# ============================================================
# 1) USER CONFIG
# 每天主要改這裡
# ============================================================

CORE_TICKER = "MSFT"
BENCH_TICKER = "QQQ"

EQUITY_USD = 32810.43
FREE_CASH_USD = 498.18
HAIRCUT = 1.00

MSFT_SHARES = 0.0
MSFT_AVG_COST = 0.0

DEFAULT_START = "2020-01-18"
DEFAULT_END = datetime.today().strftime("%Y-%m-%d")

ALLOW_FRACTIONAL = False
FRACTIONAL_DP = 3
MIN_TRADE_USD = 2.0
MAX_DAILY_CASH_USE_FRAC = 1.00

ALLOW_MARGIN_BUY = False
MAX_MANUAL_GROSS_LEVERAGE = 1.20

SIGMA_TARGET = 0.12
DD_WALLS = [
    (-0.30, 0.50),
    (-0.22, 0.80),
    (-0.12, 1.20),
]
DATA_UNSTABLE_MAX_LEV = 0.50

# ============================================================
# 2) MSFT MANUAL DRIVER INPUTS
# 財報後手動更新。留空/0 代表中性。
# 分數規則：+1 = 強順風；0 = 中性；-1 = 轉弱/逆風
# ============================================================

MSFT_MANUAL = {
    # Azure / Intelligent Cloud：MSFT 股價最核心的成長引擎
    # 例：0.30 = Azure YoY +30%；0.03 = guidance 高於市場預期 3%
    "AZURE_GROWTH_YOY": np.nan,
    "CLOUD_GUIDANCE_SURPRISE": np.nan,

    # Copilot / AI monetization：AI 有沒有變成收入，而不只是 CapEx
    "COPILOT_MONETIZATION_SCORE": 0.0,

    # AI CapEx efficiency：花 AI CapEx 是否換得到 Azure / AI 收入加速
    "AI_CAPEX_EFFICIENCY_SCORE": 0.0,

    # Enterprise durability：Office 365 / Dynamics / LinkedIn / Windows 商業需求韌性
    "ENTERPRISE_DURABILITY_SCORE": 0.0,

    # Cloud margin：雲端與 AI 折舊壓力是否壓縮 margin
    "CLOUD_MARGIN_SCORE": 0.0,

    # Regulatory / OpenAI dependency / antitrust / data center power constraint risk
    # +1 = 風險緩解；-1 = 風險明顯擴大
    "PLATFORM_RISK_SCORE": 0.0,

    # Gaming / PC / Windows 補正：通常不是核心，但可當週期補正
    "GAMING_PC_SCORE": 0.0,
}

# ============================================================
# 3) RULES
# ============================================================

RISK_RULES = {
    "ENABLE": True,

    # Trend
    "MA_FAST": 50,
    "MA_SLOW": 200,
    "BUY_TREND_MODE": "BALANCED",  # STRICT / BALANCED / LOOSE
    "BUY_SCALE_STRONG": 1.00,
    "BUY_SCALE_RECOVERY": 0.55,
    "BUY_SCALE_NEUTRAL": 0.30,
    "BUY_SCALE_WEAK": 0.00,
    "NO_BUY_BELOW_MA200": False,

    # Vol / drawdown
    "USE_ATR": True,
    "ATR_DAYS": 14,
    "DD_LOOKBACK": 120,
    "ADD_ENABLE": True,
    "ADD_DD": 0.12,
    "ADD_BUY_FRAC_OF_CASH": 0.25,
    "NO_BUY_IF_ATR_ABOVE": 0.045,
    "NO_BUY_IF_DD_BELOW": -0.35,

    # PE valuation: tuned for MSFT quality-growth profile
    "PE_ENABLE": True,
    "PE_SOURCE": "FORWARD",  # FORWARD / TRAILING / BLENDED / CONSERVATIVE
    "PE_MISSING_SCALE": 1.00,
    "PE_CHEAP": 24.0,
    "PE_FAIR": 32.0,
    "PE_WARM": 40.0,
    "PE_EXPENSIVE": 50.0,
    "PE_HARD_BLOCK": 65.0,
    "PE_SCALE_CHEAP": 1.20,
    "PE_SCALE_FAIR": 1.00,
    "PE_SCALE_WARM": 0.70,
    "PE_SCALE_EXPENSIVE": 0.40,
    "PE_SCALE_VERY_EXPENSIVE": 0.15,
    "PE_HARD_BLOCK_ENABLE": False,

    # Azure/Copilot-adjusted PEG
    "PEG_ENABLE": True,
    "PEG_GROWTH_SOURCE": "MSFT_AI_ADJUSTED",  # MSFT_AI_ADJUSTED / CAPPED_FORWARD_EPS / MANUAL / YF_EARNINGS_GROWTH / BLENDED
    "PEG_FALLBACK_SOURCE": "CAPPED_FORWARD_EPS",
    "MANUAL_EPS_GROWTH": 0.14,
    "PEG_MIN_GROWTH": 0.04,
    "PEG_MAX_GROWTH": 0.28,
    "PEG_UNKNOWN_FALLBACK_GROWTH": 0.12,
    "PEG_MIN_ADJUSTED_GROWTH": 0.06,
    "PEG_GROWTH_QUALITY_RULES": {
        "ACCELERATING": {"reliability": 0.88, "soft_upper": 0.30, "scale_bias": 1.05},
        "STRONG":       {"reliability": 0.78, "soft_upper": 0.24, "scale_bias": 1.00},
        "STABLE":       {"reliability": 0.62, "soft_upper": 0.18, "scale_bias": 1.00},
        "WEAK":         {"reliability": 0.38, "soft_upper": 0.12, "scale_bias": 0.75},
        "UNKNOWN":      {"reliability": 0.48, "soft_upper": 0.15, "scale_bias": 0.88},
    },
    "PEG_CHEAP": 1.10,
    "PEG_FAIR": 1.70,
    "PEG_WARM": 2.30,
    "PEG_EXPENSIVE": 3.00,
    "PEG_HARD_BLOCK": 4.00,
    "PEG_SCALE_CHEAP": 1.20,
    "PEG_SCALE_FAIR": 1.00,
    "PEG_SCALE_WARM": 0.70,
    "PEG_SCALE_EXPENSIVE": 0.40,
    "PEG_SCALE_VERY_EXPENSIVE": 0.15,
    "PEG_MISSING_SCALE": 1.00,
    "PEG_HARD_BLOCK_ENABLE": False,
    "VALUATION_COMBINE_MODE": "MIN",  # MIN / PRODUCT / AVERAGE

    # MSFT CapEx signal rules. CapEx rising is a commitment signal, but efficiency matters more.
    "CAPEX_TREND_WINDOW": 4,
    "CAPEX_QOQ_STRONG": 0.05,
    "CAPEX_QOQ_WEAK": -0.08,
    "CAPEX_YOY_STRONG": 0.15,
    "CAPEX_YOY_WEAK": -0.05,
    "CAPEX_UP_SLOPE_REL": 0.03,
    "CAPEX_DOWN_SLOPE_REL": -0.03,

    # Stock driver weights
    "DRIVER_WEIGHTS": {
        "Azure_Cloud_AI": 0.30,
        "Copilot_Monetization": 0.20,
        "Margin_FCF": 0.15,
        "AI_CapEx_Efficiency": 0.12,
        "Enterprise_Durability": 0.10,
        "Platform_Risk": 0.05,
        "Valuation_Macro": 0.08,
    },
    "DRIVER_SCALE_STRONG": 1.20,
    "DRIVER_SCALE_STABLE": 1.00,
    "DRIVER_SCALE_WEAK": 0.60,
    "DRIVER_SCALE_BAD": 0.25,

    "MACRO_HARD_BLOCK_ENABLE": True,
}

# Macro uses yfinance only: safer for Streamlit Cloud.
YF_TICKERS = {
    "HYG": "High Yield Credit ETF",
    "LQD": "Investment Grade Credit ETF",
    "^VIX": "VIX",
    "TLT": "Long Treasury ETF",
    "DX-Y.NYB": "DXY Dollar Index",
    "UUP": "Dollar ETF Fallback",
    "GLD": "Gold ETF",
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "XLK": "Technology ETF",
}

DEFAULT_MACRO_WEIGHTS = {
    "Liquidity": 1.00,
    "Credit": 1.20,
    "Volatility": 1.00,
    "Growth": 0.60,
    "Rate": 0.80,
    "Geo": 0.50,
}

DEFAULT_MACRO_THRESHOLDS = {
    "VIX": 35.0,
    "Credit": 1.50,
    "Vol": 1.20,
    "MinFlags": 2,
}
DEFAULT_FFILL_LIMIT = 10
DEFAULT_LOOKBACK = 252
DEFAULT_DISLOC_THR = 1.80

# ============================================================
# HELPERS
# ============================================================

def _safe_float(x: Any) -> float:
    try:
        if x is None:
            return np.nan
        v = float(x)
        return v if np.isfinite(v) else np.nan
    except Exception:
        return np.nan


def pct_fmt(x: Any) -> str:
    x = _safe_float(x)
    return "NA" if pd.isna(x) else f"{x * 100:.2f}%"


def usd_fmt(x: Any) -> str:
    x = _safe_float(x)
    return "NA" if pd.isna(x) else f"${x:,.2f}"


def pretty(x: Any) -> str:
    x = _safe_float(x)
    return "NA" if pd.isna(x) else f"{x:+.2f}"


def clamp_score(x: Any, lo: float = -1.0, hi: float = 1.0) -> float:
    x = _safe_float(x)
    if pd.isna(x):
        return np.nan
    return float(np.clip(x, lo, hi))


def normalize_name(x: Any) -> str:
    return str(x).strip().lower().replace("_", " ").replace("-", " ")


def find_row_by_candidates(df: pd.DataFrame, candidates: list[str]) -> Any:
    if df is None or df.empty:
        return None
    norm_map = {normalize_name(idx): idx for idx in df.index}
    cand_norm = [normalize_name(c) for c in candidates]
    for c in cand_norm:
        if c in norm_map:
            return norm_map[c]
    for c in cand_norm:
        for n, raw in norm_map.items():
            if c in n or n in c:
                return raw
    return None


def linear_slope_rel(series: pd.Series) -> float:
    s = pd.Series(series).dropna()
    if len(s) < 2:
        return np.nan
    y = s.values.astype(float)
    x = np.arange(len(y))
    avg = np.nanmean(np.abs(y))
    if avg <= 0 or pd.isna(avg):
        return np.nan
    slope = np.polyfit(x, y, 1)[0]
    return float(slope / avg)


def soft_saturate_growth(raw_growth: Any, reliability: float, soft_upper: float, min_growth: float) -> float:
    raw_growth = _safe_float(raw_growth)
    if pd.isna(raw_growth) or raw_growth <= 0:
        return np.nan
    reliability = 0.48 if pd.isna(_safe_float(reliability)) or reliability <= 0 else float(reliability)
    soft_upper = 0.15 if pd.isna(_safe_float(soft_upper)) or soft_upper <= 0 else float(soft_upper)
    effective_raw = raw_growth * reliability
    adjusted = soft_upper * (1.0 - np.exp(-effective_raw / max(soft_upper, 1e-9)))
    return float(max(adjusted, min_growth))


def shares_from_usd(d_usd: Any, px: Any) -> float:
    px = _safe_float(px)
    d_usd = _safe_float(d_usd)
    if pd.isna(px) or px <= 0 or pd.isna(d_usd) or d_usd <= 0:
        return np.nan
    sh_raw = d_usd / px
    if ALLOW_FRACTIONAL:
        sh = round(sh_raw, FRACTIONAL_DP)
        return sh if sh > 0 else np.nan
    sh = int(np.floor(sh_raw))
    return sh if sh > 0 else np.nan

# ============================================================
# DATA
# ============================================================

def safe_yf_close(ticker: str, start: str | None = None, end: str | None = None, interval: str = "1d", period: str | None = None) -> pd.Series:
    try:
        if period is not None:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        else:
            df = yf.download(ticker, start=start, end=end, interval=interval, progress=False, auto_adjust=True)
        if df is None or df.empty:
            return pd.Series(dtype=float, name=ticker)
        if isinstance(df.columns, pd.MultiIndex):
            if "Close" in df.columns.get_level_values(0):
                s = df["Close"]
                if isinstance(s, pd.DataFrame):
                    s = s.iloc[:, 0]
            else:
                return pd.Series(dtype=float, name=ticker)
        else:
            if "Close" not in df.columns:
                return pd.Series(dtype=float, name=ticker)
            s = df["Close"]
        s = pd.Series(s).dropna().copy()
        s.name = ticker
        return s
    except Exception:
        return pd.Series(dtype=float, name=ticker)


def to_bday_ffill_limit(s: pd.Series, limit_days: int = 10) -> pd.Series:
    if s is None or s.empty:
        return s
    s = s.dropna()
    if s.empty:
        return s
    diffs = pd.Series(s.index).diff().dropna().dt.days
    med_gap = float(diffs.median()) if len(diffs) else 1.0
    lim = 90 if med_gap >= 20 else (25 if med_gap >= 5 else limit_days)
    idx = pd.date_range(s.index.min(), s.index.max(), freq="B")
    return s.reindex(idx).ffill(limit=int(lim))


def rolling_z(s: pd.Series, lookback: int, minp: int = 60) -> pd.Series:
    if s is None or s.empty:
        return s
    mu = s.rolling(lookback, min_periods=minp).mean()
    sd = s.rolling(lookback, min_periods=minp).std()
    z = (s - mu) / sd
    z = z.where(sd > 1e-6)
    if len(z) and pd.isna(z.iloc[-1]):
        last_valid = z.dropna()
        if not last_valid.empty:
            z.iloc[-1] = last_valid.iloc[-1]
    return z.clip(-5, 5)


def _first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns and df[c].dropna().shape[0] > 30:
            return c
    return None


def _z_or_nan(s: pd.Series, lookback: int) -> pd.Series:
    if s is None or len(pd.Series(s).dropna()) < 80:
        return pd.Series(np.nan, index=s.index if s is not None else None)
    return rolling_z(pd.Series(s), lookback, minp=60)

# ============================================================
# MACRO ENGINE
# ============================================================

def classify_regime(latest: Dict[str, Any]) -> str:
    L = latest.get("Liquidity", np.nan)
    C = latest.get("Credit", np.nan)
    V = latest.get("Volatility", np.nan)
    G = latest.get("Growth", np.nan)
    R = latest.get("Rate", np.nan)
    cov = latest.get("Coverage", 0.0)
    if cov < 0.6:
        return "DATA-UNSTABLE"
    if (C >= 1.5) and (V >= 1.2):
        return "CRISIS"
    if (C >= 0.8) or (V >= 0.9):
        return "RISK-OFF"
    if (R >= 0.8) and (L <= 0.3):
        return "LATE-CYCLE"
    if (L >= 0.4) and (G >= 0.2) and (C <= 0.3) and (V <= 0.3):
        return "RISK-ON"
    return "NEUTRAL"


def decision_limits(regime: str, crisis_on: bool) -> Dict[str, Any]:
    limits = {"max_leverage": 0.80, "notes": []}
    if regime == "DATA-UNSTABLE":
        limits["max_leverage"] = DATA_UNSTABLE_MAX_LEV
        limits["notes"].append("DATA-UNSTABLE：資料不足，只當 advisory")
    elif crisis_on or regime == "CRISIS":
        limits["max_leverage"] = 0.00
        limits["notes"].append("CRISIS：禁止買進")
    elif regime == "RISK-OFF":
        limits["max_leverage"] = 0.50
        limits["notes"].append("RISK-OFF：禁止追價")
    elif regime == "LATE-CYCLE":
        limits["max_leverage"] = 0.70
        limits["notes"].append("LATE-CYCLE：控制高估值風險")
    elif regime == "RISK-ON":
        limits["max_leverage"] = 1.00
        limits["notes"].append("RISK-ON：允許正常買進")
    else:
        limits["notes"].append("NEUTRAL：正常但不激進")
    return limits


def build_macro_dashboard(start: str, end: str, lookback: int, weights: Dict[str, float], thresholds: Dict[str, float], disloc_thr: float = 1.8, ffill_limit: int = 10) -> Dict[str, Any] | None:
    yfs = {t: safe_yf_close(t, start=start, end=end) for t in YF_TICKERS}
    series = [to_bday_ffill_limit(s, limit_days=ffill_limit) for s in yfs.values() if s is not None and not s.empty]
    if not series:
        return None
    df = pd.concat(series, axis=1).sort_index().ffill(limit=ffill_limit)

    dollar_col = _first_existing_col(df, ["DX-Y.NYB", "UUP"])
    hyg_col = _first_existing_col(df, ["HYG"])
    lqd_col = _first_existing_col(df, ["LQD"])
    vix_col = _first_existing_col(df, ["^VIX"])
    tlt_col = _first_existing_col(df, ["TLT"])
    gld_col = _first_existing_col(df, ["GLD"])
    growth_col = _first_existing_col(df, ["XLK", "QQQ", "SPY"])

    ret21 = df.pct_change(21)
    ret63 = df.pct_change(63)
    ret1 = df.pct_change()
    Z = pd.DataFrame(index=df.index)

    if hyg_col and lqd_col:
        credit_ratio = (df[hyg_col] / df[lqd_col]).replace([np.inf, -np.inf], np.nan)
        Z["z_credit_ratio_21"] = _z_or_nan(credit_ratio.pct_change(21), lookback)
        Credit = -1.0 * Z["z_credit_ratio_21"]
        Growth_credit = Z["z_credit_ratio_21"]
    else:
        Credit = pd.Series(np.nan, index=df.index)
        Growth_credit = pd.Series(np.nan, index=df.index)

    if vix_col:
        Z["z_vix"] = _z_or_nan(df[vix_col], lookback)
        Volatility = Z["z_vix"]
        vix_latest = _safe_float(df[vix_col].dropna().iloc[-1]) if df[vix_col].dropna().shape[0] else np.nan
    else:
        Volatility = pd.Series(np.nan, index=df.index)
        vix_latest = np.nan

    Z["z_tlt_21"] = _z_or_nan(ret21[tlt_col], lookback) if tlt_col else np.nan
    Z["z_dollar_21"] = _z_or_nan(ret21[dollar_col], lookback) if dollar_col else np.nan
    Liquidity = 0.6 * Z["z_tlt_21"].fillna(0) - 0.6 * Z["z_dollar_21"].fillna(0)
    Rate = -0.8 * Z["z_tlt_21"].fillna(0) + 0.4 * Z["z_dollar_21"].fillna(0)

    Z["z_gld_21"] = _z_or_nan(ret21[gld_col], lookback) if gld_col else np.nan
    Geo = 0.45 * Z["z_gld_21"].fillna(0) + 0.35 * Z["z_dollar_21"].fillna(0) + 0.20 * Volatility.fillna(0)

    if growth_col:
        Z["z_growth_63"] = _z_or_nan(ret63[growth_col], lookback)
        Growth = 0.65 * Growth_credit.fillna(0) + 0.35 * Z["z_growth_63"].fillna(0)
    else:
        Growth = Growth_credit

    shock_parts = []
    for col in [hyg_col, lqd_col, vix_col, tlt_col, dollar_col, gld_col, growth_col]:
        if col and col in ret1.columns:
            shock_parts.append(_z_or_nan(ret1[col].abs(), lookback).fillna(0))
    Dislocation = sum(shock_parts) / len(shock_parts) if shock_parts else pd.Series(np.nan, index=df.index)

    factors = pd.DataFrame({
        "Liquidity": Liquidity,
        "Credit": Credit,
        "Volatility": Volatility,
        "Growth": Growth,
        "Rate": Rate,
        "Geo": Geo,
        "Dislocation": Dislocation,
    }, index=df.index)

    cols = ["Liquidity", "Credit", "Volatility", "Growth", "Rate", "Geo"]
    W = pd.Series(weights)
    avail = factors[cols].notna().astype(float)
    w_eff = avail.mul(W[cols], axis=1)
    w_sum = w_eff.sum(axis=1).replace(0, np.nan)
    w_norm = w_eff.div(w_sum, axis=0)
    risk_components = pd.DataFrame({
        "Liquidity": -factors["Liquidity"],
        "Credit": factors["Credit"],
        "Volatility": factors["Volatility"],
        "Growth": -factors["Growth"],
        "Rate": factors["Rate"],
        "Geo": factors["Geo"],
    }, index=factors.index)
    factors["TotalScore"] = (risk_components[cols] * w_norm).sum(axis=1, skipna=True)
    factors["Coverage"] = avail.sum(axis=1) / len(cols)

    latest = factors.dropna(how="all").iloc[-1].to_dict()
    regime = classify_regime(latest)
    flags = {
        "VIX > threshold": (not pd.isna(vix_latest)) and (vix_latest > thresholds["VIX"]),
        "CreditStress > threshold": (not pd.isna(latest.get("Credit", np.nan))) and (latest["Credit"] > thresholds["Credit"]),
        "VolScore > threshold": (not pd.isna(latest.get("Volatility", np.nan))) and (latest["Volatility"] > thresholds["Vol"]),
        "Dislocation > thr": (not pd.isna(latest.get("Dislocation", np.nan))) and (latest["Dislocation"] > disloc_thr),
    }
    crisis_on = False
    if regime != "DATA-UNSTABLE":
        base = sum(bool(v) for k, v in flags.items() if k != "Dislocation > thr") >= thresholds["MinFlags"]
        crisis_on = base or bool(flags["Dislocation > thr"])
    limits = decision_limits(regime, crisis_on)

    return {
        "raw": df,
        "Z": Z,
        "factors": factors,
        "latest": latest,
        "regime": regime,
        "crisis_flags": flags,
        "crisis_on": crisis_on,
        "limits": limits,
        "disloc_thr": disloc_thr,
        "vix_latest": float(vix_latest) if not pd.isna(vix_latest) else np.nan,
        "market_cols": {"hyg": hyg_col, "lqd": lqd_col, "vix": vix_col, "tlt": tlt_col, "dollar": dollar_col, "gld": gld_col, "growth": growth_col},
    }

# ============================================================
# PRICE / RISK
# ============================================================

def download_ohlc(ticker: str, end: str, days: int = 700) -> pd.DataFrame:
    end_dt = pd.to_datetime(end)
    start_dt = end_dt - pd.Timedelta(days=days * 2)
    df = yf.download(ticker, start=start_dt.strftime("%Y-%m-%d"), end=(end_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), interval="1d", auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"{ticker} price download failed.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna(how="all")


def classify_ma_trend(last_close: float, ma_fast: float, ma_slow: float, rules: Dict[str, Any]) -> Dict[str, Any]:
    above_fast = last_close > ma_fast
    above_slow = last_close > ma_slow
    fast_above_slow = ma_fast > ma_slow
    mode = str(rules.get("BUY_TREND_MODE", "BALANCED")).upper()
    if above_fast and fast_above_slow:
        state, scale = "STRONG", float(rules.get("BUY_SCALE_STRONG", 1.0))
    elif above_fast and not fast_above_slow:
        state, scale = "RECOVERY", float(rules.get("BUY_SCALE_RECOVERY", 0.55))
    elif above_slow and not above_fast:
        state, scale = "WEAK_PULLBACK", float(rules.get("BUY_SCALE_NEUTRAL", 0.3))
    elif last_close > min(ma_fast, ma_slow):
        state, scale = "NEUTRAL", float(rules.get("BUY_SCALE_NEUTRAL", 0.3))
    else:
        state, scale = "WEAK", float(rules.get("BUY_SCALE_WEAK", 0.0))
    if mode == "STRICT":
        scale = float(rules.get("BUY_SCALE_STRONG", 1.0)) if state == "STRONG" else 0.0
    elif mode == "LOOSE":
        if above_fast:
            scale = max(scale, float(rules.get("BUY_SCALE_RECOVERY", 0.55)))
        elif above_slow:
            scale = max(scale, float(rules.get("BUY_SCALE_NEUTRAL", 0.3)))
    if rules.get("NO_BUY_BELOW_MA200", False) and not above_slow:
        scale = 0.0
    return {"ma_fast": float(ma_fast), "ma_slow": float(ma_slow), "above_ma_fast": bool(above_fast), "above_ma_slow": bool(above_slow), "ma_fast_above_ma_slow": bool(fast_above_slow), "trend_state": state, "trend_scale": float(scale), "trend_ok": bool(scale > 0)}


def compute_stock_risk(ticker: str, end: str, rules: Dict[str, Any], avg_cost: float | None = None) -> Dict[str, Any]:
    df = download_ohlc(ticker, end=end, days=700)
    close = df["Close"].dropna()
    high = df["High"].dropna()
    low = df["Low"].dropna()
    ma_fast_n = int(rules.get("MA_FAST", 50))
    ma_slow_n = int(rules.get("MA_SLOW", 200))
    atr_n = int(rules.get("ATR_DAYS", 14))
    dd_lb = int(rules.get("DD_LOOKBACK", 120))
    last_close = float(close.iloc[-1])
    ma_fast = float(close.rolling(ma_fast_n).mean().iloc[-1])
    ma_slow = float(close.rolling(ma_slow_n).mean().iloc[-1])
    trend_pack = classify_ma_trend(last_close, ma_fast, ma_slow, rules)
    peak_120 = float(close.rolling(dd_lb, min_periods=min(60, dd_lb)).max().iloc[-1])
    dd_120 = last_close / peak_120 - 1.0
    prev_close = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.rolling(atr_n, min_periods=min(atr_n, 10)).mean()
    atr_last = float(atr.iloc[-1])
    atr_pct = atr_last / last_close
    ret = close.pct_change().dropna()
    sigma_60 = float(ret.tail(60).std(ddof=1) * np.sqrt(252))
    sigma_120 = float(ret.tail(120).std(ddof=1) * np.sqrt(252))
    pnl_pct = np.nan
    if avg_cost is not None and avg_cost > 0:
        pnl_pct = last_close / avg_cost - 1.0
    out = {"df": df, "close": close, "ret": ret, "last_price": last_close, "peak_120": peak_120, "dd_120": float(dd_120), "atr": atr_last, "atr_pct": float(atr_pct), "sigma_60": sigma_60, "sigma_120": sigma_120, "pnl_pct": float(pnl_pct) if not pd.isna(pnl_pct) else np.nan}
    out.update(trend_pack)
    return out

# ============================================================
# FUNDAMENTALS / PE
# ============================================================

def fetch_fundamentals(ticker: str) -> Dict[str, Any]:
    out = {"trailing_pe": np.nan, "forward_pe": np.nan, "trailing_eps": np.nan, "forward_eps": np.nan, "gross_margin": np.nan, "operating_margin": np.nan, "profit_margin": np.nan, "revenue_growth": np.nan, "earnings_growth": np.nan, "free_cashflow": np.nan, "total_revenue": np.nan, "fcf_margin": np.nan, "source_ok": False, "error": ""}
    try:
        info = yf.Ticker(ticker).info or {}
        out.update({
            "trailing_pe": _safe_float(info.get("trailingPE", np.nan)),
            "forward_pe": _safe_float(info.get("forwardPE", np.nan)),
            "trailing_eps": _safe_float(info.get("trailingEps", np.nan)),
            "forward_eps": _safe_float(info.get("forwardEps", np.nan)),
            "gross_margin": _safe_float(info.get("grossMargins", np.nan)),
            "operating_margin": _safe_float(info.get("operatingMargins", np.nan)),
            "profit_margin": _safe_float(info.get("profitMargins", np.nan)),
            "revenue_growth": _safe_float(info.get("revenueGrowth", np.nan)),
            "earnings_growth": _safe_float(info.get("earningsGrowth", np.nan)),
            "free_cashflow": _safe_float(info.get("freeCashflow", np.nan)),
            "total_revenue": _safe_float(info.get("totalRevenue", np.nan)),
            "source_ok": True,
        })
        if not pd.isna(out["free_cashflow"]) and not pd.isna(out["total_revenue"]) and out["total_revenue"] > 0:
            out["fcf_margin"] = out["free_cashflow"] / out["total_revenue"]
    except Exception as e:
        out["error"] = str(e)
    return out


def compute_pe_pack(ticker: str, price: float, rules: Dict[str, Any]) -> Dict[str, Any]:
    if not rules.get("PE_ENABLE", True):
        return {"pe_enabled": False, "pe_source": "DISABLED", "selected_pe": np.nan, "forward_pe": np.nan, "trailing_pe": np.nan, "forward_eps": np.nan, "trailing_eps": np.nan, "pe_state": "DISABLED", "pe_scale": 1.0, "pe_block": False, "pe_note": "PE disabled"}
    f = fetch_fundamentals(ticker)
    forward_pe = _safe_float(f.get("forward_pe"))
    trailing_pe = _safe_float(f.get("trailing_pe"))
    forward_eps = _safe_float(f.get("forward_eps"))
    trailing_eps = _safe_float(f.get("trailing_eps"))
    if pd.isna(forward_pe) and not pd.isna(forward_eps) and forward_eps > 0:
        forward_pe = price / forward_eps
    if pd.isna(trailing_pe) and not pd.isna(trailing_eps) and trailing_eps > 0:
        trailing_pe = price / trailing_eps
    source = str(rules.get("PE_SOURCE", "FORWARD")).upper()
    if source == "FORWARD":
        selected_pe = forward_pe if not pd.isna(forward_pe) else trailing_pe
    elif source == "TRAILING":
        selected_pe = trailing_pe if not pd.isna(trailing_pe) else forward_pe
    elif source == "BLENDED":
        selected_pe = 0.65 * forward_pe + 0.35 * trailing_pe if not pd.isna(forward_pe) and not pd.isna(trailing_pe) else (forward_pe if not pd.isna(forward_pe) else trailing_pe)
    elif source == "CONSERVATIVE":
        vals = [x for x in [forward_pe, trailing_pe] if not pd.isna(x)]
        selected_pe = max(vals) if vals else np.nan
    else:
        selected_pe = forward_pe if not pd.isna(forward_pe) else trailing_pe
    if pd.isna(selected_pe) or selected_pe <= 0:
        return {"pe_enabled": True, "pe_source": source, "selected_pe": np.nan, "forward_pe": forward_pe, "trailing_pe": trailing_pe, "forward_eps": forward_eps, "trailing_eps": trailing_eps, "pe_state": "PE_DATA_MISSING", "pe_scale": float(rules.get("PE_MISSING_SCALE", 1.0)), "pe_block": False, "pe_note": "PE missing"}
    cheap, fair, warm, expensive, hard_block = [float(rules[k]) for k in ["PE_CHEAP", "PE_FAIR", "PE_WARM", "PE_EXPENSIVE", "PE_HARD_BLOCK"]]
    if selected_pe <= cheap:
        state, scale = "CHEAP", float(rules["PE_SCALE_CHEAP"])
    elif selected_pe <= fair:
        state, scale = "FAIR", float(rules["PE_SCALE_FAIR"])
    elif selected_pe <= warm:
        state, scale = "WARM", float(rules["PE_SCALE_WARM"])
    elif selected_pe <= expensive:
        state, scale = "EXPENSIVE", float(rules["PE_SCALE_EXPENSIVE"])
    elif selected_pe <= hard_block:
        state, scale = "VERY_EXPENSIVE", float(rules["PE_SCALE_VERY_EXPENSIVE"])
    else:
        state = "EXTREME"
        scale = 0.0 if rules.get("PE_HARD_BLOCK_ENABLE", False) else float(rules["PE_SCALE_VERY_EXPENSIVE"])
    return {"pe_enabled": True, "pe_source": source, "selected_pe": float(selected_pe), "forward_pe": forward_pe, "trailing_pe": trailing_pe, "forward_eps": forward_eps, "trailing_eps": trailing_eps, "pe_state": state, "pe_scale": float(scale), "pe_block": bool(state == "EXTREME" and rules.get("PE_HARD_BLOCK_ENABLE", False)), "pe_note": f"{source} PE selected"}

# ============================================================
# CAPEX MODULE
# ============================================================

def extract_capex_from_cashflow(ticker: str) -> Tuple[pd.Series, str]:
    tk = yf.Ticker(ticker)
    try:
        qcf = tk.quarterly_cashflow
    except Exception:
        qcf = pd.DataFrame()
    try:
        acf = tk.cashflow
    except Exception:
        acf = pd.DataFrame()
    capex_candidates = ["Capital Expenditure", "Capital Expenditures", "Capital Spending", "Purchase Of PPE", "Purchase of Property Plant And Equipment", "Purchase Of Property Plant Equipment", "Investments In Property Plant And Equipment"]
    cfo_candidates = ["Operating Cash Flow", "Total Cash From Operating Activities", "Cash Flow From Continuing Operating Activities"]
    fcf_candidates = ["Free Cash Flow", "FreeCashFlow"]
    capex_series = pd.Series(dtype=float)
    source = "NONE"
    if qcf is not None and not qcf.empty:
        capex_row = find_row_by_candidates(qcf, capex_candidates)
        if capex_row is not None:
            raw = qcf.loc[capex_row].copy()
            raw.index = pd.to_datetime(raw.index)
            capex_series = raw.sort_index().astype(float).abs()
            source = f"quarterly_cashflow:{capex_row}"
        if capex_series.empty:
            cfo_row = find_row_by_candidates(qcf, cfo_candidates)
            fcf_row = find_row_by_candidates(qcf, fcf_candidates)
            if cfo_row is not None and fcf_row is not None:
                proxy = qcf.loc[cfo_row].copy() - qcf.loc[fcf_row].copy()
                proxy.index = pd.to_datetime(proxy.index)
                capex_series = proxy.sort_index().astype(float).abs()
                source = f"quarterly_proxy:{cfo_row}-{fcf_row}"
    if capex_series.empty and acf is not None and not acf.empty:
        capex_row = find_row_by_candidates(acf, capex_candidates)
        if capex_row is not None:
            raw = acf.loc[capex_row].copy()
            raw.index = pd.to_datetime(raw.index)
            capex_series = raw.sort_index().astype(float).abs()
            source = f"annual_cashflow:{capex_row}"
    capex_series = capex_series.dropna()
    capex_series = capex_series[capex_series > 0]
    return capex_series, source


def compute_capex_signal(capex_series: pd.Series, rules: Dict[str, Any]) -> Dict[str, Any]:
    if capex_series is None or len(capex_series.dropna()) < 2:
        return {"quality": "UNKNOWN", "qoq": np.nan, "yoy": np.nan, "ttm_latest": np.nan, "slope_rel": np.nan, "trend": "UNKNOWN", "score": np.nan, "table": pd.DataFrame(), "note": "CapEx data missing"}
    s = capex_series.dropna().sort_index()
    s = s[s > 0]
    if len(s) < 2:
        return {"quality": "UNKNOWN", "qoq": np.nan, "yoy": np.nan, "ttm_latest": np.nan, "slope_rel": np.nan, "trend": "UNKNOWN", "score": np.nan, "table": pd.DataFrame({"capex": s}), "note": "CapEx data insufficient"}
    qoq = _safe_float(s.iloc[-1] / s.iloc[-2] - 1.0) if s.iloc[-2] > 0 else np.nan
    recent = s.tail(min(int(rules.get("CAPEX_TREND_WINDOW", 4)), len(s)))
    slope_rel = linear_slope_rel(recent) if len(recent) >= 3 else np.nan
    up_slope = float(rules.get("CAPEX_UP_SLOPE_REL", 0.03))
    down_slope = float(rules.get("CAPEX_DOWN_SLOPE_REL", -0.03))
    if pd.isna(slope_rel):
        trend = "UNKNOWN"
    elif slope_rel >= up_slope:
        trend = "UP"
    elif slope_rel <= down_slope:
        trend = "DOWN"
    else:
        trend = "FLAT"
    ttm = s.rolling(4).sum().dropna()
    ttm_latest = _safe_float(ttm.iloc[-1]) if len(ttm) >= 1 else np.nan
    yoy = _safe_float(ttm.iloc[-1] / ttm.iloc[-5] - 1.0) if len(ttm) >= 5 else np.nan
    qoq_strong, qoq_weak = float(rules.get("CAPEX_QOQ_STRONG", 0.05)), float(rules.get("CAPEX_QOQ_WEAK", -0.08))
    yoy_strong, yoy_weak = float(rules.get("CAPEX_YOY_STRONG", 0.15)), float(rules.get("CAPEX_YOY_WEAK", -0.05))
    parts = []
    if not pd.isna(qoq):
        parts.append((1.0 if qoq >= qoq_strong else (-1.0 if qoq <= qoq_weak else 0.0), 0.40))
    if trend == "UP":
        parts.append((1.0, 0.35))
    elif trend == "DOWN":
        parts.append((-1.0, 0.35))
    elif trend == "FLAT":
        parts.append((0.0, 0.35))
    if not pd.isna(yoy):
        parts.append((1.0 if yoy >= yoy_strong else (-1.0 if yoy <= yoy_weak else 0.0), 0.25))
    if parts:
        score = sum(v * w for v, w in parts) / sum(w for _, w in parts)
        if score >= 0.55:
            quality = "ACCELERATING"
        elif score >= 0.25:
            quality = "STRONG"
        elif score <= -0.35:
            quality = "WEAK"
        else:
            quality = "STABLE"
    else:
        score, quality = np.nan, "UNKNOWN"
    table = pd.DataFrame({"capex": s})
    if len(ttm) > 0:
        table["capex_ttm"] = ttm
    return {"quality": quality, "qoq": qoq, "yoy": yoy, "ttm_latest": ttm_latest, "slope_rel": slope_rel, "trend": trend, "score": score, "table": table, "note": f"MSFT CapEx commitment: qoq={pct_fmt(qoq)}, yoy={pct_fmt(yoy)}, trend={trend}, score={pretty(score)}"}

# ============================================================
# DRIVER SCORE
# ============================================================

def score_azure_cloud(manual: Dict[str, Any], capex_signal: Dict[str, Any]) -> Tuple[float, str]:
    azure_yoy = _safe_float(manual.get("AZURE_GROWTH_YOY"))
    guide = _safe_float(manual.get("CLOUD_GUIDANCE_SURPRISE"))
    parts = []
    if not pd.isna(azure_yoy):
        if azure_yoy >= 0.30:
            parts.append((1.0, 0.55))
        elif azure_yoy >= 0.22:
            parts.append((0.45, 0.55))
        elif azure_yoy >= 0.16:
            parts.append((0.0, 0.55))
        elif azure_yoy >= 0.10:
            parts.append((-0.45, 0.55))
        else:
            parts.append((-0.9, 0.55))
    if not pd.isna(guide):
        if guide >= 0.04:
            parts.append((1.0, 0.30))
        elif guide >= 0.00:
            parts.append((0.20, 0.30))
        elif guide >= -0.03:
            parts.append((-0.30, 0.30))
        else:
            parts.append((-1.0, 0.30))
    capex_score = _safe_float(capex_signal.get("score"))
    if not pd.isna(capex_score):
        parts.append((clamp_score(capex_score), 0.15))
    if not parts:
        return 0.0, "No Azure/guidance manual input; neutral."
    score = sum(v * w for v, w in parts) / sum(w for _, w in parts)
    return clamp_score(score), f"Azure score from Azure YoY={pct_fmt(azure_yoy)}, guidance surprise={pct_fmt(guide)}, CapEx commitment={pretty(capex_score)}"


def score_margin_fcf(fundamentals: Dict[str, Any], manual: Dict[str, Any]) -> Tuple[float, str]:
    gm = _safe_float(fundamentals.get("gross_margin"))
    om = _safe_float(fundamentals.get("operating_margin"))
    fcfm = _safe_float(fundamentals.get("fcf_margin"))
    cloud_margin_score = clamp_score(manual.get("CLOUD_MARGIN_SCORE", 0.0))
    if pd.isna(cloud_margin_score):
        cloud_margin_score = 0.0
    parts = []
    if not pd.isna(om):
        if om >= 0.43:
            parts.append((1.0, 0.35))
        elif om >= 0.38:
            parts.append((0.4, 0.35))
        elif om >= 0.32:
            parts.append((0.0, 0.35))
        else:
            parts.append((-0.7, 0.35))
    if not pd.isna(fcfm):
        if fcfm >= 0.28:
            parts.append((1.0, 0.30))
        elif fcfm >= 0.22:
            parts.append((0.4, 0.30))
        elif fcfm >= 0.16:
            parts.append((0.0, 0.30))
        else:
            parts.append((-0.7, 0.30))
    if not pd.isna(gm):
        if gm >= 0.68:
            parts.append((0.6, 0.15))
        elif gm >= 0.62:
            parts.append((0.2, 0.15))
        else:
            parts.append((-0.4, 0.15))
    parts.append((cloud_margin_score, 0.20))
    score = sum(v * w for v, w in parts) / sum(w for _, w in parts)
    return clamp_score(score), f"Margin/FCF from operating margin={pct_fmt(om)}, FCF margin={pct_fmt(fcfm)}, gross margin={pct_fmt(gm)}, manual cloud margin={pretty(cloud_margin_score)}"


def compute_msft_driver_score(capex_signal: Dict[str, Any], pe_pack: Dict[str, Any], peg_pack: Dict[str, Any], res_macro: Dict[str, Any] | None, fundamentals: Dict[str, Any], manual: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    azure_score, azure_note = score_azure_cloud(manual, capex_signal)
    copilot_score = clamp_score(manual.get("COPILOT_MONETIZATION_SCORE", 0.0)); copilot_score = 0.0 if pd.isna(copilot_score) else copilot_score
    margin_score, margin_note = score_margin_fcf(fundamentals, manual)
    capex_eff = clamp_score(manual.get("AI_CAPEX_EFFICIENCY_SCORE", 0.0)); capex_eff = 0.0 if pd.isna(capex_eff) else capex_eff
    enterprise = clamp_score(manual.get("ENTERPRISE_DURABILITY_SCORE", 0.0)); enterprise = 0.0 if pd.isna(enterprise) else enterprise
    platform_risk = clamp_score(manual.get("PLATFORM_RISK_SCORE", 0.0)); platform_risk = 0.0 if pd.isna(platform_risk) else platform_risk
    gaming_pc = clamp_score(manual.get("GAMING_PC_SCORE", 0.0)); gaming_pc = 0.0 if pd.isna(gaming_pc) else gaming_pc
    enterprise_score = clamp_score(0.80 * enterprise + 0.20 * gaming_pc)

    valuation_scale = combine_valuation_scale(pe_pack.get("pe_scale", 1.0), peg_pack.get("peg_scale", 1.0), rules)
    valuation_score = clamp_score((valuation_scale - 0.60) / 0.60)
    macro_risk = _safe_float(res_macro.get("latest", {}).get("TotalScore", np.nan)) if res_macro else np.nan
    macro_score = 0.0 if pd.isna(macro_risk) else clamp_score(-macro_risk / 1.5)
    valuation_macro_score = clamp_score(0.65 * valuation_score + 0.35 * macro_score)

    scores = {
        "Azure_Cloud_AI": azure_score,
        "Copilot_Monetization": copilot_score,
        "Margin_FCF": margin_score,
        "AI_CapEx_Efficiency": capex_eff,
        "Enterprise_Durability": enterprise_score,
        "Platform_Risk": platform_risk,
        "Valuation_Macro": valuation_macro_score,
    }
    weights = rules.get("DRIVER_WEIGHTS", {})
    total_w = sum(weights.values())
    total_score = sum(scores[k] * weights.get(k, 0.0) for k in scores) / total_w if total_w > 0 else 0.0
    if total_score >= 0.45:
        state, driver_scale = "STRONG", float(rules["DRIVER_SCALE_STRONG"])
    elif total_score >= -0.15:
        state, driver_scale = "STABLE", float(rules["DRIVER_SCALE_STABLE"])
    elif total_score >= -0.45:
        state, driver_scale = "WEAK", float(rules["DRIVER_SCALE_WEAK"])
    else:
        state, driver_scale = "BAD", float(rules["DRIVER_SCALE_BAD"])
    score_df = pd.DataFrame([{"driver": k, "score": v, "weight": weights.get(k, 0.0), "weighted": v * weights.get(k, 0.0)} for k, v in scores.items()])
    notes = {
        "azure_note": azure_note,
        "margin_note": margin_note,
        "copilot_note": "Manual score. Update after Copilot adoption, ARPU, seat expansion, and AI revenue commentary.",
        "capex_note": capex_signal.get("note", ""),
        "capex_efficiency_note": "Manual score. Positive only if AI CapEx turns into Azure/AI revenue acceleration, not just higher depreciation.",
        "risk_note": "Manual score. Negative means antitrust/OpenAI dependency/power constraint risk expands.",
    }
    return {"total_score": float(total_score), "driver_state": state, "driver_scale": float(driver_scale), "score_df": score_df, "scores": scores, "notes": notes}

# ============================================================
# PEG
# ============================================================

def _cap_growth_for_peg(growth_rate: Any, rules: Dict[str, Any]) -> float:
    growth_rate = _safe_float(growth_rate)
    if pd.isna(growth_rate):
        return np.nan
    min_g, max_g = float(rules["PEG_MIN_GROWTH"]), float(rules["PEG_MAX_GROWTH"])
    if growth_rate < min_g:
        return np.nan
    return float(np.clip(growth_rate, min_g, max_g))


def compute_msft_ai_adjusted_growth(raw_forward_eps_growth: float, manual: Dict[str, Any], capex_signal: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    azure_score, _ = score_azure_cloud(manual, capex_signal)
    copilot = clamp_score(manual.get("COPILOT_MONETIZATION_SCORE", 0.0)); copilot = 0.0 if pd.isna(copilot) else copilot
    capex_eff = clamp_score(manual.get("AI_CAPEX_EFFICIENCY_SCORE", 0.0)); capex_eff = 0.0 if pd.isna(capex_eff) else capex_eff
    quality_score = 0.55 * azure_score + 0.25 * copilot + 0.20 * capex_eff
    if quality_score >= 0.60:
        quality = "ACCELERATING"
    elif quality_score >= 0.25:
        quality = "STRONG"
    elif quality_score <= -0.35:
        quality = "WEAK"
    else:
        quality = "STABLE"
    qr = rules.get("PEG_GROWTH_QUALITY_RULES", {}).get(quality, rules["PEG_GROWTH_QUALITY_RULES"]["UNKNOWN"])
    reliability = float(qr["reliability"])
    soft_upper = float(qr["soft_upper"])
    scale_bias = float(qr["scale_bias"])
    min_adj = float(rules["PEG_MIN_ADJUSTED_GROWTH"])
    if pd.isna(raw_forward_eps_growth) or raw_forward_eps_growth <= 0:
        adjusted = float(rules["PEG_UNKNOWN_FALLBACK_GROWTH"])
        note = "Raw forward EPS growth missing; using conservative fallback"
    else:
        adjusted = soft_saturate_growth(raw_forward_eps_growth, reliability, soft_upper, min_adj)
        note = f"MSFT AI-adjusted growth by quality={quality}"
    return {"adjusted_growth_rate": float(adjusted), "growth_quality": quality, "growth_quality_score": float(quality_score), "growth_reliability": reliability, "growth_soft_upper": soft_upper, "growth_scale_bias": scale_bias, "growth_note": note}


def compute_peg_pack(ticker: str, pe_pack: Dict[str, Any], manual: Dict[str, Any], capex_signal: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    if not rules.get("PEG_ENABLE", True):
        return {"peg_enabled": False, "peg": np.nan, "raw_growth_rate": np.nan, "used_growth_rate": np.nan, "growth_source": "DISABLED", "growth_quality": "DISABLED", "peg_state": "DISABLED", "peg_scale": 1.0, "peg_block": False, "peg_note": "PEG disabled"}
    selected_pe = _safe_float(pe_pack.get("selected_pe"))
    forward_eps = _safe_float(pe_pack.get("forward_eps"))
    trailing_eps = _safe_float(pe_pack.get("trailing_eps"))
    fundamentals = fetch_fundamentals(ticker)
    yf_earnings_growth = _safe_float(fundamentals.get("earnings_growth"))
    manual_growth = _safe_float(rules.get("MANUAL_EPS_GROWTH"))
    raw_forward_eps_growth = np.nan
    if not pd.isna(forward_eps) and not pd.isna(trailing_eps) and trailing_eps > 0:
        raw_forward_eps_growth = forward_eps / trailing_eps - 1.0
    source = str(rules.get("PEG_GROWTH_SOURCE", "MSFT_AI_ADJUSTED")).upper()
    chosen_source = source
    growth_quality, growth_scale_bias, growth_note = "UNKNOWN", 1.0, ""
    growth_reliability, growth_soft_upper = np.nan, np.nan
    raw_growth_rate, used_growth_rate = np.nan, np.nan
    if source == "MSFT_AI_ADJUSTED":
        raw_growth_rate = raw_forward_eps_growth
        adj = compute_msft_ai_adjusted_growth(raw_forward_eps_growth, manual, capex_signal, rules)
        used_growth_rate = adj["adjusted_growth_rate"]
        growth_quality = adj["growth_quality"]
        growth_reliability = adj["growth_reliability"]
        growth_soft_upper = adj["growth_soft_upper"]
        growth_scale_bias = adj["growth_scale_bias"]
        growth_note = adj["growth_note"]
        chosen_source = "MSFT_AI_ADJUSTED"
    elif source == "CAPPED_FORWARD_EPS":
        raw_growth_rate = raw_forward_eps_growth
        used_growth_rate = _cap_growth_for_peg(raw_forward_eps_growth, rules)
        growth_note = "Capped forward EPS growth"
    elif source == "MANUAL":
        raw_growth_rate = manual_growth
        used_growth_rate = _cap_growth_for_peg(manual_growth, rules)
        growth_note = "Manual EPS growth"
    elif source == "YF_EARNINGS_GROWTH":
        raw_growth_rate = yf_earnings_growth
        used_growth_rate = _cap_growth_for_peg(yf_earnings_growth, rules)
        growth_note = "YFinance earningsGrowth"
    elif source == "BLENDED":
        candidates = [_cap_growth_for_peg(x, rules) for x in [raw_forward_eps_growth, yf_earnings_growth, manual_growth]]
        candidates = [x for x in candidates if not pd.isna(x)]
        used_growth_rate = float(np.mean(candidates)) if candidates else np.nan
        raws = [x for x in [raw_forward_eps_growth, yf_earnings_growth, manual_growth] if not pd.isna(x)]
        raw_growth_rate = float(np.mean(raws)) if raws else np.nan
        growth_note = "Blended capped growth"
    if pd.isna(used_growth_rate) or used_growth_rate <= 0:
        fb = _cap_growth_for_peg(raw_forward_eps_growth, rules)
        if not pd.isna(fb):
            used_growth_rate = fb
            chosen_source = "FALLBACK_CAPPED_FORWARD_EPS"
            growth_note = "Adjusted growth failed; fallback to capped forward EPS"
        else:
            used_growth_rate = float(rules["PEG_UNKNOWN_FALLBACK_GROWTH"])
            chosen_source = "UNKNOWN_FALLBACK"
            growth_note = "All PEG growth sources failed; using fallback"
    if pd.isna(selected_pe) or selected_pe <= 0:
        return {"peg_enabled": True, "peg": np.nan, "raw_growth_rate": raw_growth_rate, "used_growth_rate": used_growth_rate, "raw_growth_pct": raw_growth_rate * 100 if not pd.isna(raw_growth_rate) else np.nan, "used_growth_pct": used_growth_rate * 100 if not pd.isna(used_growth_rate) else np.nan, "growth_source": chosen_source, "growth_quality": growth_quality, "growth_reliability": growth_reliability, "growth_soft_upper": growth_soft_upper, "peg_state": "PE_MISSING", "peg_scale": float(rules["PEG_MISSING_SCALE"]), "peg_block": False, "peg_note": "Cannot compute PEG because PE is missing"}
    used_growth_pct = used_growth_rate * 100.0
    peg = selected_pe / used_growth_pct
    cheap, fair, warm, expensive, hard_block = [float(rules[k]) for k in ["PEG_CHEAP", "PEG_FAIR", "PEG_WARM", "PEG_EXPENSIVE", "PEG_HARD_BLOCK"]]
    if peg <= cheap:
        state, scale = "CHEAP", float(rules["PEG_SCALE_CHEAP"])
    elif peg <= fair:
        state, scale = "FAIR", float(rules["PEG_SCALE_FAIR"])
    elif peg <= warm:
        state, scale = "WARM", float(rules["PEG_SCALE_WARM"])
    elif peg <= expensive:
        state, scale = "EXPENSIVE", float(rules["PEG_SCALE_EXPENSIVE"])
    elif peg <= hard_block:
        state, scale = "VERY_EXPENSIVE", float(rules["PEG_SCALE_VERY_EXPENSIVE"])
    else:
        state = "EXTREME"
        scale = 0.0 if rules.get("PEG_HARD_BLOCK_ENABLE", False) else float(rules["PEG_SCALE_VERY_EXPENSIVE"])
    scale *= float(growth_scale_bias)
    return {"peg_enabled": True, "peg": float(peg), "raw_growth_rate": raw_growth_rate, "used_growth_rate": float(used_growth_rate), "raw_growth_pct": raw_growth_rate * 100 if not pd.isna(raw_growth_rate) else np.nan, "used_growth_pct": float(used_growth_pct), "forward_eps_growth": raw_forward_eps_growth, "yf_earnings_growth": yf_earnings_growth, "manual_growth": manual_growth, "growth_source": chosen_source, "growth_quality": growth_quality, "growth_reliability": growth_reliability, "growth_soft_upper": growth_soft_upper, "growth_scale_bias": growth_scale_bias, "peg_state": state, "peg_scale": float(scale), "peg_block": bool(state == "EXTREME" and rules.get("PEG_HARD_BLOCK_ENABLE", False)), "peg_note": f"{growth_note}; PEG = PE / adjusted growth%"}


def combine_valuation_scale(pe_scale: Any, peg_scale: Any, rules: Dict[str, Any]) -> float:
    mode = str(rules.get("VALUATION_COMBINE_MODE", "MIN")).upper()
    pe_scale = float(pe_scale)
    peg_scale = float(peg_scale)
    if mode == "PRODUCT":
        return pe_scale * peg_scale
    if mode == "AVERAGE":
        return (pe_scale + peg_scale) / 2.0
    return min(pe_scale, peg_scale)

# ============================================================
# HOLDINGS / LEVERAGE / BUY PLAN
# ============================================================

def equity_curve(daily_ret: pd.Series, base: float = 1.0) -> pd.Series:
    return base * (1.0 + daily_ret).cumprod()


def drawdown_now(daily_ret: pd.Series) -> float:
    eq = equity_curve(daily_ret)
    peak = eq.cummax()
    return float(((eq - peak) / peak).iloc[-1])


def compute_holdings(price: float) -> pd.DataFrame:
    market_value = MSFT_SHARES * price
    cost_value = MSFT_SHARES * MSFT_AVG_COST
    unreal_pnl = market_value - cost_value
    unreal_pnl_pct = unreal_pnl / cost_value if cost_value > 0 else np.nan
    return pd.DataFrame([{"ticker": CORE_TICKER, "shares": MSFT_SHARES, "price": price, "market_value": market_value, "avg_cost": MSFT_AVG_COST, "cost_value": cost_value, "unreal_pnl": unreal_pnl, "unreal_pnl_pct": unreal_pnl_pct, "stock_ratio": market_value / EQUITY_USD if EQUITY_USD > 0 else np.nan, "cash_ratio": FREE_CASH_USD / EQUITY_USD if EQUITY_USD > 0 else np.nan}]).set_index("ticker")


def dd_governor(L_raw: float, dd_now: float) -> float:
    L = float(L_raw)
    for wall, cap in DD_WALLS:
        if dd_now < wall:
            L = min(L, cap)
            break
    return float(max(L, 0.0))


def leverage_from_cash_or_margin(equity_usd: float, free_cash_usd: float, current_stock_usd: float) -> float:
    if equity_usd <= 0:
        return 1.0
    if ALLOW_MARGIN_BUY:
        return float(MAX_MANUAL_GROSS_LEVERAGE)
    max_stock_usd = current_stock_usd + max(0.0, free_cash_usd) * HAIRCUT
    return float(max_stock_usd / equity_usd)


def leverage_engine(sigma_ann: float, dd_now: float, regime: str, crisis_on: bool, limits: Dict[str, Any], equity_usd: float, free_cash_usd: float, current_stock_usd: float) -> Dict[str, float]:
    L_vol = SIGMA_TARGET / sigma_ann if sigma_ann and sigma_ann > 1e-9 else 0.0
    L_dd = dd_governor(L_vol, dd_now)
    if crisis_on or regime == "CRISIS":
        L_reg = 0.0
    elif regime == "DATA-UNSTABLE":
        L_reg = min(L_dd, DATA_UNSTABLE_MAX_LEV)
    else:
        L_reg = min(L_dd, float(limits.get("max_leverage", 1.0)))
    L_bp = leverage_from_cash_or_margin(equity_usd, free_cash_usd, current_stock_usd)
    return {"L_vol": float(max(L_vol, 0.0)), "L_dd": float(max(L_dd, 0.0)), "L_reg": float(max(L_reg, 0.0)), "L_buying_power": float(max(L_bp, 0.0)), "L_final": float(max(min(L_reg, L_bp), 0.0))}


def build_msft_buy_plan(stock_risk: Dict[str, Any], holdings: pd.DataFrame, lev_pack: Dict[str, Any], res_macro: Dict[str, Any] | None) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    px = stock_risk["last_price"]
    trend_scale = float(stock_risk["trend_scale"])
    pe_pack = compute_pe_pack(CORE_TICKER, px, RISK_RULES)
    capex_series, capex_source = extract_capex_from_cashflow(CORE_TICKER)
    capex_signal = compute_capex_signal(capex_series, RISK_RULES)
    capex_signal["capex_source"] = capex_source
    peg_pack = compute_peg_pack(CORE_TICKER, pe_pack, MSFT_MANUAL, capex_signal, RISK_RULES)
    valuation_scale = combine_valuation_scale(pe_pack["pe_scale"], peg_pack["peg_scale"], RISK_RULES)
    fundamentals = fetch_fundamentals(CORE_TICKER)
    driver_pack = compute_msft_driver_score(capex_signal, pe_pack, peg_pack, res_macro, fundamentals, MSFT_MANUAL, RISK_RULES)
    driver_scale = float(driver_pack["driver_scale"])

    regime = res_macro["regime"] if res_macro else "DATA-UNSTABLE"
    crisis_on = bool(res_macro["crisis_on"]) if res_macro else False
    disloc = res_macro["latest"].get("Dislocation", np.nan) if res_macro else np.nan
    disloc_thr = res_macro["disloc_thr"] if res_macro else DEFAULT_DISLOC_THR
    dd_120 = stock_risk["dd_120"]
    atr_pct = stock_risk["atr_pct"]

    max_cash_buy_usd = max(0.0, FREE_CASH_USD * HAIRCUT) * MAX_DAILY_CASH_USE_FRAC
    current_msft_usd = float(holdings.loc[CORE_TICKER, "market_value"])
    if ALLOW_MARGIN_BUY:
        gross_cap_usd = EQUITY_USD * MAX_MANUAL_GROSS_LEVERAGE
        max_buy_usd = max(0.0, gross_cap_usd - current_msft_usd)
    else:
        max_buy_usd = max_cash_buy_usd

    buy_scale = trend_scale * valuation_scale * driver_scale
    buy_scale = float(np.clip(buy_scale, 0.0, 1.20))
    desired_buy_usd = max_buy_usd * buy_scale
    if RISK_RULES.get("ADD_ENABLE", True) and dd_120 <= -float(RISK_RULES.get("ADD_DD", 0.12)):
        desired_buy_usd = max(desired_buy_usd, max_buy_usd * float(RISK_RULES.get("ADD_BUY_FRAC_OF_CASH", 0.25)))
    desired_buy_usd = min(desired_buy_usd, max_buy_usd)

    reasons = []
    block = False
    if RISK_RULES.get("MACRO_HARD_BLOCK_ENABLE", True):
        if crisis_on or regime == "CRISIS":
            reasons.append("Macro crisis hard block")
            block = True
        if not pd.isna(disloc) and disloc > disloc_thr:
            reasons.append("Fast dislocation hard block")
            block = True
    if trend_scale <= 0:
        reasons.append("Trend scale = 0")
        block = True
    if pe_pack.get("pe_block", False):
        reasons.append("PE hard block")
        block = True
    if peg_pack.get("peg_block", False):
        reasons.append("PEG hard block")
        block = True
    if not pd.isna(atr_pct) and atr_pct > float(RISK_RULES.get("NO_BUY_IF_ATR_ABOVE", 0.045)):
        reasons.append("ATR too high")
        block = True
    if not pd.isna(dd_120) and dd_120 < float(RISK_RULES.get("NO_BUY_IF_DD_BELOW", -0.35)):
        reasons.append("Extreme drawdown catching-knife block")
        block = True

    if block:
        desired_buy_usd = 0.0
    shares = shares_from_usd(desired_buy_usd, px)
    est_buy_usd = shares * px if not pd.isna(shares) else 0.0
    if est_buy_usd < MIN_TRADE_USD or pd.isna(shares):
        action = "HOLD"
        if not block:
            reasons.append("Insufficient cash or scale too small")
    else:
        action = "BUY"

    unused_cash = max(0.0, FREE_CASH_USD - est_buy_usd) if not ALLOW_MARGIN_BUY else FREE_CASH_USD
    buy_plan = {
        "ticker": CORE_TICKER,
        "action": action,
        "block": bool(block),
        "reasons": reasons,
        "shares": shares,
        "price": px,
        "est_buy_usd": float(est_buy_usd),
        "unused_cash_usd": float(unused_cash),
        "max_buy_usd": float(max_buy_usd),
        "buy_scale": float(buy_scale),
        "trend_state": stock_risk["trend_state"],
        "trend_scale": trend_scale,
        "pe_state": pe_pack["pe_state"],
        "pe_scale": pe_pack["pe_scale"],
        "peg_state": peg_pack["peg_state"],
        "peg_scale": peg_pack["peg_scale"],
        "valuation_scale": float(valuation_scale),
        "driver_state": driver_pack["driver_state"],
        "driver_scale": driver_scale,
        "driver_total_score": driver_pack["total_score"],
        "capex_quality": capex_signal["quality"],
        "capex_score": capex_signal["score"],
        "regime": regime,
        "crisis_on": crisis_on,
        "dd_120": dd_120,
        "atr_pct": atr_pct,
        "sigma_60": stock_risk["sigma_60"],
        "forward_pe": pe_pack.get("forward_pe"),
        "trailing_pe": pe_pack.get("trailing_pe"),
        "selected_pe": pe_pack.get("selected_pe"),
        "peg": peg_pack.get("peg"),
        "used_growth_pct": peg_pack.get("used_growth_pct"),
        "gross_margin": fundamentals.get("gross_margin"),
        "operating_margin": fundamentals.get("operating_margin"),
        "fcf_margin": fundamentals.get("fcf_margin"),
        "manual_execution_only": True,
    }
    return buy_plan, pe_pack, peg_pack, capex_signal, driver_pack, fundamentals


def run_system(show_charts: bool = False) -> Dict[str, Any]:
    res_macro = build_macro_dashboard(DEFAULT_START, DEFAULT_END, DEFAULT_LOOKBACK, DEFAULT_MACRO_WEIGHTS, DEFAULT_MACRO_THRESHOLDS, DEFAULT_DISLOC_THR, DEFAULT_FFILL_LIMIT)
    stock_risk = compute_stock_risk(CORE_TICKER, DEFAULT_END, RISK_RULES, MSFT_AVG_COST)
    holdings = compute_holdings(stock_risk["last_price"])
    current_stock_usd = float(holdings.loc[CORE_TICKER, "market_value"])
    dd = drawdown_now(stock_risk["ret"])
    lev_pack = leverage_engine(stock_risk["sigma_60"], dd, res_macro["regime"] if res_macro else "DATA-UNSTABLE", res_macro["crisis_on"] if res_macro else False, res_macro["limits"] if res_macro else {"max_leverage": DATA_UNSTABLE_MAX_LEV}, EQUITY_USD, FREE_CASH_USD, current_stock_usd)
    buy_plan, pe_pack, peg_pack, capex_signal, driver_pack, fundamentals = build_msft_buy_plan(stock_risk, holdings, lev_pack, res_macro)
    return {"stock_risk": stock_risk, "holdings": holdings, "leverage": lev_pack, "macro": res_macro, "buy_plan": buy_plan, "pe": pe_pack, "peg": peg_pack, "capex": capex_signal, "driver": driver_pack, "fundamentals": fundamentals}
