"""
engine.py - Strategies, backtesting (with stop loss / take profit / trailing stop),
scanner, trade plans and catalyst scoring. Pure pandas, no UI.
"""
import math

import numpy as np
import pandas as pd

import ta

# =====================================================================
# Universe (US market)
# =====================================================================
SECTORS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "AMD", "INTC", "QCOM", "TXN", "MU",
                   "AMAT", "LRCX", "KLAC", "ADI", "MRVL", "PANW", "CRWD", "NOW", "INTU", "PLTR", "SNOW",
                   "NET", "DDOG", "ARM", "SMCI", "DELL", "IBM", "CSCO", "ANET", "SHOP"],
    "Communication": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ", "T"],
    "Consumer": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TGT", "COST", "WMT", "PG", "KO",
                 "PEP", "CMG", "LULU", "BKNG", "ABNB", "UBER"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "C", "SCHW", "BLK", "V", "MA", "AXP", "PYPL",
                   "COIN", "HOOD", "SOFI"],
    "Healthcare": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "TMO", "ABT", "ISRG", "AMGN", "GILD",
                   "VRTX", "REGN", "MRNA"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "OXY"],
    "Industrials": ["CAT", "DE", "BA", "GE", "HON", "UPS", "LMT", "RTX"],
    "Autos & Other": ["MSTR", "RIVN", "LCID", "F", "GM"],
}
SECTOR_OF = {s: sec for sec, syms in SECTORS.items() for s in syms}
US_UNIVERSE = [s for syms in SECTORS.values() for s in syms]

SECTOR_ETFS = {"XLK": "Technology", "XLC": "Communication", "XLY": "Cons. Discretionary",
               "XLP": "Cons. Staples", "XLF": "Financials", "XLV": "Health Care", "XLE": "Energy",
               "XLI": "Industrials", "XLB": "Materials", "XLU": "Utilities", "XLRE": "Real Estate"}

MARKET_TILES = {
    "Indices": {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones", "^RUT": "Russell 2000",
                "^VIX": "VIX (Fear)"},
    "Futures": {"ES=F": "S&P Futures", "NQ=F": "Nasdaq Futures", "YM=F": "Dow Futures",
                "RTY=F": "Russell Futures"},
    "Treasury Yields": {"^IRX": "13W T-Bill", "^FVX": "5Y Yield", "^TNX": "10Y Yield", "^TYX": "30Y Yield"},
    "Commodities": {"GC=F": "Gold", "SI=F": "Silver", "CL=F": "WTI Crude", "BZ=F": "Brent Crude",
                    "NG=F": "Natural Gas", "HG=F": "Copper"},
    "Currencies": {"DX-Y.NYB": "US Dollar Index", "EURUSD=X": "EUR/USD", "JPY=X": "USD/JPY",
                   "GBPUSD=X": "GBP/USD"},
    "Crypto": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"},
}

# FRED economic series: id -> (name, transform, unit, higher_is_bad)
MACRO_SERIES = {
    "FEDFUNDS": ("Fed Funds Rate", "level", "%", None),
    "CPIAUCSL": ("CPI Inflation (YoY)", "yoy", "%", True),
    "CPILFESL": ("Core CPI (YoY)", "yoy", "%", True),
    "PCEPILFE": ("Core PCE (YoY)", "yoy", "%", True),
    "UNRATE": ("Unemployment Rate", "level", "%", True),
    "PAYEMS": ("Nonfarm Payrolls (MoM)", "diff", "K", False),
    "A191RL1Q225SBEA": ("Real GDP Growth (QoQ ann.)", "level", "%", False),
    "ICSA": ("Initial Jobless Claims", "level_k", "K", True),
    "T10Y2Y": ("10Y-2Y Yield Spread", "level", "%", False),
    "RSAFS": ("Retail Sales (MoM)", "mom", "%", False),
    "INDPRO": ("Industrial Production (YoY)", "yoy", "%", False),
    "UMCSENT": ("Consumer Sentiment", "level", "", False),
    "MORTGAGE30US": ("30Y Mortgage Rate", "level", "%", True),
    "M2SL": ("M2 Money Supply (YoY)", "yoy", "%", None),
}


