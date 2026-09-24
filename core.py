"""
core.py: الحسابات (بدون واجهة)
المؤشرات، الاختبار، استخراج الصفقات، صائد الفرص، وتنظيف الأخبار.
"""
import numpy as np
import pandas as pd

# ============ قوائم جاهزة ============
WATCHLISTS = {
    "أسهم أمريكية كبرى": [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX",
        "JPM", "V", "MA", "UNH", "XOM", "LLY", "COST", "WMT", "ORCL", "CRM",
        "ADBE", "INTC", "QCOM", "PLTR", "COIN", "MSTR", "SMCI", "ARM", "UBER", "SHOP",
    ],
    "كريبتو": [
        "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
        "ADA-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "DOT-USD",
    ],
    "السوق السعودي": [
        "2222.SR", "1120.SR", "2010.SR", "1180.SR", "7010.SR",
        "2082.SR", "1211.SR", "4030.SR", "1150.SR", "2380.SR",
    ],
}


# ============ تنظيف البيانات ============
def flatten(df: pd.DataFrame) -> pd.DataFrame:
    """بعض إصدارات yfinance ترجع أعمدة بمستويين، نخليها مستوى واحد."""
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df.dropna(subset=["Close"])


def split_multi(df: pd.DataFrame, symbols: list) -> dict:
    """يفصل تحميل عدة رموز لجدول لكل رمز."""
    out = {}
    if df is None or df.empty:
        return out
    if not isinstance(df.columns, pd.MultiIndex):
        if len(symbols) == 1:
            out[symbols[0]] = df.dropna(subset=["Close"])
        return out
    lvl0 = set(df.columns.get_level_values(0))
    for s in symbols:
        try:
            sub = df[s] if s in lvl0 else df.xs(s, axis=1, level=1)
        except KeyError:
            continue
        sub = sub.dropna(subset=["Close"])
        if not sub.empty:
            out[s] = sub
    return out


# ============ المؤشرات ============
def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df["Close"]
    df["SMA20"] = c.rolling(20).mean()
    df["SMA50"] = c.rolling(50).mean()
    df["SMA200"] = c.rolling(200).mean()
    df["RSI"] = rsi(c)
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    if "Volume" in df:
        df["VolAvg20"] = df["Volume"].rolling(20).mean()
    return df


def quote_from_daily(df: pd.DataFrame) -> dict:
    """ملخص السعر (زي رأس الصفحة في Webull) من البيانات اليومية."""
    last, prev = df.iloc[-1], df.iloc[-2] if len(df) > 1 else df.iloc[-1]
    yr = df.tail(252)
    return {
        "price": float(last["Close"]),
        "change": float(last["Close"] - prev["Close"]),
        "change_pct": float((last["Close"] / prev["Close"] - 1) * 100),
        "open": float(last.get("Open", np.nan)),
        "high": float(last.get("High", np.nan)),
        "low": float(last.get("Low", np.nan)),
        "volume": float(last.get("Volume", np.nan)),
        "avg_volume": float(df["Volume"].tail(20).mean()) if "Volume" in df else np.nan,
        "high_52w": float(yr["High"].max()) if "High" in yr else float(yr["Close"].max()),
        "low_52w": float(yr["Low"].min()) if "Low" in yr else float(yr["Close"].min()),
        "date": df.index[-1],
    }


# ============ الاستراتيجية والاختبار ============
def run_backtest(df, short_w=20, long_w=50, capital=10000, fee=0.001):
    data = df[["Close"]].copy()
    data["SMA_short"] = data["Close"].rolling(short_w).mean()
    data["SMA_long"] = data["Close"].rolling(long_w).mean()
    data = data.dropna()
    if data.empty:
        return data

    data["Position"] = (data["SMA_short"] > data["SMA_long"]).astype(int)
    data["Trade"] = data["Position"].diff()
    data.iloc[0, data.columns.get_loc("Trade")] = data["Position"].iloc[0]  # لو بدأنا داخل السوق

    data["Market_Return"] = data["Close"].pct_change().fillna(0)
    data["Strategy_Return"] = data["Position"].shift(1).fillna(0) * data["Market_Return"]
    data["Strategy_Return"] -= data["Trade"].abs().shift(1).fillna(0) * fee

    data["Bot_Equity"] = capital * (1 + data["Strategy_Return"]).cumprod()
    data["Hold_Equity"] = capital * (1 + data["Market_Return"]).cumprod()
    return data


