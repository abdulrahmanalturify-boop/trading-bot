"""
app.py: واجهة الموقع (ستايل قريب من Webull)
الصفحات: السوق والتشارت · صائد الفرص · المحفزات (Catalysts) · بوت التداول · الصفقات
"""
import html
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

import core

# ============ الألوان (ستايل Webull الداكن) ============
BG, CARD, BORDER = "#0B0E14", "#151A23", "#232A36"
TEXT, MUTED = "#E6E8EB", "#8A93A3"
UP, DOWN, ACCENT = "#00C087", "#FF4D4F", "#2F7BFF"

st.set_page_config(page_title="منصتي للتداول", page_icon="📈", layout="wide")

st.markdown(f"""
<style>
.block-container {{padding-top: 1.2rem; padding-bottom: 2rem;}}
.stMarkdown, .stAlert, h1, h2, h3, h4, [data-testid="stMetricLabel"], [data-testid="stCaptionContainer"] {{
  direction: rtl; text-align: right;
}}
[data-testid="stMetric"] {{
  background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 10px 14px;
}}
.card {{background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:14px 16px; margin-bottom:10px;}}
.up {{color:{UP};}} .down {{color:{DOWN};}} .muted {{color:{MUTED};}}
.q-name {{color:{MUTED}; font-size:1rem; direction:ltr; text-align:left;}}
.q-price {{font-size:2.4rem; font-weight:700; direction:ltr; text-align:left; line-height:1.2;}}
.q-chg {{font-size:1.05rem; font-weight:600; direction:ltr; text-align:left;}}
.stats {{display:grid; grid-template-columns:repeat(auto-fit,minmax(115px,1fr)); gap:8px; margin:6px 0 4px;}}
.stat {{background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:8px 10px; direction:ltr;}}
.stat .l {{color:{MUTED}; font-size:.75rem;}} .stat .v {{font-weight:600; font-size:.95rem;}}
.news {{background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:12px 14px; margin-bottom:8px; direction:ltr; text-align:left;}}
.news a {{color:{TEXT}; text-decoration:none; font-weight:600;}} .news a:hover {{color:{ACCENT};}}
.news .meta {{color:{MUTED}; font-size:.8rem; margin-top:4px;}}
.tag {{background:{ACCENT}22; color:{ACCENT}; border-radius:4px; padding:1px 6px; font-size:.75rem; margin-right:6px;}}
.wl-price {{direction:ltr; text-align:right; font-size:.85rem; padding-top:8px;}}
</style>
""", unsafe_allow_html=True)


# ============ الحالة المشتركة بين الصفحات ============
ss = st.session_state
ss.setdefault("active_symbol", "AAPL")
ss.setdefault("watchlist", ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "META", "BTC-USD", "ETH-USD"])
ss.setdefault("bot_cfg", {"symbol": "AAPL", "period": "2y", "short": 20, "long": 50,
                          "capital": 10000, "fee": 0.1})


# ============ تحميل البيانات (مع حفظ مؤقت عشان السرعة) ============
@st.cache_data(ttl=900, show_spinner=False)
def load_daily(symbol, period="2y"):
    try:
        df = yf.download(symbol, period=period, interval="1d", auto_adjust=True, progress=False)
        return core.flatten(df)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def load_intraday(symbol, period, interval):
    try:
        df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
        return core.flatten(df)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=900, show_spinner=False)
def load_many(symbols: tuple, period="1y"):
    try:
        df = yf.download(list(symbols), period=period, interval="1d", auto_adjust=True,
                         progress=False, threads=True)
        return core.split_multi(df, list(symbols))
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def load_news(symbol):
    try:
        return core.parse_news(yf.Ticker(symbol).news)
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def load_catalyst(symbol):
    t = yf.Ticker(symbol)
    out = {"earnings": None, "ratings": pd.DataFrame()}
    try:
        out["earnings"] = core.earnings_date(t.calendar)
    except Exception:
        pass
    try:
        out["ratings"] = core.recent_ratings(t.upgrades_downgrades, days=30)
    except Exception:
        pass
    return out


@st.cache_data(ttl=86400, show_spinner=False)
def load_profile(symbol):
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        info = {}
    return {
        "name": info.get("shortName") or info.get("longName") or symbol,
        "market_cap": info.get("marketCap"),
        "pe": info.get("trailingPE"),
        "sector": info.get("sector") or "",
        "currency": info.get("currency") or currency_of(symbol),
    }


