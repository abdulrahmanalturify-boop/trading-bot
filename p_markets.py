"""
p_markets.py - Overview · Heatmap · Economy · What's Trending · News
"""
import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import theme as T
import ui
import universe as U
from i18n import L, industry_name, is_ar, sector_name

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
    items = [(U.TAPE_NAMES.get(s, s), *_last(px, s)[::2]) for s in U.TAPE if _last(px, s)[0] is not None]
    if items:
        ui.html(T.tape(items))


def _universe_moves(period="5d"):
    uni = data.history_many(tuple(U.US_UNIVERSE), period)
    rows = []
    for s, df in uni.items():
        if len(df) >= 2:
            rows.append({"Symbol": s, "Name": U.name_of(s), "Chg %": float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100),
                         "Price": float(df["Close"].iloc[-1]), "Volume": float(df["Volume"].iloc[-1]), "Avg Vol": float(df["Volume"].mean()),
                         "Mkt Cap": U.STOCKS[s][3] * 1e9})
    return pd.DataFrame(rows)


# =====================================================================
# OVERVIEW
# =====================================================================
def page_overview():
    px = _tile_prices()
    ticker_tape(px)
    chips = ""
    for s, name in (("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ"), ("^DJI", "DOW"), ("^TNX", "US10Y"), ("GC=F", "GOLD"), ("BTC-USD", "BTC")):
        p, _, c = _last(px, s)
        if p is not None:
            chips += f'<span class="chip"><b>{name}</b>{f"{p:.2f}%" if s == "^TNX" else T.fmt_price(p)} <span class="{T.cls(c)}">{c:+.2f}%</span></span>'
    ui.html(T.hero("A.Alturaifi Pro", L("Invest with <b>clarity</b>", "استثمر <b>بوضوح</b>"),
                   L("US market intelligence in one place: live markets, research, screeners, an academy and an automated trading lab.",
                     "كل ما تحتاجه عن السوق الأمريكي في مكان واحد: أسواق مباشرة، أبحاث، فلاتر، أكاديمية، ومختبر تداول آلي."), chips, rtl=is_ar()))
    ui.header("monitoring", "Market Overview", "نظرة عامة على السوق",
              "Live snapshot of US stocks, futures, rates, commodities, currencies and crypto.",
              "لمحة مباشرة عن الأسهم والعقود والسندات والسلع والعملات والعملات الرقمية.")
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

    c1, c2 = st.columns([1.15, 1])
    with c1:
        ui.sec("donut_small", "Sector Performance", "أداء القطاعات")
        per = st.segmented_control(L("Period", "الفترة"), ["1D", "1W", "1M"], default="1D", key="ov_per", label_visibility="collapsed") or "1D"
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
            st.plotly_chart(charts.pie([L("Advancing", "صاعدة"), L("Declining", "نازلة")], [adv, dec], L("Top 175 US stocks", "أكبر 175 سهم أمريكي")))
    a, b = st.columns(2)
    if a.button(L("Open market heatmap", "افتح الخريطة الحرارية"), icon=":material/grid_view:", width="stretch"):
        ui.goto("heatmap")
    if b.button(L("Open economy dashboard", "افتح لوحة الاقتصاد"), icon=":material/account_balance:", width="stretch"):
        ui.goto("economy")
    ui.foot()


# =====================================================================
# ECONOMY
# =====================================================================
BAD_UP = ("cpi", "ppi", "inflation", "unemployment", "jobless", "claims", "pce")