def macro_transform(s: pd.Series, how: str) -> pd.Series:
    s = s.dropna()
    if how == "yoy":
        freq = 52 if len(s) > 2 and (s.index[-1] - s.index[-2]).days < 10 else 12
        return (s / s.shift(freq) - 1) * 100
    if how == "mom":
        return (s / s.shift(1) - 1) * 100
    if how == "diff":
        return s.diff()
    if how == "level_k":
        return s / 1000
    return s


# =====================================================================
# Strategies: each returns (entries, exits) boolean Series
# =====================================================================
def _cross_up(a, b):
    return (a > b) & (a.shift(1) <= b.shift(1))


def _cross_down(a, b):
    return (a < b) & (a.shift(1) >= b.shift(1))


def strat_sma(df, fast=20, slow=50):
    f, s = ta.sma(df["Close"], int(fast)), ta.sma(df["Close"], int(slow))
    return _cross_up(f, s), _cross_down(f, s)


def strat_ema(df, fast=9, slow=21):
    f, s = ta.ema(df["Close"], int(fast)), ta.ema(df["Close"], int(slow))
    return _cross_up(f, s), _cross_down(f, s)


def strat_rsi(df, period=14, buy_below=30, sell_above=60):
    r = ta.rsi(df["Close"], int(period))
    trend = df["Close"] > ta.sma(df["Close"], 200)
    trend = trend | ta.sma(df["Close"], 200).isna()
    return _cross_up(r, pd.Series(buy_below, index=r.index)) & trend, r > sell_above


def strat_macd(df, fast=12, slow=26, signal=9):
    line, sig, _ = ta.macd(df["Close"], int(fast), int(slow), int(signal))
    return _cross_up(line, sig), _cross_down(line, sig)


def strat_bollinger(df, period=20, std=2.0):
    mid, up, _, _ = ta.bollinger(df["Close"], int(period), float(std))
    return _cross_up(df["Close"], up), _cross_down(df["Close"], mid)


def strat_donchian(df, entry=20, exit=10):
    hh = df["High"].rolling(int(entry)).max().shift(1)
    ll = df["Low"].rolling(int(exit)).min().shift(1)
    return df["Close"] > hh, df["Close"] < ll


STRATEGIES = {
    "SMA Crossover": (strat_sma, [("fast", "Fast SMA", 5, 100, 20, 1), ("slow", "Slow SMA", 10, 250, 50, 1)]),
    "EMA Crossover": (strat_ema, [("fast", "Fast EMA", 3, 50, 9, 1), ("slow", "Slow EMA", 5, 200, 21, 1)]),
    "Golden Cross (50/200)": (strat_sma, [("fast", "Fast SMA", 20, 100, 50, 1),
                                          ("slow", "Slow SMA", 100, 300, 200, 1)]),
    "RSI Mean Reversion": (strat_rsi, [("period", "RSI Period", 2, 30, 14, 1),
                                       ("buy_below", "Buy when RSI crosses up", 5, 50, 30, 1),
                                       ("sell_above", "Sell when RSI above", 50, 95, 60, 1)]),
    "MACD Crossover": (strat_macd, [("fast", "Fast", 5, 30, 12, 1), ("slow", "Slow", 10, 60, 26, 1),
                                    ("signal", "Signal", 3, 20, 9, 1)]),
    "Bollinger Breakout": (strat_bollinger, [("period", "Period", 10, 50, 20, 1),
                                             ("std", "Std Dev", 1.0, 3.5, 2.0, 0.1)]),
    "Donchian Breakout (Turtle)": (strat_donchian, [("entry", "Entry High (days)", 5, 100, 20, 1),
                                                    ("exit", "Exit Low (days)", 3, 60, 10, 1)]),
}


