"""
app.py - Pro Trading Platform (Webull-style). US market.
Pages: Market Overview · What's Trending · News · Stock · Scanner · Catalyst Pro · Strategy Lab · Trades
Run locally:  streamlit run app.py
"""
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import engine
import ta
import theme as T

SITE_NAME = "A.Alturaifi Pro"
st.set_page_config(page_title=f"{SITE_NAME} · US Markets", page_icon="📈", layout="wide")
st.markdown(T.CSS, unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("symbol", "AAPL")
ss.setdefault("watchlist", ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "GOOGL", "AMD"])
ss.setdefault("lab_cfg", {"symbol": "AAPL", "period": "2y", "strategy": "SMA Crossover", "params": {},
                          "capital": 10000, "fee": 0.05, "stop": 7.0, "atr": 0.0, "tp": 0.0, "trail": 0.0})
ss.setdefault("acct", {"size": 10000, "risk": 1.0})

AR_COLS = {"Symbol": "الرمز", "Name": "الشركة", "Price": "السعر", "Chg %": "التغير %", "Volume": "الحجم",
           "Avg Vol (3M)": "متوسط الحجم (3 أشهر)", "Mkt Cap": "القيمة السوقية", "Rel Vol": "الحجم النسبي"}


def section(title):
    st.markdown(f'<div class="section">{title}</div>', unsafe_allow_html=True)


def ar(text, tag="div", size=None):
    style = f' style="font-size:{size}"' if size else ""
    st.markdown(f'<{tag} class="rtl"{style}>{text}</{tag}>', unsafe_allow_html=True)


def open_stock(sym):
    ss.symbol = sym.upper()
    st.switch_page(PAGES["stock"])


def spy_daily():
    return data.history("SPY", "2y")


def arabic_news(items, limit=20, tag_key=None, translate=True):
    items = items[:limit]
    if not items:
        ar("لا توجد أخبار متاحة حالياً.", size=".95rem")
        return
    titles = [n["title"] for n in items]
    sums = [(n["summary"] or "")[:320] for n in items]
    if translate:
        with st.spinner("جاري الترجمة للعربية..."):
            tr = data.translate(tuple(titles + sums))
        titles, sums = tr[:len(items)], tr[len(items):]
    html = "".join(T.news_html(n, t, s, tag=n.get(tag_key) if tag_key else None, arabic=translate)
                   for n, t, s in zip(items, titles, sums))
    st.markdown(html, unsafe_allow_html=True)