def page_economy():
    ui.header("account_balance", "US Economy", "الاقتصاد الأمريكي",
              "Latest releases (actual vs expected), key indicators and the economic calendar.",
              "آخر البيانات الصادرة (الفعلي مقابل المتوقع)، أهم المؤشرات، والتقويم الاقتصادي.")
    # ---- latest releases from the Yahoo economic calendar
    ui.sec("campaign", "Latest US releases", "آخر البيانات الأمريكية الصادرة")
    rel = data.econ_releases(45)
    if not rel.empty:
        items = []
        exp = next((c for c in rel.columns if c.lower() == "expected"), None)
        last = next((c for c in rel.columns if c.lower() == "last"), None)
        tcol = next((c for c in rel.columns if "Time" in c or "Date" in c), None)
        for _, r in rel.head(16).iterrows():
            a = pd.to_numeric(r.get("Actual"), errors="coerce")
            e = pd.to_numeric(r.get(exp), errors="coerce") if exp else np.nan
            pr = pd.to_numeric(r.get(last), errors="coerce") if last else np.nan
            surprise = a - e if pd.notna(e) else None
            bad = any(k in str(r["Event"]).lower() for k in BAD_UP)
            when = f"{r[tcol]:%b %d}" if tcol and pd.notna(r[tcol]) else ""
            sub = L(f"Exp {e:g} · Prev {pr:g} · {when}" if pd.notna(e) else f"Prev {pr:g} · {when}",
                    f"المتوقع {e:g} · السابق {pr:g} · {when}" if pd.notna(e) else f"السابق {pr:g} · {when}")
            items.append(T.tile(str(r["Event"]), f"{a:g}", surprise, None, None, sub, invert=bad))
        ui.html(T.tiles(items))
        st.caption(L("Colored by surprise vs expectations (for inflation and jobless data, above expectations is shown in red).",
                     "اللون حسب المفاجأة مقارنة بالتوقعات (للتضخم والبطالة: الأعلى من المتوقع يظهر بالأحمر)."))
    else:
        st.caption(L("Release data is not available right now.", "بيانات الإصدارات غير متاحة حالياً."))

    # ---- indicator tiles (FRED / BLS)
    ui.sec("query_stats", "Key indicators", "أهم المؤشرات")
    with st.spinner(L("Loading economic data...", "جاري تحميل البيانات الاقتصادية...")):
        mac, errors, status = data.macro()
    if mac:
        items = []
        for sid, m in mac.items():
            chg = m["value"] - m["prev"]
            unit = m["unit"]
            val = f"{m['value']:,.2f}{unit}" if unit == "%" else f"{m['value']:,.1f}{unit}"
            c = T.cls(chg, bool(m["higher_is_bad"])) if m["higher_is_bad"] is not None else "muted"
            color = {"up": T.UP, "down": T.DOWN}.get(c, T.ACCENT)
            sub = L(f"{m['date']:%b %Y} · prior {m['prev']:,.2f} · {m['source']}", f"{m['date']:%Y-%m} · السابق {m['prev']:,.2f} · {m['source']}")
            items.append(f'<div class="tile"><div class="t-name">{T.esc(L(m["en"], m["ar"]))}</div><div class="t-row"><div>'
                         f'<div class="t-val">{val}</div><div class="t-chg {c}">{chg:+,.2f} {L("vs prior", "عن السابق")}</div></div>'
                         f'{T.sparkline(m["hist"].values, color)}</div><div class="t-sub">{sub}</div></div>')
        ui.html(T.tiles(items))
        names = {L(m["en"], m["ar"]): sid for sid, m in mac.items()}
        pick = st.selectbox(L("Explore an indicator", "استعرض مؤشراً"), list(names))
        st.plotly_chart(charts.line(mac[names[pick]]["hist"], pick, height=320, fill=False))
    else:
        st.warning(L("Indicator sources (FRED and BLS) could not be reached from the server right now. Releases above come from Yahoo. "
                     "For a permanent fix add a free FRED API key in Streamlit secrets as FRED_API_KEY.",
                     "تعذر الوصول لمصادر المؤشرات (FRED وBLS) من الخادم حالياً، والبيانات أعلاه من ياهو. "
                     "للحل الدائم أضف مفتاح FRED المجاني في إعدادات Streamlit باسم FRED_API_KEY."), icon=":material/cloud_off:")
    with st.expander(L("Data source status", "حالة مصادر البيانات"), icon=":material/lan:"):
        st.write({**status, "Yahoo calendar": "ok" if not rel.empty else "no data"})
        if errors:
            st.code("\n".join(errors[:8]))

    # ---- calendar
    ui.sec("event", "Economic calendar (US)", "التقويم الاقتصادي (أمريكا)")
    cal = data.econ_calendar(7, 7)
    if cal.empty:
        st.caption(L("Economic calendar is not available right now.", "التقويم الاقتصادي غير متاح حالياً."))
    else:
        cal = cal.copy()
        tcol = next((c for c in cal.columns if "Time" in c or "Date" in c), None)
        if tcol:
            cal[tcol] = pd.to_datetime(cal[tcol], errors="coerce", utc=True)
            now = pd.Timestamp.now(tz="UTC")
            past, upcoming = cal[cal[tcol] < now].sort_values(tcol, ascending=False), cal[cal[tcol] >= now].sort_values(tcol)
            for fr in (past, upcoming):
                fr[tcol] = fr[tcol].dt.tz_convert("America/New_York").dt.strftime("%a %b %d · %H:%M ET")
        else:
            past, upcoming = cal, cal.iloc[0:0]
        ar_cols = {"Event": "الحدث", "Region": "المنطقة", "Event Time": "الوقت", "For": "الفترة", "Actual": "الفعلي",
                   "Expected": "المتوقع", "Last": "السابق", "Revised": "المعدّل"}
        t1, t2 = st.tabs([L("Recent releases", "صدرت مؤخراً"), L("Upcoming", "القادمة")])
        for tab, df in ((t1, past), (t2, upcoming)):
            with tab:
                if df.empty:
                    st.caption("—")
                else:
                    st.dataframe(df.rename(columns=ar_cols) if is_ar() else df, hide_index=True, height=min(460, 38 + 35 * len(df)))
    ui.foot()


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
        rows.append({"Symbol": s, "Name": name, "Sector": sec, "SectorLabel": sector_name(sec), "Industry": industry_name(ind),
                     "Chg %": float(chg), "Price": float(c.iloc[-1]), "Cap": float(caps.get(s, 1e9)) if sizing == "cap" else 1.0})
    return pd.DataFrame(rows)


