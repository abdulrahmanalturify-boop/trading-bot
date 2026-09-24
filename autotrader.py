"""
autotrader.py - "Run the bot": a full portfolio simulation of the trading bot.
Every trading day it scans the universe, hunts the best setups (breakout, pullback, golden cross, MACD cross, dip in an uptrend),
buys stocks and/or call options at the next open, manages stops / targets / trailing stops / time exits,
and records every trade. Daily data only: signals on the close, fills at the next open.
Options are priced with Black-Scholes using the stock's own recent volatility (a model, not real quotes).
"""
from math import erf, exp, log, sqrt

import numpy as np
import pandas as pd

import ta

SETUP_NAMES = {1: ("Breakout", "اختراق"), 2: ("Pullback", "ارتداد للمتوسط"), 3: ("Golden cross", "التقاطع الذهبي"),
               4: ("MACD cross", "تقاطع الماكد"), 5: ("Dip in uptrend", "هبوط داخل اتجاه صاعد")}
REASON_AR = {"Stop Loss": "وقف خسارة", "Trailing Stop": "وقف متحرك", "Take Profit": "جني أرباح", "Time Exit": "انتهاء المدة",
             "Trend Exit": "كسر الاتجاه", "Open": "مفتوحة"}


def _ncdf(x):
    return 0.5 * (1 + erf(x / sqrt(2)))


def bs_call(S, K, T, sigma, r=0.04):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0.0)
    d1 = (log(S / K) + (r + sigma * sigma / 2) * T) / (sigma * sqrt(T))
    return S * _ncdf(d1) - K * exp(-r * T) * _ncdf(d1 - sigma * sqrt(T))


def strike_for(price):
    step = 1 if price < 50 else (2.5 if price < 100 else (5 if price < 300 else 10))
    return round(price / step) * step


def features(df, spy_close):
    c, h, l, o, v = df["Close"], df["High"], df["Low"], df["Open"], df["Volume"]
    sma20, sma50, sma200 = c.rolling(20).mean(), c.rolling(50).mean(), c.rolling(200).mean()
    rsi = ta.rsi(c)
    macd, sig, _ = ta.macd(c)
    atr = ta.atr(df)
    adx = ta.adx(df)[0]
    hh20 = h.rolling(20).max().shift(1)
    vol20 = v.rolling(20).mean()
    rs = c.pct_change(63) - spy_close.reindex(c.index).pct_change(63)
    trend = (c > sma50) & (sma50 > sma200)
    brk = (c > hh20) & (v > 1.5 * vol20) & (c > sma50)
    gold = (sma50 > sma200) & (sma50.shift(1) <= sma200.shift(1)) & (c > sma50)
    pull = trend & (l <= sma20 * 1.01) & (c > sma20) & rsi.between(40, 62)
    mx = (macd > sig) & (macd.shift(1) <= sig.shift(1)) & trend
    dip = (rsi < 32) & (c > sma200)
    setup = pd.Series(np.select([brk, pull, gold, mx, dip], [1, 2, 3, 4, 5], 0), index=c.index)
    score = (brk * 3.0 + pull * 2.5 + gold * 2.0 + mx * 1.5 + dip * 1.5 + trend * 1.0 + (rs > 0) * 1.0
             + (adx > 25) * 0.5 + (v > vol20) * 0.5)
    score = score.where(setup > 0, 0.0)
    hv = c.pct_change().rolling(20).std() * np.sqrt(252)
    return pd.DataFrame({"O": o, "H": h, "L": l, "C": c, "ATR": atr, "SMA50": sma50, "HV": hv, "Score": score, "Setup": setup,
                         "RS": rs.fillna(0)})


def prepare(hist, spy):
    """hist: {symbol: OHLCV}, spy: OHLCV -> panels {field: DataFrame(dates x symbols)}."""
    cal = spy.index
    feats = {s: features(df, spy["Close"]) for s, df in hist.items() if df is not None and len(df) >= 220}
    if not feats:
        return None, cal
    panels = {k: pd.DataFrame({s: f[k] for s, f in feats.items()}).reindex(cal) for k in ("O", "H", "L", "C", "ATR", "SMA50", "HV", "Score", "Setup", "RS")}
    return panels, cal