# =====================================================================
# Backtest engine (signals on close, fills on next open, intraday stops)
# =====================================================================
def backtest(df, entries, exits, capital=10000.0, fee=0.0005, stop_pct=None, atr_mult=None,
             tp_pct=None, trail_pct=None):
    o, h, l, c = (df[k].values for k in ("Open", "High", "Low", "Close"))
    atr_v = ta.atr(df).values
    ent, ex = entries.fillna(False).values, exits.fillna(False).values
    idx = df.index
    n = len(df)

    cash, shares = capital, 0.0
    equity = np.empty(n)
    pos = np.zeros(n)
    trades = []
    pending_entry = pending_exit = False
    entry_px = stop = target = peak = 0.0
    entry_i = 0

    def close_trade(i, px, reason):
        nonlocal cash, shares
        proceeds = shares * px * (1 - fee)
        cost = shares * entry_px * (1 + fee)
        trades.append({"Entry Date": idx[entry_i], "Entry": entry_px, "Exit Date": idx[i], "Exit": px,
                       "Shares": shares, "P&L $": proceeds - cost, "P&L %": (proceeds / cost - 1) * 100,
                       "Bars": i - entry_i, "Exit Reason": reason})
        cash += proceeds
        shares = 0.0

    for i in range(n):
        # 1) execute orders from yesterday's signal at today's open
        if pending_exit and shares > 0:
            close_trade(i, o[i], "Signal")
        pending_exit = False
        if pending_entry and shares == 0:
            entry_px, entry_i, peak = o[i], i, o[i]
            shares = cash / (entry_px * (1 + fee))
            cash -= shares * entry_px * (1 + fee)
            stops = []
            if stop_pct:
                stops.append(entry_px * (1 - stop_pct / 100))
            if atr_mult and not np.isnan(atr_v[i - 1 if i else 0]):
                stops.append(entry_px - atr_mult * atr_v[i - 1 if i else 0])
            stop = max(stops) if stops else 0.0
            target = entry_px * (1 + tp_pct / 100) if tp_pct else np.inf
        pending_entry = False

        # 2) intraday risk management
        if shares > 0:
            peak = max(peak, h[i])
            trail = peak * (1 - trail_pct / 100) if trail_pct else 0.0
            eff_stop = max(stop, trail)
            if l[i] <= eff_stop:
                px = min(o[i], eff_stop)
                close_trade(i, px, "Trailing Stop" if trail >= stop and trail_pct else "Stop Loss")
            elif h[i] >= target:
                close_trade(i, max(o[i], target), "Take Profit")

        # 3) new signals at the close
        if shares > 0 and ex[i]:
            pending_exit = True
        elif shares == 0 and ent[i]:
            pending_entry = True

        equity[i] = cash + shares * c[i]
        pos[i] = 1.0 if shares > 0 else 0.0

    if shares > 0:
        entry_row = {"Entry Date": idx[entry_i], "Entry": entry_px, "Exit Date": idx[-1], "Exit": c[-1],
                     "Shares": shares, "P&L $": shares * (c[-1] - entry_px * (1 + fee)),
                     "P&L %": (c[-1] / (entry_px * (1 + fee)) - 1) * 100, "Bars": n - 1 - entry_i,
                     "Exit Reason": "Open"}
        trades.append(entry_row)

    return {"equity": pd.Series(equity, index=idx), "position": pd.Series(pos, index=idx),
            "trades": pd.DataFrame(trades, columns=["Entry Date", "Entry", "Exit Date", "Exit", "Shares",
                                                    "P&L $", "P&L %", "Bars", "Exit Reason"])}


