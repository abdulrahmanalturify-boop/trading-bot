"""
ta.py - Technical indicators (pure pandas, no UI).
Every function takes an OHLCV DataFrame (Open, High, Low, Close, Volume) or a Series.
"""
import numpy as np
import pandas as pd


def sma(s, n):
    return s.rolling(n).mean()


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(close, n=14):
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


def macd(close, fast=12, slow=26, signal=9):
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return line, sig, line - sig


def bollinger(close, n=20, k=2.0):
    mid = sma(close, n)
    sd = close.rolling(n).std()
    upper, lower = mid + k * sd, mid - k * sd
    width = (upper - lower) / mid
    return mid, upper, lower, width


def true_range(df):
    prev = df["Close"].shift(1)
    return pd.concat([df["High"] - df["Low"], (df["High"] - prev).abs(), (df["Low"] - prev).abs()],
                     axis=1).max(axis=1)


def atr(df, n=14):
    return true_range(df).ewm(alpha=1 / n, adjust=False).mean()


def stochastic(df, n=14, d=3):
    ll, hh = df["Low"].rolling(n).min(), df["High"].rolling(n).max()
    k = 100 * (df["Close"] - ll) / (hh - ll).replace(0, np.nan)
    return k, k.rolling(d).mean()


def adx(df, n=14):
    up = df["High"].diff()
    down = -df["Low"].diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = true_range(df).ewm(alpha=1 / n, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / tr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / tr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), plus_di, minus_di


def obv(df):
    direction = np.sign(df["Close"].diff()).fillna(0)
    return (direction * df["Volume"]).cumsum()


def cci(df, n=20):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    md = tp.rolling(n).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - tp.rolling(n).mean()) / (0.015 * md)


def williams_r(df, n=14):
    hh, ll = df["High"].rolling(n).max(), df["Low"].rolling(n).min()
    return -100 * (hh - df["Close"]) / (hh - ll).replace(0, np.nan)


def mfi(df, n=14):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    flow = tp * df["Volume"]
    pos = flow.where(tp > tp.shift(1), 0).rolling(n).sum()
    neg = flow.where(tp < tp.shift(1), 0).rolling(n).sum()
    return 100 - 100 / (1 + pos / neg.replace(0, np.nan))