def currency_of(symbol):
    return "SAR" if symbol.endswith(".SR") else "USD"


# ============ أدوات مساعدة للعرض ============
def pct_html(v):
    cls = "up" if v >= 0 else "down"
    return f'<span class="{cls}">{v:+.2f}%</span>'


def color_pct(v):
    try:
        return f"color: {UP}" if v > 0 else (f"color: {DOWN}" if v < 0 else "")
    except TypeError:
        return ""


def style_layout(fig, height):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=BG, height=height,
        margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
        legend=dict(orientation="h", y=1.04, x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis_rangeslider_visible=False, font=dict(color=TEXT),
    )
    fig.update_yaxes(gridcolor=BORDER, side="right", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


def price_chart(df, overlays, lower, intraday):
    fmt = "%m-%d %H:%M" if intraday else "%Y-%m-%d"
    x = df.index.strftime(fmt)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        row_heights=[0.62, 0.15, 0.23])
    fig.add_trace(go.Candlestick(
        x=x, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="السعر",
        increasing_line_color=UP, decreasing_line_color=DOWN,
        increasing_fillcolor=UP, decreasing_fillcolor=DOWN, showlegend=False), row=1, col=1)

    colors = {"SMA20": "#F5C542", "SMA50": ACCENT, "SMA200": "#C77DFF"}
    for name in overlays:
        if name in df and df[name].notna().any():
            fig.add_trace(go.Scatter(x=x, y=df[name], name=name, mode="lines",
                                     line=dict(width=1.4, color=colors.get(name))), row=1, col=1)

    if "Volume" in df:
        vcol = [UP if c >= o else DOWN for o, c in zip(df["Open"], df["Close"])]
        fig.add_trace(go.Bar(x=x, y=df["Volume"], marker_color=vcol, name="الحجم",
                             showlegend=False, opacity=0.7), row=2, col=1)

    if lower == "RSI":
        fig.add_trace(go.Scatter(x=x, y=df["RSI"], name="RSI", line=dict(color="#F5C542", width=1.3)),
                      row=3, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color=DOWN, row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color=UP, row=3, col=1)
    else:
        hist = df["MACD"] - df["MACD_signal"]
        fig.add_trace(go.Bar(x=x, y=hist, name="Hist", showlegend=False,
                             marker_color=[UP if h >= 0 else DOWN for h in hist]), row=3, col=1)
        fig.add_trace(go.Scatter(x=x, y=df["MACD"], name="MACD", line=dict(color=ACCENT, width=1.3)),
                      row=3, col=1)
        fig.add_trace(go.Scatter(x=x, y=df["MACD_signal"], name="Signal",
                                 line=dict(color="#F5C542", width=1.3)), row=3, col=1)

    style_layout(fig, 660)
    fig.update_xaxes(type="category", nticks=8)
    return fig


def news_cards(items, limit=15, tag_key=None):
    if not items:
        st.info("ما فيه أخبار متوفرة حالياً.")
        return
    for n in items[:limit]:
        tag = f'<span class="tag">{html.escape(n[tag_key])}</span>' if tag_key else ""
        summary = html.escape(n["summary"][:220]) + ("…" if len(n["summary"]) > 220 else "")
        st.markdown(
            f'<div class="news">{tag}<a href="{html.escape(n["link"])}" target="_blank">'
            f'{html.escape(n["title"])}</a>'
            f'<div class="meta">{html.escape(n["source"])} · {core.time_ago(n["time"])}</div>'
            f'<div class="muted" style="font-size:.85rem;margin-top:4px">{summary}</div></div>',
            unsafe_allow_html=True)


def open_symbol(symbol):
    ss.active_symbol = symbol
    st.switch_page(market_page)


