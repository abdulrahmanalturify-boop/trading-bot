"""
p_bot.py - Auto Trader (run the bot over several months) · Strategy Lab (backtests) · Trade Journal (dashboard)
"""
import numpy as np
import pandas as pd
import streamlit as st

import autotrader
import charts
import data
import engine
import ta
import taxonomy as X
import tdash
import theme as T
import ui
import universe as U
from i18n import L, is_ar, sector_name

ss = st.session_state
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
METRIC_AR = {"Total Return %": "العائد الكلي %", "Sharpe": "شارب", "Max Drawdown %": "أقصى تراجع %", "Win Rate %": "نسبة النجاح %",
             "CAGR %": "العائد السنوي المركب %"}


def strat_name(k):
    return L(k, engine.STRATEGY_AR.get(k, k))


def lab_settings():
    cfg = ss.lab_cfg
    with st.container(border=True):
        c = st.columns([1, 0.8, 1.6, 1, 0.8])
        cfg["symbol"] = c[0].text_input(L("Symbol", "الرمز"), cfg["symbol"]).strip().upper() or "AAPL"
        periods = ["1y", "2y", "5y", "10y"]
        cfg["period"] = c[1].selectbox(L("History", "المدة"), periods, index=periods.index(cfg["period"]),
                                       format_func=lambda p: L(p, p.replace("y", " سنة")))
        names = list(engine.STRATEGIES)
        cfg["strategy"] = c[2].selectbox(L("Strategy", "الاستراتيجية"), names, index=names.index(cfg["strategy"]), format_func=strat_name)
        cfg["capital"] = c[3].number_input(L("Capital ($)", "رأس المال ($)"), 100, 100_000_000, int(cfg["capital"]), step=1000)
        cfg["fee"] = c[4].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, float(cfg["fee"]), step=0.01)
        spec = engine.STRATEGIES[cfg["strategy"]][1]
        params = cfg["params"].setdefault(cfg["strategy"], {k: dflt for k, _, _, _, dflt, _ in spec})
        pc = st.columns(len(spec) + 4)
        for i, (k, label, lo, hi, dflt, step) in enumerate(spec):
            lab = L(label, engine.PARAM_AR.get(label, label))
            if isinstance(step, float):
                params[k] = pc[i].number_input(lab, float(lo), float(hi), float(params.get(k, dflt)), step=float(step))
            else:
                params[k] = pc[i].number_input(lab, int(lo), int(hi), int(params.get(k, dflt)), step=int(step))
        j = len(spec)
        off = L("0 = off", "0 = إيقاف")
        cfg["stop"] = pc[j].number_input(L("Stop loss %", "وقف الخسارة %"), 0.0, 50.0, float(cfg["stop"]), step=0.5, help=off)
        cfg["atr"] = pc[j + 1].number_input(L("ATR stop ×", "وقف ATR ×"), 0.0, 10.0, float(cfg["atr"]), step=0.5, help=off)
        cfg["tp"] = pc[j + 2].number_input(L("Take profit %", "جني الأرباح %"), 0.0, 500.0, float(cfg["tp"]), step=1.0, help=off)
        cfg["trail"] = pc[j + 3].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, float(cfg["trail"]), step=0.5, help=off)
    return cfg


def risk_kwargs(cfg):
    return {"stop_pct": cfg["stop"] or None, "atr_mult": cfg["atr"] or None, "tp_pct": cfg["tp"] or None,
            "trail_pct": cfg["trail"] or None}


def run_lab(cfg):
    df = data.history(cfg["symbol"], cfg["period"])
    if df.empty or len(df) < 60:
        st.error(L(f"Not enough data for {cfg['symbol']}.", f"لا توجد بيانات كافية للرمز {cfg['symbol']}."))
        return None, None
    spec = engine.STRATEGIES[cfg["strategy"]][1]
    params = cfg["params"].setdefault(cfg["strategy"], {k: dflt for k, _, _, _, dflt, _ in spec})
    if "fast" in params and "slow" in params and params["fast"] >= params["slow"]:
        st.error(L("Fast period must be smaller than slow period.", "الفترة السريعة لازم تكون أصغر من البطيئة."))
        return None, None
    res = engine.run_strategy(df, cfg["strategy"], params, cfg["capital"], cfg["fee"] / 100, **risk_kwargs(cfg))
    ss.lab = {"cfg": {**cfg, "params": dict(params)}, "res": res}
    return df, res