def vwap(df):
    """Session VWAP for intraday data (resets every day)."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    day = df.index.date
    pv = (tp * df["Volume"]).groupby(day).cumsum()
    vol = df["Volume"].groupby(day).cumsum()
    return pv / vol.replace(0, np.nan)


def heikin_ashi(df):
    ha = pd.DataFrame(index=df.index)
    ha["Close"] = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
    o = [(df["Open"].iloc[0] + df["Close"].iloc[0]) / 2]
    for i in range(1, len(df)):
        o.append((o[-1] + ha["Close"].iloc[i - 1]) / 2)
    ha["Open"] = o
    ha["High"] = pd.concat([df["High"], ha["Open"], ha["Close"]], axis=1).max(axis=1)
    ha["Low"] = pd.concat([df["Low"], ha["Open"], ha["Close"]], axis=1).min(axis=1)
    if "Volume" in df:
        ha["Volume"] = df["Volume"]
    return ha


def pivot_points(df):
    """Classic floor pivots from the last completed bar."""
    h, l, c = df["High"].iloc[-2], df["Low"].iloc[-2], df["Close"].iloc[-2]
    p = (h + l + c) / 3
    return {"R3": h + 2 * (p - l), "R2": p + (h - l), "R1": 2 * p - l, "P": p,
            "S1": 2 * p - h, "S2": p - (h - l), "S3": l - 2 * (h - p)}


def swing_levels(df, lookback=120, window=5, tol=0.015):
    """Support/resistance from swing highs/lows, clustered."""
    d = df.tail(lookback)
    highs = d["High"][(d["High"] == d["High"].rolling(2 * window + 1, center=True).max())]
    lows = d["Low"][(d["Low"] == d["Low"].rolling(2 * window + 1, center=True).min())]
    levels = sorted(list(highs.values) + list(lows.values))
    clustered = []
    for lv in levels:
        if clustered and abs(lv / clustered[-1][-1] - 1) < tol:
            clustered[-1].append(lv)
        else:
            clustered.append([lv])
    return [float(np.mean(c)) for c in clustered]


def add_all(df):
    """Adds every indicator used by the site."""
    df = df.copy()
    c = df["Close"]
    for n in (10, 20, 50, 100, 200):
        df[f"SMA{n}"] = sma(c, n)
    for n in (9, 10, 20, 21, 50, 100, 200):
        df[f"EMA{n}"] = ema(c, n)
    df["RSI"] = rsi(c)
    df["MACD"], df["MACD_signal"], df["MACD_hist"] = macd(c)
    df["BB_mid"], df["BB_up"], df["BB_low"], df["BB_width"] = bollinger(c)
    has_hl = {"High", "Low"}.issubset(df.columns)
    if has_hl:
        df["ATR"] = atr(df)
        df["STOCH_K"], df["STOCH_D"] = stochastic(df)
        df["ADX"], df["DI_plus"], df["DI_minus"] = adx(df)
        df["CCI"] = cci(df)
        df["WILLR"] = williams_r(df)
        df["HH20"] = df["High"].rolling(20).max()
        df["LL20"] = df["Low"].rolling(20).min()
    if "Volume" in df:
        df["OBV"] = obv(df)
        df["VolAvg20"] = df["Volume"].rolling(20).mean()
        if has_hl:
            df["MFI"] = mfi(df)
    df["MOM10"] = c - c.shift(10)
    return df


def technical_summary(d):
    """TradingView-style vote: each indicator says Buy / Sell / Neutral."""
    last = d.iloc[-1]
    price = last["Close"]
    rows = []

    def vote(name, value, signal):
        rows.append({"Indicator": name, "Value": value, "Signal": signal})

    def osc(name, val, buy_cond, sell_cond):
        if pd.isna(val):
            return
        vote(name, round(float(val), 2), "Buy" if buy_cond else ("Sell" if sell_cond else "Neutral"))

    osc("RSI (14)", last.get("RSI"), last.get("RSI", 50) < 30, last.get("RSI", 50) > 70)
    osc("Stochastic %K (14,3)", last.get("STOCH_K"), last.get("STOCH_K", 50) < 20, last.get("STOCH_K", 50) > 80)
    osc("CCI (20)", last.get("CCI"), last.get("CCI", 0) < -100, last.get("CCI", 0) > 100)
    osc("Williams %R (14)", last.get("WILLR"), last.get("WILLR", -50) < -80, last.get("WILLR", -50) > -20)
    osc("MACD (12,26,9)", last.get("MACD"), last.get("MACD", 0) > last.get("MACD_signal", 0),
        last.get("MACD", 0) < last.get("MACD_signal", 0))
    osc("Momentum (10)", last.get("MOM10"), last.get("MOM10", 0) > 0, last.get("MOM10", 0) < 0)
    if pd.notna(last.get("ADX", np.nan)):
        strong = last["ADX"] > 20
        osc("ADX (14)", last["ADX"], strong and last["DI_plus"] > last["DI_minus"],
            strong and last["DI_minus"] > last["DI_plus"])
    osc("MFI (14)", last.get("MFI"), last.get("MFI", 50) < 20, last.get("MFI", 50) > 80)
    n_osc = len(rows)

    for kind in ("EMA", "SMA"):
        for n in (10, 20, 50, 100, 200):
            v = last.get(f"{kind}{n}")
            if pd.notna(v):
                vote(f"{kind} ({n})", round(float(v), 2), "Buy" if price > v else "Sell")

    table = pd.DataFrame(rows)
    if table.empty:
        return table, 0.0, "Neutral", {}

    def score(t):
        if t.empty:
            return 0.0
        return ((t["Signal"] == "Buy").sum() - (t["Signal"] == "Sell").sum()) / len(t)

    parts = {"Oscillators": score(table.iloc[:n_osc]), "Moving Averages": score(table.iloc[n_osc:])}
    total = score(table)
    return table, total, label_for(total), parts


def label_for(s):
    if s > 0.5:
        return "Strong Buy"
    if s > 0.1:
        return "Buy"
    if s < -0.5:
        return "Strong Sell"
    if s < -0.1:
        return "Sell"
    return "Neutral"
