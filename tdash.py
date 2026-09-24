"""
tdash.py - Trading dashboard (journal style): KPI cards with gauges and goals, cumulative & daily P&L,
recent trades, a P&L calendar with weekly totals, and open positions. Used by the Auto Trader and the Trade Journal.
"""
import calendar as _cal

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import theme as T
import ui
from i18n import L, is_ar

DAYS = [("Mon", "الاثنين"), ("Tue", "الثلاثاء"), ("Wed", "الأربعاء"), ("Thu", "الخميس"), ("Fri", "الجمعة")]
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
GOALS = {"win": 55.0, "pf": 1.5, "day": 55.0, "wl": 1.5, "dd": 20.0}


def month_name(y, m):
    return f"{MONTHS_AR[m - 1]} {y}" if is_ar() else f"{_cal.month_name[m]} {y}"


def _goal(value, goal, fmt, higher=True):
    met = value >= goal if higher else value <= goal
    share = (value / goal * 100) if higher and goal else ((goal / value * 100) if value else 100)
    return T.goal(share, L(f"{min(share, 999):.0f}% of goal", f"{min(share, 999):.0f}% من الهدف") if not met else L("Goal met", "تحقق الهدف"),
                  L(f"Goal: {fmt(goal)}", f"الهدف: {fmt(goal)}"), met)


def kpi_cards(s, capital):
    net = s["net"]
    wr, dr = s["win_rate"], s["day_win_rate"]
    pf = s["pf"]
    pf_txt = "∞" if pf == float("inf") else f"{pf:.2f}"
    pf_ring = 100 if pf == float("inf") else min(pf / 3, 1) * 100
    wl = s["wl_ratio"]
    wl_txt = "∞" if wl == float("inf") else f"{wl:.2f}"
    aw, al = s["avg_win"], abs(s["avg_loss"])
    share = aw / (aw + al) * 100 if aw + al else 50
    exp_goal = capital * 0.002
    dd_txt, dd_kind = f"{s['max_dd']:.1f}%", ("neg" if s["max_dd"] < -0.05 else "neu")
    cards = [
        f'<div class="tdc"><div class="h">{L("Net P&L", "صافي الربح")}</div><div class="big">{T.pbox(T.money(net, 2), net)}</div>'
        f'<div><span class="chip2">{s["trades"]} {L("trades", "صفقة")}</span></div>'
        f'<div class="foot2"><div>{L("GROSS", "الإجمالي")}<b>{T.money(s["gross"])}</b></div>'
        f'<div>{L("FEES", "العمولات")}<b class="dnt">-{T.money(s["fees"])}</b></div></div></div>',
        f'<div class="tdc"><div class="h">{L("Trade win %", "نسبة الصفقات الرابحة")}</div>{T.semi(wr)}'
        f'<div class="wl2"><span class="upt">{s["wins"]}W</span><span class="muted">|</span><span class="dnt">{s["losses"]}L</span></div>'
        f'{_goal(wr, GOALS["win"], lambda g: f"{g:.0f}%")}</div>',
        f'<div class="tdc"><div class="h">{L("Profit factor", "معامل الربح")}</div>{T.ring(pf_ring, 96, T.ACCENT, pf_txt, "", stroke=10)}'
        f'{_goal(pf if pf != float("inf") else 99, GOALS["pf"], lambda g: f"{g:.1f}")}</div>',
        f'<div class="tdc"><div class="h">{L("Day win %", "نسبة الأيام الرابحة")}</div>{T.semi(dr)}'
        f'<div class="wl2"><span class="upt">{s["day_wins"]}W</span><span class="muted">|</span><span class="dnt">{s["day_losses"]}L</span></div>'
        f'{_goal(dr, GOALS["day"], lambda g: f"{g:.0f}%")}</div>',
        f'<div class="tdc"><div class="h">{L("Avg win / loss", "متوسط الربح / الخسارة")}</div><div class="big" style="color:#fff">{wl_txt}</div>'
        f'<div class="split"><span style="width:{share:.0f}%;background:{T.UP}"></span><span style="width:{100 - share:.0f}%;background:{T.DOWN}"></span></div>'
        f'<div class="vals"><span class="upt">{T.money(aw)}</span><span class="dnt">-{T.money(al)}</span></div>'
        f'{_goal(wl if wl != float("inf") else 99, GOALS["wl"], lambda g: f"{g:.1f}")}</div>',
        f'<div class="tdc"><div class="h">{L("Max drawdown", "أقصى تراجع")}</div><div class="big">{T.pbox(dd_txt, None, dd_kind)}</div>'
        f'<div class="vals" style="margin-top:12px"><span>{L("Return", "العائد")} {T.pill(s["ret"])}</span></div>'
        f'<div class="vals" style="margin-top:6px"><span class="muted">S&amp;P</span>{T.pill(s["bench_ret"])}</div>'
        f'{_goal(abs(s["max_dd"]), GOALS["dd"], lambda g: f"< {g:.0f}%", higher=False)}</div>',
        f'<div class="tdc"><div class="h">{L("Expectancy", "العائد المتوقع للصفقة")}</div><div class="big">{T.pbox(T.money(s["expectancy"], 2), s["expectancy"])}</div>'
        f'<div class="muted" style="font-size:.72rem;margin-top:8px">{L("average profit per trade", "متوسط الربح لكل صفقة")}</div>'
        f'{_goal(s["expectancy"], exp_goal, lambda g: T.money(g))}</div>',
    ]
    return '<div class="tdk">' + "".join(cards) + "</div>"