def page_lab():
    ui.header("smart_toy", "Strategy Lab", "مختبر الاستراتيجيات",
              "Backtest the trading bot: signals on the daily close, orders at the next open, stops checked intraday.",
              "اختبر بوت التداول: الإشارة على الإغلاق اليومي، التنفيذ عند افتتاح اليوم التالي، والوقف يُفحص خلال اليوم.")
    cfg = lab_settings()
    df, res = run_lab(cfg)
    if res is None:
        return
    m, tr = res["metrics"], res["trades"]
    open_tr = tr[tr["Exit Reason"] == "Open"]
    if res["position"].iloc[-1] and not open_tr.empty:
        o = open_tr.iloc[0]
        st.success(L(f"Bot is LONG since {o['Entry Date']:%b %d, %Y} at ${o['Entry']:,.2f} · open P&L {o['P&L %']:+.2f}%",
                     f"البوت في صفقة شراء منذ {o['Entry Date']:%Y-%m-%d} بسعر ${o['Entry']:,.2f} · الربح الحالي {o['P&L %']:+.2f}%"),
                   icon=":material/trending_up:")
    else:
        st.info(L("Bot is FLAT (no open position).", "البوت خارج السوق (لا توجد صفقة مفتوحة)."), icon=":material/pause_circle:")
    pf = "∞" if m["Profit Factor"] == np.inf else f"{m['Profit Factor']:.2f}"
    kp = [("trending_up", L("Total return", "العائد الكلي"), f"{m['Total Return %']:+.1f}%", f"B&H {m['Buy & Hold %']:+.1f}%", T.cls(m["Total Return %"])),
          ("speed", L("CAGR", "العائد السنوي"), f"{m['CAGR %']:+.1f}%", "", T.cls(m["CAGR %"])),
          ("insights", L("Sharpe", "شارب"), f"{m['Sharpe']:.2f}", "", "pos" if m["Sharpe"] >= 1 else ("neg" if m["Sharpe"] < 0 else None)),
          ("south_east", L("Max drawdown", "أقصى تراجع"), f"{m['Max Drawdown %']:.1f}%", "", "neg" if m["Max Drawdown %"] < -0.05 else None),
          ("target", L("Win rate", "نسبة النجاح"), f"{m['Win Rate %']:.0f}%", L(f"{m['Trades']} trades", f"{m['Trades']} صفقة"),
           "pos" if m["Win Rate %"] >= 50 else "neg"),
          ("balance", L("Profit factor", "معامل الربح"), pf, "", "pos" if m["Profit Factor"] >= 1 else "neg")]
    for col, (ic, lab, val, sub, kind) in zip(st.columns(6), kp):
        col.markdown(T.kpi(ic, lab, val, sub, kind), unsafe_allow_html=True)

    d = ta.add_all(df)
    overlays = {"SMA Crossover": ["SMA 20", "SMA 50"], "Golden Cross (50/200)": ["SMA 50", "SMA 200"],
                "EMA Crossover": ["EMA 9", "EMA 21"], "Bollinger Breakout": ["Bollinger Bands"]}.get(cfg["strategy"], [])
    panels = {"RSI Mean Reversion": ["RSI"], "MACD Crossover": ["MACD"]}.get(cfg["strategy"], [])
    ui.chart(charts.price_chart(d, "Candles" if len(df) <= 800 else "Line", overlays, panels, False, trades=tr), key="lab_price")
    bench = df["Close"] / df["Close"].iloc[0] * cfg["capital"]
    ui.chart(charts.equity_chart(res["equity"], bench, (L("Strategy", "الاستراتيجية"), L("Buy & Hold", "شراء واحتفاظ"),
                                                         L("Drawdown %", "التراجع %"))), key="lab_eq")
    ui.chart(charts.monthly_heatmap(engine.monthly_returns(res["equity"]), L("Monthly returns", "العوائد الشهرية"),
                                    MONTHS_AR if is_ar() else None), key="lab_month")
    if st.button(L("Open trade journal", "افتح سجل الصفقات"), icon=":material/receipt_long:"):
        ui.goto("trades")

    with st.expander(L("Parameter optimizer (heatmap)", "محسّن الإعدادات (خريطة حرارية)"), icon=":material/tune:"):
        spec = engine.STRATEGIES[cfg["strategy"]][1]
        keys = [s[0] for s in spec]
        labels = {s[0]: L(s[1], engine.PARAM_AR.get(s[1], s[1])) for s in spec}
        o1, o2, o3 = st.columns(3)
        px_ = o1.selectbox(L("X parameter", "المحور الأفقي"), keys, index=0, format_func=labels.get)
        py_ = o2.selectbox(L("Y parameter", "المحور الرأسي"), keys, index=min(1, len(keys) - 1), format_func=labels.get)
        metric = o3.selectbox(L("Optimize", "المعيار"), list(METRIC_AR), format_func=lambda k: L(k, METRIC_AR[k]))
        if st.button(L("Run optimizer", "شغّل المحسّن"), icon=":material/play_arrow:"):
            def rng(key):
                s = next(x for x in spec if x[0] == key)
                vals = np.linspace(s[2], s[3], 6)
                return [round(float(v), 1) if isinstance(s[5], float) else int(v) for v in vals]
            if px_ == py_:
                st.warning(L("Pick two different parameters.", "اختر إعدادين مختلفين."))
            else:
                with st.spinner(L("Running 36 backtests...", "جاري تشغيل 36 اختبار...")):
                    grid = engine.optimize(df, cfg["strategy"], px_, rng(px_), py_, rng(py_), cfg["params"][cfg["strategy"]],
                                           cfg["capital"], cfg["fee"] / 100, metric, **risk_kwargs(cfg))
                ui.chart(charts.optimizer_heatmap(grid, labels[px_], labels[py_], L(metric, METRIC_AR[metric])), key="lab_opt")
                st.caption(L("The best cell in the past is often overfit. Prefer stable regions.",
                             "أفضل خانة في الماضي غالباً تكون مبالغة؛ فضّل المناطق المستقرة."))

    with st.expander(L("Compare all strategies on this symbol", "قارن كل الاستراتيجيات على هذا السهم"), icon=":material/leaderboard:"):
        if st.button(L("Run comparison", "شغّل المقارنة"), icon=":material/play_arrow:"):
            rows = []
            for name, (_, spec) in engine.STRATEGIES.items():
                p = {k: dflt for k, _, _, _, dflt, _ in spec}
                mm = engine.run_strategy(df, name, p, cfg["capital"], cfg["fee"] / 100, **risk_kwargs(cfg))["metrics"]
                rows.append({L("Strategy", "الاستراتيجية"): strat_name(name), **{L(k, METRIC_AR[k]): mm[k] for k in METRIC_AR},
                             L("Trades", "الصفقات"): mm["Trades"]})
            comp = pd.DataFrame(rows).sort_values(L("Sharpe", "شارب"), ascending=False)
            tr_col, cagr = L("Total Return %", METRIC_AR["Total Return %"]), L("CAGR %", METRIC_AR["CAGR %"])
            st.dataframe(comp.style.map(T.color_style, subset=[tr_col, cagr]).format(
                {tr_col: "{:+.1f}%", cagr: "{:+.1f}%", L("Sharpe", "شارب"): "{:.2f}",
                 L("Max Drawdown %", METRIC_AR["Max Drawdown %"]): "{:.1f}%", L("Win Rate %", METRIC_AR["Win Rate %"]): "{:.0f}%"}),
                hide_index=True)
            ui.chart(charts.hbar(list(comp[L("Strategy", "الاستراتيجية")]), list(comp[tr_col]),
                                 L("Total return by strategy", "العائد الكلي حسب الاستراتيجية")), key="lab_cmp")
    ui.foot()