# =====================================================================
# صفحة 1: السوق والتشارت
# =====================================================================
TIMEFRAMES = {"1D": ("5d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "60m"),
              "3M": 63, "6M": 126, "1Y": 252, "5Y": ("5y", "1wk")}


def page_market():
    c1, c2 = st.columns([1, 2])
    sym = c1.text_input("🔍 ابحث عن رمز", value=ss.active_symbol,
                        help="أمثلة: AAPL, TSLA, BTC-USD, 2222.SR").strip().upper()
    if sym:
        ss.active_symbol = sym
    tf = c2.radio("الفترة", list(TIMEFRAMES), index=4, horizontal=True)

    with st.spinner("جاري التحميل..."):
        daily = load_daily(sym, "5y" if tf == "5Y" else "2y")
    if daily.empty or len(daily) < 2:
        st.error(f"ما لقيت بيانات للرمز {sym}. تأكد إنه مكتوب صح (الأسهم السعودية تنتهي بـ .SR).")
        return

    prof = load_profile(sym)
    q = core.quote_from_daily(daily)
    cls = "up" if q["change"] >= 0 else "down"
    st.markdown(
        f'<div class="q-name">{html.escape(prof["name"])} · {sym} · {prof["currency"]}</div>'
        f'<div class="q-price">{q["price"]:,.2f}</div>'
        f'<div class="q-chg {cls}">{q["change"]:+,.2f} ({q["change_pct"]:+.2f}%)'
        f'<span class="muted" style="font-weight:400"> · {q["date"]:%Y-%m-%d}</span></div>',
        unsafe_allow_html=True)

    stats = [("Open", f'{q["open"]:,.2f}'), ("High", f'{q["high"]:,.2f}'), ("Low", f'{q["low"]:,.2f}'),
             ("Volume", core.fmt_big(q["volume"])), ("Avg Vol (20D)", core.fmt_big(q["avg_volume"])),
             ("52W High", f'{q["high_52w"]:,.2f}'), ("52W Low", f'{q["low_52w"]:,.2f}'),
             ("Market Cap", core.fmt_big(prof["market_cap"])),
             ("P/E", f'{prof["pe"]:.1f}' if prof["pe"] else "—")]
    st.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><div class="l">{l}</div><div class="v">{v}</div></div>' for l, v in stats)
        + "</div>", unsafe_allow_html=True)

    tab_chart, tab_news, tab_cat = st.tabs(["📈 التشارت", "📰 الأخبار", "⚡ المحفزات"])

    with tab_chart:
        o1, o2 = st.columns([3, 1])
        overlays = o1.multiselect("المؤشرات على السعر", ["SMA20", "SMA50", "SMA200"],
                                  default=["SMA20", "SMA50"])
        lower = o2.radio("المؤشر السفلي", ["RSI", "MACD"], horizontal=True)

        spec = TIMEFRAMES[tf]
        if isinstance(spec, int):  # فترات يومية: نحسب المؤشرات على تاريخ أطول ثم نقص
            df = core.add_indicators(daily).tail(spec)
            intraday = False
        else:
            raw = load_intraday(sym, *spec)
            if raw.empty:
                st.warning("البيانات اللحظية مو متوفرة لهالرمز، جرّب فترة 3M أو أطول.")
                return
            df = core.add_indicators(raw)
            if tf == "1D":
                df = df[df.index.date == df.index[-1].date()]
            intraday = tf in ("1D", "5D", "1M")
        st.plotly_chart(price_chart(df, overlays, lower, intraday))

        last = core.add_indicators(daily).iloc[-1]
        trend = "صاعد 🟢" if last["SMA20"] > last["SMA50"] else "هابط 🔴"
        st.caption(f"الاتجاه (متوسط 20 مقابل 50): {trend} · RSI اليوم: {last['RSI']:.0f}")

        if st.button("➕ أضف لقائمة المتابعة") and sym not in ss.watchlist:
            ss.watchlist.append(sym)
            st.rerun()

    with tab_news:
        news_cards(load_news(sym))

    with tab_cat:
        cat = load_catalyst(sym)
        a, b, c = st.columns(3)
        if cat["earnings"] is not None:
            days = (cat["earnings"].normalize() - pd.Timestamp.now().normalize()).days
            a.metric("📅 إعلان الأرباح القادم", f'{cat["earnings"]:%Y-%m-%d}', f"بعد {days} يوم",
                     delta_color="off")
        else:
            a.metric("📅 إعلان الأرباح القادم", "—")
        vr = q["volume"] / q["avg_volume"] if q["avg_volume"] else 0
        b.metric("🔥 الحجم مقارنة بالمتوسط", f"×{vr:.1f}")
        b_news = [n for n in load_news(sym) if pd.notna(n["time"])
                  and (pd.Timestamp.now(tz="UTC") - n["time"]).days < 1]
        c.metric("📰 أخبار آخر 24 ساعة", len(b_news))
        st.markdown("#### تحركات المحللين (آخر 30 يوم)")
        if cat["ratings"].empty:
            st.info("ما فيه ترقيات أو تخفيضات من المحللين آخر 30 يوم.")
        else:
            st.dataframe(cat["ratings"])


