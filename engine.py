"""
engine.py - Strategies, backtesting (stop loss / take profit / trailing stop), scanner, trade plans and
catalyst scoring. Pure pandas. Text outputs are bilingual: every message has an English and an Arabic version.
"""
import math

import numpy as np
import pandas as pd

import ta
import universe as U


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
STRATEGY_AR = {"SMA Crossover": "تقاطع المتوسطات البسيطة", "EMA Crossover": "تقاطع المتوسطات الأسية",
               "Golden Cross (50/200)": "التقاطع الذهبي 50/200", "RSI Mean Reversion": "الارتداد بمؤشر RSI",
               "MACD Crossover": "تقاطع الماكد", "Bollinger Breakout": "اختراق بولنجر",
               "Donchian Breakout (Turtle)": "اختراق دونشيان (السلحفاة)"}
PARAM_AR = {"Fast SMA": "المتوسط السريع", "Slow SMA": "المتوسط البطيء", "Fast EMA": "الأسي السريع",
            "Slow EMA": "الأسي البطيء", "RSI Period": "فترة RSI", "Buy when RSI crosses up": "شراء عند صعود RSI فوق",
            "Sell when RSI above": "بيع عندما RSI فوق", "Fast": "السريع", "Slow": "البطيء", "Signal": "الإشارة",
            "Period": "الفترة", "Std Dev": "الانحراف المعياري", "Entry High (days)": "قمة الدخول (أيام)",
            "Exit Low (days)": "قاع الخروج (أيام)"}
SETUP_AR = {"Breakout": "اختراق", "Pullback to SMA20": "ارتداد لمتوسط 20", "Oversold Bounce": "ارتداد من تشبع بيعي",
            "Downtrend": "اتجاه هابط", "Range / Wait": "تذبذب / انتظار"}
BIAS_AR = {"Long": "شراء", "Long (aggressive)": "شراء (مغامر)", "Avoid / No Long": "تجنّب", "Neutral": "محايد"}
EXIT_REASON_AR = {"Signal": "إشارة", "Stop Loss": "وقف خسارة", "Trailing Stop": "وقف متحرك", "Take Profit": "جني أرباح",
                  "Open": "مفتوحة"}