def page_trades():
    ui.header("receipt_long", "Trade Journal", "سجل الصفقات",
              "Every trade the bot made with the current Strategy Lab settings, as a trading dashboard.",
              "كل صفقة سواها البوت بإعدادات مختبر الاستراتيجيات الحالية، على شكل لوحة تداول.")
    if not ss.get("lab"):
        _, res = run_lab(ss.lab_cfg)
        if res is None:
            return
    cfg, res = ss.lab["cfg"], ss.lab["res"]
    risk = []
    for k, en, ar_, suf in (("stop", "SL", "وقف", "%"), ("atr", "ATR×", "ATR×", ""), ("tp", "TP", "هدف", "%"), ("trail", "Trail", "متحرك", "%")):
        if cfg[k]:
            risk.append(f"{L(en, ar_)} {cfg[k]}{suf}")
    ui.html(T.badge(cfg["symbol"], "gold", "sell") + T.badge(strat_name(cfg["strategy"]), "acc", "smart_toy") +
            T.badge(str(cfg["params"]), "neu") + T.badge(cfg["period"], "neu", "date_range") +
            T.badge(", ".join(risk) or L("No risk rules", "بدون وقف"), "neu", "shield"))
    tr = res["trades"]
    if tr.empty:
        st.info(L("The bot made no trades with these settings.", "البوت ما سوى أي صفقة بهذه الإعدادات."))
        return
    fee = cfg["fee"] / 100
    norm = pd.DataFrame({"Symbol": cfg["symbol"], "Type": "Stock", "Contract": cfg["symbol"], "Setup": 0, "Sector": "",
                         "Entry Date": pd.to_datetime(tr["Entry Date"]), "Entry": tr["Entry"], "Exit Date": pd.to_datetime(tr["Exit Date"]),
                         "Exit": tr["Exit"], "Qty": tr["Shares"], "P&L $": tr["P&L $"], "P&L %": tr["P&L %"],
                         "Fees": (tr["Entry"] + tr["Exit"]) * tr["Shares"] * fee, "Days": tr["Bars"], "Exit Reason": tr["Exit Reason"]})
    closed, open_tr = norm[norm["Exit Reason"] != "Open"], norm[norm["Exit Reason"] == "Open"]
    df = data.history(cfg["symbol"], cfg["period"])
    bench = df["Close"] / df["Close"].iloc[0] * cfg["capital"] if not df.empty else res["equity"] * 0 + cfg["capital"]
    s = autotrader.stats({"trades": closed, "open": open_tr, "equity": res["equity"], "bench": bench.reindex(res["equity"].index).ffill(),
                          "positions": res["position"], "capital": cfg["capital"]})
    tdash.render(closed, open_tr, s, cfg["capital"], key="journal")
    c1, c2 = st.columns(2)
    reasons = tr["Exit Reason"].value_counts()
    ui.chart(charts.pie([L(x, engine.EXIT_REASON_AR.get(x, x)) for x in reasons.index], list(reasons.values),
                        L("Exit reasons", "أسباب الخروج"), center=str(int(reasons.sum()))), key="tj_pie", container=c1)
    ui.chart(charts.trade_bars(tr, L("P&L per trade (%)", "ربح/خسارة كل صفقة (%)")), key="tj_bars", container=c2)
    ui.sec("table_rows", "All trades", "كل الصفقات")
    show = tr.copy()
    show.insert(0, "#", range(1, len(show) + 1))
    show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
    show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
    show["Exit Reason"] = show["Exit Reason"].map(lambda x: L(x, engine.EXIT_REASON_AR.get(x, x)))
    N = {"Entry Date": L("Entry date", "تاريخ الدخول"), "Entry": L("Entry", "سعر الدخول"), "Exit Date": L("Exit date", "تاريخ الخروج"),
         "Exit": L("Exit", "سعر الخروج"), "Shares": L("Shares", "الأسهم"), "P&L $": L("P&L $", "الربح $"), "P&L %": L("P&L %", "الربح %"),
         "Bars": L("Days", "الأيام"), "Exit Reason": L("Exit reason", "سبب الخروج")}
    show = show.rename(columns=N)
    st.dataframe(show.iloc[::-1].style.map(T.color_style, subset=[N["P&L %"], N["P&L $"]]).format(
        {N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Shares"]: "{:,.2f}", N["P&L $"]: "{:+,.2f}", N["P&L %"]: "{:+.2f}%"}),
        hide_index=True, height=420)
    st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), f"trades_{cfg['symbol']}.csv",
                       "text/csv", icon=":material/download:")
    ui.foot()


