"""
p_markets.py - Market Overview · Heatmap · What's Trending · News
"""
import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import theme as T
import ui
import universe as U
from i18n import L, is_ar, sector_name

ss = st.session_state


def _tile_prices():
    syms = [s for g in U.MARKET_TILES.values() for s in g]
    return data.history_many(tuple(syms + list(U.TAPE)), "1mo")


def _last(px, sym):
    df = px.get(sym)
    if df is None or len(df) < 2:
        return None, None, None
    last, prev = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
    return last, last - prev, (last / prev - 1) * 100


def ticker_tape(px):
    items = []
    for s in U.TAPE:
        p, _, c = _last(px, s)
        if p is not None:
            items.append((U.TAPE_NAMES.get(s, s), p, c))
    if items:
        ui.html(T.tape(items))


def _universe_moves(period="5d"):
    uni = data.history_many(tuple(U.US_UNIVERSE), period)
    rows = []
    for s, df in uni.items():
        if len(df) >= 2:
            rows.append({"Symbol": s, "Chg %": float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100),
                         "Price": float(df["Close"].iloc[-1]), "Volume": float(df["Volume"].iloc[-1]),
                         "Avg Vol": float(df["Volume"].mean())})
    return pd.DataFrame(rows)


# =====================================================================
# MARKET OVERVIEW
# =====================================================================
def page_overview():
    px = _tile_prices()
    ticker_tape(px)
    chips = ""
    for s, name in (("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ"), ("^DJI", "DOW"), ("^TNX", "US10Y"), ("GC=F", "GOLD"), ("BTC-USD", "BTC")):
        p, _, c = _last(px, s)
        if p is not None:
            val = f"{p:.2f}%" if s == "^TNX" else T.fmt_price(p)
            chips += f'<span class="chip"><b>{name}</b>{val} <span class="{T.cls(c)}">{c:+.2f}%</span></span>'
    ui.html(T.hero("A.Alturaifi Pro", L("Invest with <b>clarity</b>", "استثمر <b>بوضوح</b>"),
                   L("Institutional-grade US market intelligence: live markets, research, screeners and an automated trading lab.",
                     "منصة احترافية للسوق الأمريكي: أسواق مباشرة، أبحاث، فلاتر للأسهم، ومختبر تداول آلي."), chips, rtl=is_ar()))
    ui.header("monitoring", "Market Overview", "نظرة عامة على السوق",
              "Live snapshot of US markets, rates, commodities, currencies and the economy.",
              "لمحة مباشرة عن الأسهم والسندات والسلع والعملات والاقتصاد الأمريكي.")

    icons = {"Indices": "show_chart", "Futures": "update", "Treasury Yields": "account_balance", "Commodities": "oil_barrel",
             "Currencies": "currency_exchange", "Crypto": "currency_bitcoin"}
    for (gen, gar), syms in U.MARKET_TILES.items():
        ui.sec(icons.get(gen, "insights"), gen, gar)
        items = []
        for sym, (nen, nar) in syms.items():
            p, chg, pct = _last(px, sym)
            if p is None:
                items.append(T.tile(L(nen, nar), "—"))
                continue
            val = f"{p:.3f}%" if gen == "Treasury Yields" else T.fmt_price(p)
            items.append(T.tile(L(nen, nar), val, chg, pct, px[sym]["Close"].tail(22).values, invert=(sym == "^VIX")))
        ui.html(T.tiles(items))

    economy_section()

    c1, c2 = st.columns([1.15, 1])
    with c1:
        ui.sec("donut_small", "Sector Performance", "أداء القطاعات")
        per = st.segmented_control(L("Period", "الفترة"), ["1D", "1W", "1M"], default="1D", key="ov_per",
                                   label_visibility="collapsed") or "1D"
        n = {"1D": 1, "1W": 5, "1M": 21}[per]
        sec = data.history_many(tuple(U.SECTOR_ETFS), "3mo")
        labels, vals = [], []
        for etf, name in U.SECTOR_ETFS.items():
            df = sec.get(etf)
            if df is not None and len(df) > n:
                labels.append(f"{sector_name(name)} ({etf})")
                vals.append((df["Close"].iloc[-1] / df["Close"].iloc[-1 - n] - 1) * 100)
        if vals:
            st.plotly_chart(charts.hbar(labels, vals, height=430))
    moves = _universe_moves()
    with c2:
        ui.sec("balance", "Market Breadth", "اتساع السوق")
        if not moves.empty:
            adv, dec = int((moves["Chg %"] > 0).sum()), int((moves["Chg %"] < 0).sum())
            m1, m2, m3 = st.columns(3)
            m1.metric(L("Advancers", "الصاعدة"), adv)
            m2.metric(L("Decliners", "النازلة"), dec)
            m3.metric(L("Avg change", "متوسط التغير"), f"{moves['Chg %'].mean():+.2f}%")
            st.plotly_chart(charts.pie([L("Advancing", "صاعدة"), L("Declining", "نازلة")], [adv, dec],
                                       L("Top 175 US stocks", "أكبر 175 سهم أمريكي")))
    ui.sec("grid_view", "Market Heatmap", "الخريطة الحرارية للسوق")
    heat = heatmap_frame("1D")
    if not heat.empty:
        st.plotly_chart(charts.treemap(heat, L("US Market", "السوق الأمريكي"), 560))
        if st.button(L("Open full heatmap", "افتح الخريطة الحرارية كاملة"), icon=":material/open_in_full:"):
            ui.goto("heatmap")
    ui.foot()