def run(hist, spy, months=6, mode="stocks", capital=100_000.0, max_pos=8, risk_pct=1.0, stop_atr=2.0, target_r=3.0,
        trail_atr=3.0, max_hold=40, opt_alloc=2.0, opt_dte=35, opt_tp=100.0, opt_sl=50.0, min_score=3.5, fee=0.0005, sectors=None):
    panels, cal = prepare(hist, spy)
    if panels is None:
        return None
    end = cal[-1]
    start = end - pd.DateOffset(months=months)
    dates = cal[cal > start]
    if len(dates) < 10:
        return None
    sectors = sectors or {}
    P = panels
    cash = float(capital)
    pos, pending, trades, log_, eq = {}, [], [], [], []
    eq_prev = cash

    def close_trade(sym, p, d, exit_px, reason):
        nonlocal cash
        if p["kind"] == "Stock":
            proceeds = p["qty"] * exit_px * (1 - fee)
            fees = p["fees"] + p["qty"] * exit_px * fee
            pnl = proceeds - p["qty"] * p["entry"] - p["fees"]
            cost = p["qty"] * p["entry"]
        else:
            proceeds = p["qty"] * 100 * exit_px - p["qty"] * 0.65
            fees = p["fees"] + p["qty"] * 0.65
            pnl = proceeds - p["qty"] * 100 * p["entry"] - p["fees"]
            cost = p["qty"] * 100 * p["entry"]
        cash += proceeds
        trades.append({"Symbol": sym, "Type": p["kind"], "Contract": p.get("contract", sym), "Setup": p["setup"], "Sector": sectors.get(sym, ""),
                       "Entry Date": p["date"], "Entry": p["entry"], "Exit Date": d, "Exit": exit_px, "Qty": p["qty"],
                       "P&L $": pnl, "P&L %": pnl / cost * 100 if cost else 0.0, "Fees": fees, "Days": p["bars"], "Exit Reason": reason})
        log_.append((d, "sell", sym, p["kind"], reason, pnl))

    for i, d in enumerate(dates):
        O, H, Lo, C = P["O"].loc[d], P["H"].loc[d], P["L"].loc[d], P["C"].loc[d]
        # ---- 1) fill yesterday's orders at today's open
        for sym, kind, score, setup, atr, hv in pending:
            if sym in pos or len(pos) >= max_pos:
                continue
            o = O.get(sym)
            if o is None or not np.isfinite(o) or not np.isfinite(atr) or atr <= 0:
                continue
            if kind == "Stock":
                stop = o - stop_atr * atr
                rps = o - stop
                qty = int(eq_prev * risk_pct / 100 / rps) if rps > 0 else 0
                qty = min(qty, int(min(cash, eq_prev * 1.5 / max_pos) / o))
                if qty < 1:
                    continue
                cash -= qty * o * (1 + fee)
                pos[sym] = {"kind": "Stock", "qty": qty, "entry": o, "date": d, "stop": stop, "target": o + target_r * rps, "high": o,
                            "atr": atr, "setup": setup, "fees": qty * o * fee, "bars": 0, "value": o}
            else:
                sigma = float(np.clip((hv if np.isfinite(hv) else 0.35) * 1.1, 0.15, 1.5))
                k = strike_for(o)
                prem = bs_call(o, k, opt_dte / 365, sigma)
                if prem < 0.05:
                    continue
                n = int(eq_prev * opt_alloc / 100 / (prem * 100))
                n = min(n, int(cash / (prem * 100 + 0.65)))
                if n < 1:
                    continue
                cash -= n * prem * 100 + n * 0.65
                expiry = d + pd.Timedelta(days=opt_dte)
                pos[sym] = {"kind": "Call", "qty": n, "entry": prem, "date": d, "K": k, "expiry": expiry, "sigma": sigma, "setup": setup,
                            "fees": n * 0.65, "bars": 0, "value": prem, "contract": f"{sym} {k:g}C {expiry:%Y-%m-%d}"}
            log_.append((d, "buy", sym, kind, setup, 0.0))
        pending = []
        # ---- 2) manage open positions on today's bar
        for sym, p in list(pos.items()):
            o, h, l, c = O.get(sym), H.get(sym), Lo.get(sym), C.get(sym)
            if c is None or not np.isfinite(c):
                continue
            p["bars"] += 1
            sma50 = P["SMA50"].at[d, sym]
            if p["kind"] == "Stock":
                trail = p["high"] - trail_atr * p["atr"] if trail_atr else -np.inf
                stop = max(p["stop"], trail)
                px, why = None, None
                if l <= stop:
                    px = o if o < stop else stop
                    why = "Trailing Stop" if trail > p["stop"] else "Stop Loss"
                elif h >= p["target"]:
                    px, why = (o if o > p["target"] else p["target"]), "Take Profit"
                elif p["bars"] >= max_hold:
                    px, why = c, "Time Exit"
                elif np.isfinite(sma50) and c < sma50 and p["bars"] > 3:
                    px, why = c, "Trend Exit"
                p["high"] = max(p["high"], c)
                p["value"] = c
                if px is not None:
                    close_trade(sym, p, d, float(px), why)
                    del pos[sym]
            else:
                t_left = (p["expiry"] - d).days
                hv = P["HV"].at[d, sym]
                sigma = float(np.clip(hv * 1.1, 0.15, 1.5)) if np.isfinite(hv) else p["sigma"]
                val = bs_call(c, p["K"], max(t_left, 0) / 365, sigma)
                p["value"] = val
                why = None
                if val >= p["entry"] * (1 + opt_tp / 100):
                    why = "Take Profit"
                elif val <= p["entry"] * (1 - opt_sl / 100):
                    why = "Stop Loss"
                elif t_left <= 7:
                    why = "Time Exit"
                elif np.isfinite(sma50) and c < sma50 and p["bars"] > 3:
                    why = "Trend Exit"
                if why:
                    close_trade(sym, p, d, float(val), why)
                    del pos[sym]
        # ---- 3) mark to market
        value = sum(p["qty"] * p["value"] * (100 if p["kind"] == "Call" else 1) for p in pos.values())
        eq_prev = cash + value
        eq.append((d, eq_prev, len(pos)))
        # ---- 4) hunt: tomorrow's orders from today's close
        free = max_pos - len(pos)
        if free > 0 and i < len(dates) - 1:
            sc = P["Score"].loc[d]
            cand = sc[sc >= min_score].drop(labels=list(pos), errors="ignore")
            if len(cand):
                rank = (cand + P["RS"].loc[d].reindex(cand.index).fillna(0).clip(-1, 1)).sort_values(ascending=False)
                for sym in rank.index[:free]:
                    s_ = float(sc[sym])
                    kind = "Stock" if mode == "stocks" else ("Call" if mode == "options" else ("Call" if s_ >= min_score + 2 else "Stock"))
                    pending.append((sym, kind, s_, int(P["Setup"].at[d, sym]), float(P["ATR"].at[d, sym]), float(P["HV"].at[d, sym])))
                    log_.append((d, "signal", sym, kind, int(P["Setup"].at[d, sym]), s_))
    last = dates[-1]
    open_rows = []
    for sym, p in pos.items():
        mult = 100 if p["kind"] == "Call" else 1
        cost = p["qty"] * p["entry"] * mult
        pnl = p["qty"] * p["value"] * mult - cost - p["fees"]
        open_rows.append({"Symbol": sym, "Type": p["kind"], "Contract": p.get("contract", sym), "Setup": p["setup"], "Sector": sectors.get(sym, ""),
                          "Entry Date": p["date"], "Entry": p["entry"], "Exit Date": last, "Exit": p["value"], "Qty": p["qty"],
                          "P&L $": pnl, "P&L %": pnl / cost * 100 if cost else 0.0, "Fees": p["fees"], "Days": p["bars"], "Exit Reason": "Open"})
    equity = pd.DataFrame(eq, columns=["Date", "Equity", "Positions"]).set_index("Date")
    bench = spy["Close"].reindex(equity.index).ffill()
    bench = bench / bench.iloc[0] * capital
    cols = ["Symbol", "Type", "Contract", "Setup", "Sector", "Entry Date", "Entry", "Exit Date", "Exit", "Qty", "P&L $", "P&L %", "Fees", "Days", "Exit Reason"]
    return {"trades": pd.DataFrame(trades, columns=cols), "open": pd.DataFrame(open_rows, columns=cols), "equity": equity["Equity"],
            "positions": equity["Positions"], "bench": bench, "log": log_, "start": dates[0], "end": last, "capital": capital}