# =====================================================================
# صفحة 2: صائد الفرص (نتائج بحث البوت)
# =====================================================================
def page_scanner():
    st.title("🔎 صائد الفرص")
    st.caption("البوت يمر على قائمة رموز ويطلع اللي انطبقت عليها الشروط اليوم. "
               "النقاط = مجموع الإشارات الإيجابية ناقص السلبية. هذي إشارات فنية، مو ضمان ربح.")

    options = list(core.WATCHLISTS) + ["قائمة المتابعة", "رموز مخصصة"]
    c1, c2 = st.columns([1, 2])
    choice = c1.selectbox("وين يدوّر البوت؟", options)
    if choice == "قائمة المتابعة":
        symbols = ss.watchlist
    elif choice == "رموز مخصصة":
        txt = c2.text_input("اكتب الرموز مفصولة بفاصلة", "AAPL, TSLA, NVDA, 2222.SR")
        symbols = [s.strip().upper() for s in txt.split(",") if s.strip()]
    else:
        symbols = core.WATCHLISTS[choice]
        c2.caption(f"{len(symbols)} رمز: " + ", ".join(symbols))

    if st.button("🤖 ابدأ البحث", type="primary"):
        with st.spinner(f"البوت يفحص {len(symbols)} رمز..."):
            data = load_many(tuple(symbols), "1y")
            ss.scan_results = core.scan(data)
            ss.scan_meta = {"list": choice, "time": datetime.now(), "count": len(data)}

    res = ss.get("scan_results")
    if res is None:
        st.info("اختر القائمة واضغط **ابدأ البحث**.")
        return
    if res.empty:
        st.warning("ما قدرت أحمّل بيانات لهالرموز. جرّب مرة ثانية بعد شوي.")
        return

    meta = ss.scan_meta
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("رموز تم فحصها", meta["count"])
    m2.metric("فرص (نقاط 2+)", int((res["النقاط"] >= 2).sum()))
    m3.metric("أعلى نقاط", f'{res.iloc[0]["الرمز"]} ({res.iloc[0]["النقاط"]})')
    m4.metric("وقت البحث", f'{meta["time"]:%H:%M}')

    lo, hi = int(res["النقاط"].min()), int(res["النقاط"].max())
    min_score = st.slider("أقل عدد نقاط", lo, hi, max(lo, min(2, hi))) if hi > lo else lo
    view = res[res["النقاط"] >= min_score]
    st.dataframe(
        view.style.map(color_pct, subset=["التغير %"]).format(
            {"السعر": "{:,.2f}", "التغير %": "{:+.2f}%", "RSI": "{:.0f}", "الحجم ×": "{:.1f}"},
            na_rep="—"), hide_index=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    pick = c1.selectbox("اختر رمز", view["الرمز"].tolist() or res["الرمز"].tolist())
    if c2.button("📈 افتح التشارت"):
        open_symbol(pick)
    if c3.button("⚡ شوف المحفزات"):
        st.switch_page(catalyst_page)


# =====================================================================
# صفحة 3: المحفزات (Catalysts)
# =====================================================================
def page_catalysts():
    st.title("⚡ المحفزات (Catalysts)")
    st.caption("الأحداث اللي ممكن تحرّك السعر: إعلانات الأرباح، تقييمات المحللين، الأخبار، والحجم الغير طبيعي.")

    res = ss.get("scan_results")
    default = (res[res["النقاط"] > 0]["الرمز"].head(5).tolist()
               if res is not None and not res.empty else ss.watchlist[:5])
    pool = sorted(set(default) | set(ss.watchlist)
                  | (set(res["الرمز"]) if res is not None and not res.empty else set()))
    symbols = st.multiselect("الرموز (أقصى شي 10)", pool, default=default, max_selections=10)
    if not symbols:
        st.info("اختر رمز واحد على الأقل.")
        return

    with st.spinner("جاري جمع المحفزات..."):
        cats = {s: load_catalyst(s) for s in symbols}
        news = {s: load_news(s) for s in symbols}
        daily = load_many(tuple(symbols), "3mo")

    t1, t2, t3, t4 = st.tabs(["📅 الأرباح", "📊 المحللين", "📰 الأخبار", "🔥 الحجم"])

    with t1:
        rows = []
        for s, c in cats.items():
            if c["earnings"] is not None:
                days = (c["earnings"].normalize() - pd.Timestamp.now().normalize()).days
                rows.append({"الرمز": s, "موعد الأرباح": c["earnings"].date(), "بعد (يوم)": days,
                             "تنبيه": "⚠️ قريب" if 0 <= days <= 14 else ""})
        if rows:
            st.dataframe(pd.DataFrame(rows).sort_values("بعد (يوم)"), hide_index=True)
            st.caption("السعر يتحرك بقوة يوم إعلان الأرباح، صعود أو نزول.")
        else:
            st.info("ما فيه مواعيد أرباح متوفرة (الكريبتو ما عندها أرباح).")

    with t2:
        frames = []
        for s, c in cats.items():
            r = c["ratings"]
            if not r.empty:
                r = r.reset_index().rename(columns={r.index.name or "index": "التاريخ"})
                r.insert(0, "الرمز", s)
                frames.append(r)
        if frames:
            all_r = pd.concat(frames, ignore_index=True)
            if "Action" in all_r:
                all_r["Action"] = all_r["Action"].map(
                    {"up": "⬆️ ترقية", "down": "⬇️ تخفيض", "init": "🆕 بداية تغطية",
                     "main": "➡️ إبقاء", "reit": "➡️ تأكيد"}).fillna(all_r["Action"])
            st.dataframe(all_r, hide_index=True)
        else:
            st.info("ما فيه تحركات للمحللين آخر 30 يوم على هالرموز.")

    with t3:
        feed = [{**n, "sym": s} for s, items in news.items() for n in items]
        feed.sort(key=lambda n: n["time"] if pd.notna(n["time"]) else pd.Timestamp("1970-01-01", tz="UTC"),
                  reverse=True)
        news_cards(feed, limit=30, tag_key="sym")

    with t4:
        rows = []
        for s, df in daily.items():
            if "Volume" in df and len(df) > 21 and df["Volume"].tail(20).mean() > 0:
                ratio = df["Volume"].iloc[-1] / df["Volume"].iloc[-21:-1].mean()
                chg = (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100
                rows.append({"الرمز": s, "الحجم ×": ratio, "التغير %": chg,
                             "ملاحظة": "🔥 غير طبيعي" if ratio >= 2 else ""})
        if rows:
            vdf = pd.DataFrame(rows).sort_values("الحجم ×", ascending=False)
            st.dataframe(vdf.style.map(color_pct, subset=["التغير %"]).format(
                {"الحجم ×": "×{:.1f}", "التغير %": "{:+.2f}%"}), hide_index=True)
        else:
            st.info("ما فيه بيانات حجم.")


# =====================================================================
# صفحة 4: بوت التداول (اختبار الاستراتيجية)
# =====================================================================
def bot_settings():
    cfg = ss.bot_cfg
    with st.container(border=True):
        c = st.columns(6)
        cfg["symbol"] = c[0].text_input("الرمز", cfg["symbol"]).strip().upper() or "AAPL"
        periods = ["6mo", "1y", "2y", "5y", "10y"]
        cfg["period"] = c[1].selectbox("المدة", periods, index=periods.index(cfg["period"]))
        cfg["short"] = c[2].number_input("المتوسط القصير", 5, 100, cfg["short"])
        cfg["long"] = c[3].number_input("المتوسط الطويل", 10, 300, cfg["long"])
        cfg["capital"] = c[4].number_input("رأس المال $", 100, 10_000_000, cfg["capital"], step=1000)
        cfg["fee"] = c[5].number_input("العمولة %", 0.0, 2.0, float(cfg["fee"]), step=0.05)
    return cfg


def run_bot(cfg):
    if cfg["short"] >= cfg["long"]:
        st.error("المتوسط القصير لازم يكون أصغر من الطويل.")
        return None
    prices = load_daily(cfg["symbol"], cfg["period"])
    if prices.empty:
        st.error(f"ما لقيت بيانات للرمز {cfg['symbol']}.")
        return None
    data = core.run_backtest(prices, cfg["short"], cfg["long"], cfg["capital"], cfg["fee"] / 100)
    if len(data) < 2:
        st.error("البيانات قليلة على هالمتوسطات. اختر مدة أطول.")
        return None
    return data


def page_bot():
    st.title("🤖 بوت التداول")
    st.caption("استراتيجية تقاطع المتوسطات: يشتري إذا صار القصير فوق الطويل، ويبيع إذا نزل تحته.")
    cfg = bot_settings()
    data = run_bot(cfg)
    if data is None:
        return

    last = data.iloc[-1]
    date = data.index[-1].date()
    if last["Trade"] == 1:
        st.success(f"🟢 {date}: إشارة شراء جديدة")
    elif last["Trade"] == -1:
        st.error(f"🔴 {date}: إشارة بيع جديدة")
    elif last["Position"] == 1:
        st.info(f"{date}: البوت داخل السوق (المتوسط القصير فوق الطويل)")
    else:
        st.warning(f"{date}: البوت خارج السوق (المتوسط القصير تحت الطويل)")

    cap = cfg["capital"]
    bot_final, hold_final = data["Bot_Equity"].iloc[-1], data["Hold_Equity"].iloc[-1]
    peak = data["Bot_Equity"].cummax()
    mdd = ((data["Bot_Equity"] - peak) / peak).min() * 100
    m = st.columns(4)
    m[0].metric("نتيجة البوت", f"${bot_final:,.0f}", f"{(bot_final / cap - 1) * 100:+.1f}%")
    m[1].metric("الشراء والاحتفاظ", f"${hold_final:,.0f}", f"{(hold_final / cap - 1) * 100:+.1f}%")
    m[2].metric("أكبر هبوط", f"{mdd:.1f}%")
    m[3].metric("وقت داخل السوق", f"{data['Position'].mean() * 100:.0f}%")

    buys, sells = data[data["Trade"] == 1], data[data["Trade"] == -1]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.6, 0.4],
                        subplot_titles=(f"{cfg['symbol']}: السعر والإشارات", "قيمة المحفظة ($)"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="السعر", line=dict(color=MUTED, width=1)), 1, 1)
    fig.add_trace(go.Scatter(x=data.index, y=data["SMA_short"], name=f"SMA {cfg['short']}",
                             line=dict(color="#F5C542", width=1.4)), 1, 1)
    fig.add_trace(go.Scatter(x=data.index, y=data["SMA_long"], name=f"SMA {cfg['long']}",
                             line=dict(color=ACCENT, width=1.4)), 1, 1)
    fig.add_trace(go.Scatter(x=buys.index, y=buys["Close"], mode="markers", name="شراء",
                             marker=dict(symbol="triangle-up", size=12, color=UP)), 1, 1)
    fig.add_trace(go.Scatter(x=sells.index, y=sells["Close"], mode="markers", name="بيع",
                             marker=dict(symbol="triangle-down", size=12, color=DOWN)), 1, 1)
    fig.add_trace(go.Scatter(x=data.index, y=data["Bot_Equity"], name="البوت",
                             line=dict(color=UP, width=1.8)), 2, 1)
    fig.add_trace(go.Scatter(x=data.index, y=data["Hold_Equity"], name="شراء واحتفاظ",
                             line=dict(color=MUTED, width=1.3, dash="dot")), 2, 1)
    st.plotly_chart(style_layout(fig, 640))

    if st.button("📋 شوف كل الصفقات"):
        st.switch_page(trades_page)