def economy_section():
    ui.sec("account_balance", "US Economic Indicators", "المؤشرات الاقتصادية الأمريكية")
    with st.spinner(L("Loading economic data...", "جاري تحميل البيانات الاقتصادية...")):
        mac, errors = data.macro()
    if mac:
        items = []
        for sid, m in mac.items():
            chg = m["value"] - m["prev"]
            unit = m["unit"]
            val = f"{m['value']:,.2f}{unit}" if unit == "%" else f"{m['value']:,.1f}{unit}"
            c = T.cls(chg, bool(m["higher_is_bad"])) if m["higher_is_bad"] is not None else "muted"
            color = {"up": T.UP, "down": T.DOWN}.get(c, T.ACCENT)
            sub = L(f"{m['date']:%b %Y} · prior {m['prev']:,.2f}", f"{m['date']:%Y-%m} · السابق {m['prev']:,.2f}")
            items.append(f'<div class="tile"><div class="t-name">{T.esc(L(m["en"], m["ar"]))}</div><div class="t-row"><div>'
                         f'<div class="t-val">{val}</div><div class="t-chg {c}">{chg:+,.2f} {L("vs prior", "عن السابق")}</div></div>'
                         f'{T.sparkline(m["hist"].values, color)}</div><div class="t-sub">{sub}</div></div>')
        ui.html(T.tiles(items))
        with st.expander(L("Explore an indicator", "استعرض مؤشراً"), icon=":material/query_stats:"):
            names = {L(m["en"], m["ar"]): sid for sid, m in mac.items()}
            pick = st.selectbox(L("Indicator", "المؤشر"), list(names))
            st.plotly_chart(charts.line(mac[names[pick]]["hist"], pick, height=320, fill=False))
    if errors and len(errors) > len(mac):
        st.warning(L("Economic data (FRED) could not be reached right now. It will retry automatically on the next refresh. "
                     "For a permanent fix add a free FRED API key in Streamlit secrets as FRED_API_KEY.",
                     "تعذر الوصول لبيانات FRED الاقتصادية حالياً وستتم إعادة المحاولة تلقائياً عند التحديث. "
                     "للحل الدائم أضف مفتاح FRED المجاني في إعدادات Streamlit باسم FRED_API_KEY."), icon=":material/cloud_off:")
        with st.expander(L("Technical details", "تفاصيل فنية")):
            st.code("\n".join(errors[:6]))

    ui.sec("event", "Economic Calendar (US)", "التقويم الاقتصادي (أمريكا)")
    cal = data.econ_calendar(7, 7)
    if cal.empty:
        st.caption(L("Economic calendar is not available right now.", "التقويم الاقتصادي غير متاح حالياً."))
        return
    cal = cal.copy()
    tcol = next((c for c in cal.columns if "Time" in c or "Date" in c), None)
    if tcol:
        cal[tcol] = pd.to_datetime(cal[tcol], errors="coerce", utc=True)
        now = pd.Timestamp.now(tz="UTC")
        past, upcoming = cal[cal[tcol] < now].sort_values(tcol, ascending=False), cal[cal[tcol] >= now].sort_values(tcol)
        for frame in (past, upcoming):
            frame[tcol] = frame[tcol].dt.tz_convert("America/New_York").dt.strftime("%a %b %d · %H:%M ET")
    else:
        past, upcoming = cal, cal.iloc[0:0]
    ar_cols = {"Event": "الحدث", "Region": "المنطقة", "Event Time": "الوقت", "For": "الفترة", "Actual": "الفعلي",
               "Expected": "المتوقع", "Last": "السابق", "Revised": "المعدّل"}

    def show(df):
        df = df.rename(columns=ar_cols) if is_ar() else df
        st.dataframe(df, hide_index=True, height=min(420, 38 + 35 * len(df)))
    t1, t2 = st.tabs([L("Recent releases", "صدرت مؤخراً"), L("Upcoming", "القادمة")])
    with t1:
        show(past) if not past.empty else st.caption("—")
    with t2:
        show(upcoming) if not upcoming.empty else st.caption("—")