def metrics(res, df, capital):
    eq = res["equity"]
    rets = eq.pct_change().fillna(0)
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1 / 365)
    bh = df["Close"] / df["Close"].iloc[0] * capital
    dd = eq / eq.cummax() - 1
    closed = res["trades"][res["trades"]["Exit Reason"] != "Open"]
    wins, losses = closed[closed["P&L $"] > 0], closed[closed["P&L $"] <= 0]
    gl = -losses["P&L $"].sum()
    std = rets.std()
    downside = rets[rets < 0].std()
    return {
        "Final Equity": eq.iloc[-1],
        "Total Return %": (eq.iloc[-1] / capital - 1) * 100,
        "Buy & Hold %": (bh.iloc[-1] / capital - 1) * 100,
        "CAGR %": ((eq.iloc[-1] / capital) ** (1 / years) - 1) * 100,
        "Sharpe": rets.mean() / std * math.sqrt(252) if std > 0 else 0.0,
        "Sortino": rets.mean() / downside * math.sqrt(252) if downside and downside > 0 else 0.0,
        "Max Drawdown %": dd.min() * 100,
        "Trades": len(closed),
        "Win Rate %": len(wins) / len(closed) * 100 if len(closed) else 0.0,
        "Profit Factor": wins["P&L $"].sum() / gl if gl > 0 else (np.inf if len(wins) else 0.0),
        "Avg Win %": wins["P&L %"].mean() if len(wins) else 0.0,
        "Avg Loss %": losses["P&L %"].mean() if len(losses) else 0.0,
        "Avg Bars Held": closed["Bars"].mean() if len(closed) else 0.0,
        "Exposure %": res["position"].mean() * 100,
    }


def run_strategy(df, name, params, capital=10000, fee=0.0005, **risk):
    fn = STRATEGIES[name][0]
    entries, exits = fn(df, **params)
    res = backtest(df, entries, exits, capital, fee, **risk)
    res["metrics"] = metrics(res, df, capital)
    return res


def monthly_returns(equity):
    m = equity.resample("ME").last().pct_change() * 100
    if len(m):
        first = equity.resample("ME").last().iloc[0] / equity.iloc[0] - 1
        m.iloc[0] = first * 100
    t = pd.DataFrame({"Year": m.index.year, "Month": m.index.month, "Ret": m.values})
    table = t.pivot(index="Year", columns="Month", values="Ret")
    return table.reindex(columns=range(1, 13))


def optimize(df, name, px, xs, py, ys, base_params, capital=10000, fee=0.0005, metric="Total Return %",
             **risk):
    grid = pd.DataFrame(index=ys, columns=xs, dtype=float)
    for y in ys:
        for x in xs:
            p = dict(base_params, **{px: x, py: y})
            if "fast" in p and "slow" in p and p["fast"] >= p["slow"]:
                continue
            grid.loc[y, x] = run_strategy(df, name, p, capital, fee, **risk)["metrics"][metric]
    return grid


