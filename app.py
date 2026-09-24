"""
app.py - A.Alturaifi Pro · US Markets platform (entry point).
Run locally:  streamlit run app.py
"""
import streamlit as st

import data
import p_academy
import p_bot
import p_markets
import p_research
import theme as T
import ui
from i18n import L

SITE_NAME = "A.Alturaifi Pro"
st.set_page_config(page_title=f"{SITE_NAME} · US Markets", page_icon=":material/candlestick_chart:", layout="wide")

ss = st.session_state
# language: widget state > ?lang= query param (kept by every link on the site) > English
if "lang_ctl" not in ss:
    ss["lang_ctl"] = "عربي" if st.query_params.get("lang") == "ar" else "EN"
ss.lang = "ar" if ss.get("lang_ctl") == "عربي" else ("en" if ss.get("lang_ctl") == "EN" else ss.get("lang", "en"))
ss.setdefault("symbol", "AAPL")
ss.setdefault("watchlist", ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "GOOGL", "AMD"])
ss.setdefault("lab_cfg", {"symbol": "AAPL", "period": "2y", "strategy": "SMA Crossover", "params": {},
                          "capital": 10000, "fee": 0.05, "stop": 7.0, "atr": 0.0, "tp": 0.0, "trail": 0.0})
ss.setdefault("acct", {"size": 10000, "risk": 1.0})

# links like  stock?symbol=NVDA  (heatmap tiles, company chips, tables) open that company
_qs = st.query_params.get("symbol")
if _qs:
    ss.symbol = str(_qs).strip().upper()[:15] or ss.symbol
    del st.query_params["symbol"]

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


# ---------------------------------------------------------------- pages · dropdown menus (Yahoo / TradingView style)
P = ui.PAGES
P.update({
    "overview": st.Page(p_markets.page_overview, title=L("Overview", "نظرة عامة"), icon=":material/monitoring:", url_path="overview", default=True),
    "futures": st.Page(p_markets.page_futures, title=L("Futures", "العقود الآجلة"), icon=":material/update:", url_path="futures"),
    "options": st.Page(p_markets.page_options, title=L("Options", "الخيارات"), icon=":material/tune:", url_path="options"),
    "economy": st.Page(p_markets.page_economy, title=L("Economy", "الاقتصاد"), icon=":material/account_balance:", url_path="economy"),
    "trending": st.Page(p_markets.page_trending, title=L("What's Trending", "الأكثر رواجاً"), icon=":material/local_fire_department:", url_path="trending"),
    "news": st.Page(p_markets.page_news, title=L("News", "الأخبار"), icon=":material/newspaper:", url_path="news"),
    "stock": st.Page(p_research.page_stock, title=L("Stock", "السهم"), icon=":material/candlestick_chart:", url_path="stock"),
    "screener": st.Page(p_research.page_screener, title=L("Screener", "فلتر الأسهم"), icon=":material/filter_alt:", url_path="screener"),
    "academy": st.Page(p_academy.page_academy, title=L("Courses", "الدورات"), icon=":material/school:", url_path="academy"),
    "glossary": st.Page(p_academy.page_glossary, title=L("Glossary", "قاموس المصطلحات"), icon=":material/menu_book:", url_path="glossary"),
    "auto": st.Page(p_bot.page_autotrader, title=L("Auto Trader", "التداول الآلي"), icon=":material/rocket_launch:", url_path="auto-trader"),
    "scanner": st.Page(p_research.page_scanner, title=L("Scanner", "صائد الفرص"), icon=":material/radar:", url_path="scanner"),
    "catalyst": st.Page(p_research.page_catalyst, title="Catalyst Pro", icon=":material/bolt:", url_path="catalyst"),
    "lab": st.Page(p_bot.page_lab, title=L("Strategy Lab", "مختبر الاستراتيجيات"), icon=":material/smart_toy:", url_path="strategy-lab"),
    "trades": st.Page(p_bot.page_trades, title=L("Trade Journal", "سجل الصفقات"), icon=":material/receipt_long:", url_path="trades"),
})
pg = st.navigation({
    L("Markets", "الأسواق"): [P["overview"], P["futures"], P["options"], P["economy"]],
    L("Discover", "اكتشف"): [P["trending"], P["news"]],
    L("Research", "الأبحاث"): [P["stock"], P["screener"]],
    L("Academy", "الأكاديمية"): [P["academy"], P["glossary"]],
    L("Trading Bot", "بوت التداول"): [P["auto"], P["scanner"], P["catalyst"], P["lab"], P["trades"]],
}, position="top")

if ss.get("goto"):
    ui.goto(ss.pop("goto"))

# arriving at the Academy from another page shows the course catalog (unless a course link was opened)
_cur = getattr(pg, "url_path", "")
if ss.get("_page") != _cur:
    if _cur == "academy" and ss.get("_page") is not None and not st.query_params.get("course"):
        ss.pop("course", None)
    ss["_page"] = _cur

# ---------------------------------------------------------------- header bar: status · search · language
h1, h2, h3 = st.columns([1.3, 2.6, 0.9], vertical_alignment="center")
h1.markdown(T.market_status(ss.lang == "ar"), unsafe_allow_html=True)
h2.text_input("search", key="gq", on_change=_global_search, label_visibility="collapsed",
              placeholder=L("Search a symbol or company (e.g. Apple, NVDA)…", "ابحث عن سهم أو شركة (مثال: Apple أو NVDA)…"))
h3.segmented_control("Language", ["EN", "عربي"], key="lang_ctl", label_visibility="collapsed")

# ---------------------------------------------------------------- sidebar watchlist
with st.sidebar:
    st.markdown(T.sec("star", L("Watchlist", "قائمة المتابعة")), unsafe_allow_html=True)
    wl = data.history_many(tuple(ss.watchlist), "1mo") if ss.watchlist else {}
    for s in ss.watchlist:
        df = wl.get(s)
        a, b = st.columns([1.3, 1])
        if a.button(s, key=f"wl_{s}", width="stretch"):
            ui.open_stock(s)
        if df is not None and len(df) > 1:
            p, pr = df["Close"].iloc[-1], df["Close"].iloc[-2]
            pct = (p / pr - 1) * 100
            b.markdown(f'<div class="wl">{T.fmt_price(p)}<br>{T.pill(pct)}</div>', unsafe_allow_html=True)
        else:
            b.markdown('<div class="wl muted">—</div>', unsafe_allow_html=True)
    with st.expander(L("Edit watchlist", "تعديل القائمة"), icon=":material/edit:"):
        txt = st.text_area(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), ", ".join(ss.watchlist))
        if st.button(L("Save", "حفظ")):
            ss.watchlist = [x.strip().upper() for x in txt.split(",") if x.strip()]
            st.rerun()

# ---------------------------------------------------------------- page (one error never takes the whole site down)
try:
    pg.run()
except Exception as e:  # Streamlit's own rerun / page-switch signals are not Exceptions, so they pass through
    st.error(L("Something went wrong on this page. Please refresh, or try again in a minute.",
               "حدث خطأ في هذه الصفحة. حدّث الصفحة أو حاول بعد دقيقة."), icon=":material/error:")
    with st.expander(L("Technical details", "تفاصيل فنية")):
        st.exception(e)