# =====================================================================
# صفحة 5: الصفقات
# =====================================================================
def page_trades():
    st.title("📋 الصفقات")
    st.caption("كل صفقة سواها البوت: متى دخل ومتى طلع وكم ربح أو خسر. "
               "كل صفقة تستخدم كامل رصيد المحفظة وقتها.")
    cfg = bot_settings()
    data = run_bot(cfg)
    if data is None:
        return

    trades = core.extract_trades(data, cfg["capital"], cfg["fee"] / 100)
    if trades.empty:
        st.info("البوت ما سوى أي صفقة في هالفترة.")
        return
    s = core.trade_stats(trades)

    open_t = trades[trades["الحالة"] == "مفتوحة"]
    if not open_t.empty:
        t = open_t.iloc[0]
        cls = "up" if t["الربح %"] >= 0 else "down"
        st.markdown(
            f'<div class="card">🟢 <b>صفقة مفتوحة الحين</b> · دخل {t["الدخول"]:%Y-%m-%d} بسعر '
            f'{t["سعر الدخول"]:,.2f} · السعر الحالي {t["سعر الخروج"]:,.2f} · '
            f'<span class="{cls}">{t["الربح %"]:+.2f}%</span> · من {t["الأيام"]} يوم</div>',
            unsafe_allow_html=True)

    if s["count"]:
        m = st.columns(4)
        m[0].metric("صفقات مغلقة", s["count"])
        m[1].metric("نسبة النجاح", f'{s["win_rate"]:.0f}%')
        m[2].metric("متوسط الربح", f'{s["avg_win"]:+.2f}%')
        m[3].metric("متوسط الخسارة", f'{s["avg_loss"]:+.2f}%')
        m = st.columns(4)
        pf = "∞" if s["profit_factor"] == float("inf") else f'{s["profit_factor"]:.2f}'
        m[0].metric("معامل الربح", pf, help="مجموع الأرباح ÷ مجموع الخسائر. فوق 1 يعني رابح.")
        m[1].metric("أفضل صفقة", f'{s["best"]:+.2f}%')
        m[2].metric("أسوأ صفقة", f'{s["worst"]:+.2f}%')
        m[3].metric("متوسط المدة", f'{s["avg_days"]:.0f} يوم')

    fig = go.Figure(go.Bar(
        x=[f"#{i + 1}" for i in range(len(trades))], y=trades["الربح %"],
        marker_color=[UP if v >= 0 else DOWN for v in trades["الربح %"]],
        text=[f"{v:+.1f}%" for v in trades["الربح %"]], textposition="outside",
        hovertext=[f'{a:%Y-%m-%d} → {b:%Y-%m-%d}' for a, b in zip(trades["الدخول"], trades["الخروج"])]))
    fig.update_layout(title="ربح/خسارة كل صفقة (%)")
    st.plotly_chart(style_layout(fig, 360))

    show = trades.copy()
    show.insert(0, "#", range(1, len(show) + 1))
    show["الدخول"] = show["الدخول"].dt.date
    show["الخروج"] = show["الخروج"].dt.date
    st.dataframe(
        show.iloc[::-1].style.map(color_pct, subset=["الربح %", "الربح $"]).format(
            {"سعر الدخول": "{:,.2f}", "سعر الخروج": "{:,.2f}", "الربح %": "{:+.2f}%", "الربح $": "{:+,.0f}"}), hide_index=True)

    st.download_button("⬇️ نزّل الصفقات (CSV)", show.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"trades_{cfg['symbol']}.csv", mime="text/csv")