def trade_plan(d, account=10000, risk_pct=1.0):
    """d must already have ta.add_all() columns (daily bars). Every text field has _en and _ar versions."""
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
        trig = (f"Buy on a daily close above ${entry:,.2f} (20-day high) with volume ≥ 1.5× average.",
                f"اشترِ عند إغلاق يومي فوق ${entry:,.2f} (قمة 20 يوم) مع حجم تداول ≥ 1.5 ضعف المتوسط.")
        stop = entry - 1.5 * a
    elif up_trend and abs(price - sma20) <= 1.2 * a:
        setup, bias = "Pullback to SMA20", "Long"
        entry = float(sma20) + 0.2 * a
        zone = (float(sma20) - 0.25 * a, float(sma20) + 0.5 * a)
        trig = (f"Buy near the 20-day average (${zone[0]:,.2f} – ${zone[1]:,.2f}) once a green candle closes above the prior day's high.",
                f"اشترِ قرب متوسط 20 يوم (${zone[0]:,.2f} – ${zone[1]:,.2f}) بعد إغلاق شمعة خضراء فوق قمة اليوم السابق.")
        stop = min(entry - 1.5 * a, support - 0.25 * a) if entry - support < 3 * a else entry - 1.5 * a
    elif last["RSI"] < 35 and (pd.isna(sma200) or price > sma200):
        setup, bias = "Oversold Bounce", "Long (aggressive)"
        entry = float(d["High"].iloc[-1]) * 1.001
        zone = (price, entry)
        trig = (f"Buy only after a close above yesterday's high ${entry:,.2f} (reversal confirmation).",
                f"اشترِ فقط بعد إغلاق فوق قمة الأمس ${entry:,.2f} (تأكيد الارتداد).")
        stop = float(d["Low"].tail(10).min()) - 0.5 * a
    elif down_trend:
        setup, bias = "Downtrend", "Avoid / No Long"
        entry = float(sma50)
        zone = (entry, entry + 0.5 * a)
        trig = (f"No long setup. Re-check only after the price reclaims the 50-day average (${entry:,.2f}).",
                f"لا توجد فرصة شراء. أعد التقييم بعد عودة السعر فوق متوسط 50 يوم (${entry:,.2f}).")
        stop = entry - 1.5 * a
    else:
        setup, bias = "Range / Wait", "Neutral"
        level = min(hh20, resist) if resist > price else hh20
        entry = level * 1.001
        zone = (entry, entry + 0.5 * a)
        trig = (f"Wait. A daily close above ${entry:,.2f} (nearest resistance) would confirm strength.",
                f"انتظر. إغلاق يومي فوق ${entry:,.2f} (أقرب مقاومة) يؤكد القوة.")
        stop = max(support - 0.25 * a, entry - 2 * a)

    risk = max(entry - stop, 0.01)
    t1, t2 = entry + 2 * risk, entry + 3 * risk
    shares = int(account * risk_pct / 100 / risk)
    shares = min(shares, int(account / entry)) if entry > 0 else 0
    trail = float(d["High"].tail(20).max()) - 3 * a
    exits = [
        (f"Stop loss: exit if price trades below ${stop:,.2f} ({(stop / entry - 1) * 100:.1f}% / {risk / a:.1f}× ATR).",
         f"وقف الخسارة: اخرج إذا نزل السعر تحت ${stop:,.2f} ({(stop / entry - 1) * 100:.1f}% / {risk / a:.1f} ضعف ATR)."),
        (f"Target 1 (2R): ${t1:,.2f}. Sell half and move the stop to break-even (${entry:,.2f}).",
         f"الهدف الأول (2R): ${t1:,.2f}. بِع النصف وارفع الوقف لسعر الدخول (${entry:,.2f})."),
        (f"Target 2 (3R): ${t2:,.2f}. Nearest resistance: ${resist:,.2f}.",
         f"الهدف الثاني (3R): ${t2:,.2f}. أقرب مقاومة: ${resist:,.2f}."),
        (f"Trailing stop after T1: highest high − 3× ATR (≈ ${trail:,.2f} today).",
         f"وقف متحرك بعد الهدف الأول: أعلى قمة − 3 أضعاف ATR (≈ ${trail:,.2f} اليوم)."),
        (f"Trend exit: daily close below the 20-day average (${sma20:,.2f}).",
         f"خروج الاتجاه: إغلاق يومي تحت متوسط 20 يوم (${sma20:,.2f})."),
        ("Time stop: exit if the trade hasn't reached T1 within 15 trading days.",
         "وقف زمني: اخرج إذا لم تصل الصفقة للهدف الأول خلال 15 يوم تداول."),
    ]
    return {
        "setup": setup, "setup_ar": SETUP_AR[setup], "bias": bias, "bias_ar": BIAS_AR[bias],
        "price": price, "atr": a, "atr_pct": a / price * 100, "entry": entry, "zone": zone,
        "trigger": trig[0], "trigger_ar": trig[1], "stop": stop, "t1": t1, "t2": t2,
        "rr1": (t1 - entry) / risk, "rr2": (t2 - entry) / risk, "risk_per_share": risk,
        "shares": shares, "position_value": shares * entry, "support": support, "resistance": resist,
        "exits": exits,
    }


# =====================================================================
# Scanner
# =====================================================================
SCAN_PRESETS = {  # key -> (english, arabic, tag)
    "all": ("All Signals", "كل الإشارات", None), "breakout": ("Momentum Breakout", "اختراق بزخم", "breakout"),
    "pullback": ("Trend Pullback", "ارتداد في اتجاه صاعد", "pullback"), "oversold": ("Oversold Bounce", "ارتداد من تشبع بيعي", "oversold"),
    "golden": ("Golden Cross", "تقاطع ذهبي", "golden"), "volume": ("Unusual Volume", "حجم غير طبيعي", "volume"),
    "squeeze": ("Volatility Squeeze", "انضغاط التذبذب", "squeeze"),
}