# =====================================================================
# AUTO TRADER: run the bot on the market over several months
# =====================================================================
def _auto_universes():
    from sp500 import SP500
    u = {"top": (L("Top 175 US stocks", "أكبر 175 سهم أمريكي"), list(U.US_UNIVERSE)),
         "sp500": (L("S&P 500 (slower)", "إس آند بي 500 (أبطأ)"), list(SP500))}
    for tk, (en, ar, _, _) in X.THEMES.items():
        u[f"t:{tk}"] = (L(f"Theme · {en}", f"ثيم · {ar}"), X.theme_tickers(tk))
    for sec, syms in U.by_sector().items():
        u[f"s:{sec}"] = (L(f"Sector · {sec}", f"قطاع · {sector_name(sec)}"), syms)
    u["wl"] = (L("My watchlist", "قائمة المتابعة"), list(ss.watchlist))
    return u


def _sector_map(syms):
    from sp500 import SP500
    out = {}
    for s in syms:
        if U.known(s):
            out[s] = U.sector_of(s)
        elif s in SP500:
            out[s] = SP500[s][1]
        elif s in X.EXTRA:
            out[s] = X.EXTRA[s][1]
    return out


def auto_settings():
    cfg = ss.setdefault("auto_cfg", {"uni": "top", "mode": "both", "months": 6, "capital": 100000, "max_pos": 8, "risk": 1.0, "min_score": 3.5,
                                     "stop_atr": 2.0, "target_r": 3.0, "trail_atr": 3.0, "max_hold": 40, "opt_alloc": 2.0, "opt_dte": 35,
                                     "opt_tp": 100.0, "opt_sl": 50.0})
    unis = _auto_universes()
    if cfg["uni"] not in unis:
        cfg["uni"] = "top"
    with st.container(border=True):
        c = st.columns([1.5, 1.2, 1.2, 1])
        cfg["uni"] = c[0].selectbox(L("Market to scan", "السوق الذي يبحث فيه البوت"), list(unis), index=list(unis).index(cfg["uni"]),
                                    format_func=lambda k: unis[k][0])
        cfg["mode"] = c[1].segmented_control(L("What it trades", "ماذا يتداول"), ["stocks", "options", "both"], default=cfg["mode"], key="au_mode",
                                             format_func=lambda k: {"stocks": L("Stocks", "أسهم"), "options": L("Options", "عقود"),
                                                                    "both": L("Both", "الاثنين")}[k]) or cfg["mode"]
        cfg["months"] = c[2].segmented_control(L("Trading period", "مدة التداول"), [3, 6, 12, 24], default=cfg["months"], key="au_months",
                                               format_func=lambda m: L(f"{m} months", f"{m} أشهر") if m < 12 else L(f"{m // 12} year" + ("s" if m > 12 else ""), "سنة" if m == 12 else "سنتين")) or cfg["months"]
        cfg["capital"] = c[3].number_input(L("Capital ($)", "رأس المال ($)"), 1000, 100_000_000, int(cfg["capital"]), step=5000)
        with st.expander(L("Bot rules (risk & exits)", "قواعد البوت (المخاطرة والخروج)"), icon=":material/tune:"):
            r = st.columns(4)
            cfg["max_pos"] = r[0].number_input(L("Max open positions", "أقصى عدد مراكز"), 1, 30, int(cfg["max_pos"]), step=1)
            cfg["risk"] = r[1].number_input(L("Risk per stock trade (%)", "المخاطرة لكل صفقة سهم (%)"), 0.1, 5.0, float(cfg["risk"]), step=0.1)
            cfg["min_score"] = r[2].number_input(L("Minimum setup score", "أقل تقييم للفرصة"), 1.0, 9.0, float(cfg["min_score"]), step=0.5)
            cfg["max_hold"] = r[3].number_input(L("Max holding (days)", "أقصى مدة احتفاظ (يوم)"), 5, 120, int(cfg["max_hold"]), step=5)
            r = st.columns(4)
            cfg["stop_atr"] = r[0].number_input(L("Stop (× ATR)", "الوقف (× ATR)"), 0.5, 6.0, float(cfg["stop_atr"]), step=0.5)
            cfg["target_r"] = r[1].number_input(L("Target (× risk)", "الهدف (× المخاطرة)"), 1.0, 10.0, float(cfg["target_r"]), step=0.5)
            cfg["trail_atr"] = r[2].number_input(L("Trailing stop (× ATR, 0 = off)", "الوقف المتحرك (× ATR، 0 = إيقاف)"), 0.0, 10.0, float(cfg["trail_atr"]), step=0.5)
            cfg["opt_alloc"] = r[3].number_input(L("Per option trade (% of capital)", "لكل صفقة عقود (% من رأس المال)"), 0.5, 10.0, float(cfg["opt_alloc"]), step=0.5)
            r = st.columns(4)
            cfg["opt_dte"] = r[0].number_input(L("Option days to expiry", "أيام حتى انتهاء العقد"), 14, 120, int(cfg["opt_dte"]), step=7)
            cfg["opt_tp"] = r[1].number_input(L("Option take profit (%)", "جني ربح العقد (%)"), 20.0, 500.0, float(cfg["opt_tp"]), step=10.0)
            cfg["opt_sl"] = r[2].number_input(L("Option stop loss (%)", "وقف خسارة العقد (%)"), 10.0, 90.0, float(cfg["opt_sl"]), step=5.0)
            r[3].caption(L("Options: at-the-money calls on the strongest setups. In 'Both' mode, scores 2+ points above the minimum trade calls.",
                           "العقود: عقود شراء CALL عند سعر السوق على أقوى الفرص. في وضع 'الاثنين' الفرص الأعلى بنقطتين من الحد الأدنى تُتداول بعقود."))
    return cfg, unis