def page_heatmap():
    ui.header("grid_view", "Market Heatmap", "الخريطة الحرارية",
              "Click a sector to see its industries, click an industry to see its companies. Use the bar on top to go back.",
              "اضغط على القطاع لتظهر الصناعات، ثم على الصناعة لتظهر الشركات. استخدم الشريط العلوي للرجوع.")
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    period = c1.segmented_control(L("Performance", "الأداء"), list(PERIODS), default="1D", key="hm_per") or "1D"
    sizing = c2.segmented_control(L("Size by", "الحجم حسب"), ["cap", "equal"], default="cap", key="hm_size",
                                  format_func=lambda k: L("Market cap", "القيمة السوقية") if k == "cap" else L("Equal", "متساوٍ")) or "cap"
    sectors = ["all"] + U.SECTORS
    pick = c3.selectbox(L("Sector", "القطاع"), sectors, format_func=lambda s: L("All sectors", "كل القطاعات") if s == "all" else sector_name(s))
    with st.spinner(L("Building heatmap...", "جاري بناء الخريطة...")):
        df = heatmap_frame(period, sizing)
    if df.empty:
        st.warning(L("Market data is temporarily unavailable.", "بيانات السوق غير متاحة مؤقتاً."))
        return
    view = df if pick == "all" else df[df["Sector"] == pick]
    root = L("US Market", "السوق الأمريكي") if pick == "all" else sector_name(pick)
    st.plotly_chart(charts.treemap(view, root, 720))
    _, live = data.market_caps()
    st.caption(L("Size = market cap (live)" if live else "Size = market cap (estimated)", "الحجم = القيمة السوقية") + " · " + L("Color = % change", "اللون = نسبة التغير"))

    ui.sec("account_tree", "Sector → Industry → Company", "القطاع ← الصناعة ← الشركة")
    a, b = st.columns(2)
    sec_sel = a.selectbox(L("Sector ", "القطاع "), sorted(view["Sector"].unique()), format_func=sector_name)
    sdf = view[view["Sector"] == sec_sel]
    w = sdf.assign(_w=sdf["Chg %"] * sdf["Cap"]).groupby("Industry")[["_w", "Cap"]].sum()
    ind_perf = (w["_w"] / w["Cap"]).sort_values(ascending=False)
    ind_sel = b.selectbox(L("Industry", "الصناعة"), ["all"] + list(ind_perf.index), format_func=lambda i: L("All industries", "كل الصناعات") if i == "all" else i)
    left, right = st.columns([1, 1.2])
    with left:
        st.plotly_chart(charts.hbar(list(ind_perf.index), list(ind_perf.values), L(f"{sector_name(sec_sel)}: industries", f"{sector_name(sec_sel)}: الصناعات"),
                                    height=max(280, 34 * len(ind_perf) + 80)))
    with right:
        comp = (sdf if ind_sel == "all" else sdf[sdf["Industry"] == ind_sel]).sort_values("Cap", ascending=False)
        lg = data.logos(comp["Symbol"].head(20).tolist())
        ui.html(f'<div class="card">{ui.row_list(comp.head(20), lg)}</div>')
        x, y = st.columns([2, 1])
        s = x.selectbox(L("Open company", "افتح شركة"), comp["Symbol"].tolist(), label_visibility="collapsed")
        if y.button(L("Open", "افتح"), icon=":material/open_in_new:", key="hm_open"):
            ui.open_stock(s)
    ui.foot()