def scan_symbol(df, spy_ret_63=None):
    if df is None or len(df) < 60 or not {"High", "Low", "Open"}.issubset(df.columns):
        return None
    d = ta.add_all(df)
    last, prev = d.iloc[-1], d.iloc[-2]
    tags, sig, score = set(), [], 0

    def add(en, ar, pts, tag=None):
        nonlocal score
        sig.append((en, ar))
        score += pts
        if tag:
            tags.add(tag)

    above = (d["SMA20"] > d["SMA50"]).astype(int)
    if above.iloc[-1] == 1 and above.iloc[-4:-1].min() == 0:
        add("Golden Cross 20/50", "تقاطع ذهبي 20/50", 2, "golden")
    elif above.iloc[-1] == 0 and above.iloc[-4:-1].max() == 1:
        add("Death Cross 20/50", "تقاطع سلبي 20/50", -2)
    if last["Close"] >= d["High"].iloc[-21:-1].max():
        add("20D Breakout", "اختراق قمة 20 يوم", 2, "breakout")
    if last["Close"] >= 0.98 * d["High"].tail(252).max():
        add("Near 52W High", "قرب القمة السنوية", 1)
    vr = last["Volume"] / last["VolAvg20"] if last.get("VolAvg20", 0) > 0 else np.nan
    if pd.notna(vr) and vr >= 2:
        add(f"Volume {vr:.1f}×", f"حجم {vr:.1f}×", 1, "volume")
    if last["RSI"] < 30:
        add("RSI Oversold", "تشبع بيعي RSI", 1, "oversold")
    elif last["RSI"] > 75:
        add("RSI Overbought", "تشبع شرائي RSI", -1)
    if last["MACD"] > last["MACD_signal"] and prev["MACD"] <= prev["MACD_signal"]:
        add("MACD Bull Cross", "تقاطع ماكد إيجابي", 1)
    trend_up = pd.notna(last["SMA200"]) and last["Close"] > last["SMA50"] > last["SMA200"]
    if trend_up:
        score += 1
        if abs(last["Close"] - last["SMA20"]) <= last["ATR"] and last["RSI"] < 60:
            add("Pullback to SMA20", "ارتداد لمتوسط 20", 1, "pullback")
    elif pd.notna(last["SMA200"]) and last["Close"] < last["SMA200"]:
        add("Below SMA200", "تحت متوسط 200", -1)
    if pd.notna(last["ADX"]) and last["ADX"] > 25 and last["DI_plus"] > last["DI_minus"]:
        add(f"Strong Trend (ADX {last['ADX']:.0f})", f"اتجاه قوي (ADX {last['ADX']:.0f})", 1)
    bw = d["BB_width"].tail(126)
    if len(bw.dropna()) > 50 and bw.iloc[-1] <= bw.quantile(0.1):
        add("BB Squeeze", "انضغاط بولنجر", 0, "squeeze")
    gap = (last["Open"] / prev["Close"] - 1) * 100
    if gap >= 3:
        add(f"Gap Up {gap:.1f}%", f"فجوة صاعدة {gap:.1f}%", 1)
    elif gap <= -3:
        add(f"Gap Down {gap:.1f}%", f"فجوة هابطة {gap:.1f}%", -1)
    ret_63 = (last["Close"] / d["Close"].iloc[-64] - 1) * 100 if len(d) > 64 else np.nan
    rs = ret_63 - spy_ret_63 if spy_ret_63 is not None and pd.notna(ret_63) else np.nan
    if pd.notna(rs) and rs > 10:
        add("Outperforming SPY", "يتفوق على السوق", 1)

    plan = trade_plan(d)
    trend = "Up" if trend_up else ("Down" if last["Close"] < last["SMA50"] else "Mixed")
    return {
        "Price": float(last["Close"]), "Chg %": float((last["Close"] / prev["Close"] - 1) * 100),
        "1M %": float((last["Close"] / d["Close"].iloc[-22] - 1) * 100),
        "3M %": float(ret_63) if pd.notna(ret_63) else None, "RSI": float(last["RSI"]),
        "ADX": float(last["ADX"]) if pd.notna(last["ADX"]) else None, "Vol ×": float(vr) if pd.notna(vr) else None,
        "Trend": trend, "Score": score, "Setup": plan["setup"], "Setup_ar": plan["setup_ar"],
        "Entry": plan["entry"], "Stop": plan["stop"], "Target": plan["t2"], "R:R": plan["rr2"],
        "Signals": " · ".join(e for e, _ in sig) or "—", "Signals_ar": " · ".join(a for _, a in sig) or "—",
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
            rows.append({"Symbol": sym, "Sector": U.sector_of(sym), **r})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["Score", "Vol ×"], ascending=False).reset_index(drop=True)


