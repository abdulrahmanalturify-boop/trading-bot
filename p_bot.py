"""
p_bot.py - Strategy Lab (trading bot backtests) · Trades journal
"""
import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import engine
import ta
import theme as T
import ui
from i18n import L, is_ar

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
    params = cfg["params"][cfg["strategy"]]
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
    r = st.columns(6)
    r[0].metric(L("Total return", "العائد الكلي"), f"{m['Total Return %']:+.1f}%", f"B&H {m['Buy & Hold %']:+.1f}%", delta_color="off")
    r[1].metric(L("CAGR", "العائد السنوي"), f"{m['CAGR %']:+.1f}%")
    r[2].metric(L("Sharpe", "شارب"), f"{m['Sharpe']:.2f}")
    r[3].metric(L("Max drawdown", "أقصى تراجع"), f"{m['Max Drawdown %']:.1f}%")
    r[4].metric(L("Win rate", "نسبة النجاح"), f"{m['Win Rate %']:.0f}%", L(f"{m['Trades']} trades", f"{m['Trades']} صفقة"), delta_color="off")
    r[5].metric(L("Profit factor", "معامل الربح"), "∞" if m["Profit Factor"] == np.inf else f"{m['Profit Factor']:.2f}")

    d = ta.add_all(df)
    overlays = {"SMA Crossover": ["SMA 20", "SMA 50"], "Golden Cross (50/200)": ["SMA 50", "SMA 200"],
                "EMA Crossover": ["EMA 9", "EMA 21"], "Bollinger Breakout": ["Bollinger Bands"]}.get(cfg["strategy"], [])
    panels = {"RSI Mean Reversion": ["RSI"], "MACD Crossover": ["MACD"]}.get(cfg["strategy"], [])
    st.plotly_chart(charts.price_chart(d, "Candles" if len(df) <= 800 else "Line", overlays, panels, False, trades=tr))
    bench = df["Close"] / df["Close"].iloc[0] * cfg["capital"]
    st.plotly_chart(charts.equity_chart(res["equity"], bench, (L("Strategy", "الاستراتيجية"), L("Buy & Hold", "شراء واحتفاظ"),
                                                                L("Drawdown %", "التراجع %"))))
    st.plotly_chart(charts.monthly_heatmap(engine.monthly_returns(res["equity"]), L("Monthly returns", "العوائد الشهرية"),
                                           MONTHS_AR if is_ar() else None))
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
                st.plotly_chart(charts.optimizer_heatmap(grid, labels[px_], labels[py_], L(metric, METRIC_AR[metric])))
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
            st.plotly_chart(charts.hbar(list(comp[L("Strategy", "الاستراتيجية")]), list(comp[tr_col]),
                                        L("Total return by strategy", "العائد الكلي حسب الاستراتيجية")))
    ui.foot()


def page_trades():
    ui.header("receipt_long", "Trade Journal", "سجل الصفقات",
              "Every trade the bot made with the current Strategy Lab settings.", "كل صفقة سواها البوت بإعدادات مختبر الاستراتيجيات الحالية.")
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
    m = res["metrics"]
    closed, open_tr = tr[tr["Exit Reason"] != "Open"], tr[tr["Exit Reason"] == "Open"]
    if not open_tr.empty:
        o = open_tr.iloc[0]
        ui.html(f'<div class="card">{T.icon("radio_button_checked", T.UP)} <b>{L("Open position", "صفقة مفتوحة")}</b> · '
                f'{L("entered", "دخول")} {o["Entry Date"]:%Y-%m-%d} @ ${o["Entry"]:,.2f} · {L("now", "الآن")} ${o["Exit"]:,.2f} · '
                f'<span class="{T.cls(o["P&L %"])}">{o["P&L %"]:+.2f}% (${o["P&L $"]:+,.0f})</span></div>')
    r = st.columns(6)
    r[0].metric(L("Closed trades", "صفقات مغلقة"), m["Trades"])
    r[1].metric(L("Win rate", "نسبة النجاح"), f"{m['Win Rate %']:.0f}%")
    r[2].metric(L("Avg win", "متوسط الربح"), f"{m['Avg Win %']:+.2f}%")
    r[3].metric(L("Avg loss", "متوسط الخسارة"), f"{m['Avg Loss %']:+.2f}%")
    r[4].metric(L("Net P&L", "صافي الربح"), f"${closed['P&L $'].sum():+,.0f}")
    r[5].metric(L("Avg holding", "متوسط المدة"), L(f"{m['Avg Bars Held']:.0f} days", f"{m['Avg Bars Held']:.0f} يوم"))
    c1, c2 = st.columns(2)
    c1.plotly_chart(charts.trade_bars(tr, L("P&L per trade (%)", "ربح/خسارة كل صفقة (%)")))
    c2.plotly_chart(charts.cumulative_pnl(tr, L("Cumulative P&L ($)", "الربح التراكمي ($)"), L("Trade #", "رقم الصفقة")))
    c3, c4 = st.columns(2)
    reasons = tr["Exit Reason"].value_counts()
    c3.plotly_chart(charts.pie([L(x, engine.EXIT_REASON_AR.get(x, x)) for x in reasons.index], list(reasons.values),
                               L("Exit reasons", "أسباب الخروج")))
    c4.plotly_chart(charts.histogram(tr["P&L %"], L("P&L distribution (%)", "توزيع الأرباح والخسائر (%)")))
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