# =====================================================================
# HEATMAP
# =====================================================================
PERIODS = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": "ytd"}


def heatmap_frame(period="1D", sizing="cap"):
    hist = data.history_many(tuple(U.US_UNIVERSE), "1y")
    caps, _ = data.market_caps()
    n = PERIODS[period]
    rows = []
    for s, df in hist.items():
        c = df["Close"]
        if n == "ytd":
            ytd = c[c.index.year == c.index[-1].year]
            if len(ytd) < 2:
                continue
            chg = (c.iloc[-1] / ytd.iloc[0] - 1) * 100
        elif len(c) > n:
            chg = (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100
        else:
            continue
        name, sec, ind, _ = U.STOCKS[s]
        rows.append({"Symbol": s, "Name": name, "Sector": sec, "SectorLabel": sector_name(sec), "Industry": ind,
                     "Chg %": float(chg), "Price": float(c.iloc[-1]), "Cap": float(caps.get(s, 1e9)) if sizing == "cap" else 1.0})
    return pd.DataFrame(rows)


def page_heatmap():
    ui.header("grid_view", "Market Heatmap", "الخريطة الحرارية",
              "Click a sector to see its industries, click an industry to see its companies. Use the bar on top to go back.",
              "اضغط على القطاع لتظهر الصناعات، ثم على الصناعة لتظهر الشركات. استخدم الشريط العلوي للرجوع.")
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    period = c1.segmented_control(L("Performance", "الأداء"), list(PERIODS), default="1D", key="hm_per") or "1D"
    sizing = c2.segmented_control(L("Size by", "الحجم حسب"), [L("Market cap", "القيمة السوقية"), L("Equal", "متساوٍ")],
                                  default=L("Market cap", "القيمة السوقية"), key="hm_size")
    sectors = [L("All sectors", "كل القطاعات")] + U.SECTORS
    pick = c3.selectbox(L("Sector", "القطاع"), sectors, format_func=lambda s: s if s == sectors[0] else sector_name(s))
    with st.spinner(L("Building heatmap...", "جاري بناء الخريطة...")):
        df = heatmap_frame(period, "equal" if sizing == L("Equal", "متساوٍ") else "cap")
    if df.empty:
        st.warning(L("Market data is temporarily unavailable.", "بيانات السوق غير متاحة مؤقتاً."))
        return
    view = df if pick == sectors[0] else df[df["Sector"] == pick]
    root = L("US Market", "السوق الأمريكي") if pick == sectors[0] else sector_name(pick)
    st.plotly_chart(charts.treemap(view, root, 720))
    _, live = data.market_caps()
    st.caption(L("Size = market cap (live)" if live else "Size = market cap (estimated)", "الحجم = القيمة السوقية") +
               " · " + L("Color = % change", "اللون = نسبة التغير"))

    ui.sec("account_tree", "Sector → Industry → Company explorer", "مستكشف القطاع ← الصناعة ← الشركة")
    a, b = st.columns(2)
    sec_sel = a.selectbox(L("Sector ", "القطاع "), sorted(view["Sector"].unique()), format_func=sector_name)
    sdf = view[view["Sector"] == sec_sel]
    w = sdf.assign(_w=sdf["Chg %"] * sdf["Cap"]).groupby("Industry")[["_w", "Cap"]].sum()
    ind_perf = w["_w"] / w["Cap"]
    ind_sel = b.selectbox(L("Industry", "الصناعة"), [L("All industries", "كل الصناعات")] + list(ind_perf.sort_values(ascending=False).index))
    left, right = st.columns([1, 1.2])
    with left:
        st.plotly_chart(charts.hbar(list(ind_perf.index), list(ind_perf.values),
                                    L(f"{sector_name(sec_sel)}: industries", f"{sector_name(sec_sel)}: الصناعات"),
                                    height=max(280, 34 * len(ind_perf) + 80)))
    with right:
        comp = sdf if ind_sel == L("All industries", "كل الصناعات") else sdf[sdf["Industry"] == ind_sel]
        comp = comp.sort_values("Cap", ascending=False)
        show = comp[["Symbol", "Name", "Industry", "Price", "Chg %", "Cap"]].copy()
        show["Cap"] = show["Cap"].map(T.fmt_big)
        cols = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Industry": L("Industry", "الصناعة"),
                "Price": L("Price", "السعر"), "Chg %": L("Change %", "التغير %"), "Cap": L("Market cap", "القيمة السوقية")}
        show = show.rename(columns=cols)
        st.dataframe(show.style.map(T.color_style, subset=[cols["Chg %"]]).format(
            {cols["Price"]: "{:,.2f}", cols["Chg %"]: "{:+.2f}%"}), hide_index=True, height=360)
        x, y = st.columns([2, 1])
        s = x.selectbox(L("Open company", "افتح شركة"), comp["Symbol"].tolist(), label_visibility="collapsed")
        if y.button(L("Open", "افتح"), icon=":material/open_in_new:", key="hm_open"):
            ui.open_stock(s)
    ui.foot()