def _daily(tr):
    if tr.empty:
        return pd.DataFrame(columns=["pnl", "n", "wins"])
    d = pd.to_datetime(tr["Exit Date"]).dt.normalize()
    g = tr.assign(_d=d, _w=tr["P&L $"] > 0).groupby("_d")
    return pd.DataFrame({"pnl": g["P&L $"].sum(), "n": g.size(), "wins": g["_w"].sum()})


def calendar_html(tr, year, month):
    daily = _daily(tr)
    first = pd.Timestamp(year=year, month=month, day=1)
    last = first + pd.offsets.MonthEnd(0)
    start = first - pd.Timedelta(days=first.weekday())
    cells = [f'<div class="dh">{L(e, a)}</div>' for e, a in DAYS] + [f'<div class="dh wkh">{L("Week", "الأسبوع")}</div>']
    w, day = 1, start
    while day <= last:
        wk_pnl, wk_days = 0.0, 0
        for k in range(5):
            dd = day + pd.Timedelta(days=k)
            if dd.month != month:
                cells.append(f'<div class="d off"><span class="n">{dd.day}</span></div>')
                continue
            if dd in daily.index:
                r = daily.loc[dd]
                wk_pnl += r["pnl"]
                wk_days += 1
                wr = r["wins"] / r["n"] * 100 if r["n"] else 0
                cells.append(f'<div class="d {T.cls(r["pnl"])}"><span class="n">{dd.day}</span><div class="p">{T.money(r["pnl"], short=True)}</div>'
                             f'<div class="s">{int(r["n"])} {L("trade" if r["n"] == 1 else "trades", "صفقة" if r["n"] == 1 else "صفقات")}</div><div class="s">{wr:.0f}% {L("win", "ربح")}</div></div>')
            else:
                cells.append(f'<div class="d"><span class="n">{dd.day}</span></div>')
        wk = T.pbox(T.money(wk_pnl, short=True), wk_pnl) if wk_days else '<span class="muted">$0</span>'
        cells.append(f'<div class="wk"><div class="l">{L("WEEK", "الأسبوع")} {w}</div><div class="p">{wk}</div>'
                     f'<div class="s">{wk_days} {L("days", "أيام")}</div></div>')
        day += pd.Timedelta(days=7)
        w += 1
    return '<div class="cal">' + "".join(cells) + "</div>"


def recent_html(tr, lg, n=8):
    if tr.empty:
        return f'<div class="muted">{L("No closed trades yet.", "لا توجد صفقات مغلقة بعد.")}</div>'
    rows = []
    for _, r in tr.sort_values("Exit Date", ascending=False).head(n).iterrows():
        side = T.badge("CALL", "acc") if r["Type"] == "Call" else T.badge("LONG", "up")
        rows.append(f'<tr><td><a href="{ui.href(r["Symbol"])}" target="_self" style="display:flex;align-items:center;gap:6px">'
                    f'{T.logo_circle(r["Symbol"], lg.get(r["Symbol"]), 22)}{T.esc(r["Symbol"])}</a></td><td>{side}</td>'
                    f'<td class="muted">{pd.Timestamp(r["Exit Date"]):%Y-%m-%d}</td><td>{T.pbox(T.money(r["P&L $"]), r["P&L $"])}</td></tr>')
    return (f'<table class="rtab"><thead><tr><th>{L("Ticker", "الرمز")}</th><th>{L("Side", "النوع")}</th><th>{L("Date", "التاريخ")}</th>'
            f'<th>P&amp;L</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')