# =====================================================================
# Catalyst scoring (bilingual)
# =====================================================================
def _check(en, ar, ok, detail):
    return {"Check": en, "Check_ar": ar, "Pass": bool(ok), "Detail": detail}


def technical_checks(d, spy_df=None):
    last = d.iloc[-1]
    c = []
    has200 = pd.notna(last["SMA200"])
    c.append(_check("Primary trend up (above SMA200)", "الاتجاه الرئيسي صاعد (فوق متوسط 200)",
                    has200 and last["Close"] > last["SMA200"],
                    f"{last['Close']:,.2f} vs {last['SMA200']:,.2f}" if has200 else "n/a"))
    c.append(_check("Bullish MA stack (20 > 50 > 200)", "ترتيب متوسطات إيجابي (20 > 50 > 200)",
                    has200 and last["SMA20"] > last["SMA50"] > last["SMA200"],
                    f"SMA20 {last['SMA20']:,.2f} · SMA50 {last['SMA50']:,.2f}"))
    c.append(_check("Healthy momentum (RSI 50–70)", "زخم صحي (RSI بين 50 و70)", 50 <= last["RSI"] <= 70, f"RSI {last['RSI']:.0f}"))
    c.append(_check("MACD above signal", "الماكد فوق خط الإشارة", last["MACD"] > last["MACD_signal"], f"Hist {last['MACD_hist']:.3f}"))
    c.append(_check("Trend strength (ADX > 20, +DI > −DI)", "قوة الاتجاه (ADX > 20)",
                    pd.notna(last["ADX"]) and last["ADX"] > 20 and last["DI_plus"] > last["DI_minus"],
                    f"ADX {last['ADX']:.0f}" if pd.notna(last["ADX"]) else "n/a"))
    obv_up = bool(d["OBV"].iloc[-1] > d["OBV"].iloc[-21]) if len(d) > 21 else False
    c.append(_check("Accumulation (OBV rising 1M)", "تجميع (OBV صاعد خلال شهر)", obv_up, "OBV ↑" if obv_up else "OBV ↓"))
    hi = d["High"].tail(252).max()
    c.append(_check("Within 5% of 52W high", "ضمن 5% من القمة السنوية", last["Close"] >= 0.95 * hi, f"52W high {hi:,.2f}"))
    bw = d["BB_width"].tail(126).dropna()
    sq = len(bw) > 50 and bw.iloc[-1] <= bw.quantile(0.2)
    c.append(_check("Volatility squeeze (coiling)", "انضغاط التذبذب (تجميع قبل حركة)", sq, "BB width low" if sq else "normal"))
    vr = last["Volume"] / last["VolAvg20"] if last.get("VolAvg20", 0) > 0 else 0
    c.append(_check("Volume confirmation (≥ 1.5× avg)", "تأكيد بالحجم (≥ 1.5 ضعف)", vr >= 1.5, f"{vr:.1f}×"))
    if spy_df is not None and len(spy_df) > 64 and len(d) > 64:
        rs = (last["Close"] / d["Close"].iloc[-64] - 1) - (spy_df["Close"].iloc[-1] / spy_df["Close"].iloc[-64] - 1)
        c.append(_check("Relative strength vs S&P 500 (3M)", "قوة نسبية مقابل السوق (3 أشهر)", rs > 0, f"{rs * 100:+.1f}%"))
    return c