# =====================================================================
# WHAT'S TRENDING (dashboard)
# =====================================================================
LISTS = {"day_gainers": ("Top Gainers", "الأكثر ارتفاعاً", "trending_up"),
         "day_losers": ("Top Losers", "الأكثر انخفاضاً", "trending_down"),
         "most_actives": ("Most Active", "الأكثر تداولاً", "bolt"),
         "most_shorted_stocks": ("Most Shorted", "الأكثر بيعاً على المكشوف", "south_east"),
         "small_cap_gainers": ("Small-Cap Gainers", "شركات صغيرة صاعدة", "rocket_launch")}


def _list(kind, moves):
    df = data.screen(kind, 25)
    if not df.empty:
        return df, False
    if moves.empty:
        return pd.DataFrame(), True
    t = moves.copy()
    t["Name"] = t["Symbol"].map(U.name_of)
    t["Mkt Cap"] = t["Symbol"].map(lambda s: U.STOCKS[s][3] * 1e9)
    if kind == "day_losers":
        t = t.sort_values("Chg %")
    elif kind in ("most_actives", "most_shorted_stocks"):
        t = t.sort_values("Volume", ascending=False)
    else:
        t = t.sort_values("Chg %", ascending=False)
    return t.head(25), True


def summary_points(px, moves, lists):
    pts = []
    sp = _last(px, "^GSPC")[2]
    nq = _last(px, "^IXIC")[2]
    if sp is not None:
        mood = ("higher", "على ارتفاع") if sp > 0 else ("lower", "على انخفاض")
        pts.append((f"S&P 500 is trading {mood[0]} ({sp:+.2f}%), Nasdaq {nq:+.2f}%.",
                    f"مؤشر إس آند بي 500 يتداول {mood[1]} ({sp:+.2f}%) وناسداك ({nq:+.2f}%)."))
    if not moves.empty:
        adv = (moves["Chg %"] > 0).mean() * 100
        pts.append((f"Breadth: {adv:.0f}% of the top 175 US stocks are up today.",
                    f"اتساع السوق: {adv:.0f}% من أكبر 175 سهم أمريكي صاعدة اليوم."))
    sec = data.history_many(tuple(U.SECTOR_ETFS), "5d")
    perf = {U.SECTOR_ETFS[e]: (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100 for e, df in sec.items() if len(df) > 1}
    if perf:
        best, worst = max(perf, key=perf.get), min(perf, key=perf.get)
        pts.append((f"Leading sector: {best} ({perf[best]:+.2f}%). Lagging: {worst} ({perf[worst]:+.2f}%).",
                    f"القطاع الأقوى: {sector_name(best)} ({perf[best]:+.2f}%)، والأضعف: {sector_name(worst)} ({perf[worst]:+.2f}%)."))
    v = _last(px, "^VIX")
    if v[0] is not None:
        fear = ("rising fear", "ارتفاع القلق") if v[2] > 0 else ("easing fear", "تراجع القلق")
        pts.append((f"VIX at {v[0]:.2f} ({v[2]:+.2f}%): {fear[0]}.", f"مؤشر الخوف VIX عند {v[0]:.2f} ({v[2]:+.2f}%): {fear[1]}."))
    y = _last(px, "^TNX")
    if y[0] is not None:
        pts.append((f"10-year Treasury yield {y[0]:.2f}% ({y[1] * 100:+.0f} bps).", f"عائد السندات لأجل 10 سنوات {y[0]:.2f}% ({y[1] * 100:+.0f} نقطة أساس)."))
    oil, gold, btc = _last(px, "CL=F"), _last(px, "GC=F"), _last(px, "BTC-USD")
    if oil[0] is not None and gold[0] is not None:
        pts.append((f"Oil {oil[2]:+.2f}% · Gold {gold[2]:+.2f}% · Bitcoin {btc[2] if btc[2] is not None else 0:+.2f}%.",
                    f"النفط {oil[2]:+.2f}% · الذهب {gold[2]:+.2f}% · بيتكوين {btc[2] if btc[2] is not None else 0:+.2f}%."))
    g, lo, sh = lists["day_gainers"][0], lists["day_losers"][0], lists["most_shorted_stocks"][0]
    if not g.empty and not lo.empty:
        pts.append((f"Biggest gainer: {g.iloc[0]['Symbol']} ({g.iloc[0]['Chg %']:+.1f}%). Biggest loser: {lo.iloc[0]['Symbol']} ({lo.iloc[0]['Chg %']:+.1f}%).",
                    f"الأكثر ارتفاعاً: {g.iloc[0]['Symbol']} ({g.iloc[0]['Chg %']:+.1f}%)، والأكثر انخفاضاً: {lo.iloc[0]['Symbol']} ({lo.iloc[0]['Chg %']:+.1f}%)."))
    if not sh.empty:
        names = ", ".join(sh["Symbol"].head(3))
        pts.append((f"Heavily shorted names in focus: {names}.", f"أسهم عليها بيع على المكشوف مرتفع: {names}."))
    return pts


def page_trending():
    ui.header("local_fire_department", "What's Trending", "الأكثر رواجاً",
              "Today's market dashboard: top stories, movers, short interest and a full summary.",
              "لوحة السوق اليوم: أهم الأخبار، الأسهم الأكثر حركة، البيع على المكشوف، وملخص شامل.")
    px = _tile_prices()
    moves = _universe_moves()
    lists = {k: _list(k, moves) for k in LISTS}

    # ---- top 3 stories with affected companies
    ui.sec("newspaper", "Top 3 trending stories", "أهم 3 أخبار رائجة")
    stories = data.trending_stories(3)
    if stories:
        titles = [n["title"] for n in stories]
        if is_ar():
            titles = data.translate(titles)
        tickers = sorted({s for n in stories for s in n["tickers"]})
        chg = data.changes(tickers) if tickers else {}
        cols = st.columns(len(stories))
        for i, (col, n, t) in enumerate(zip(cols, stories, titles)):
            chips = ui.affected_chips(n["tickers"], chg) or f'<span class="muted">{L("Broad market", "السوق بشكل عام")}</span>'
            rtl = ' rtl' if is_ar() else ''
            col.markdown(f'<div class="story{rtl}"><div class="rank">0{i + 1}</div><a href="{T.esc(n["link"])}" target="_blank">{T.esc(t)}</a>'
                         f'<div class="meta muted" style="font-size:.78rem;margin-top:6px">{T.esc(n["source"])} · {T.time_ago(n["time"], is_ar())}</div>'
                         f'<div class="aff" style="margin-top:12px;display:flex;flex-wrap:wrap;gap:6px">'
                         f'<span class="muted" style="font-size:.74rem;width:100%">{L("Affected companies", "الشركات المتأثرة")}</span>{chips}</div></div>',
                         unsafe_allow_html=True)
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))

    # ---- KPIs
    ui.sec("dashboard", "Dashboard", "لوحة المؤشرات")
    k = st.columns(5)

    def first(kind, key="Chg %"):
        df = lists[kind][0]
        return None if df.empty else df.iloc[0]
    g, lo, act, sh = first("day_gainers"), first("day_losers"), first("most_actives"), first("most_shorted_stocks")
    if g is not None:
        k[0].markdown(T.kpi("trending_up", L("Top gainer", "الأعلى ارتفاعاً"), g["Symbol"], f"{g['Chg %']:+.2f}%", "up"), unsafe_allow_html=True)
    if lo is not None:
        k[1].markdown(T.kpi("trending_down", L("Top loser", "الأكثر انخفاضاً"), lo["Symbol"], f"{lo['Chg %']:+.2f}%", "down"), unsafe_allow_html=True)
    if act is not None:
        k[2].markdown(T.kpi("bolt", L("Most active", "الأكثر تداولاً"), act["Symbol"], f"{T.fmt_big(act['Volume'])} {L('shares', 'سهم')}"), unsafe_allow_html=True)
    if sh is not None:
        k[3].markdown(T.kpi("south_east", L("Most shorted", "الأكثر بيعاً على المكشوف"), sh["Symbol"],
                            f"{sh['Chg %']:+.2f}%" if pd.notna(sh["Chg %"]) else "", T.cls(sh["Chg %"])), unsafe_allow_html=True)
    if not moves.empty:
        adv = int((moves["Chg %"] > 0).sum())
        k[4].markdown(T.kpi("balance", L("Breadth (top 175)", "اتساع السوق"), f"{adv}/{len(moves)}",
                            L("advancing", "صاعدة"), "up" if adv > len(moves) / 2 else "down"), unsafe_allow_html=True)

    # ---- summary
    ui.sec("summarize", "Market summary", "ملخص السوق")
    pts = summary_points(px, moves, lists)
    ui.html(f'<div class="card {"rtl" if is_ar() else ""}"><ul class="summary">' +
            "".join(f"<li>{T.esc(L(e, a))}</li>" for e, a in pts) + "</ul></div>")

    # ---- mini tables grid
    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    keys = list(LISTS)
    for row in (keys[:3], keys[3:]):
        cols = st.columns(3)
        for col, kind in zip(cols, row):
            df, _ = lists[kind]
            en, ar, ic = LISTS[kind]
            rows = []
            for _, r in df.head(6).iterrows():
                pct = r["Chg %"]
                rows.append((f'<b>{T.esc(r["Symbol"])}</b> <span class="muted">{T.esc(str(r["Name"])[:22])}</span>',
                             f'{T.fmt_price(r["Price"])} <span class="{T.cls(pct)}">{pct:+.2f}%</span>' if pd.notna(pct) else "—"))
            col.markdown(f'<div class="card"><div class="sec" style="margin-top:0">{T.icon(ic)}<span>{T.esc(L(en, ar))}</span></div>'
                         f'{T.mini_table(rows)}</div>', unsafe_allow_html=True)

    # ---- full lists
    ui.sec("table_rows", "Full lists", "القوائم الكاملة")
    tabs = st.tabs([L(v[0], v[1]) for v in LISTS.values()])
    for tab, kind in zip(tabs, LISTS):
        with tab:
            df, fallback = lists[kind]
            if df.empty:
                st.info(L("Data unavailable right now.", "البيانات غير متاحة حالياً."))
                continue
            df = df.copy()
            df["Rel Vol"] = df["Volume"] / df["Avg Vol"]
            top = df.head(15)
            st.plotly_chart(charts.hbar(list(top["Symbol"]), list(top["Chg %"].fillna(0)), height=440))
            show = df[["Symbol", "Name", "Price", "Chg %", "Volume", "Rel Vol", "Mkt Cap"]].copy()
            show["Volume"] = show["Volume"].map(T.fmt_big)
            show["Mkt Cap"] = show["Mkt Cap"].map(T.fmt_big)
            names = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Price": L("Price", "السعر"),
                     "Chg %": L("Change %", "التغير %"), "Volume": L("Volume", "الحجم"), "Rel Vol": L("Rel. volume", "الحجم النسبي"),
                     "Mkt Cap": L("Market cap", "القيمة السوقية")}
            show = show.rename(columns=names)
            st.dataframe(show.style.map(T.color_style, subset=[names["Chg %"]]).format(
                {names["Price"]: "{:,.2f}", names["Chg %"]: "{:+.2f}%", names["Rel Vol"]: "{:.1f}×"}, na_rep="—"),
                hide_index=True, height=420)
            if fallback:
                st.caption(L("Computed from the top 175 US stocks (screener source unavailable).",
                             "محسوبة من أكبر 175 سهم أمريكي (مصدر القوائم غير متاح حالياً)."))
            a, b = st.columns([3, 1])
            pick = a.selectbox(L("Open a stock", "افتح سهماً"), df["Symbol"].tolist(), key=f"tr_{kind}")
            if b.button(L("Open", "افتح"), icon=":material/open_in_new:", key=f"trb_{kind}"):
                ui.open_stock(pick)
    ui.foot()


# =====================================================================
# NEWS
# =====================================================================
def page_news():
    ui.header("newspaper", "Market News", "أخبار السوق",
              "Latest US market headlines with the companies affected by each story.",
              "آخر أخبار السوق الأمريكي مع الشركات المتأثرة بكل خبر.")
    c1, c2, c3 = st.columns([2, 1, 1])
    sym = c1.text_input(L("Symbol (leave empty for market news)", "رمز سهم (اتركه فارغاً لأخبار السوق)"), "").strip().upper()
    count = c2.selectbox(L("Headlines", "عدد الأخبار"), [10, 20, 30], index=1)
    translate = c3.toggle(L("Translate to Arabic", "ترجمة للعربية"), value=is_ar())
    items = data.news(sym, 30) if sym else data.market_news()
    ui.news_list(items, count, translate=translate)
    ui.foot()
