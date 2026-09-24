"""
app.py - A.Alturaifi Pro · US Markets platform (entry point).
Run locally:  streamlit run app.py
"""
import streamlit as st

import data
import p_bot
import p_markets
import p_research
import theme as T
import ui
from i18n import L

SITE_NAME = "A.Alturaifi Pro"
st.set_page_config(page_title=f"{SITE_NAME} · US Markets", page_icon=":material/candlestick_chart:", layout="wide")

ss = st.session_state
ss.setdefault("lang", "en")
if ss.get("lang_ctl"):
    ss.lang = "ar" if ss.lang_ctl == "عربي" else "en"
ss.setdefault("symbol", "AAPL")
ss.setdefault("watchlist", ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "GOOGL", "AMD"])
ss.setdefault("lab_cfg", {"symbol": "AAPL", "period": "2y", "strategy": "SMA Crossover", "params": {},
                          "capital": 10000, "fee": 0.05, "stop": 7.0, "atr": 0.0, "tp": 0.0, "trail": 0.0})
ss.setdefault("acct", {"size": 10000, "risk": 1.0})

st.markdown(T.CSS + (T.RTL_CSS if ss.lang == "ar" else ""), unsafe_allow_html=True)
st.logo(T.LOGO_WORDMARK, icon_image=T.LOGO_ICON, size="large")


def _global_search():
    q = (ss.get("gq") or "").strip()
    if not q:
        return
    res = data.search(q)
    sym = res[0]["symbol"] if res else (q.upper() if len(q) <= 6 else None)
    if sym:
        ss.symbol = sym.upper()
        ss.goto = "stock"
    ss.gq = ""


# ---------------------------------------------------------------- pages (top navigation)
ui.PAGES.update({
    "overview": st.Page(p_markets.page_overview, title=L("Overview", "نظرة عامة"), icon=":material/monitoring:", default=True),
    "heatmap": st.Page(p_markets.page_heatmap, title=L("Heatmap", "الخريطة الحرارية"), icon=":material/grid_view:"),
    "trending": st.Page(p_markets.page_trending, title=L("What's Trending", "الأكثر رواجاً"), icon=":material/local_fire_department:"),
    "news": st.Page(p_markets.page_news, title=L("News", "الأخبار"), icon=":material/newspaper:"),
    "screener": st.Page(p_research.page_screener, title=L("Screener", "فلتر الأسهم"), icon=":material/filter_alt:"),
    "stock": st.Page(p_research.page_stock, title=L("Stock", "السهم"), icon=":material/candlestick_chart:"),
    "scanner": st.Page(p_research.page_scanner, title=L("Scanner", "صائد الفرص"), icon=":material/radar:"),
    "catalyst": st.Page(p_research.page_catalyst, title="Catalyst Pro", icon=":material/bolt:"),
    "lab": st.Page(p_bot.page_lab, title=L("Strategy Lab", "مختبر الاستراتيجيات"), icon=":material/smart_toy:"),
    "trades": st.Page(p_bot.page_trades, title=L("Trades", "الصفقات"), icon=":material/receipt_long:"),
})
pg = st.navigation(list(ui.PAGES.values()), position="top")

if ss.get("goto"):
    ui.goto(ss.pop("goto"))

# ---------------------------------------------------------------- header bar: status · search · language
h1, h2, h3 = st.columns([1.3, 2.6, 0.9], vertical_alignment="center")
h1.markdown(T.market_status(ss.lang == "ar"), unsafe_allow_html=True)
h2.text_input("search", key="gq", on_change=_global_search, label_visibility="collapsed",
              placeholder=L("Search a symbol or company (e.g. Apple, NVDA)…", "ابحث عن سهم أو شركة (مثال: Apple أو NVDA)…"))
h3.segmented_control("Language", ["EN", "عربي"], default="EN", key="lang_ctl", label_visibility="collapsed")

# ---------------------------------------------------------------- sidebar watchlist
with st.sidebar:
    st.markdown(T.sec("star", L("Watchlist", "قائمة المتابعة")), unsafe_allow_html=True)
    wl = data.history_many(tuple(ss.watchlist), "1mo") if ss.watchlist else {}
    for s in ss.watchlist:
        df = wl.get(s)
        a, b = st.columns([1, 1.25])
        if a.button(s, key=f"wl_{s}"):
            ui.open_stock(s)
        if df is not None and len(df) > 1:
            p, pr = df["Close"].iloc[-1], df["Close"].iloc[-2]
            pct = (p / pr - 1) * 100
            b.markdown(f'<div class="wl">{T.fmt_price(p)}<br><span class="{T.cls(pct)}">{pct:+.2f}%</span></div>',
                       unsafe_allow_html=True)
        else:
            b.markdown('<div class="wl muted">—</div>', unsafe_allow_html=True)
    with st.expander(L("Edit watchlist", "تعديل القائمة"), icon=":material/edit:"):
        txt = st.text_area(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), ", ".join(ss.watchlist))
        if st.button(L("Save", "حفظ")):
            ss.watchlist = [x.strip().upper() for x in txt.split(",") if x.strip()]
            st.rerun()

pg.run()