def page_autotrader():
    ui.header("rocket_launch", "Auto Trader", "التداول الآلي",
              "Run the bot: every day it scans the market, hunts the best setups, buys stocks or call options, manages its exits, and reports the results.",
              "شغّل البوت: كل يوم يمسح السوق، يصطاد أفضل الفرص، يشتري أسهم أو عقود CALL، يدير الخروج بنفسه، ثم يعرض لك النتائج.")
    cfg, unis = auto_settings()
    if st.button(L("Run the bot", "شغّل البوت"), type="primary", icon=":material/play_arrow:"):
        syms = unis[cfg["uni"]][1]
        period = "5y" if cfg["months"] > 12 else "2y"
        with st.spinner(L(f"Downloading {len(syms)} stocks and running {cfg['months']} months of trading...",
                          f"جاري تحميل {len(syms)} سهم وتشغيل {cfg['months']} أشهر من التداول...")):
            hist = data.history_many(tuple(syms), period)
            spy = data.history("SPY", period)
            res = None
            if hist and not spy.empty:
                res = autotrader.run(hist, spy, int(cfg["months"]), cfg["mode"], float(cfg["capital"]), int(cfg["max_pos"]), float(cfg["risk"]),
                                     float(cfg["stop_atr"]), float(cfg["target_r"]), float(cfg["trail_atr"]), int(cfg["max_hold"]),
                                     float(cfg["opt_alloc"]), int(cfg["opt_dte"]), float(cfg["opt_tp"]), float(cfg["opt_sl"]),
                                     float(cfg["min_score"]), sectors=_sector_map(syms))
        if res is None:
            st.error(L("Not enough market data to run the bot right now. Try again in a minute.", "لا توجد بيانات كافية لتشغيل البوت حالياً. حاول بعد دقيقة."))
            return
        ss.auto = {"res": res, "cfg": dict(cfg), "n": len(hist), "uni": unis[cfg["uni"]][0]}
    au = ss.get("auto")
    if not au:
        msg = L("Choose the market, what the bot may trade (stocks, call options or both) and how many months, then press <b>Run the bot</b>. "
                "It replays those months day by day: scanning after each close, buying at the next open, and exiting by stop, target, trailing stop or time.",
                "اختر السوق، وماذا يتداول البوت (أسهم أو عقود CALL أو الاثنين)، وعدد الأشهر، ثم اضغط <b>شغّل البوت</b>. "
                "البوت يعيد تشغيل هذه الأشهر يوماً بيوم: يبحث بعد كل إغلاق، ويشتري عند الافتتاح التالي، ويخرج بالوقف أو الهدف أو الوقف المتحرك أو انتهاء المدة.")
        ui.html(f'<div class="card" style="line-height:1.9">{T.ico("smart_toy", "acc")} {msg}</div>')
        ui.foot()
        return
    res, cfg_run = au["res"], au["cfg"]
    s = autotrader.stats(res)
    tr, op = res["trades"], res["open"]
    signals = sum(1 for e in res["log"] if e[1] == "signal")
    mode_txt = {"stocks": L("stocks", "أسهم"), "options": L("call options", "عقود CALL"), "both": L("stocks + call options", "أسهم + عقود CALL")}[cfg_run["mode"]]
    n_syms = au["n"]
    span = f"{res['start']:%Y-%m-%d} → {res['end']:%Y-%m-%d}"
    ui.html(f'<div class="card">{T.badge(au["uni"], "acc", "public")}{T.badge(mode_txt, "vio", "swap_horiz")}'
            f'{T.badge(span, "neu", "date_range")}'
            f'{T.badge(L(f"{n_syms} stocks scanned daily", f"{n_syms} سهم يُفحص يومياً"), "neu", "radar")}'
            f'{T.badge(L(f"{signals} signals found", f"{signals} إشارة"), "gold", "bolt")}'
            f'{T.badge(L(f"{len(tr)} closed · {len(op)} open", f"{len(tr)} مغلقة · {len(op)} مفتوحة"), "neu", "receipt_long")}</div>')
    tdash.render(tr, op, s, res["capital"], key="auto")

    ui.sec("show_chart", "Equity vs S&P 500", "المحفظة مقابل إس آند بي 500")
    a, b = st.columns([1.6, 1])
    with a:
        ui.chart(charts.equity_chart(res["equity"], res["bench"], (L("Bot portfolio", "محفظة البوت"), "S&P 500 (SPY)", L("Drawdown %", "التراجع %"))),
                 key="au_eq")
    with b:
        m = res["equity"].resample("ME").last()
        prev = pd.concat([pd.Series([res["capital"]]), m.iloc[:-1]]).values
        mret = (m.values / prev - 1) * 100
        labels = [f"{MONTHS_AR[d.month - 1]} {d.year % 100}" if is_ar() else f"{d:%b %y}" for d in m.index]
        fig = charts.signed_bars(labels, mret, L("Monthly return (%)", "العائد الشهري (%)"), 470, prefix="", fmt="+.2f")
        fig.update_yaxes(ticksuffix="%")
        ui.chart(fig, key="au_month")

    if len(tr):
        ui.sec("pie_chart", "What worked", "ماذا نجح")
        c1, c2, c3 = st.columns(3)
        with c1:
            g = tr.groupby("Type")["P&L $"].sum()
            names = {"Stock": L("Stocks", "أسهم"), "Call": L("Call options", "عقود CALL")}
            ui.chart(charts.pie([names.get(k, k) for k in g.index], list(tr.groupby("Type").size().values),
                                L("Trades by type", "الصفقات حسب النوع"), [T.ACCENT, T.VIOLET], f"{len(tr)}"), key="au_type")
            ui.html("".join(f'<div class="vals" style="display:flex;justify-content:space-between;margin:4px 6px"><span>{names.get(k, k)}</span>{T.pbox(T.money(v), v)}</div>'
                            for k, v in g.items()))
        with c2:
            g = tr.groupby("Setup")["P&L $"].sum()
            ui.chart(charts.hbar([L(*autotrader.SETUP_NAMES.get(int(k), ("?", "?"))) for k in g.index], [float(v) for v in g.values],
                                 L("P&L by setup ($)", "الربح حسب نوع الفرصة ($)"), 320, suffix=""), key="au_setup")
        with c3:
            g = tr[tr["Sector"] != ""].groupby("Sector")["P&L $"].sum()
            if len(g):
                ui.chart(charts.hbar([sector_name(k) for k in g.index], [float(v) for v in g.values], L("P&L by sector ($)", "الربح حسب القطاع ($)"),
                                     max(320, 30 * len(g) + 70), suffix=""), key="au_sector")
        best, worst = tr.sort_values("P&L $", ascending=False).head(3), tr.sort_values("P&L $").head(3)
        lg = data.logos(list(best["Symbol"]) + list(worst["Symbol"]))

        def mini(r):
            return (f'<div class="o"><div>{T.company(r["Symbol"], "", lg.get(r["Symbol"]), 26, sub=r["Contract"], href=ui.href(r["Symbol"]))}'
                    f'<div class="m">{pd.Timestamp(r["Entry Date"]):%Y-%m-%d} → {pd.Timestamp(r["Exit Date"]):%Y-%m-%d} · '
                    f'{L(r["Exit Reason"], autotrader.REASON_AR.get(r["Exit Reason"], r["Exit Reason"]))}</div></div>'
                    f'<div style="text-align:right">{T.pbox(T.money(r["P&L $"]), r["P&L $"])}<div class="m">{r["P&L %"]:+.1f}%</div></div></div>')
        x, y = st.columns(2)
        x.markdown(f'<div class="tdp"><div class="tt">{L("Best trades", "أفضل الصفقات")}</div><div class="opos">{"".join(mini(r) for _, r in best.iterrows())}</div></div>',
                   unsafe_allow_html=True)
        y.markdown(f'<div class="tdp"><div class="tt">{L("Worst trades", "أسوأ الصفقات")}</div><div class="opos">{"".join(mini(r) for _, r in worst.iterrows())}</div></div>',
                   unsafe_allow_html=True)

    ui.sec("table_rows", "All trades", "كل الصفقات")
    allt = pd.concat([tr, op], ignore_index=True) if len(op) else tr.copy()
    if allt.empty:
        st.info(L("The bot found no trades with these rules. Lower the minimum score or choose a longer period.",
                  "البوت ما لقى صفقات بهذه القواعد. خفّض أقل تقييم أو اختر مدة أطول."))
    else:
        show = allt.sort_values("Entry Date", ascending=False).copy()
        show.insert(0, "Logo", show["Symbol"].map(data.logo_url))
        show["Setup"] = show["Setup"].map(lambda k: L(*autotrader.SETUP_NAMES.get(int(k), ("?", "?"))))
        show["Type"] = show["Type"].map(lambda t: L("Stock", "سهم") if t == "Stock" else "CALL")
        show["Exit Reason"] = show["Exit Reason"].map(lambda r: L(r, autotrader.REASON_AR.get(r, r)))
        show["Sector"] = show["Sector"].map(lambda v: sector_name(v) if v else "—")
        for c_ in ("Entry Date", "Exit Date"):
            show[c_] = pd.to_datetime(show[c_]).dt.date
        N = {"Symbol": L("Symbol", "الرمز"), "Type": L("Type", "النوع"), "Contract": L("Position", "المركز"), "Setup": L("Setup", "الفرصة"),
             "Sector": L("Sector", "القطاع"), "Entry Date": L("Entry date", "تاريخ الدخول"), "Entry": L("Entry", "الدخول"),
             "Exit Date": L("Exit date", "تاريخ الخروج"), "Exit": L("Exit", "الخروج"), "Qty": L("Qty", "الكمية"), "P&L $": L("P&L $", "الربح $"),
             "P&L %": L("P&L %", "الربح %"), "Fees": L("Fees", "العمولة"), "Days": L("Days", "الأيام"), "Exit Reason": L("Exit reason", "سبب الخروج")}
        show = show.rename(columns=N)
        st.dataframe(show.style.map(T.color_style, subset=[N["P&L $"], N["P&L %"]]).format(
            {N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Qty"]: "{:,.0f}", N["P&L $"]: "{:+,.2f}", N["P&L %"]: "{:+.2f}%", N["Fees"]: "{:,.2f}"}, na_rep="—"),
            hide_index=True, height=440, column_config={"Logo": st.column_config.ImageColumn(" ", width="small")})
        st.download_button(L("Export CSV", "تصدير CSV"), show.drop(columns=["Logo"]).to_csv(index=False).encode("utf-8-sig"), "bot_trades.csv",
                           "text/csv", icon=":material/download:")
    with st.expander(L("Bot activity log", "سجل نشاط البوت"), icon=":material/history:"):
        rows = []
        for d, kind, sym, typ, det, val in reversed(res["log"][-80:]):
            if kind == "signal":
                txt = L(f"Signal: {L(*autotrader.SETUP_NAMES.get(det, ('?', '?')))} (score {val:.1f}), order for tomorrow's open",
                        f"إشارة: {L(*autotrader.SETUP_NAMES.get(det, ('?', '?')))} (تقييم {val:.1f})، أمر للافتتاح التالي")
                ic = T.ico("bolt", "gold")
            elif kind == "buy":
                txt = L(f"Bought {'call options' if typ == 'Call' else 'shares'}", f"اشترى {'عقود CALL' if typ == 'Call' else 'أسهم'}")
                ic = T.ico("shopping_cart", "acc")
            else:
                txt = L(f"Sold ({det})", f"باع ({autotrader.REASON_AR.get(det, det)})") + f" {T.money(val)}"
                ic = T.ico("sell", "pos" if val > 0 else "neg")
            rows.append(f'<div class="log">{ic}<b>{T.esc(sym)}</b><span class="muted">{pd.Timestamp(d):%Y-%m-%d}</span><span>{T.esc(txt)}</span></div>')
        ui.html("".join(rows) or "—")
    st.caption(L("Simulation on real historical prices: signals on the daily close, orders at the next open, 0.05% slippage per side and "
                 "$0.65 per option contract. Option prices come from the Black-Scholes model with the stock's own volatility, so real fills will differ. "
                 "Past results do not guarantee future returns.",
                 "محاكاة على أسعار تاريخية حقيقية: الإشارة على الإغلاق اليومي، والتنفيذ عند الافتتاح التالي، مع انزلاق 0.05% لكل جهة و0.65$ لكل عقد. "
                 "أسعار العقود محسوبة بنموذج بلاك-شولز بتذبذب السهم نفسه، لذلك التنفيذ الحقيقي يختلف. النتائج السابقة لا تضمن المستقبل."))
    ui.foot()