# =====================================================================
# Trade plan: entry / stop / targets / timing
# =====================================================================
def trade_plan(d, account=10000, risk_pct=1.0):
    """d must already have ta.add_all() columns (daily bars)."""
    last = d.iloc[-1]
    price, a = float(last["Close"]), float(last["ATR"])
    sma20, sma50, sma200 = last["SMA20"], last["SMA50"], last["SMA200"]
    hh20 = float(d["High"].iloc[-21:-1].max())
    levels = ta.swing_levels(d)
    supports = [x for x in levels if x < price]
    resists = [x for x in levels if x > price]
    support = max(supports) if supports else float(d["Low"].tail(20).min())
    resist = min(resists) if resists else float(d["High"].tail(252).max())

    up_trend = price > sma50 and (pd.isna(sma200) or sma50 > sma200)
    down_trend = price < sma50 and pd.notna(sma200) and sma50 < sma200

    if up_trend and price >= hh20 * 0.985:
        setup, bias = "Breakout", "Long"
        entry = hh20 * 1.001
        zone = (entry, entry + 0.5 * a)
        trigger = f"Buy on a daily close above ${entry:,.2f} (20-day high) with volume ≥ 1.5× average."
        stop = entry - 1.5 * a
    elif up_trend and abs(price - sma20) <= 1.2 * a:
        setup, bias = "Pullback to SMA20", "Long"
        entry = float(sma20) + 0.2 * a
        zone = (float(sma20) - 0.25 * a, float(sma20) + 0.5 * a)
        trigger = (f"Buy near the 20-day average (${zone[0]:,.2f} – ${zone[1]:,.2f}) once a green candle "
                   f"closes above the prior day's high.")
        stop = min(entry - 1.5 * a, support - 0.25 * a) if entry - support < 3 * a else entry - 1.5 * a
    elif last["RSI"] < 35 and (pd.isna(sma200) or price > sma200):
        setup, bias = "Oversold Bounce", "Long (aggressive)"
        entry = float(d["High"].iloc[-1]) * 1.001
        zone = (price, entry)
        trigger = f"Buy only after a close above yesterday's high ${entry:,.2f} (reversal confirmation)."
        stop = float(d["Low"].tail(10).min()) - 0.5 * a
    elif down_trend:
        setup, bias = "Downtrend", "Avoid / No Long"
        entry = float(sma50)
        zone = (entry, entry + 0.5 * a)
        trigger = f"No long setup. Re-check only after the price reclaims the 50-day average (${entry:,.2f})."
        stop = entry - 1.5 * a
    else:
        setup, bias = "Range / Wait", "Neutral"
        level = min(hh20, resist) if resist > price else hh20
        entry = level * 1.001
        zone = (entry, entry + 0.5 * a)
        trigger = f"Wait. A daily close above ${entry:,.2f} (nearest resistance) would confirm strength."
        stop = max(support - 0.25 * a, entry - 2 * a)

    risk = max(entry - stop, 0.01)
    t1, t2 = entry + 2 * risk, entry + 3 * risk
    shares = int(account * risk_pct / 100 / risk)
    shares = min(shares, int(account / entry)) if entry > 0 else 0

    exits = [
        f"Stop loss: exit if price trades below ${stop:,.2f} ({(stop / entry - 1) * 100:.1f}% / "
        f"{risk / a:.1f}× ATR).",
        f"Target 1 (2R): ${t1:,.2f}. Sell 1/2 and move the stop to break-even (${entry:,.2f}).",
        f"Target 2 (3R): ${t2:,.2f}. Nearest resistance: ${resist:,.2f}.",
        f"Trailing stop after T1: highest high − 3× ATR (≈ ${float(d['High'].tail(20).max()) - 3 * a:,.2f} today).",
        f"Trend exit: daily close below the 20-day average (${sma20:,.2f}).",
        "Time stop: exit if the trade hasn't reached T1 within 15 trading days.",
    ]
    return {
        "setup": setup, "bias": bias, "price": price, "atr": a, "atr_pct": a / price * 100,
        "entry": entry, "zone": zone, "trigger": trigger, "stop": stop, "t1": t1, "t2": t2,
        "rr1": (t1 - entry) / risk, "rr2": (t2 - entry) / risk, "risk_per_share": risk,
        "shares": shares, "position_value": shares * entry, "support": support, "resistance": resist,
        "exits": exits,
    }


# =====================================================================
# Scanner
# =====================================================================
SCAN_PRESETS = {
    "All Signals": None,
    "Momentum Breakout": "breakout",
    "Trend Pullback": "pullback",
    "Oversold Bounce": "oversold",
    "Golden Cross": "golden",
    "Unusual Volume": "volume",
    "Volatility Squeeze": "squeeze",
}