def extract_trades(data: pd.DataFrame, capital=10000, fee=0.001) -> pd.DataFrame:
    """يحوّل إشارات البوت لجدول صفقات: دخول، خروج، ربح/خسارة."""
    cols = ["الدخول", "سعر الدخول", "الخروج", "سعر الخروج", "الأيام", "الربح %", "الربح $", "الحالة"]
    if data.empty:
        return pd.DataFrame(columns=cols)

    rows, entry_date, entry_price = [], None, None
    for date, row in data.iterrows():
        if row["Trade"] == 1:
            entry_date, entry_price = date, row["Close"]
        elif row["Trade"] == -1 and entry_date is not None:
            rows.append([entry_date, entry_price, date, row["Close"], "مغلقة"])
            entry_date = None
    if entry_date is not None:  # صفقة ما زالت مفتوحة
        rows.append([entry_date, entry_price, data.index[-1], data["Close"].iloc[-1], "مفتوحة"])

    equity, out = capital, []
    for e_date, e_price, x_date, x_price, status in rows:
        fees = 2 * fee if status == "مغلقة" else fee
        pnl = x_price / e_price - 1 - fees
        profit = equity * pnl
        equity += profit
        out.append([e_date, e_price, x_date, x_price, (x_date - e_date).days, pnl * 100, profit, status])
    return pd.DataFrame(out, columns=cols)


def trade_stats(trades: pd.DataFrame) -> dict:
    closed = trades[trades["الحالة"] == "مغلقة"] if not trades.empty else trades
    if closed.empty:
        return {"count": 0}
    wins = closed[closed["الربح %"] > 0]
    losses = closed[closed["الربح %"] <= 0]
    gross_win = wins["الربح $"].sum()
    gross_loss = -losses["الربح $"].sum()
    return {
        "count": len(closed),
        "win_rate": len(wins) / len(closed) * 100,
        "avg_win": wins["الربح %"].mean() if len(wins) else 0.0,
        "avg_loss": losses["الربح %"].mean() if len(losses) else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss > 0 else np.inf,
        "best": closed["الربح %"].max(),
        "worst": closed["الربح %"].min(),
        "avg_days": closed["الأيام"].mean(),
        "total_profit": closed["الربح $"].sum(),
    }


# ============ صائد الفرص ============
def scan_symbol(df: pd.DataFrame) -> dict | None:
    """يفحص رمز واحد ويرجع الإشارات اللي انطبقت عليه اليوم."""
    if df is None or len(df) < 60:
        return None
    d = add_indicators(df)
    last, prev = d.iloc[-1], d.iloc[-2]
    signals, score = [], 0

    # تقاطع ذهبي خلال آخر 3 أيام
    above = (d["SMA20"] > d["SMA50"]).astype(int)
    if above.iloc[-1] == 1 and above.iloc[-4:-1].min() == 0:
        signals.append("🟢 تقاطع ذهبي"); score += 2
    elif above.iloc[-1] == 0 and above.iloc[-4:-1].max() == 1:
        signals.append("🔴 تقاطع سلبي"); score -= 2

    if last["RSI"] < 30:
        signals.append("🟢 تشبع بيعي (RSI)"); score += 1
    elif last["RSI"] > 70:
        signals.append("🟠 تشبع شرائي (RSI)"); score -= 1

    vol_ratio = np.nan
    if "Volume" in d and last.get("VolAvg20", 0) > 0:
        vol_ratio = last["Volume"] / last["VolAvg20"]
        if vol_ratio >= 2:
            signals.append(f"🔥 حجم ×{vol_ratio:.1f}"); score += 1

    if last["Close"] >= d["Close"].iloc[-21:-1].max():
        signals.append("🚀 اختراق قمة 20 يوم"); score += 1

    high_52 = d["Close"].tail(252).max()
    if last["Close"] >= 0.98 * high_52:
        signals.append("⭐ قرب القمة السنوية"); score += 1

    if "Open" in d:
        gap = (last["Open"] / prev["Close"] - 1) * 100
        if gap >= 3:
            signals.append(f"⬆️ فجوة +{gap:.1f}%"); score += 1
        elif gap <= -3:
            signals.append(f"⬇️ فجوة {gap:.1f}%")

    if pd.notna(last["SMA200"]):
        if last["Close"] > last["SMA200"]:
            score += 1
        else:
            signals.append("⚠️ تحت متوسط 200")

    if last["MACD"] > last["MACD_signal"] and prev["MACD"] <= prev["MACD_signal"]:
        signals.append("🟢 تقاطع MACD"); score += 1

    return {
        "السعر": float(last["Close"]),
        "التغير %": float((last["Close"] / prev["Close"] - 1) * 100),
        "RSI": float(last["RSI"]),
        "الحجم ×": float(vol_ratio) if pd.notna(vol_ratio) else None,
        "النقاط": score,
        "الإشارات": " · ".join(signals) if signals else "—",
    }