# =====================================================================
# WHAT'S TRENDING
# =====================================================================
LISTS = {"day_gainers": ("Top Gainers", "الأكثر ارتفاعاً", "trending_up"), "day_losers": ("Top Losers", "الأكثر انخفاضاً", "trending_down"),
         "most_actives": ("Most Active", "الأكثر تداولاً", "bolt"), "most_shorted_stocks": ("Most Shorted", "الأكثر بيعاً على المكشوف", "south_east"),
         "small_cap_gainers": ("Small-Cap Gainers", "شركات صغيرة صاعدة", "rocket_launch"),
         "aggressive_small_caps": ("Aggressive Small Caps", "شركات صغيرة سريعة النمو", "speed")}


def _list(kind, moves):
    df = data.screen(kind, 25)
    if not df.empty:
        df = df.copy()
    elif moves.empty:
        return pd.DataFrame(), True
    else:
        t = moves.copy()
        if kind == "day_losers":
            t = t.sort_values("Chg %")
        elif kind in ("most_actives", "most_shorted_stocks"):
            t = t.sort_values("Volume", ascending=False)
        else:
            t = t.sort_values("Chg %", ascending=False)
        df = t.head(25).copy()
        df["_fallback"] = True
    df["Rel Vol"] = df["Volume"] / df["Avg Vol"]
    return df, "_fallback" in df


def summary_points(px, moves, lists):
    pts = []
    sp, nq = _last(px, "^GSPC")[2], _last(px, "^IXIC")[2]
    if sp is not None:
        mood = ("higher", "على ارتفاع") if sp > 0 else ("lower", "على انخفاض")
        pts.append((f"S&P 500 is trading {mood[0]} ({sp:+.2f}%), Nasdaq {nq:+.2f}%.", f"مؤشر إس آند بي 500 يتداول {mood[1]} ({sp:+.2f}%) وناسداك ({nq:+.2f}%)."))
    if not moves.empty:
        adv = (moves["Chg %"] > 0).mean() * 100
        pts.append((f"Breadth: {adv:.0f}% of the top 175 US stocks are up today.", f"اتساع السوق: {adv:.0f}% من أكبر 175 سهم أمريكي صاعدة اليوم."))
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
        b = btc[2] if btc[2] is not None else 0
        pts.append((f"Oil {oil[2]:+.2f}% · Gold {gold[2]:+.2f}% · Bitcoin {b:+.2f}%.", f"النفط {oil[2]:+.2f}% · الذهب {gold[2]:+.2f}% · بيتكوين {b:+.2f}%."))
    g, lo, sh = lists["day_gainers"][0], lists["day_losers"][0], lists["most_shorted_stocks"][0]
    if not g.empty and not lo.empty:
        pts.append((f"Biggest gainer: {g.iloc[0]['Symbol']} ({g.iloc[0]['Chg %']:+.1f}%). Biggest loser: {lo.iloc[0]['Symbol']} ({lo.iloc[0]['Chg %']:+.1f}%).",
                    f"الأكثر ارتفاعاً: {g.iloc[0]['Symbol']} ({g.iloc[0]['Chg %']:+.1f}%)، والأكثر انخفاضاً: {lo.iloc[0]['Symbol']} ({lo.iloc[0]['Chg %']:+.1f}%)."))
    if not sh.empty:
        names = ", ".join(sh["Symbol"].head(3))
        pts.append((f"Heavily shorted names in focus: {names}.", f"أسهم عليها بيع على المكشوف مرتفع: {names}."))
    return pts