def scan_symbol(df, spy_ret_63=None):
    if df is None or len(df) < 60 or not {"High", "Low", "Open"}.issubset(df.columns):
        return None
    d = ta.add_all(df)
    last, prev = d.iloc[-1], d.iloc[-2]
    tags, signals, score = set(), [], 0

    above = (d["SMA20"] > d["SMA50"]).astype(int)
    if above.iloc[-1] == 1 and above.iloc[-4:-1].min() == 0:
        signals.append("Golden Cross 20/50"); score += 2; tags.add("golden")
    elif above.iloc[-1] == 0 and above.iloc[-4:-1].max() == 1:
        signals.append("Death Cross 20/50"); score -= 2

    if last["Close"] >= d["High"].iloc[-21:-1].max():
        signals.append("20D Breakout"); score += 2; tags.add("breakout")
    if last["Close"] >= 0.98 * d["High"].tail(252).max():
        signals.append("Near 52W High"); score += 1

    vr = last["Volume"] / last["VolAvg20"] if last.get("VolAvg20", 0) > 0 else np.nan
    if pd.notna(vr) and vr >= 2:
        signals.append(f"Volume {vr:.1f}×"); score += 1; tags.add("volume")

    if last["RSI"] < 30:
        signals.append("RSI Oversold"); score += 1; tags.add("oversold")
    elif last["RSI"] > 75:
        signals.append("RSI Overbought"); score -= 1

    if last["MACD"] > last["MACD_signal"] and prev["MACD"] <= prev["MACD_signal"]:
        signals.append("MACD Bull Cross"); score += 1

    trend_up = pd.notna(last["SMA200"]) and last["Close"] > last["SMA50"] > last["SMA200"]
    if trend_up:
        score += 1
        if abs(last["Close"] - last["SMA20"]) <= last["ATR"] and last["RSI"] < 60:
            signals.append("Pullback to SMA20"); score += 1; tags.add("pullback")
    elif pd.notna(last["SMA200"]) and last["Close"] < last["SMA200"]:
        signals.append("Below SMA200"); score -= 1

    if pd.notna(last["ADX"]) and last["ADX"] > 25 and last["DI_plus"] > last["DI_minus"]:
        signals.append(f"Strong Trend (ADX {last['ADX']:.0f})"); score += 1

    bw = d["BB_width"].tail(126)
    if len(bw.dropna()) > 50 and bw.iloc[-1] <= bw.quantile(0.1):
        signals.append("BB Squeeze"); tags.add("squeeze")

    gap = (last["Open"] / prev["Close"] - 1) * 100
    if gap >= 3:
        signals.append(f"Gap Up {gap:.1f}%"); score += 1
    elif gap <= -3:
        signals.append(f"Gap Down {gap:.1f}%"); score -= 1

    ret_63 = (last["Close"] / d["Close"].iloc[-64] - 1) * 100 if len(d) > 64 else np.nan
    rs = ret_63 - spy_ret_63 if spy_ret_63 is not None and pd.notna(ret_63) else np.nan
    if pd.notna(rs) and rs > 10:
        signals.append("Outperforming SPY"); score += 1

    plan = trade_plan(d)
    return {
        "Price": float(last["Close"]),
        "Chg %": float((last["Close"] / prev["Close"] - 1) * 100),
        "1M %": float((last["Close"] / d["Close"].iloc[-22] - 1) * 100),
        "3M %": float(ret_63) if pd.notna(ret_63) else None,
        "RSI": float(last["RSI"]),
        "ADX": float(last["ADX"]) if pd.notna(last["ADX"]) else None,
        "Vol ×": float(vr) if pd.notna(vr) else None,
        "Trend": "Up" if trend_up else ("Down" if last["Close"] < last["SMA50"] else "Mixed"),
        "Score": score,
        "Setup": plan["setup"],
        "Entry": plan["entry"], "Stop": plan["stop"], "Target": plan["t2"],
        "R:R": plan["rr2"],
        "Signals": " · ".join(signals) if signals else "—",
        "_tags": ",".join(sorted(tags)),
    }


def scan(data_by_symbol, spy_df=None):
    spy_ret = None
    if spy_df is not None and len(spy_df) > 64:
        spy_ret = (spy_df["Close"].iloc[-1] / spy_df["Close"].iloc[-64] - 1) * 100
    rows = []
    for sym, df in data_by_symbol.items():
        try:
            r = scan_symbol(df, spy_ret)
        except Exception:
            r = None
        if r:
            rows.append({"Symbol": sym, "Sector": SECTOR_OF.get(sym, "—"), **r})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["Score", "Vol ×"], ascending=False).reset_index(drop=True)