def scan(data_by_symbol: dict) -> pd.DataFrame:
    rows = []
    for sym, df in data_by_symbol.items():
        r = scan_symbol(df)
        if r:
            rows.append({"الرمز": sym, **r})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("النقاط", ascending=False).reset_index(drop=True)


# ============ الأخبار والمحفزات ============
def parse_news(items) -> list:
    """يوحّد شكل الأخبار (yfinance غيّر شكلها أكثر من مرة)."""
    out = []
    for it in items or []:
        c = it.get("content", it) if isinstance(it, dict) else {}
        title = c.get("title")
        if not title:
            continue
        link = ((c.get("canonicalUrl") or {}).get("url")
                or (c.get("clickThroughUrl") or {}).get("url")
                or c.get("link") or "")
        prov = c.get("provider")
        source = prov.get("displayName", "") if isinstance(prov, dict) else (c.get("publisher") or "")
        pub = c.get("pubDate") or c.get("displayTime") or c.get("providerPublishTime")
        if isinstance(pub, (int, float)):
            ts = pd.to_datetime(pub, unit="s", utc=True)
        else:
            ts = pd.to_datetime(pub, utc=True, errors="coerce")
        out.append({"title": title, "link": link, "source": source,
                    "time": ts, "summary": c.get("summary") or ""})
    return out


def earnings_date(calendar):
    """يطلع أقرب موعد إعلان أرباح من calendar."""
    try:
        if isinstance(calendar, dict):
            dates = calendar.get("Earnings Date") or []
        elif isinstance(calendar, pd.DataFrame) and "Earnings Date" in calendar.index:
            dates = list(calendar.loc["Earnings Date"].values)
        else:
            return None
        dates = [pd.Timestamp(x) for x in dates if x is not None]
        return min(dates) if dates else None
    except Exception:
        return None


def recent_ratings(df: pd.DataFrame, days=30) -> pd.DataFrame:
    """ترقيات وتخفيضات المحللين خلال آخر X يوم."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    d = df.copy()
    idx = pd.to_datetime(d.index, errors="coerce")
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    d.index = idx
    d = d[d.index >= pd.Timestamp.now() - pd.Timedelta(days=days)].sort_index(ascending=False)
    return d


def time_ago(ts) -> str:
    if ts is None or pd.isna(ts):
        return ""
    mins = (pd.Timestamp.now(tz="UTC") - ts).total_seconds() / 60
    if mins < 60:
        return f"قبل {int(max(mins, 1))} دقيقة"
    if mins < 60 * 24:
        return f"قبل {int(mins // 60)} ساعة"
    return f"قبل {int(mins // 1440)} يوم"


def fmt_big(x) -> str:
    if x is None or pd.isna(x):
        return "—"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(x) >= div:
            return f"{x / div:.2f}{unit}"
    return f"{x:,.0f}"