# =====================================================================
# التنقل + قائمة المتابعة الجانبية
# =====================================================================
market_page = st.Page(page_market, title="السوق والتشارت", icon="📈", default=True)
scanner_page = st.Page(page_scanner, title="صائد الفرص", icon="🔎")
catalyst_page = st.Page(page_catalysts, title="المحفزات", icon="⚡")
bot_page = st.Page(page_bot, title="بوت التداول", icon="🤖")
trades_page = st.Page(page_trades, title="الصفقات", icon="📋")

pg = st.navigation({"السوق": [market_page],
                    "البوت": [scanner_page, catalyst_page, bot_page, trades_page]})

with st.sidebar:
    st.markdown("### ⭐ قائمة المتابعة")
    wl_data = load_many(tuple(ss.watchlist), "1mo") if ss.watchlist else {}
    for s in ss.watchlist:
        df = wl_data.get(s)
        a, b = st.columns([1, 1.3])
        if a.button(s, key=f"wl_{s}"):
            open_symbol(s)
        if df is not None and len(df) > 1:
            p, chg = df["Close"].iloc[-1], (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100
            b.markdown(f'<div class="wl-price">{p:,.2f}<br>{pct_html(chg)}</div>', unsafe_allow_html=True)
        else:
            b.markdown('<div class="wl-price muted">—</div>', unsafe_allow_html=True)
    with st.expander("✏️ تعديل القائمة"):
        txt = st.text_area("الرموز مفصولة بفاصلة", ", ".join(ss.watchlist))
        if st.button("حفظ"):
            ss.watchlist = [x.strip().upper() for x in txt.split(",") if x.strip()]
            st.rerun()
    st.caption("⚠️ للتعلّم فقط، مو نصيحة استثمارية.")

pg.run()