# =====================================================================
# Catalyst scoring
# =====================================================================
def technical_checks(d, spy_df=None):
    last = d.iloc[-1]
    checks = []

    def add(name, ok, detail):
        checks.append({"Check": name, "Pass": bool(ok), "Detail": detail})

    add("Primary trend up", pd.notna(last["SMA200"]) and last["Close"] > last["SMA200"],
        f"Price {last['Close']:,.2f} vs SMA200 {last['SMA200']:,.2f}" if pd.notna(last["SMA200"]) else "n/a")
    add("MA stack bullish (20 > 50 > 200)",
        pd.notna(last["SMA200"]) and last["SMA20"] > last["SMA50"] > last["SMA200"],
        f"SMA20 {last['SMA20']:,.2f} · SMA50 {last['SMA50']:,.2f}")
    add("Healthy momentum (RSI 50–70)", 50 <= last["RSI"] <= 70, f"RSI {last['RSI']:.0f}")
    add("MACD above signal", last["MACD"] > last["MACD_signal"], f"Hist {last['MACD_hist']:.3f}")
    add("Trend strength (ADX > 20, +DI > −DI)",
        pd.notna(last["ADX"]) and last["ADX"] > 20 and last["DI_plus"] > last["DI_minus"],
        f"ADX {last['ADX']:.0f}" if pd.notna(last["ADX"]) else "n/a")
    obv_up = d["OBV"].iloc[-1] > d["OBV"].iloc[-21] if len(d) > 21 else False
    add("Accumulation (OBV rising 1M)", obv_up, "OBV higher than 20 days ago" if obv_up else "OBV falling")
    near_high = last["Close"] >= 0.95 * d["High"].tail(252).max()
    add("Within 5% of 52W high", near_high, f"52W high {d['High'].tail(252).max():,.2f}")
    bw = d["BB_width"].tail(126).dropna()
    squeeze = len(bw) > 50 and bw.iloc[-1] <= bw.quantile(0.2)
    add("Volatility squeeze (coiling)", squeeze, "Bollinger width in lowest 20%" if squeeze else "Normal width")
    vr = last["Volume"] / last["VolAvg20"] if last.get("VolAvg20", 0) > 0 else 0
    add("Volume confirmation (≥ 1.5× avg)", vr >= 1.5, f"{vr:.1f}× average")
    if spy_df is not None and len(spy_df) > 64 and len(d) > 64:
        rs = (last["Close"] / d["Close"].iloc[-64] - 1) - (spy_df["Close"].iloc[-1] / spy_df["Close"].iloc[-64] - 1)
        add("Relative strength vs SPY (3M)", rs > 0, f"{rs * 100:+.1f}% vs S&P 500")
    return checks


def fundamental_checks(info, earnings_hist=None):
    checks = []

    def add(name, val, ok, fmt):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return
        checks.append({"Check": name, "Pass": bool(ok), "Detail": fmt})

    g = info.get
    add("Revenue growth > 10%", g("revenueGrowth"), (g("revenueGrowth") or 0) > 0.10,
        f"{(g('revenueGrowth') or 0) * 100:+.1f}% YoY")
    add("Earnings growth > 10%", g("earningsGrowth"), (g("earningsGrowth") or 0) > 0.10,
        f"{(g('earningsGrowth') or 0) * 100:+.1f}% YoY")
    add("Profit margin > 10%", g("profitMargins"), (g("profitMargins") or 0) > 0.10,
        f"{(g('profitMargins') or 0) * 100:.1f}%")
    add("ROE > 15%", g("returnOnEquity"), (g("returnOnEquity") or 0) > 0.15,
        f"{(g('returnOnEquity') or 0) * 100:.1f}%")
    if g("forwardPE") and g("trailingPE"):
        add("Forward P/E < Trailing P/E", g("forwardPE"), g("forwardPE") < g("trailingPE"),
            f"{g('forwardPE'):.1f} vs {g('trailingPE'):.1f}")
    peg = g("trailingPegRatio") or g("pegRatio")
    add("PEG < 2", peg, (peg or 99) < 2, f"{peg:.2f}" if peg else "")
    add("Debt/Equity < 150%", g("debtToEquity"), (g("debtToEquity") or 999) < 150,
        f"{g('debtToEquity'):.0f}%" if g("debtToEquity") else "")
    add("Positive free cash flow", g("freeCashflow"), (g("freeCashflow") or 0) > 0,
        f"${(g('freeCashflow') or 0) / 1e9:,.2f}B")
    price, tgt = g("currentPrice") or g("regularMarketPrice"), g("targetMeanPrice")
    if price and tgt:
        up = (tgt / price - 1) * 100
        add("Analyst upside > 10%", up, up > 10, f"Mean target ${tgt:,.2f} ({up:+.1f}%)")
    rm = g("recommendationMean")
    add("Analysts rate Buy (mean ≤ 2.5)", rm, (rm or 5) <= 2.5,
        f"{rm:.2f} · {g('recommendationKey', '')} ({g('numberOfAnalystOpinions', 0)} analysts)" if rm else "")
    if earnings_hist is not None and isinstance(earnings_hist, pd.DataFrame) and not earnings_hist.empty:
        col = next((c for c in earnings_hist.columns if "Surprise" in c), None)
        if col:
            rep = earnings_hist[col].dropna().head(4)
            if len(rep):
                beats = int((rep > 0).sum())
                add("Beat EPS estimates (last 4)", beats, beats >= 3, f"{beats}/{len(rep)} beats")
    return checks