def fundamental_checks(info, earnings_hist=None):
    c = []
    g = info.get

    def add(en, ar, val, ok, detail):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return
        c.append(_check(en, ar, ok, detail))

    add("Revenue growth > 10%", "نمو الإيرادات > 10%", g("revenueGrowth"), (g("revenueGrowth") or 0) > 0.10,
        f"{(g('revenueGrowth') or 0) * 100:+.1f}%")
    add("Earnings growth > 10%", "نمو الأرباح > 10%", g("earningsGrowth"), (g("earningsGrowth") or 0) > 0.10,
        f"{(g('earningsGrowth') or 0) * 100:+.1f}%")
    add("Profit margin > 10%", "هامش الربح > 10%", g("profitMargins"), (g("profitMargins") or 0) > 0.10,
        f"{(g('profitMargins') or 0) * 100:.1f}%")
    add("ROE > 15%", "العائد على حقوق المساهمين > 15%", g("returnOnEquity"), (g("returnOnEquity") or 0) > 0.15,
        f"{(g('returnOnEquity') or 0) * 100:.1f}%")
    if g("forwardPE") and g("trailingPE"):
        add("Forward P/E < Trailing P/E", "مكرر الربحية المستقبلي أقل من الحالي", g("forwardPE"), g("forwardPE") < g("trailingPE"),
            f"{g('forwardPE'):.1f} vs {g('trailingPE'):.1f}")
    peg = g("trailingPegRatio") or g("pegRatio")
    add("PEG < 2", "مؤشر PEG < 2", peg, (peg or 99) < 2, f"{peg:.2f}" if peg else "")
    de = g("debtToEquity")
    add("Debt/Equity < 150%", "الديون/حقوق المساهمين < 150%", de, (de or 999) < 150, f"{de:.0f}%" if de else "")
    fcf = g("freeCashflow")
    add("Positive free cash flow", "تدفق نقدي حر إيجابي", fcf, (fcf or 0) > 0, f"${(fcf or 0) / 1e9:,.2f}B")
    price, tgt = g("currentPrice") or g("regularMarketPrice"), g("targetMeanPrice")
    if price and tgt:
        up = (tgt / price - 1) * 100
        add("Analyst upside > 10%", "مساحة صعود حسب المحللين > 10%", up, up > 10, f"${tgt:,.2f} ({up:+.1f}%)")
    rm = g("recommendationMean")
    add("Analysts rate Buy (mean ≤ 2.5)", "المحللون يوصون بالشراء", rm, (rm or 5) <= 2.5,
        f"{rm:.2f} · {g('numberOfAnalystOpinions', 0)} analysts" if rm else "")
    if isinstance(earnings_hist, pd.DataFrame) and not earnings_hist.empty:
        col = next((x for x in earnings_hist.columns if "Surprise" in x), None)
        if col:
            rep = earnings_hist[col].dropna().head(4)
            if len(rep):
                beats = int((rep > 0).sum())
                add("Beat EPS estimates (last 4)", "تجاوز توقعات الأرباح (آخر 4)", beats, beats >= 3, f"{beats}/{len(rep)}")
    return c


def _event(en, ar, impact, detail_en, detail_ar):
    """impact: pos | neg | warn | neutral | hot"""
    return {"Event": en, "Event_ar": ar, "Impact": impact, "Detail": detail_en, "Detail_ar": detail_ar}