# =====================================================================
# 1. MARKET OVERVIEW
# =====================================================================
def page_home():
    st.markdown(f'<div class="brand-sub">{SITE_NAME}</div>', unsafe_allow_html=True)
    st.title("Market Overview")
    st.markdown(f'<div class="muted">{T.market_status()} · Data: Yahoo Finance & FRED (may be delayed)</div>',
                unsafe_allow_html=True)

    all_syms = tuple(s for g in engine.MARKET_TILES.values() for s in g)
    with st.spinner("Loading markets..."):
        px = data.history_many(all_syms, "1mo")

    for group, syms in engine.MARKET_TILES.items():
        section(group)
        items = []
        for sym, name in syms.items():
            df = px.get(sym)
            if df is None or len(df) < 2:
                items.append(T.tile(name, "—"))
                continue
            last, prev = df["Close"].iloc[-1], df["Close"].iloc[-2]
            is_yield = group == "Treasury Yields"
            value = f"{last:.3f}%" if is_yield else T.fmt_price(last)
            items.append(T.tile(name, value, last - prev, (last / prev - 1) * 100, df["Close"].tail(22).values,
                                invert=(sym == "^VIX")))
        st.markdown(T.tiles(items), unsafe_allow_html=True)

    # ---- economic indicators
    section("US Economic Indicators (FRED)")
    with st.spinner("Loading economic data..."):
        mac = data.macro()
    if not mac:
        st.info("Economic data is temporarily unavailable. Refresh in a minute.")
    else:
        items = []
        for sid, m in mac.items():
            chg = m["value"] - m["prev"]
            unit = m["unit"]
            val = f"{m['value']:,.2f}{unit}" if unit == "%" else (f"{m['value']:,.1f}{unit}" if unit else f"{m['value']:,.1f}")
            sub = f"as of {m['date']:%b %Y} · prev {m['prev']:,.2f}{unit if unit == '%' else ''}"
            invert = bool(m["higher_is_bad"])
            c = T.cls(chg, invert) if m["higher_is_bad"] is not None else "muted"
            color = {"up": T.UP, "down": T.DOWN}.get(c, T.ACCENT)
            items.append(
                f'<div class="tile"><div class="t-name">{T.esc(m["name"])}</div><div class="t-row"><div>'
                f'<div class="t-val">{val}</div><div class="t-chg {c}">{chg:+,.2f} vs prior</div></div>'
                f'{T.sparkline(m["hist"].values, color)}</div><div class="t-sub">{sub}</div></div>')
        st.markdown(T.tiles(items), unsafe_allow_html=True)
        with st.expander("📈 Explore an indicator"):
            names = {m["name"]: sid for sid, m in mac.items()}
            pick = st.selectbox("Indicator", list(names))
            s = mac[names[pick]]["hist"]
            st.plotly_chart(charts.line(s, pick, height=300, fill=False))

    # ---- sectors + breadth
    c1, c2 = st.columns([1.1, 1])
    with c1:
        section("Sector Performance")
        per = st.radio("Period", ["1D", "1W", "1M"], horizontal=True, label_visibility="collapsed")
        n = {"1D": 1, "1W": 5, "1M": 21}[per]
        sec = data.history_many(tuple(engine.SECTOR_ETFS), "3mo")
        labels, vals = [], []
        for etf, name in engine.SECTOR_ETFS.items():
            df = sec.get(etf)
            if df is not None and len(df) > n:
                labels.append(f"{name} ({etf})")
                vals.append((df["Close"].iloc[-1] / df["Close"].iloc[-1 - n] - 1) * 100)
        if vals:
            st.plotly_chart(charts.hbar(labels, vals, height=420))
    uni = data.history_many(tuple(engine.US_UNIVERSE), "5d")
    rows = []
    for s, df in uni.items():
        if len(df) >= 2:
            chg = (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100
            rows.append({"Symbol": s, "Sector": engine.SECTOR_OF.get(s, "Other"), "Chg %": chg,
                         "Size": float(df["Close"].iloc[-1] * df["Volume"].iloc[-1]) or 1.0})
    heat = pd.DataFrame(rows)
    with c2:
        section("Market Breadth (Top 100 US stocks)")
        if not heat.empty:
            adv, dec = int((heat["Chg %"] > 0).sum()), int((heat["Chg %"] < 0).sum())
            m1, m2, m3 = st.columns(3)
            m1.metric("Advancers", adv)
            m2.metric("Decliners", dec)
            m3.metric("Avg Change", f"{heat['Chg %'].mean():+.2f}%")
            st.plotly_chart(charts.pie(["Advancing", "Declining"], [adv, dec], "Advance / Decline"))

    section("Market Heatmap (size = dollar volume)")
    if not heat.empty:
        st.plotly_chart(charts.treemap(heat))


# =====================================================================
# 2. WHAT'S TRENDING  (Arabic)
# =====================================================================
TREND_TABS = {"🚀 الأكثر ارتفاعاً": "day_gainers", "🔻 الأكثر انخفاضاً": "day_losers",
              "🔥 الأكثر تداولاً": "most_actives", "🩳 الأكثر بيعاً على المكشوف": "most_shorted_stocks",
              "💎 شركات صغيرة صاعدة": "small_cap_gainers"}


def trending_fallback(kind):
    uni = data.history_many(tuple(engine.US_UNIVERSE), "3mo")
    rows = []
    for s, df in uni.items():
        if len(df) > 2:
            rows.append({"Symbol": s, "Name": s, "Price": df["Close"].iloc[-1],
                         "Chg %": (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100,
                         "Volume": df["Volume"].iloc[-1], "Avg Vol (3M)": df["Volume"].mean(), "Mkt Cap": None})
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    if kind == "day_losers":
        return t.sort_values("Chg %").head(25)
    if kind in ("most_actives", "most_shorted_stocks"):
        return t.sort_values("Volume", ascending=False).head(25)
    return t.sort_values("Chg %", ascending=False).head(25)


def page_trending():
    ar("🔥 الأكثر رواجاً في السوق الأمريكي", "h1")
    ar(f"الأسهم الأكثر حركة اليوم · <span class='muted'>{T.market_status()}</span>", size=".9rem")
    tabs = st.tabs(list(TREND_TABS))
    for tab, (label, kind) in zip(tabs, TREND_TABS.items()):
        with tab:
            df = data.screen(kind, 25)
            source_note = ""
            if df.empty:
                df = trending_fallback(kind)
                source_note = "ملاحظة: القائمة محسوبة من أكبر 100 سهم أمريكي لأن مصدر البيانات غير متاح حالياً."
            if df.empty:
                ar("البيانات غير متاحة حالياً، حاول بعد قليل.")
                continue
            df = df.copy()
            df["Rel Vol"] = df["Volume"] / df["Avg Vol (3M)"]
            top = df.head(15)
            st.plotly_chart(charts.hbar(list(top["Symbol"]), list(top["Chg %"].fillna(0)), height=440))
            show = df[["Symbol", "Name", "Price", "Chg %", "Volume", "Rel Vol", "Mkt Cap"]].copy()
            show["Volume"] = show["Volume"].map(T.fmt_big)
            show["Mkt Cap"] = show["Mkt Cap"].map(T.fmt_big)
            show = show.rename(columns=AR_COLS)
            st.dataframe(show.style.map(T.color_style, subset=["التغير %"]).format(
                {"السعر": "{:,.2f}", "التغير %": "{:+.2f}%", "الحجم النسبي": "{:.1f}×"}, na_rep="—"),
                hide_index=True, height=420)
            if source_note:
                ar(source_note, size=".8rem")
            c1, c2 = st.columns([3, 1])
            pick = c1.selectbox("اختر سهماً لعرض التفاصيل", df["Symbol"].tolist(), key=f"tr_{kind}")
            if c2.button("📈 افتح السهم", key=f"trb_{kind}"):
                open_stock(pick)


# =====================================================================
# 3. NEWS  (Arabic)
# =====================================================================
def page_news():
    ar("📰 أخبار السوق الأمريكي", "h1")
    c1, c2, c3 = st.columns([2, 1, 1])
    sym = c1.text_input("رمز سهم (اتركه فارغاً لأخبار السوق العامة)", "").strip().upper()
    count = c2.selectbox("عدد الأخبار", [10, 20, 30], index=1)
    translate = c3.toggle("ترجمة للعربية", value=True)
    items = data.news(sym, 30) if sym else data.market_news()
    if sym:
        ar(f"آخر أخبار <b>{T.esc(sym)}</b>", size="1.05rem")
    arabic_news(items, count, translate=translate)


# =====================================================================
# 4. STOCK (quote, chart, technicals, financials, analysts, news)
# =====================================================================
TF = {"1D": ("5d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "60m"), "3M": 63, "6M": 126, "YTD": "ytd",
      "1Y": 252, "5Y": ("5y", "1wk"), "MAX": ("max", "1mo")}


def _pick_symbol(sym):
    ss.symbol = sym
    ss["stock_q"] = ""


def search_box():
    q = st.text_input("Search", key="stock_q", placeholder="🔍  Search symbol or company (e.g. Apple, NVDA, Tesla)",
                      label_visibility="collapsed").strip()
    if not q:
        return
    results = data.search(q)
    if not results:
        st.caption("No matches. Try a ticker symbol like AAPL.")
        return
    st.caption("Search results")
    cols = st.columns(2)
    for i, r in enumerate(results[:8]):
        label = f"**{r['symbol']}** · {r['name'][:38]} · {r['exchange']} {r['type']}"
        cols[i % 2].button(label, key=f"sr_{r['symbol']}_{i}", on_click=_pick_symbol, args=(r["symbol"],))


def quote_header(sym, daily, inf):
    last, prev = daily["Close"].iloc[-1], daily["Close"].iloc[-2]
    chg, pct = last - prev, (last / prev - 1) * 100
    name = inf.get("longName") or inf.get("shortName") or sym
    exch = inf.get("fullExchangeName") or inf.get("exchange") or ""
    badges = "".join(T.badge(b, "acc") for b in (inf.get("sector"), inf.get("industry")) if b)
    st.markdown(
        f'<div class="q-name">{T.esc(name)} · <b>{sym}</b> · {T.esc(exch)} {badges}</div>'
        f'<div class="q-price">{T.fmt_price(last)} <span style="font-size:1rem" class="muted">'
        f'{inf.get("currency", "USD")}</span></div>'
        f'<div class="q-chg {T.cls(chg)}">{chg:+,.2f} ({pct:+.2f}%) '
        f'<span class="muted" style="font-weight:400">· {daily.index[-1]:%b %d, %Y} · {T.market_status()}</span></div>',
        unsafe_allow_html=True)
    return last


def key_stats(daily, inf):
    last = daily["Close"].iloc[-1]
    yr = daily.tail(252)
    lo52, hi52 = yr["Low"].min(), yr["High"].max()
    div = inf.get("dividendRate")
    stats = [
        ("Open", T.fmt_price(daily["Open"].iloc[-1])), ("High", T.fmt_price(daily["High"].iloc[-1])),
        ("Low", T.fmt_price(daily["Low"].iloc[-1])), ("Prev Close", T.fmt_price(daily["Close"].iloc[-2])),
        ("Volume", T.fmt_big(daily["Volume"].iloc[-1])), ("Avg Vol (3M)", T.fmt_big(inf.get("averageVolume"))),
        ("Market Cap", T.fmt_big(inf.get("marketCap"))),
        ("P/E (TTM)", f"{inf['trailingPE']:.2f}" if inf.get("trailingPE") else "—"),
        ("Fwd P/E", f"{inf['forwardPE']:.2f}" if inf.get("forwardPE") else "—"),
        ("EPS (TTM)", f"{inf['trailingEps']:.2f}" if inf.get("trailingEps") else "—"),
        ("Beta", f"{inf['beta']:.2f}" if inf.get("beta") else "—"),
        ("Div Yield", f"{div / last * 100:.2f}%" if div else "—"),
        ("Short % Float", f"{inf['shortPercentOfFloat'] * 100:.1f}%" if inf.get("shortPercentOfFloat") else "—"),
        ("Shares Out", T.fmt_big(inf.get("sharesOutstanding"))),
    ]
    pos = (last - lo52) / (hi52 - lo52) * 100 if hi52 > lo52 else 50
    st.markdown(
        '<div class="stats">' + "".join(f'<div class="stat"><div class="l">{l}</div><div class="v">{v}</div></div>'
                                        for l, v in stats) + "</div>"
        f'<div class="muted" style="font-size:.75rem;display:flex;justify-content:space-between">'
        f'<span>52W Low {T.fmt_price(lo52)}</span><span>52W High {T.fmt_price(hi52)}</span></div>'
        f'<div class="range"><div class="dot" style="left:calc({pos:.1f}% - 7px)"></div></div>',
        unsafe_allow_html=True)


def chart_tab(sym, daily):
    c1, c2 = st.columns([3, 1.2])
    tf = c1.radio("Range", list(TF), index=6, horizontal=True, label_visibility="collapsed")
    ctype = c2.selectbox("Chart type", charts.CHART_TYPES, label_visibility="collapsed")
    c3, c4 = st.columns(2)
    overlays = c3.multiselect("Overlays", charts.OVERLAYS, default=["SMA 20", "SMA 50", "SMA 200"])
    panels = c4.multiselect("Indicator panels", charts.PANELS, default=["RSI", "MACD"])
    spec = TF[tf]
    intraday = tf in ("1D", "5D", "1M")
    if isinstance(spec, int) or spec == "ytd":
        full = ta.add_all(daily)
        d = full[full.index.year == full.index[-1].year] if spec == "ytd" else full.tail(spec)
    else:
        raw = data.history(sym, *spec)
        if raw.empty:
            st.warning("Intraday data isn't available for this symbol. Try 3M or longer.")
            return
        d = ta.add_all(raw)
        if tf == "1D":
            d = d[d.index.date == d.index[-1].date()]
    if len(d) < 2:
        st.warning("Not enough data for this range.")
        return
    st.plotly_chart(charts.price_chart(d, ctype, overlays, panels, intraday))


def technicals_tab(daily):
    d = ta.add_all(daily)
    table, total, label, parts = ta.technical_summary(d)
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(charts.gauge(total, f"Summary: {label}"))
    c2.plotly_chart(charts.gauge(parts.get("Oscillators", 0), f"Oscillators: {ta.label_for(parts.get('Oscillators', 0))}"))
    c3.plotly_chart(charts.gauge(parts.get("Moving Averages", 0),
                                 f"Moving Averages: {ta.label_for(parts.get('Moving Averages', 0))}"))
    left, right = st.columns([1.3, 1])
    with left:
        section("Indicator signals")

        def sig_style(v):
            return {"Buy": f"color:{T.UP};font-weight:600", "Sell": f"color:{T.DOWN};font-weight:600"}.get(v, "")
        st.dataframe(table.style.map(sig_style, subset=["Signal"]).format({"Value": "{:,.2f}"}),
                     hide_index=True, height=560)
    with right:
        section("Pivot points (classic)")
        piv = ta.pivot_points(daily)
        st.dataframe(pd.DataFrame({"Level": list(piv), "Price": [round(v, 2) for v in piv.values()]}),
                     hide_index=True)
        section("Support & resistance (swing levels)")
        price = daily["Close"].iloc[-1]
        lv = ta.swing_levels(daily)
        sr = pd.DataFrame({"Level": [round(x, 2) for x in lv],
                           "Type": ["Support" if x < price else "Resistance" for x in lv],
                           "Distance %": [(x / price - 1) * 100 for x in lv]})
        st.dataframe(sr.iloc[::-1].style.map(T.color_style, subset=["Distance %"]).format({"Distance %": "{:+.2f}%"}),
                     hide_index=True)
        last = d.iloc[-1]
        section("Volatility")
        m1, m2 = st.columns(2)
        m1.metric("ATR (14)", f"{last['ATR']:.2f}", f"{last['ATR'] / last['Close'] * 100:.2f}% of price",
                  delta_color="off")
        m2.metric("BB Width", f"{last['BB_width'] * 100:.1f}%")
    st.plotly_chart(charts.returns_bars(daily))


def financials_tab(sym, inf):
    f = data.fundamentals(sym)

    def pct(k):
        v = inf.get(k)
        return f"{v * 100:.2f}%" if isinstance(v, (int, float)) else "—"

    def num(k, dec=2):
        v = inf.get(k)
        return f"{v:,.{dec}f}" if isinstance(v, (int, float)) else "—"

    groups = {
        "Valuation": [("Market Cap", T.fmt_big(inf.get("marketCap"))), ("Enterprise Value", T.fmt_big(inf.get("enterpriseValue"))),
                      ("P/E (TTM)", num("trailingPE")), ("Forward P/E", num("forwardPE")),
                      ("PEG", num("trailingPegRatio")), ("Price/Sales", num("priceToSalesTrailing12Months")),
                      ("Price/Book", num("priceToBook")), ("EV/EBITDA", num("enterpriseToEbitda"))],
        "Profitability": [("Gross Margin", pct("grossMargins")), ("Operating Margin", pct("operatingMargins")),
                          ("Profit Margin", pct("profitMargins")), ("ROE", pct("returnOnEquity")),
                          ("ROA", pct("returnOnAssets"))],
        "Growth": [("Revenue Growth (YoY)", pct("revenueGrowth")), ("Earnings Growth (YoY)", pct("earningsGrowth")),
                   ("Qtr Earnings Growth", pct("earningsQuarterlyGrowth")), ("Revenue (TTM)", T.fmt_big(inf.get("totalRevenue"))),
                   ("EBITDA", T.fmt_big(inf.get("ebitda")))],
        "Balance Sheet": [("Total Cash", T.fmt_big(inf.get("totalCash"))), ("Total Debt", T.fmt_big(inf.get("totalDebt"))),
                          ("Debt/Equity", num("debtToEquity", 1)), ("Current Ratio", num("currentRatio")),
                          ("Free Cash Flow", T.fmt_big(inf.get("freeCashflow")))],
    }
    cols = st.columns(4)
    for col, (g, items) in zip(cols, groups.items()):
        with col:
            section(g)
            st.markdown("".join(f'<div class="stat" style="margin-bottom:6px"><div class="l">{l}</div>'
                                f'<div class="v">{v}</div></div>' for l, v in items), unsafe_allow_html=True)
    inc = f["income_q"]
    if isinstance(inc, pd.DataFrame) and not inc.empty:
        st.plotly_chart(charts.income_chart(inc))
    else:
        st.info("Quarterly statements are not available for this symbol.")


def analysts_tab(sym, inf, price):
    f = data.fundamentals(sym)
    c1, c2 = st.columns(2)
    with c1:
        if f["targets"]:
            st.plotly_chart(charts.target_chart(price, f["targets"]))
            mean = f["targets"].get("mean")
            if mean:
                st.metric("Upside to mean target", f"{(mean / price - 1) * 100:+.1f}%",
                          f"{inf.get('recommendationKey', '').replace('_', ' ').title()} · "
                          f"{inf.get('numberOfAnalystOpinions', 0)} analysts", delta_color="off")
        rec = f["rec_summary"]
        if isinstance(rec, pd.DataFrame) and not rec.empty:
            st.plotly_chart(charts.rec_chart(rec))
    with c2:
        eh = f["earnings_hist"]
        if isinstance(eh, pd.DataFrame) and not eh.empty:
            fig = charts.eps_chart(eh)
            if fig is not None:
                st.plotly_chart(fig)
        if f["earnings_date"] is not None:
            days = (pd.Timestamp(f["earnings_date"]).normalize() - pd.Timestamp.now().normalize()).days
            st.metric("Next earnings", f"{pd.Timestamp(f['earnings_date']):%b %d, %Y}", f"in {days} days",
                      delta_color="off")
    section("Upgrades & downgrades (90 days)")
    r = f["ratings"]
    if isinstance(r, pd.DataFrame) and not r.empty:
        st.dataframe(r, height=260)
    else:
        st.caption("No rating changes in the last 90 days.")
    section("Insider transactions")
    ins = f["insiders"]
    if isinstance(ins, pd.DataFrame) and not ins.empty:
        st.dataframe(ins.head(15), hide_index=True, height=300)
    else:
        st.caption("No insider data available.")


def page_stock():
    search_box()
    sym = ss.symbol
    with st.spinner(f"Loading {sym}..."):
        daily = data.history(sym, "2y")
    if daily.empty or len(daily) < 3:
        st.error(f"No data found for **{sym}**. Check the symbol or search by company name above.")
        return
    inf = data.info(sym)
    h1, h2 = st.columns([4, 1])
    with h1:
        price = quote_header(sym, daily, inf)
    with h2:
        st.write("")
        if sym not in ss.watchlist:
            if st.button("☆ Add to Watchlist"):
                ss.watchlist.append(sym)
                st.rerun()
        else:
            st.button("★ In Watchlist", disabled=True)
        if st.button("⚡ Catalyst Pro"):
            st.switch_page(PAGES["catalyst"])
    key_stats(daily, inf)
    t1, t2, t3, t4, t5 = st.tabs(["📈 Chart", "🧭 Technicals", "💼 Financials", "🎯 Analysts", "📰 الأخبار"])
    with t1:
        chart_tab(sym, daily)
    with t2:
        technicals_tab(daily)
    with t3:
        financials_tab(sym, inf)
    with t4:
        analysts_tab(sym, inf, price)
    with t5:
        arabic_news(data.news(sym, 20), 15)


# =====================================================================
# 5. SCANNER
# =====================================================================
def page_scanner():
    st.title("Opportunity Scanner")
    st.caption("The bot scans US stocks for technical setups and builds a trade plan (entry · stop · target) "
               "for each one. Score = bullish signals minus bearish signals.")
    universes = {"US Top 100+ (all sectors)": engine.US_UNIVERSE, **{f"Sector: {k}": v for k, v in engine.SECTORS.items()},
                 "My Watchlist": ss.watchlist, "Custom list": None}
    c1, c2, c3 = st.columns([1.4, 1, 1])
    uni_name = c1.selectbox("Universe", list(universes))
    preset = c2.selectbox("Setup filter", list(engine.SCAN_PRESETS))
    if universes[uni_name] is None:
        txt = c3.text_input("Symbols (comma separated)", "AAPL, MSFT, NVDA, TSLA, AMD")
        symbols = [s.strip().upper() for s in txt.split(",") if s.strip()]
    else:
        symbols = universes[uni_name]
        c3.metric("Symbols", len(symbols))
    if st.button("🤖 Run Scan", type="primary"):
        with st.spinner(f"Scanning {len(symbols)} symbols..."):
            dmap = data.history_many(tuple(symbols), "1y")
            ss.scan = {"res": engine.scan(dmap, spy_daily()), "time": datetime.now(), "universe": uni_name,
                       "count": len(dmap)}
    sc = ss.get("scan")
    if not sc:
        st.info("Choose a universe and press **Run Scan**.")
        return
    res = sc["res"]
    if res.empty:
        st.warning("No data returned. Try again in a minute.")
        return
    tag = engine.SCAN_PRESETS[preset]
    view = res[res["_tags"].str.contains(tag)] if tag else res
    m = st.columns(5)
    m[0].metric("Scanned", sc["count"])
    m[1].metric("Bullish (score ≥ 3)", int((res["Score"] >= 3).sum()))
    m[2].metric("Bearish (score < 0)", int((res["Score"] < 0).sum()))
    m[3].metric(f"Matches: {preset}", len(view))
    m[4].metric("Scan time", f"{sc['time']:%H:%M}")

    lo, hi = int(res["Score"].min()), int(res["Score"].max())
    min_score = st.slider("Minimum score", lo, hi, max(lo, min(2, hi))) if hi > lo else lo
    view = view[view["Score"] >= min_score]
    cols = ["Symbol", "Sector", "Price", "Chg %", "1M %", "3M %", "RSI", "ADX", "Vol ×", "Trend", "Score",
            "Setup", "Entry", "Stop", "Target", "R:R", "Signals"]
    st.dataframe(view[cols].style.map(T.color_style, subset=["Chg %", "1M %", "3M %"]).format(
        {"Price": "{:,.2f}", "Chg %": "{:+.2f}%", "1M %": "{:+.1f}%", "3M %": "{:+.1f}%", "RSI": "{:.0f}",
         "ADX": "{:.0f}", "Vol ×": "{:.1f}", "Entry": "{:,.2f}", "Stop": "{:,.2f}", "Target": "{:,.2f}",
         "R:R": "{:.1f}"}, na_rep="—"), hide_index=True, height=440)

    a, b, c = st.columns([2, 1, 1])
    choices = view["Symbol"].tolist() or res["Symbol"].tolist()
    pick = a.selectbox("Selected symbol", choices)
    if b.button("📈 Open Chart"):
        open_stock(pick)
    if c.button("⚡ Catalyst Pro"):
        ss.symbol = pick
        st.switch_page(PAGES["catalyst"])

    v1, v2 = st.columns([1.6, 1])
    v1.plotly_chart(charts.scan_scatter(res))
    by_sec = res.groupby("Sector")["Score"].mean().sort_values()
    v2.plotly_chart(charts.hbar(list(by_sec.index), list(by_sec.values), "Average score by sector", 460, suffix=""))
    st.download_button("⬇️ Download results (CSV)", res.drop(columns=["_tags"]).to_csv(index=False).encode(),
                       "scan_results.csv", "text/csv")


# =====================================================================
# 6. CATALYST PRO
# =====================================================================
def page_catalyst():
    st.title("Catalyst Pro")
    st.caption("Technical + fundamental + event catalysts, combined into a score and a complete trade plan "
               "with entry timing, stop loss and targets.")
    c1, c2, c3 = st.columns([1.2, 1, 1])
    sym = c1.text_input("Symbol", ss.symbol).strip().upper() or "AAPL"
    ss.symbol = sym
    ss.acct["size"] = c2.number_input("Account size ($)", 100, 100_000_000, int(ss.acct["size"]), step=1000)
    ss.acct["risk"] = c3.number_input("Risk per trade (%)", 0.1, 10.0, float(ss.acct["risk"]), step=0.25)

    with st.spinner(f"Analyzing {sym}..."):
        daily = data.history(sym, "2y")
        if daily.empty or len(daily) < 60:
            st.error(f"Not enough data for {sym}.")
            return
        d = ta.add_all(daily)
        inf = data.info(sym)
        f = data.fundamentals(sym)
        nws = data.news(sym, 20)
        tech = engine.technical_checks(d, spy_daily())
        fund = engine.fundamental_checks(inf, f["earnings_hist"])
        recent_ratings = f["ratings"]
        if isinstance(recent_ratings, pd.DataFrame) and not recent_ratings.empty:
            recent_ratings = recent_ratings[recent_ratings.index >= pd.Timestamp.now() - pd.Timedelta(days=30)]
        events = engine.event_checks(f["earnings_date"], recent_ratings, nws, inf, d)
        score = engine.catalyst_score(tech, fund, events)
        plan = engine.trade_plan(d, ss.acct["size"], ss.acct["risk"])

    # ---- verdict
    name = inf.get("shortName") or sym
    kind = "up" if score["total"] >= 55 else ("down" if score["total"] < 45 else "neu")
    bias_kind = "up" if plan["bias"].startswith("Long") else ("down" if "Avoid" in plan["bias"] else "neu")
    st.markdown(f"### {T.esc(name)} ({sym}) {T.badge(score['label'], kind)} {T.badge('Bias: ' + plan['bias'], bias_kind)}"
                f" {T.badge('Setup: ' + plan['setup'], 'acc')}", unsafe_allow_html=True)
    g1, g2, g3, g4 = st.columns([1.3, 1, 1, 1])
    g1.plotly_chart(charts.score_gauge(score["total"], "Catalyst Score"))

    def sc(v):
        return "n/a" if v is None else f"{v:.0f}/100"
    g2.metric("Technical (50%)", sc(score["technical"]), f"{sum(c['Pass'] for c in tech)}/{len(tech)} checks",
              delta_color="off")
    g3.metric("Fundamental (30%)", sc(score["fundamental"]),
              f"{sum(c['Pass'] for c in fund)}/{len(fund)} checks" if fund else "no data", delta_color="off")
    g4.metric("Events (20%)", sc(score["event"]), f"{len(events)} catalysts", delta_color="off")

    # ---- trade plan
    section("Trade plan")
    p = plan
    cards = [("Current price", f"${p['price']:,.2f}"), ("Entry zone", f"${p['zone'][0]:,.2f} – ${p['zone'][1]:,.2f}"),
             ("Stop loss", f"${p['stop']:,.2f}"), ("Target 1 (2R)", f"${p['t1']:,.2f}"),
             ("Target 2 (3R)", f"${p['t2']:,.2f}"), ("Risk / share", f"${p['risk_per_share']:,.2f}"),
             ("Position size", f"{p['shares']:,} sh"), ("Position value", f"${p['position_value']:,.0f}"),
             ("Max loss", f"${p['shares'] * p['risk_per_share']:,.0f}"), ("ATR (14)", f"${p['atr']:,.2f} ({p['atr_pct']:.1f}%)"),
             ("Support", f"${p['support']:,.2f}"), ("Resistance", f"${p['resistance']:,.2f}")]
    colors = {"Stop loss": T.DOWN, "Target 1 (2R)": T.UP, "Target 2 (3R)": T.UP, "Entry zone": T.ACCENT}
    st.markdown('<div class="plan">' + "".join(
        f'<div class="p" style="border-left-color:{colors.get(l, T.BORDER)}"><div class="l">{l}</div>'
        f'<div class="v">{v}</div></div>' for l, v in cards) + "</div>", unsafe_allow_html=True)

    left, right = st.columns([1.6, 1])
    with left:
        levels = [("Entry", p["entry"], T.ACCENT, "solid"), ("Stop", p["stop"], T.DOWN, "dash"),
                  ("T1", p["t1"], T.UP, "dot"), ("T2", p["t2"], T.UP, "dash")]
        st.plotly_chart(charts.price_chart(d.tail(126), "Candles", ["SMA 20", "SMA 50"], [], False,
                                           levels=levels, height=520))
    with right:
        section("⏱ Entry timing")
        earn = f["earnings_date"]
        earn_days = (pd.Timestamp(earn).normalize() - pd.Timestamp.now().normalize()).days if earn is not None else None
        timing = [f"<b>Trigger:</b> {T.esc(p['trigger'])}",
                  f"<b>Market now:</b> {T.market_status()}",
                  "<b>Best window:</b> avoid the first 30 min after the 9:30 ET open; confirm on the daily close "
                  "or after 10:00 ET with above-average volume.",
                  "<b>Holding period:</b> " + ("2–6 weeks (swing)" if p["setup"] in ("Breakout", "Pullback to SMA20")
                                               else "1–2 weeks (short swing)")]
        if earn_days is not None and 0 <= earn_days <= 14:
            timing.append(f"<b class='down'>⚠️ Earnings in {earn_days} days</b>: half size, or wait until after the report.")
        st.markdown("".join(f'<div class="check">{t}</div>' for t in timing), unsafe_allow_html=True)
        section("🚪 Exit rules")
        st.markdown("".join(f'<div class="check">{T.esc(e)}</div>' for e in p["exits"]), unsafe_allow_html=True)

    # ---- checklists
    def checklist(items):
        return "".join(f'<div class="check">{"✅" if c["Pass"] else "❌"} <b>{T.esc(c["Check"])}</b> '
                       f'<span class="muted">· {T.esc(c["Detail"])}</span></div>' for c in items)
    c1, c2 = st.columns(2)
    with c1:
        section("Technical catalysts")
        st.markdown(checklist(tech), unsafe_allow_html=True)
    with c2:
        section("Fundamental catalysts")
        if fund:
            st.markdown(checklist(fund), unsafe_allow_html=True)
        else:
            st.caption("No fundamental data (ETF, index or crypto).")
    section("Event catalysts")
    if events:
        st.dataframe(pd.DataFrame(events), hide_index=True)
    else:
        st.caption("No special events detected right now.")
    section("آخر الأخبار")
    arabic_news(nws, 6)
    st.caption("⚠️ Educational tool, not investment advice. Always confirm with your own analysis.")


# =====================================================================
# 7. STRATEGY LAB (trading bot)
# =====================================================================
def lab_settings():
    cfg = ss.lab_cfg
    with st.container(border=True):
        c = st.columns([1, 0.8, 1.6, 1, 0.8])
        cfg["symbol"] = c[0].text_input("Symbol", cfg["symbol"]).strip().upper() or "AAPL"
        periods = ["1y", "2y", "5y", "10y"]
        cfg["period"] = c[1].selectbox("History", periods, index=periods.index(cfg["period"]))
        names = list(engine.STRATEGIES)
        cfg["strategy"] = c[2].selectbox("Strategy", names, index=names.index(cfg["strategy"]))
        cfg["capital"] = c[3].number_input("Capital ($)", 100, 100_000_000, int(cfg["capital"]), step=1000)
        cfg["fee"] = c[4].number_input("Fee % / side", 0.0, 1.0, float(cfg["fee"]), step=0.01)
        spec = engine.STRATEGIES[cfg["strategy"]][1]
        params = cfg["params"].setdefault(cfg["strategy"], {k: dflt for k, _, _, _, dflt, _ in spec})
        pc = st.columns(len(spec) + 4)
        for i, (k, label, lo, hi, dflt, step) in enumerate(spec):
            if isinstance(step, float):
                params[k] = pc[i].number_input(label, float(lo), float(hi), float(params.get(k, dflt)), step=float(step))
            else:
                params[k] = pc[i].number_input(label, int(lo), int(hi), int(params.get(k, dflt)), step=int(step))
        j = len(spec)
        cfg["stop"] = pc[j].number_input("Stop loss %", 0.0, 50.0, float(cfg["stop"]), step=0.5, help="0 = off")
        cfg["atr"] = pc[j + 1].number_input("ATR stop ×", 0.0, 10.0, float(cfg["atr"]), step=0.5, help="0 = off")
        cfg["tp"] = pc[j + 2].number_input("Take profit %", 0.0, 500.0, float(cfg["tp"]), step=1.0, help="0 = off")
        cfg["trail"] = pc[j + 3].number_input("Trailing stop %", 0.0, 50.0, float(cfg["trail"]), step=0.5, help="0 = off")
    return cfg


def risk_kwargs(cfg):
    return {"stop_pct": cfg["stop"] or None, "atr_mult": cfg["atr"] or None, "tp_pct": cfg["tp"] or None,
            "trail_pct": cfg["trail"] or None}


def run_lab(cfg):
    df = data.history(cfg["symbol"], cfg["period"])
    if df.empty or len(df) < 60:
        st.error(f"Not enough data for {cfg['symbol']}.")
        return None, None
    params = cfg["params"][cfg["strategy"]]
    if "fast" in params and "slow" in params and params["fast"] >= params["slow"]:
        st.error("Fast period must be smaller than slow period.")
        return None, None
    res = engine.run_strategy(df, cfg["strategy"], params, cfg["capital"], cfg["fee"] / 100, **risk_kwargs(cfg))
    ss.lab = {"cfg": {**cfg, "params": dict(params)}, "res": res}
    return df, res


def page_lab():
    st.title("Strategy Lab")
    st.caption("Backtest the trading bot: signals on the daily close, orders filled at the next open, "
               "stop loss / take profit / trailing stop checked intraday.")
    cfg = lab_settings()
    df, res = run_lab(cfg)
    if res is None:
        return
    m = res["metrics"]
    tr = res["trades"]
    last_pos = res["position"].iloc[-1]
    open_tr = tr[tr["Exit Reason"] == "Open"]
    if last_pos and not open_tr.empty:
        o = open_tr.iloc[0]
        st.success(f"🟢 Bot is LONG since {o['Entry Date']:%b %d, %Y} at ${o['Entry']:,.2f} · "
                   f"open P&L {o['P&L %']:+.2f}%")
    else:
        st.info("⚪ Bot is FLAT (no open position).")

    row1 = st.columns(6)
    row1[0].metric("Total Return", f"{m['Total Return %']:+.1f}%", f"B&H {m['Buy & Hold %']:+.1f}%", delta_color="off")
    row1[1].metric("CAGR", f"{m['CAGR %']:+.1f}%")
    row1[2].metric("Sharpe", f"{m['Sharpe']:.2f}")
    row1[3].metric("Max Drawdown", f"{m['Max Drawdown %']:.1f}%")
    row1[4].metric("Win Rate", f"{m['Win Rate %']:.0f}%", f"{m['Trades']} trades", delta_color="off")
    pf = "∞" if m["Profit Factor"] == np.inf else f"{m['Profit Factor']:.2f}"
    row1[5].metric("Profit Factor", pf)

    ctype = "Candles" if len(df) <= 800 else "Line"
    d = ta.add_all(df)
    ma_keys = {"SMA Crossover": ["SMA 20", "SMA 50"], "Golden Cross (50/200)": ["SMA 50", "SMA 200"],
               "EMA Crossover": ["EMA 9", "EMA 21"], "Bollinger Breakout": ["Bollinger Bands"]}
    panels = {"RSI Mean Reversion": ["RSI"], "MACD Crossover": ["MACD"]}.get(cfg["strategy"], [])
    st.plotly_chart(charts.price_chart(d, ctype, ma_keys.get(cfg["strategy"], []), panels, False, trades=tr))
    bench = df["Close"] / df["Close"].iloc[0] * cfg["capital"]
    st.plotly_chart(charts.equity_chart(res["equity"], bench))
    st.plotly_chart(charts.monthly_heatmap(engine.monthly_returns(res["equity"])))

    b1, b2 = st.columns(2)
    if b1.button("📋 Open trade journal"):
        st.switch_page(PAGES["trades"])

    with st.expander("🧪 Parameter optimizer (heatmap)"):
        spec = engine.STRATEGIES[cfg["strategy"]][1]
        keys = [s[0] for s in spec]
        o1, o2, o3 = st.columns(3)
        px_ = o1.selectbox("X parameter", keys, index=0)
        py_ = o2.selectbox("Y parameter", keys, index=min(1, len(keys) - 1))
        metric = o3.selectbox("Optimize", ["Total Return %", "Sharpe", "Max Drawdown %", "Win Rate %", "CAGR %"])
        if st.button("Run optimizer"):
            def rng(key):
                s = next(x for x in spec if x[0] == key)
                vals = np.linspace(s[2], s[3], 6)
                return [round(float(v), 1) if isinstance(s[5], float) else int(v) for v in vals]
            if px_ == py_:
                st.warning("Pick two different parameters.")
            else:
                with st.spinner("Running 36 backtests..."):
                    grid = engine.optimize(df, cfg["strategy"], px_, rng(px_), py_, rng(py_),
                                           cfg["params"][cfg["strategy"]], cfg["capital"], cfg["fee"] / 100,
                                           metric, **risk_kwargs(cfg))
                st.plotly_chart(charts.optimizer_heatmap(grid, px_, py_, metric))
                st.caption("⚠️ The best cell in the past is often overfit. Prefer stable regions (neighbours with similar results).")

    with st.expander("🏁 Compare all strategies on this symbol"):
        if st.button("Run comparison"):
            rows = []
            for name, (_, spec) in engine.STRATEGIES.items():
                p = {k: dflt for k, _, _, _, dflt, _ in spec}
                mm = engine.run_strategy(df, name, p, cfg["capital"], cfg["fee"] / 100, **risk_kwargs(cfg))["metrics"]
                rows.append({"Strategy": name, **{k: mm[k] for k in ("Total Return %", "CAGR %", "Sharpe",
                                                                      "Max Drawdown %", "Win Rate %", "Trades")}})
            comp = pd.DataFrame(rows).sort_values("Sharpe", ascending=False)
            st.dataframe(comp.style.map(T.color_style, subset=["Total Return %", "CAGR %"]).format(
                {"Total Return %": "{:+.1f}%", "CAGR %": "{:+.1f}%", "Sharpe": "{:.2f}", "Max Drawdown %": "{:.1f}%",
                 "Win Rate %": "{:.0f}%"}), hide_index=True)
            st.plotly_chart(charts.hbar(list(comp["Strategy"]), list(comp["Total Return %"]), "Total return by strategy"))


# =====================================================================
# 8. TRADES
# =====================================================================
def page_trades():
    st.title("Trade Journal")
    if not ss.get("lab"):
        _, res = run_lab(ss.lab_cfg)
        if res is None:
            return
    lab = ss.lab
    cfg, res = lab["cfg"], lab["res"]
    risk = ", ".join(f"{k} {v}" for k, v in (("SL", f"{cfg['stop']}%"), ("ATR×", cfg["atr"]), ("TP", f"{cfg['tp']}%"),
                                              ("Trail", f"{cfg['trail']}%")) if str(v).rstrip("%") not in ("0", "0.0"))
    st.caption(f"Bot trades for **{cfg['symbol']}** · {cfg['strategy']} {cfg['params']} · {cfg['period']} · "
               f"Risk: {risk or 'none'} · change settings in Strategy Lab")
    tr = res["trades"]
    if tr.empty:
        st.info("The bot made no trades with these settings.")
        return
    m = res["metrics"]
    closed = tr[tr["Exit Reason"] != "Open"]
    open_tr = tr[tr["Exit Reason"] == "Open"]
    if not open_tr.empty:
        o = open_tr.iloc[0]
        st.markdown(f'<div class="card">🟢 <b>Open position</b> · entered {o["Entry Date"]:%b %d, %Y} at '
                    f'${o["Entry"]:,.2f} · now ${o["Exit"]:,.2f} · <span class="{T.cls(o["P&L %"])}">'
                    f'{o["P&L %"]:+.2f}% (${o["P&L $"]:+,.0f})</span> · {o["Bars"]} bars</div>',
                    unsafe_allow_html=True)
    r = st.columns(6)
    r[0].metric("Closed trades", m["Trades"])
    r[1].metric("Win rate", f"{m['Win Rate %']:.0f}%")
    r[2].metric("Avg win", f"{m['Avg Win %']:+.2f}%")
    r[3].metric("Avg loss", f"{m['Avg Loss %']:+.2f}%")
    r[4].metric("Net P&L", f"${closed['P&L $'].sum():+,.0f}")
    r[5].metric("Avg holding", f"{m['Avg Bars Held']:.0f} days")

    c1, c2 = st.columns(2)
    c1.plotly_chart(charts.trade_bars(tr))
    c2.plotly_chart(charts.cumulative_pnl(tr))
    c3, c4 = st.columns(2)
    reasons = tr["Exit Reason"].value_counts()
    c3.plotly_chart(charts.pie(list(reasons.index), list(reasons.values), "Exit reasons"))
    c4.plotly_chart(charts.histogram(tr["P&L %"], "P&L distribution (%)"))

    show = tr.copy()
    show.insert(0, "#", range(1, len(show) + 1))
    show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
    show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
    st.dataframe(show.iloc[::-1].style.map(T.color_style, subset=["P&L %", "P&L $"]).format(
        {"Entry": "{:,.2f}", "Exit": "{:,.2f}", "Shares": "{:,.2f}", "P&L $": "{:+,.2f}", "P&L %": "{:+.2f}%"}),
        hide_index=True, height=420)
    st.download_button("⬇️ Download trades (CSV)", show.to_csv(index=False).encode("utf-8-sig"),
                       f"trades_{cfg['symbol']}.csv", "text/csv")


# =====================================================================
# Navigation + sidebar
# =====================================================================
PAGES = {
    "home": st.Page(page_home, title="Market Overview", icon="🏠", default=True),
    "trending": st.Page(page_trending, title="What's Trending", icon="🔥"),
    "news": st.Page(page_news, title="News", icon="📰"),
    "stock": st.Page(page_stock, title="Stock", icon="📈"),
    "scanner": st.Page(page_scanner, title="Scanner", icon="🔎"),
    "catalyst": st.Page(page_catalyst, title="Catalyst Pro", icon="⚡"),
    "lab": st.Page(page_lab, title="Strategy Lab", icon="🤖"),
    "trades": st.Page(page_trades, title="Trades", icon="📋"),
}
pg = st.navigation({"Markets": [PAGES["home"], PAGES["trending"], PAGES["news"]],
                    "Research": [PAGES["stock"], PAGES["scanner"], PAGES["catalyst"]],
                    "Trading Bot": [PAGES["lab"], PAGES["trades"]]})

with st.sidebar:
    st.markdown(f'<div class="brand"><div class="logo">A</div><div><div class="name">{SITE_NAME}</div>'
                f'<div class="tag-line">US Markets · Trading Bot</div></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status">{T.market_status()}</div>', unsafe_allow_html=True)
    st.markdown("**⭐ Watchlist**")
    wl = data.history_many(tuple(ss.watchlist), "1mo") if ss.watchlist else {}
    for s in ss.watchlist:
        df = wl.get(s)
        a, b = st.columns([1, 1.25])
        if a.button(s, key=f"wl_{s}"):
            open_stock(s)
        if df is not None and len(df) > 1:
            p, pr = df["Close"].iloc[-1], df["Close"].iloc[-2]
            pct = (p / pr - 1) * 100
            b.markdown(f'<div class="wl">{T.fmt_price(p)}<br><span class="{T.cls(pct)}">{pct:+.2f}%</span></div>',
                       unsafe_allow_html=True)
        else:
            b.markdown('<div class="wl muted">—</div>', unsafe_allow_html=True)
    with st.expander("✏️ Edit watchlist"):
        txt = st.text_area("Symbols (comma separated)", ", ".join(ss.watchlist))
        if st.button("Save"):
            ss.watchlist = [x.strip().upper() for x in txt.split(",") if x.strip()]
            st.rerun()
    st.caption("Educational use only · not investment advice.")

pg.run()