def stats(res):
    tr, eq = res["trades"], res["equity"]
    cap = res["capital"]
    out = {"trades": len(tr), "net": float(tr["P&L $"].sum()) if len(tr) else 0.0, "fees": float(tr["Fees"].sum()) if len(tr) else 0.0}
    out["gross"] = out["net"] + out["fees"]
    wins, losses = tr[tr["P&L $"] > 0], tr[tr["P&L $"] <= 0]
    out["wins"], out["losses"] = len(wins), len(losses)
    out["win_rate"] = len(wins) / len(tr) * 100 if len(tr) else 0.0
    gl = -losses["P&L $"].sum()
    out["pf"] = float(wins["P&L $"].sum() / gl) if gl > 0 else (float("inf") if len(wins) else 0.0)
    out["avg_win"] = float(wins["P&L $"].mean()) if len(wins) else 0.0
    out["avg_loss"] = float(losses["P&L $"].mean()) if len(losses) else 0.0
    out["wl_ratio"] = out["avg_win"] / abs(out["avg_loss"]) if out["avg_loss"] else (float("inf") if out["avg_win"] else 0.0)
    out["expectancy"] = out["net"] / len(tr) if len(tr) else 0.0
    daily = tr.groupby(pd.to_datetime(tr["Exit Date"]).dt.normalize())["P&L $"].sum() if len(tr) else pd.Series(dtype=float)
    out["day_wins"], out["day_losses"] = int((daily > 0).sum()), int((daily <= 0).sum())
    out["day_win_rate"] = out["day_wins"] / len(daily) * 100 if len(daily) else 0.0
    out["max_dd"] = float(((eq / eq.cummax()) - 1).min() * 100) if len(eq) else 0.0
    out["ret"] = float((eq.iloc[-1] / cap - 1) * 100) if len(eq) else 0.0
    out["bench_ret"] = float((res["bench"].iloc[-1] / cap - 1) * 100) if len(res["bench"]) else 0.0
    open_pnl = float(res["open"]["P&L $"].sum()) if len(res["open"]) else 0.0
    out["open_pnl"] = open_pnl
    out["exposure"] = float((res["positions"] > 0).mean() * 100) if len(res["positions"]) else 0.0
    return out