def _leaderboard(df, lg, n=12):
    cards = []
    for i, (_, r) in enumerate(df.head(n).iterrows(), 1):
        rv = r.get("Rel Vol")
        meter = ""
        if pd.notna(rv):
            meter = (f'<div class="muted" style="font-size:.7rem;margin-top:6px">{L("Rel. volume", "الحجم النسبي")} {rv:.1f}×</div>'
                     f'<div class="meter"><span style="width:{min(100, rv / 5 * 100):.0f}%"></span></div>')
        cap = T.fmt_big(r.get("Mkt Cap"))
        cards.append(f'<div class="lc"><div class="top">{T.company(r["Symbol"], str(r.get("Name") or "")[:26], lg.get(r["Symbol"]), 36)}'
                     f'<span class="rank">#{i}</span></div><div class="bot"><div><div class="px" style="font-size:1.15rem;text-align:left">'
                     f'{T.fmt_price(r["Price"])}</div><div class="muted" style="font-size:.72rem">{L("Mkt cap", "القيمة")} {cap}</div></div>'
                     f'{T.pill(r["Chg %"])}</div>{meter}</div>')
    return '<div class="lead">' + "".join(cards) + "</div>"


def page_trending():
    ui.header("local_fire_department", "What's Trending", "الأكثر رواجاً",
              "Today's market dashboard: top stories, movers, short interest and a full summary.",
              "لوحة السوق اليوم: أهم الأخبار، الأسهم الأكثر حركة، البيع على المكشوف، وملخص شامل.")
    px = _tile_prices()
    moves = _universe_moves()
    lists = {k: _list(k, moves) for k in LISTS}
    all_syms = [s for df, _ in lists.values() if not df.empty for s in df["Symbol"].head(12)]

    # ---- top stories
    ui.sec("newspaper", "Top 3 trending stories", "أهم 3 أخبار رائجة")
    stories = data.trending_stories(3)
    tick = sorted({s for n in stories for s in n["tickers"]})
    lg = data.logos(list(dict.fromkeys(all_syms + tick)))
    if stories:
        titles = [n["title"] for n in stories]
        if is_ar():
            titles = data.translate(titles)
        chg = data.changes(tick) if tick else {}
        cols = st.columns(len(stories))
        for i, (col, n, t) in enumerate(zip(cols, stories, titles)):
            ch = ui.chips(n["tickers"], chg, lg) or f'<span class="muted">{L("Broad market", "السوق بشكل عام")}</span>'
            col.markdown(f'<div class="story{" rtl" if is_ar() else ""}"><div class="rank">0{i + 1}</div><a href="{T.esc(n["link"])}" target="_blank">{T.esc(t)}</a>'
                         f'<div class="muted" style="font-size:.78rem;margin-top:6px">{T.esc(n["source"])} · {T.time_ago(n["time"], is_ar())}</div>'
                         f'<div class="aff"><span class="lbl" style="width:100%">{L("Affected companies", "الشركات المتأثرة")}</span>{ch}</div></div>',
                         unsafe_allow_html=True)
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))

    # ---- KPIs
    ui.sec("dashboard", "Dashboard", "لوحة المؤشرات")
    k = st.columns(5)
    spec = [("day_gainers", "trending_up", ("Top gainer", "الأعلى ارتفاعاً")), ("day_losers", "trending_down", ("Top loser", "الأكثر انخفاضاً")),
            ("most_actives", "bolt", ("Most active", "الأكثر تداولاً")), ("most_shorted_stocks", "south_east", ("Most shorted", "الأكثر بيعاً على المكشوف"))]
    for col, (kind, ic, (en, ar)) in zip(k, spec):
        df = lists[kind][0]
        if df.empty:
            continue
        r = df.iloc[0]
        sub = f"{T.fmt_big(r['Volume'])} {L('shares', 'سهم')}" if kind == "most_actives" else (f"{r['Chg %']:+.2f}%" if pd.notna(r["Chg %"]) else "")
        col.markdown(T.kpi(ic, L(en, ar), f'{T.logo_circle(r["Symbol"], lg.get(r["Symbol"]), 30)}{T.esc(r["Symbol"])}', sub,
                           "muted" if kind == "most_actives" else T.cls(r["Chg %"])), unsafe_allow_html=True)
    if not moves.empty:
        adv = int((moves["Chg %"] > 0).sum())
        k[4].markdown(T.kpi("balance", L("Breadth (top 175)", "اتساع السوق"), f"{adv}/{len(moves)}", L("advancing", "صاعدة"),
                            "up" if adv > len(moves) / 2 else "down"), unsafe_allow_html=True)

    # ---- summary
    ui.sec("summarize", "Market summary", "ملخص السوق")
    ui.html(f'<div class="card{" rtl" if is_ar() else ""}"><ul class="summary">' +
            "".join(f"<li>{T.esc(L(e, a))}</li>" for e, a in summary_points(px, moves, lists)) + "</ul></div>")

    # ---- movers at a glance
    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    keys = list(LISTS)
    for row in (keys[:3], keys[3:]):
        cols = st.columns(3)
        for col, kind in zip(cols, row):
            df, _ = lists[kind]
            en, ar, ic = LISTS[kind]
            body = ui.row_list(df.head(6), lg) if not df.empty else f'<div class="muted">{L("No data", "لا بيانات")}</div>'
            col.markdown(f'<div class="mcard"><div class="hd">{T.icon(ic)}<span>{T.esc(L(en, ar))}</span></div>{body}</div>', unsafe_allow_html=True)

    # ---- full lists
    ui.sec("table_rows", "Full lists", "القوائم الكاملة")
    tabs = st.tabs([f":material/{v[2]}: {L(v[0], v[1])}" for v in LISTS.values()])
    for tab, kind in zip(tabs, LISTS):
        with tab:
            df, fallback = lists[kind]
            if df.empty:
                st.info(L("Data unavailable right now.", "البيانات غير متاحة حالياً."))
                continue
            ui.html(_leaderboard(df, lg))
            st.plotly_chart(charts.movers_bubble(df, L("Change vs relative volume (bubble = market cap)", "التغير مقابل الحجم النسبي (حجم الفقاعة = القيمة السوقية)"),
                                                 L("Relative volume (×)", "الحجم النسبي (×)"), L("Change %", "التغير %")))
            show = df[["Symbol", "Name", "Price", "Chg %", "Volume", "Rel Vol", "Mkt Cap"]].copy()
            show.insert(0, "Logo", show["Symbol"].map(data.logo_url))
            show["Volume"] = show["Volume"].map(T.fmt_big)
            show["Mkt Cap"] = show["Mkt Cap"].map(T.fmt_big)
            N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Price": L("Price", "السعر"), "Chg %": L("Change %", "التغير %"),
                 "Volume": L("Volume", "الحجم"), "Rel Vol": L("Rel. volume", "الحجم النسبي"), "Mkt Cap": L("Market cap", "القيمة السوقية")}
            show = show.rename(columns=N)
            st.dataframe(show.style.map(T.color_style, subset=[N["Chg %"]]).format({N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["Rel Vol"]: "{:.1f}×"}, na_rep="—"),
                         hide_index=True, height=420, column_config={"Logo": st.column_config.ImageColumn("", width="small")})
            if fallback:
                st.caption(L("Computed from the top 175 US stocks (screener source unavailable).", "محسوبة من أكبر 175 سهم أمريكي (مصدر القوائم غير متاح حالياً)."))
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
              "Latest US market headlines with the companies affected by each story.", "آخر أخبار السوق الأمريكي مع الشركات المتأثرة بكل خبر.")
    c1, c2, c3 = st.columns([2, 1, 1])
    sym = c1.text_input(L("Symbol (leave empty for market news)", "رمز سهم (اتركه فارغاً لأخبار السوق)"), "").strip().upper()
    count = c2.selectbox(L("Headlines", "عدد الأخبار"), [10, 20, 30], index=1)
    translate = c3.toggle(L("Translate to Arabic", "ترجمة للعربية"), value=is_ar())
    items = data.news(sym, 30) if sym else data.market_news()
    ui.news_list(items, count, translate=translate)
    ui.foot()