def event_checks(earn_date, ratings, news, info, d):
    items = []
    now = pd.Timestamp.now().normalize()
    if earn_date is not None:
        days = (pd.Timestamp(earn_date).normalize() - now).days
        if 0 <= days <= 14:
            items.append({"Event": "Earnings soon", "Impact": "⚠️ High volatility",
                          "Detail": f"{pd.Timestamp(earn_date):%b %d} (in {days} days). Size down or exit before."})
        elif days > 14:
            items.append({"Event": "Next earnings", "Impact": "Neutral",
                          "Detail": f"{pd.Timestamp(earn_date):%b %d, %Y} (in {days} days)"})
    if isinstance(ratings, pd.DataFrame) and not ratings.empty and "Action" in ratings:
        ups, downs = int((ratings["Action"] == "up").sum()), int((ratings["Action"] == "down").sum())
        if ups or downs:
            items.append({"Event": "Analyst actions (30D)", "Impact": "🟢 Positive" if ups > downs else
                          ("🔴 Negative" if downs > ups else "Neutral"),
                          "Detail": f"{ups} upgrades · {downs} downgrades"})
    recent = [n for n in news if pd.notna(n["time"]) and (pd.Timestamp.now(tz="UTC") - n["time"]).days < 3]
    if len(recent) >= 3:
        items.append({"Event": "In the news", "Impact": "🔥 Attention",
                      "Detail": f"{len(recent)} headlines in the last 3 days"})
    si = info.get("shortPercentOfFloat")
    if si and si > 0.15:
        items.append({"Event": "High short interest", "Impact": "🚀 Squeeze potential",
                      "Detail": f"{si * 100:.1f}% of float sold short"})
    last, prev = d.iloc[-1], d.iloc[-2]
    vr = last["Volume"] / last["VolAvg20"] if last.get("VolAvg20", 0) > 0 else 0
    if vr >= 2:
        items.append({"Event": "Unusual volume", "Impact": "🔥 Institutional interest",
                      "Detail": f"{vr:.1f}× the 20-day average"})
    gap = (last["Open"] / prev["Close"] - 1) * 100
    if abs(gap) >= 3:
        items.append({"Event": "Price gap", "Impact": "🟢 Positive" if gap > 0 else "🔴 Negative",
                      "Detail": f"{gap:+.1f}% gap at the open"})
    return items


def catalyst_score(tech, fund, events):
    def pct(ch):
        return sum(c["Pass"] for c in ch) / len(ch) * 100 if ch else None

    t, f = pct(tech), pct(fund)
    e = 50.0
    for ev in events:
        imp = ev["Impact"]
        if "Positive" in imp or "Squeeze" in imp or "Institutional" in imp:
            e += 12
        elif "Negative" in imp:
            e -= 15
        elif "High volatility" in imp:
            e -= 5
    e = max(0.0, min(100.0, e))
    parts = [(t, 0.5), (f, 0.3), (e, 0.2)]
    avail = [(v, w) for v, w in parts if v is not None]
    total = sum(v * w for v, w in avail) / sum(w for _, w in avail)
    if total >= 70:
        label = "Strong Bullish"
    elif total >= 55:
        label = "Bullish"
    elif total >= 45:
        label = "Neutral"
    elif total >= 30:
        label = "Bearish"
    else:
        label = "Strong Bearish"
    return {"total": total, "technical": t, "fundamental": f, "event": e, "label": label}