IMPACT = {"pos": ("Positive", "إيجابي", "up", "trending_up"), "neg": ("Negative", "سلبي", "down", "trending_down"),
          "warn": ("High volatility", "تذبذب عالٍ", "gold", "warning"), "neutral": ("Neutral", "محايد", "neu", "schedule"),
          "hot": ("Attention", "اهتمام مرتفع", "acc", "local_fire_department")}


def event_checks(earn_date, ratings, news, info, d):
    items = []
    now = pd.Timestamp.now().normalize()
    if earn_date is not None:
        ed = pd.Timestamp(earn_date)
        days = (ed.normalize() - now).days
        if 0 <= days <= 14:
            items.append(_event("Earnings soon", "إعلان أرباح قريب", "warn", f"{ed:%b %d} (in {days} days) — size down or wait",
                                f"{ed:%Y-%m-%d} (بعد {days} يوم) — خفّف الحجم أو انتظر"))
        elif days > 14:
            items.append(_event("Next earnings", "إعلان الأرباح القادم", "neutral", f"{ed:%b %d, %Y} (in {days} days)",
                                f"{ed:%Y-%m-%d} (بعد {days} يوم)"))
    if isinstance(ratings, pd.DataFrame) and not ratings.empty and "Action" in ratings:
        ups, downs = int((ratings["Action"] == "up").sum()), int((ratings["Action"] == "down").sum())
        if ups or downs:
            items.append(_event("Analyst actions (30D)", "تحركات المحللين (30 يوم)", "pos" if ups > downs else ("neg" if downs > ups else "neutral"),
                                f"{ups} upgrades · {downs} downgrades", f"{ups} ترقية · {downs} تخفيض"))
    recent = [n for n in news if pd.notna(n["time"]) and (pd.Timestamp.now(tz="UTC") - n["time"]).days < 3]
    if len(recent) >= 3:
        items.append(_event("In the news", "في الأخبار", "hot", f"{len(recent)} headlines in 3 days", f"{len(recent)} خبر خلال 3 أيام"))
    si = info.get("shortPercentOfFloat")
    if si and si > 0.15:
        items.append(_event("High short interest", "بيع على المكشوف مرتفع", "hot", f"{si * 100:.1f}% of float — squeeze potential",
                            f"{si * 100:.1f}% من الأسهم الحرة — احتمال ضغط شراء"))
    last, prev = d.iloc[-1], d.iloc[-2]
    vr = last["Volume"] / last["VolAvg20"] if last.get("VolAvg20", 0) > 0 else 0
    if vr >= 2:
        items.append(_event("Unusual volume", "حجم تداول غير طبيعي", "pos", f"{vr:.1f}× the 20-day average", f"{vr:.1f} ضعف متوسط 20 يوم"))
    gap = (last["Open"] / prev["Close"] - 1) * 100
    if abs(gap) >= 3:
        items.append(_event("Price gap", "فجوة سعرية", "pos" if gap > 0 else "neg", f"{gap:+.1f}% at the open", f"{gap:+.1f}% عند الافتتاح"))
    return items


def catalyst_score(tech, fund, events):
    def pct(ch):
        return sum(x["Pass"] for x in ch) / len(ch) * 100 if ch else None

    t, f = pct(tech), pct(fund)
    e = 50.0
    for ev in events:
        e += {"pos": 12, "hot": 8, "neg": -15, "warn": -5}.get(ev["Impact"], 0)
    e = max(0.0, min(100.0, e))
    avail = [(v, w) for v, w in ((t, 0.5), (f, 0.3), (e, 0.2)) if v is not None]
    total = sum(v * w for v, w in avail) / sum(w for _, w in avail)
    for th, en, ar in ((70, "Strong Bullish", "إيجابي قوي"), (55, "Bullish", "إيجابي"), (45, "Neutral", "محايد"),
                       (30, "Bearish", "سلبي"), (-1, "Strong Bearish", "سلبي قوي")):
        if total >= th:
            return {"total": total, "technical": t, "fundamental": f, "event": e, "label": en, "label_ar": ar}