def open_html(op, lg):
    if op is None or op.empty:
        return f'<div class="muted">{L("No open positions.", "لا توجد مراكز مفتوحة.")}</div>'
    items = []
    for _, r in op.iterrows():
        what = r["Contract"] if r["Type"] == "Call" else f'{int(r["Qty"])} {L("shares", "سهم")}'
        items.append(f'<div class="o"><div>{T.company(r["Symbol"], "", lg.get(r["Symbol"]), 26, sub=what, href=ui.href(r["Symbol"]))}'
                     f'<div class="m">{L("since", "منذ")} {pd.Timestamp(r["Entry Date"]):%Y-%m-%d} · {T.fmt_price(r["Entry"])} → {T.fmt_price(r["Exit"])}</div></div>'
                     f'<div style="text-align:right">{T.pbox(T.money(r["P&L $"]), r["P&L $"])}<div class="m">{r["P&L %"]:+.1f}%</div></div></div>')
    return '<div class="opos">' + "".join(items) + "</div>"


def render(tr, op, s, capital, key="td"):
    """tr: closed trades, op: open positions (same columns), s: stats dict."""
    syms = list(dict.fromkeys(list(tr["Symbol"]) + (list(op["Symbol"]) if op is not None and len(op) else [])))
    lg = data.logos(syms[:60])
    ui.html(kpi_cards(s, capital))
    daily = _daily(tr)
    c1, c2, c3 = st.columns([1.15, 1.15, 1])
    with c1:
        if len(daily):
            cum = daily["pnl"].cumsum()
            ui.chart(charts.area(cum, L("Cumulative P&L", "الربح التراكمي"), T.CYAN, 320), key=f"{key}_cum")
        else:
            st.caption("—")
    with c2:
        if len(daily):
            ui.chart(charts.signed_bars(daily.index, daily["pnl"].values, L("Daily P&L", "الربح اليومي"), 320), key=f"{key}_daily")
    with c3:
        ui.html(f'<div class="tdp"><div class="tt">{L("Recent trades", "آخر الصفقات")}<span class="muted">{L("full list below", "القائمة الكاملة بالأسفل")}</span></div>'
                f'{recent_html(tr, lg)}</div>')
    c4, c5 = st.columns([2, 1])
    with c4:
        months = sorted({(d.year, d.month) for d in pd.to_datetime(tr["Exit Date"])}, reverse=True) if len(tr) else []
        head = st.columns([2, 1, 1], vertical_alignment="center")
        head[0].markdown(f'<div style="font-weight:800;font-size:1.02rem">{L("Calendar", "التقويم")}</div>', unsafe_allow_html=True)
        if months:
            ui.valid(f"{key}_month", months)
            ym = head[1].selectbox(L("Month", "الشهر"), months, key=f"{key}_month", format_func=lambda x: month_name(*x), label_visibility="collapsed")
            mtd = daily[(daily.index.year == ym[0]) & (daily.index.month == ym[1])]
            head[2].markdown(f'<div style="text-align:right;font-size:.8rem"><span class="muted">{L("Month", "الشهر")}</span> '
                             f'{T.pbox(T.money(mtd["pnl"].sum(), short=True), mtd["pnl"].sum())} <b>{len(mtd)}</b> '
                             f'<span class="muted">{L("days", "أيام")}</span></div>', unsafe_allow_html=True)
            ui.html(calendar_html(tr, *ym))
        else:
            st.caption(L("No trades to show on the calendar.", "لا توجد صفقات لعرضها في التقويم."))
    with c5:
        n_open = 0 if op is None else len(op)
        ui.html(f'<div class="tdp"><div class="tt"><span><span style="color:{T.GOLD}">●</span> {L("Open positions", "المراكز المفتوحة")}</span>'
                f'<span class="muted">{n_open} {L("positions", "مراكز")}</span></div>{open_html(op, lg)}</div>')
