"""
p_research.py - Stock · Screener (Finviz-style) · Scanner · Catalyst Pro
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
import ui
import universe as U
from i18n import L, is_ar, sector_name, sig

ss = st.session_state


def spy_daily():
    return data.history("SPY", "2y")


# =====================================================================
# STOCK
# =====================================================================
TF = {"1D": ("5d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "60m"), "3M": 63, "6M": 126, "YTD": "ytd",
      "1Y": 252, "5Y": ("5y", "1wk"), "MAX": ("max", "1mo")}
CHART_TYPES = {"Candles": "شموع", "Heikin Ashi": "هايكن آشي", "OHLC": "أعمدة OHLC", "Line": "خط", "Area": "مساحة"}


def quote_header(sym, daily, inf):
    last, prev = daily["Close"].iloc[-1], daily["Close"].iloc[-2]
    chg, pct = last - prev, (last / prev - 1) * 100
    name = inf.get("longName") or inf.get("shortName") or U.name_of(sym)
    exch = inf.get("fullExchangeName") or inf.get("exchange") or ""
    sec = inf.get("sector") or (U.sector_of(sym) if sym in U.STOCKS else "")
    ind = inf.get("industry") or (U.industry_of(sym) if sym in U.STOCKS else "")
    badges = (T.badge(sector_name(sec), "acc", "category") if sec else "") + (T.badge(ind, "gold", "factory") if ind else "")
    ui.html(f'<div class="q-name">{T.esc(name)} · <b>{sym}</b> · {T.esc(exch)} {badges}</div>'
            f'<div><span class="q-price">{T.fmt_price(last)}</span> <span class="muted">{inf.get("currency", "USD")}</span></div>'
            f'<div><span class="q-chg {T.cls(chg)}">{chg:+,.2f} ({pct:+.2f}%)</span> '
            f'<span class="muted" style="font-size:.85rem">· {daily.index[-1]:%Y-%m-%d} · </span>{T.market_status(is_ar())}</div>')
    return last


def key_stats(daily, inf):
    last = daily["Close"].iloc[-1]
    yr = daily.tail(252)
    lo52, hi52 = yr["Low"].min(), yr["High"].max()
    div = inf.get("dividendRate")

    def f2(k):
        return f"{inf[k]:.2f}" if isinstance(inf.get(k), (int, float)) else "—"
    stats = [
        (L("Open", "الافتتاح"), T.fmt_price(daily["Open"].iloc[-1])), (L("High", "الأعلى"), T.fmt_price(daily["High"].iloc[-1])),
        (L("Low", "الأدنى"), T.fmt_price(daily["Low"].iloc[-1])), (L("Prev close", "الإغلاق السابق"), T.fmt_price(daily["Close"].iloc[-2])),
        (L("Volume", "الحجم"), T.fmt_big(daily["Volume"].iloc[-1])), (L("Avg vol (3M)", "متوسط الحجم"), T.fmt_big(inf.get("averageVolume"))),
        (L("Market cap", "القيمة السوقية"), T.fmt_big(inf.get("marketCap"))), (L("P/E (TTM)", "مكرر الربحية"), f2("trailingPE")),
        (L("Fwd P/E", "المكرر المستقبلي"), f2("forwardPE")), (L("EPS (TTM)", "ربحية السهم"), f2("trailingEps")),
        (L("Beta", "بيتا"), f2("beta")), (L("Div yield", "عائد التوزيعات"), f"{div / last * 100:.2f}%" if div else "—"),
        (L("Short % float", "البيع على المكشوف"), f"{inf['shortPercentOfFloat'] * 100:.1f}%" if inf.get("shortPercentOfFloat") else "—"),
        (L("Shares out", "الأسهم القائمة"), T.fmt_big(inf.get("sharesOutstanding"))),
    ]
    pos = (last - lo52) / (hi52 - lo52) * 100 if hi52 > lo52 else 50
    ui.html('<div class="stats">' + "".join(f'<div class="stat"><div class="l">{l}</div><div class="v">{v}</div></div>'
                                            for l, v in stats) + "</div>"
            f'<div class="muted" style="font-size:.75rem;display:flex;justify-content:space-between;direction:ltr">'
            f'<span>52W Low {T.fmt_price(lo52)}</span><span>52W High {T.fmt_price(hi52)}</span></div>'
            f'<div class="range" style="direction:ltr"><div class="dot" style="left:calc({pos:.1f}% - 8px)"></div></div>')


def chart_tab(sym, daily):
    c1, c2 = st.columns([3, 1.2])
    tf = c1.segmented_control(L("Range", "المدى"), list(TF), default="1Y", key="st_tf", label_visibility="collapsed") or "1Y"
    ctype = c2.selectbox(L("Chart type", "نوع الرسم"), list(CHART_TYPES), format_func=lambda k: L(k, CHART_TYPES[k]),
                         label_visibility="collapsed")
    c3, c4 = st.columns(2)
    overlays = c3.multiselect(L("Overlays", "إضافات على السعر"), charts.OVERLAYS, default=["SMA 20", "SMA 50", "SMA 200"])
    panels = c4.multiselect(L("Indicator panels", "المؤشرات الفنية"), charts.PANELS, default=["RSI", "MACD"])
    spec = TF[tf]
    intraday = tf in ("1D", "5D", "1M")
    if isinstance(spec, int) or spec == "ytd":
        full = ta.add_all(daily)
        d = full[full.index.year == full.index[-1].year] if spec == "ytd" else full.tail(spec)
    else:
        raw = data.history(sym, *spec)
        if raw.empty:
            st.warning(L("Intraday data isn't available for this symbol. Try 3M or longer.",
                         "البيانات اللحظية غير متاحة لهذا الرمز. جرّب 3 أشهر أو أكثر."))
            return
        d = ta.add_all(raw)
        if tf == "1D":
            d = d[d.index.date == d.index[-1].date()]
    if len(d) < 2:
        st.warning(L("Not enough data for this range.", "لا توجد بيانات كافية لهذا المدى."))
        return
    st.plotly_chart(charts.price_chart(d, ctype, overlays, panels, intraday))


def technicals_tab(daily):
    d = ta.add_all(daily)
    table, total, label, parts = ta.technical_summary(d)
    ticks = [sig(x) for x in ("Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy")]
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(charts.gauge(total, f"{L('Summary', 'الملخص')}: {sig(label)}", ticks))
    osc, mas = parts.get("Oscillators", 0), parts.get("Moving Averages", 0)
    c2.plotly_chart(charts.gauge(osc, f"{L('Oscillators', 'المذبذبات')}: {sig(ta.label_for(osc))}", ticks))
    c3.plotly_chart(charts.gauge(mas, f"{L('Moving averages', 'المتوسطات')}: {sig(ta.label_for(mas))}", ticks))
    left, right = st.columns([1.3, 1])
    with left:
        ui.sec("tune", "Indicator signals", "إشارات المؤشرات")
        t = table.copy()
        t["Signal"] = t["Signal"].map(sig)
        t = t.rename(columns={"Indicator": L("Indicator", "المؤشر"), "Value": L("Value", "القيمة"), "Signal": L("Signal", "الإشارة")})
        buy, sell = sig("Buy"), sig("Sell")
        st.dataframe(t.style.map(lambda v: f"color:{T.UP};font-weight:600" if v == buy else (f"color:{T.DOWN};font-weight:600" if v == sell else ""),
                                 subset=[L("Signal", "الإشارة")]).format({L("Value", "القيمة"): "{:,.2f}"}), hide_index=True, height=560)
    with right:
        ui.sec("stacked_line_chart", "Pivot points", "نقاط الارتكاز")
        piv = ta.pivot_points(daily)
        st.dataframe(pd.DataFrame({L("Level", "المستوى"): list(piv), L("Price", "السعر"): [round(v, 2) for v in piv.values()]}), hide_index=True)
        ui.sec("horizontal_rule", "Support & resistance", "الدعوم والمقاومات")
        price = daily["Close"].iloc[-1]
        lv = ta.swing_levels(daily)
        sr = pd.DataFrame({L("Level", "المستوى"): [round(x, 2) for x in lv],
                           L("Type", "النوع"): [L("Support", "دعم") if x < price else L("Resistance", "مقاومة") for x in lv],
                           L("Distance %", "المسافة %"): [(x / price - 1) * 100 for x in lv]})
        st.dataframe(sr.iloc[::-1].style.map(T.color_style, subset=[L("Distance %", "المسافة %")]).format(
            {L("Distance %", "المسافة %"): "{:+.2f}%"}), hide_index=True)
        last = d.iloc[-1]
        m1, m2 = st.columns(2)
        m1.metric("ATR (14)", f"{last['ATR']:.2f}", f"{last['ATR'] / last['Close'] * 100:.2f}%", delta_color="off")
        m2.metric(L("BB width", "عرض بولنجر"), f"{last['BB_width'] * 100:.1f}%")
    st.plotly_chart(charts.returns_bars(daily, L("Performance", "الأداء")))


def financials_tab(sym, inf):
    f = data.fundamentals(sym)

    def pct(k):
        v = inf.get(k)
        return f"{v * 100:.2f}%" if isinstance(v, (int, float)) else "—"

    def num(k, dec=2):
        v = inf.get(k)
        return f"{v:,.{dec}f}" if isinstance(v, (int, float)) else "—"
    groups = {
        ("Valuation", "التقييم", "price_check"): [
            (L("Market cap", "القيمة السوقية"), T.fmt_big(inf.get("marketCap"))), (L("Enterprise value", "قيمة المنشأة"), T.fmt_big(inf.get("enterpriseValue"))),
            ("P/E (TTM)", num("trailingPE")), (L("Forward P/E", "المكرر المستقبلي"), num("forwardPE")), ("PEG", num("trailingPegRatio")),
            ("P/S", num("priceToSalesTrailing12Months")), ("P/B", num("priceToBook")), ("EV/EBITDA", num("enterpriseToEbitda"))],
        ("Profitability", "الربحية", "savings"): [
            (L("Gross margin", "الهامش الإجمالي"), pct("grossMargins")), (L("Operating margin", "الهامش التشغيلي"), pct("operatingMargins")),
            (L("Profit margin", "صافي الهامش"), pct("profitMargins")), ("ROE", pct("returnOnEquity")), ("ROA", pct("returnOnAssets"))],
        ("Growth", "النمو", "trending_up"): [
            (L("Revenue growth", "نمو الإيرادات"), pct("revenueGrowth")), (L("Earnings growth", "نمو الأرباح"), pct("earningsGrowth")),
            (L("Qtr earnings growth", "نمو الأرباح الفصلي"), pct("earningsQuarterlyGrowth")),
            (L("Revenue (TTM)", "الإيرادات"), T.fmt_big(inf.get("totalRevenue"))), ("EBITDA", T.fmt_big(inf.get("ebitda")))],
        ("Balance sheet", "الميزانية", "account_balance_wallet"): [
            (L("Total cash", "النقد"), T.fmt_big(inf.get("totalCash"))), (L("Total debt", "الديون"), T.fmt_big(inf.get("totalDebt"))),
            (L("Debt/Equity", "الديون/الملكية"), num("debtToEquity", 1)), (L("Current ratio", "نسبة التداول"), num("currentRatio")),
            (L("Free cash flow", "التدفق النقدي الحر"), T.fmt_big(inf.get("freeCashflow")))],
    }
    cols = st.columns(4)
    for col, ((gen, gar, ic), items) in zip(cols, groups.items()):
        with col:
            ui.sec(ic, gen, gar)
            ui.html("".join(f'<div class="stat" style="margin-bottom:6px"><div class="l">{l}</div><div class="v">{v}</div></div>'
                            for l, v in items))
    inc = f["income_q"]
    if isinstance(inc, pd.DataFrame) and not inc.empty:
        st.plotly_chart(charts.income_chart(inc, L("Quarterly results ($B)", "النتائج الفصلية (مليار $)")))
    else:
        st.info(L("Quarterly statements are not available for this symbol.", "القوائم الفصلية غير متاحة لهذا الرمز."))


def analysts_tab(sym, inf, price):
    f = data.fundamentals(sym)
    c1, c2 = st.columns(2)
    with c1:
        if f["targets"]:
            st.plotly_chart(charts.target_chart(price, f["targets"], L("12-month price targets", "السعر المستهدف (12 شهر)")))
            mean = f["targets"].get("mean")
            if mean:
                st.metric(L("Upside to mean target", "مساحة الصعود للهدف"), f"{(mean / price - 1) * 100:+.1f}%",
                          f"{inf.get('numberOfAnalystOpinions', 0)} {L('analysts', 'محلل')}", delta_color="off")
        rec = f["rec_summary"]
        if isinstance(rec, pd.DataFrame) and not rec.empty:
            st.plotly_chart(charts.rec_chart(rec, L("Analyst recommendations", "توصيات المحللين")))
    with c2:
        eh = f["earnings_hist"]
        if isinstance(eh, pd.DataFrame) and not eh.empty:
            fig = charts.eps_chart(eh, L("EPS: estimate vs actual", "ربحية السهم: المتوقع مقابل الفعلي"))
            if fig is not None:
                st.plotly_chart(fig)
        if f["earnings_date"] is not None:
            days = (pd.Timestamp(f["earnings_date"]).normalize() - pd.Timestamp.now().normalize()).days
            st.metric(L("Next earnings", "إعلان الأرباح القادم"), f"{pd.Timestamp(f['earnings_date']):%Y-%m-%d}",
                      L(f"in {days} days", f"بعد {days} يوم"), delta_color="off")
    ui.sec("swap_vert", "Upgrades & downgrades (90 days)", "الترقيات والتخفيضات (90 يوم)")
    r = f["ratings"]
    st.dataframe(r, height=260) if isinstance(r, pd.DataFrame) and not r.empty else st.caption("—")
    ui.sec("badge", "Insider transactions", "تعاملات المطّلعين")
    ins = f["insiders"]
    st.dataframe(ins.head(15), hide_index=True, height=300) if isinstance(ins, pd.DataFrame) and not ins.empty else st.caption("—")


def page_stock():
    sym = ss.symbol
    with st.spinner(L(f"Loading {sym}...", f"جاري تحميل {sym}...")):
        daily = data.history(sym, "2y")
    if daily.empty or len(daily) < 3:
        st.error(L(f"No data found for {sym}. Use the search box at the top.", f"لا توجد بيانات للرمز {sym}. استخدم البحث في الأعلى."))
        return
    inf = data.info(sym)
    h1, h2 = st.columns([4, 1])
    with h1:
        price = quote_header(sym, daily, inf)
    with h2:
        if sym not in ss.watchlist:
            if st.button(L("Add to watchlist", "أضف للمتابعة"), icon=":material/star:"):
                ss.watchlist.append(sym)
                st.rerun()
        else:
            st.button(L("In watchlist", "في المتابعة"), icon=":material/star:", disabled=True)
        if st.button("Catalyst Pro", icon=":material/bolt:"):
            ui.goto("catalyst")
    key_stats(daily, inf)
    tabs = st.tabs([L(":material/candlestick_chart: Chart", ":material/candlestick_chart: الرسم البياني"),
                    L(":material/speed: Technicals", ":material/speed: التحليل الفني"),
                    L(":material/request_quote: Financials", ":material/request_quote: المالية"),
                    L(":material/groups: Analysts", ":material/groups: المحللون"),
                    L(":material/newspaper: News", ":material/newspaper: الأخبار")])
    with tabs[0]:
        chart_tab(sym, daily)
    with tabs[1]:
        technicals_tab(daily)
    with tabs[2]:
        financials_tab(sym, inf)
    with tabs[3]:
        analysts_tab(sym, inf, price)
    with tabs[4]:
        ui.news_list(data.news(sym, 20), 15)
    ui.foot()


# =====================================================================
# SCREENER (Finviz-style)
# =====================================================================
def _o(en, ar, *filters):
    return (en, ar, list(filters))


F = {  # key -> (en, ar, group, [options])
    "mcap": ("Market cap", "القيمة السوقية", "desc", [_o("Any", "الكل"), _o("Mega (>200B)", "عملاقة (>200 مليار)", ("gt", "intradaymarketcap", 2e11)),
             _o("Large (10–200B)", "كبيرة (10–200 مليار)", ("btwn", "intradaymarketcap", 1e10, 2e11)),
             _o("Mid (2–10B)", "متوسطة (2–10 مليار)", ("btwn", "intradaymarketcap", 2e9, 1e10)),
             _o("Small (0.3–2B)", "صغيرة (0.3–2 مليار)", ("btwn", "intradaymarketcap", 3e8, 2e9)),
             _o("Micro (<300M)", "متناهية الصغر (<300 مليون)", ("lt", "intradaymarketcap", 3e8))]),
    "price": ("Price", "السعر", "desc", [_o("Any", "الكل"), _o("Under $5", "أقل من 5$", ("lt", "intradayprice", 5)),
              _o("$5–20", "5–20$", ("btwn", "intradayprice", 5, 20)), _o("$20–50", "20–50$", ("btwn", "intradayprice", 20, 50)),
              _o("$50–100", "50–100$", ("btwn", "intradayprice", 50, 100)), _o("Over $100", "أكثر من 100$", ("gt", "intradayprice", 100))]),
    "avgvol": ("Avg volume", "متوسط الحجم", "desc", [_o("Any", "الكل"), _o("Over 100K", "أكثر من 100 ألف", ("gt", "avgdailyvol3m", 1e5)),
               _o("Over 500K", "أكثر من 500 ألف", ("gt", "avgdailyvol3m", 5e5)), _o("Over 1M", "أكثر من مليون", ("gt", "avgdailyvol3m", 1e6)),
               _o("Over 5M", "أكثر من 5 ملايين", ("gt", "avgdailyvol3m", 5e6))]),
    "div": ("Dividend yield", "عائد التوزيعات", "desc", [_o("Any", "الكل"), _o("None (0%)", "بدون توزيعات", ("lt", "forward_dividend_yield", 0.01)),
            _o("Positive (>0%)", "يوزع (>0%)", ("gt", "forward_dividend_yield", 0)), _o("Over 2%", "أكثر من 2%", ("gt", "forward_dividend_yield", 2)),
            _o("Over 4%", "أكثر من 4%", ("gt", "forward_dividend_yield", 4))]),
    "beta": ("Beta", "بيتا", "desc", [_o("Any", "الكل"), _o("Under 0.5", "أقل من 0.5", ("lt", "beta", 0.5)),
             _o("0.5–1", "0.5–1", ("btwn", "beta", 0.5, 1)), _o("1–1.5", "1–1.5", ("btwn", "beta", 1, 1.5)), _o("Over 1.5", "أكثر من 1.5", ("gt", "beta", 1.5))]),
    "short": ("Short float", "البيع على المكشوف", "desc", [_o("Any", "الكل"), _o("Over 5%", "أكثر من 5%", ("gt", "short_percentage_of_float.value", 5)),
              _o("Over 10%", "أكثر من 10%", ("gt", "short_percentage_of_float.value", 10)),
              _o("Over 20%", "أكثر من 20%", ("gt", "short_percentage_of_float.value", 20))]),
    "pe": ("P/E", "مكرر الربحية", "fund", [_o("Any", "الكل"), _o("Low (0–15)", "منخفض (0–15)", ("btwn", "peratio.lasttwelvemonths", 0, 15)),
           _o("15–25", "15–25", ("btwn", "peratio.lasttwelvemonths", 15, 25)), _o("25–50", "25–50", ("btwn", "peratio.lasttwelvemonths", 25, 50)),
           _o("High (>50)", "مرتفع (>50)", ("gt", "peratio.lasttwelvemonths", 50))]),
    "peg": ("PEG", "PEG", "fund", [_o("Any", "الكل"), _o("Under 1", "أقل من 1", ("btwn", "pegratio_5y", 0, 1)),
            _o("1–2", "1–2", ("btwn", "pegratio_5y", 1, 2)), _o("Over 2", "أكثر من 2", ("gt", "pegratio_5y", 2))]),
    "pb": ("P/B", "السعر/القيمة الدفترية", "fund", [_o("Any", "الكل"), _o("Under 1", "أقل من 1", ("btwn", "pricebookratio.quarterly", 0, 1)),
           _o("1–3", "1–3", ("btwn", "pricebookratio.quarterly", 1, 3)), _o("Over 3", "أكثر من 3", ("gt", "pricebookratio.quarterly", 3))]),
    "roe": ("ROE", "العائد على الملكية", "fund", [_o("Any", "الكل"), _o("Over 10%", "أكثر من 10%", ("gt", "returnonequity.lasttwelvemonths", 10)),
            _o("Over 20%", "أكثر من 20%", ("gt", "returnonequity.lasttwelvemonths", 20)), _o("Negative", "سالب", ("lt", "returnonequity.lasttwelvemonths", 0))]),
    "epsg": ("EPS growth (TTM)", "نمو ربحية السهم", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "epsgrowth.lasttwelvemonths", 0)),
             _o("Over 10%", "أكثر من 10%", ("gt", "epsgrowth.lasttwelvemonths", 10)), _o("Over 25%", "أكثر من 25%", ("gt", "epsgrowth.lasttwelvemonths", 25))]),
    "revg": ("Revenue growth (Q)", "نمو الإيرادات الفصلي", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "quarterlyrevenuegrowth.quarterly", 0)),
             _o("Over 10%", "أكثر من 10%", ("gt", "quarterlyrevenuegrowth.quarterly", 10)), _o("Over 25%", "أكثر من 25%", ("gt", "quarterlyrevenuegrowth.quarterly", 25))]),
    "margin": ("Net margin", "صافي الهامش", "fund", [_o("Any", "الكل"), _o("Positive", "إيجابي", ("gt", "netincomemargin.lasttwelvemonths", 0)),
               _o("Over 10%", "أكثر من 10%", ("gt", "netincomemargin.lasttwelvemonths", 10)), _o("Over 20%", "أكثر من 20%", ("gt", "netincomemargin.lasttwelvemonths", 20))]),
    "de": ("Debt/Equity", "الديون/الملكية", "fund", [_o("Any", "الكل"), _o("Under 50%", "أقل من 50%", ("lt", "totaldebtequity.lasttwelvemonths", 50)),
           _o("Under 100%", "أقل من 100%", ("lt", "totaldebtequity.lasttwelvemonths", 100)), _o("Over 100%", "أكثر من 100%", ("gt", "totaldebtequity.lasttwelvemonths", 100))]),
    "chg": ("Change today", "التغير اليوم", "tech", [_o("Any", "الكل"), _o("Up", "صاعد", ("gt", "percentchange", 0)), _o("Up > 3%", "صاعد > 3%", ("gt", "percentchange", 3)),
            _o("Up > 5%", "صاعد > 5%", ("gt", "percentchange", 5)), _o("Down", "نازل", ("lt", "percentchange", 0)),
            _o("Down > 3%", "نازل > 3%", ("lt", "percentchange", -3)), _o("Down > 5%", "نازل > 5%", ("lt", "percentchange", -5))]),
    "perf52": ("52W performance", "أداء 52 أسبوع", "tech", [_o("Any", "الكل"), _o("Up", "صاعد", ("gt", "fiftytwowkpercentchange", 0)),
               _o("Over +20%", "أكثر من +20%", ("gt", "fiftytwowkpercentchange", 20)), _o("Over +50%", "أكثر من +50%", ("gt", "fiftytwowkpercentchange", 50)),
               _o("Down", "نازل", ("lt", "fiftytwowkpercentchange", 0))]),
    "sma50": ("SMA 50", "متوسط 50", "local", [_o("Any", "الكل"), _o("Price above", "السعر فوقه"), _o("Price below", "السعر تحته")]),
    "sma200": ("SMA 200", "متوسط 200", "local", [_o("Any", "الكل"), _o("Price above", "السعر فوقه"), _o("Price below", "السعر تحته")]),
    "high52": ("52W high", "القمة السنوية", "local", [_o("Any", "الكل"), _o("Within 5%", "ضمن 5%"), _o("Within 10%", "ضمن 10%"), _o("More than 30% below", "أقل منها بأكثر من 30%")]),
    "rsi": ("RSI (14)", "RSI (14)", "local", [_o("Any", "الكل"), _o("Oversold (<30)", "تشبع بيعي (<30)"), _o("Overbought (>70)", "تشبع شرائي (>70)"),
            _o("Neutral (40–60)", "محايد (40–60)")]),
}
SORTS = {"intradaymarketcap": ("Market cap", "القيمة السوقية", False), "percentchange": ("Change %", "التغير %", False),
         "dayvolume": ("Volume", "الحجم", False), "peratio.lasttwelvemonths": ("P/E (low first)", "مكرر الربحية (الأقل)", True),
         "forward_dividend_yield": ("Dividend yield", "عائد التوزيعات", False),
         "short_percentage_of_float.value": ("Short float", "البيع على المكشوف", False),
         "fiftytwowkpercentchange": ("52W performance", "أداء 52 أسبوع", False)}
PRESETS = {
    "custom": ("Custom", "مخصص", {}),
    "gainers": ("Top gainers (large caps)", "الأكثر ارتفاعاً (شركات كبيرة)", {"mcap": 2, "chg": 1}),
    "highs": ("Near 52-week high", "قرب القمة السنوية", {"mcap": 2, "high52": 1, "sma50": 1}),
    "oversold": ("Oversold large caps", "شركات كبيرة في تشبع بيعي", {"mcap": 2, "rsi": 1}),
    "dividend": ("Dividend payers > 4%", "توزيعات أكثر من 4%", {"div": 4, "mcap": 2}),
    "shorts": ("High short interest", "بيع على المكشوف مرتفع", {"short": 2, "avgvol": 3}),
    "value": ("Undervalued growth", "نمو بتقييم منخفض", {"pe": 1, "epsg": 2, "revg": 1}),
}


def _apply_preset():
    p = PRESETS[ss.sc_preset][2]
    for k in F:
        ss[f"sf_{k}"] = p.get(k, 0)


def _local_filters(df):
    s = {k: ss.get(f"sf_{k}", 0) for k in ("sma50", "sma200", "high52")}
    if s["sma50"] and "SMA50" in df:
        df = df[(df["Price"] > df["SMA50"]) if s["sma50"] == 1 else (df["Price"] < df["SMA50"])]
    if s["sma200"] and "SMA200" in df:
        df = df[(df["Price"] > df["SMA200"]) if s["sma200"] == 1 else (df["Price"] < df["SMA200"])]
    if s["high52"] and "52W High" in df:
        dist = df["Price"] / df["52W High"] - 1
        df = df[{1: dist >= -0.05, 2: dist >= -0.10, 3: dist < -0.30}[s["high52"]]]
    return df


def _technicals(symbols):
    hist = data.history_many(tuple(symbols), "1y")
    rows = []
    for s, df in hist.items():
        if len(df) < 30:
            continue
        c = df["Close"]
        perf = lambda n: (c.iloc[-1] / c.iloc[-n - 1] - 1) * 100 if len(c) > n else np.nan
        ytd = c[c.index.year == c.index[-1].year]
        vol = c.pct_change().tail(21).std() * np.sqrt(252) * 100
        rows.append({"Symbol": s, "Perf W": perf(5), "Perf M": perf(21), "Perf 3M": perf(63),
                     "Perf YTD": (c.iloc[-1] / ytd.iloc[0] - 1) * 100 if len(ytd) > 1 else np.nan,
                     "RSI": float(ta.rsi(c).iloc[-1]), "Volatility": vol, "_spark": c.tail(60).values})
    return pd.DataFrame(rows)


def page_screener():
    ui.header("filter_alt", "Stock Screener", "فلتر الأسهم",
              "Filter the entire US market by valuation, growth, dividends, short interest and technicals (Finviz-style).",
              "فلترة السوق الأمريكي كامل حسب التقييم والنمو والتوزيعات والبيع على المكشوف والتحليل الفني.")
    top = st.columns([1.4, 1, 1, 0.8])
    top[0].selectbox(L("Preset", "قالب جاهز"), list(PRESETS), key="sc_preset", on_change=_apply_preset,
                     format_func=lambda k: L(PRESETS[k][0], PRESETS[k][1]))
    sort = top[1].selectbox(L("Order by", "ترتيب حسب"), list(SORTS), format_func=lambda k: L(SORTS[k][0], SORTS[k][1]))
    size = top[2].selectbox(L("Results", "عدد النتائج"), [50, 100, 250], index=1)
    top[3].write("")
    run = top[3].button(L("Screen", "ابحث"), type="primary", icon=":material/search:")

    groups = {"desc": L("Descriptive", "وصفية"), "fund": L("Fundamental", "أساسية"), "tech": L("Technical", "فنية")}
    tabs = st.tabs(list(groups.values()))
    for tab, g in zip(tabs, groups):
        with tab:
            keys = [k for k, v in F.items() if v[2] == g or (g == "tech" and v[2] == "local")]
            if g == "desc":
                keys = ["sector", "industry"] + keys
            cols = st.columns(4)
            for i, k in enumerate(keys):
                col = cols[i % 4]
                if k == "sector":
                    col.selectbox(L("Sector", "القطاع"), ["Any"] + U.SECTORS, key="sf_sector",
                                  format_func=lambda s: L("Any", "الكل") if s == "Any" else sector_name(s))
                elif k == "industry":
                    sec = ss.get("sf_sector", "Any")
                    opts = ["Any"] + (U.INDUSTRIES.get(sec, []) if sec != "Any" else [])
                    if ss.get("sf_industry") not in opts:
                        ss["sf_industry"] = "Any"
                    col.selectbox(L("Industry", "الصناعة"), opts, key="sf_industry",
                                  format_func=lambda s: L("Any", "الكل") if s == "Any" else s, disabled=sec == "Any")
                else:
                    en, ar, _, opts = F[k]
                    ss.setdefault(f"sf_{k}", 0)
                    col.selectbox(L(en, ar), list(range(len(opts))), key=f"sf_{k}",
                                  format_func=lambda i, o=opts: L(o[i][0], o[i][1]))

    active = [(k, ss.get(f"sf_{k}", 0)) for k in F if ss.get(f"sf_{k}", 0)]
    if ss.get("sf_sector", "Any") != "Any":
        active.append(("sector", ss.sf_sector))
    if ss.get("sf_industry", "Any") != "Any":
        active.append(("industry", ss.sf_industry))
    if active:
        ui.html(" ".join(T.badge(f"{L(F[k][0], F[k][1])}: {L(F[k][3][v][0], F[k][3][v][1])}" if k in F else
                                 (sector_name(v) if k == "sector" else v), "gold", "filter_alt") for k, v in active))

    if run or "screen" not in ss:
        filters = []
        for k in F:
            v = ss.get(f"sf_{k}", 0)
            if v and F[k][2] != "local":
                filters += [list(f) for f in F[k][3][v][2]]
        if ss.get("sf_sector", "Any") != "Any":
            filters.append(["eq", "sector", ss.sf_sector])
        if ss.get("sf_industry", "Any") != "Any":
            filters.append(["eq", "industry", ss.sf_industry])
        with st.spinner(L("Screening the US market...", "جاري فلترة السوق الأمريكي...")):
            df, err = data.screen_custom(filters, sort, SORTS[sort][2], size)
            source = "live"
            if df.empty:
                source = "fallback"
                fb = data.changes(tuple(U.US_UNIVERSE))
                df = pd.DataFrame([{"Symbol": s, "Name": U.name_of(s), "Price": p, "Chg %": c, "Mkt Cap": U.STOCKS[s][3] * 1e9}
                                   for s, (p, c) in fb.items()])
                if ss.get("sf_sector", "Any") != "Any" and not df.empty:
                    df = df[df["Symbol"].map(U.sector_of) == ss.sf_sector]
        ss.screen = {"df": df, "err": err, "source": source, "time": datetime.now()}

    res = ss.screen
    df = _local_filters(res["df"].copy()) if not res["df"].empty else res["df"]
    if res["source"] == "fallback":
        st.warning(L("Live screener unavailable right now; showing the top 175 US stocks with price filters only.",
                     "الفلتر المباشر غير متاح حالياً؛ نعرض أكبر 175 سهم أمريكي مع فلاتر السعر فقط."), icon=":material/cloud_off:")
    if df.empty:
        st.info(L("No stocks match these filters.", "لا توجد أسهم تطابق هذه الفلاتر."))
        return
    need_tech = ss.get("sf_rsi", 0) > 0
    tech = _technicals(df["Symbol"].head(150).tolist()) if need_tech or st.session_state.get("sc_view_tech", True) else pd.DataFrame()
    if not tech.empty:
        df = df.merge(tech, on="Symbol", how="left")
        if need_tech:
            r = ss.sf_rsi
            df = df[{1: df["RSI"] < 30, 2: df["RSI"] > 70, 3: df["RSI"].between(40, 60)}[r]]
    df["Sector"] = df["Symbol"].map(lambda s: sector_name(U.sector_of(s)) if s in U.STOCKS else (sector_name(ss.sf_sector) if ss.get("sf_sector", "Any") != "Any" else "—"))

    m = st.columns(4)
    m[0].metric(L("Matches", "النتائج"), len(df))
    m[1].metric(L("Advancing", "صاعدة"), int((df["Chg %"] > 0).sum()))
    m[2].metric(L("Median P/E", "وسيط مكرر الربحية"), f"{df['P/E'].median():.1f}" if "P/E" in df and df["P/E"].notna().any() else "—")
    m[3].metric(L("Total market cap", "إجمالي القيمة السوقية"), T.fmt_big(df["Mkt Cap"].sum()) if "Mkt Cap" in df else "—")

    N = {"Symbol": L("Ticker", "الرمز"), "Name": L("Company", "الشركة"), "Sector": L("Sector", "القطاع"), "Mkt Cap": L("Market cap", "القيمة السوقية"),
         "Price": L("Price", "السعر"), "Chg %": L("Change", "التغير"), "Volume": L("Volume", "الحجم"), "P/E": "P/E", "Fwd P/E": "Fwd P/E",
         "P/B": "P/B", "EPS": "EPS", "Div %": L("Dividend", "التوزيعات"), "52W %": L("52W perf", "أداء سنوي"), "Rating": L("Analyst rating", "تقييم المحللين"),
         "Perf W": L("Perf week", "أسبوع"), "Perf M": L("Perf month", "شهر"), "Perf 3M": L("Perf quarter", "3 أشهر"), "Perf YTD": L("Perf YTD", "منذ بداية العام"),
         "RSI": "RSI", "Volatility": L("Volatility", "التذبذب"), "52W High": L("52W high", "قمة سنوية")}
    views = {L("Overview", "نظرة عامة"): ["Symbol", "Name", "Sector", "Mkt Cap", "P/E", "Price", "Chg %", "Volume"],
             L("Valuation", "التقييم"): ["Symbol", "Mkt Cap", "P/E", "Fwd P/E", "P/B", "EPS", "Div %", "Rating"],
             L("Performance", "الأداء"): ["Symbol", "Price", "Chg %", "Perf W", "Perf M", "Perf 3M", "Perf YTD", "52W %", "RSI", "Volatility"]}
    fmt = {"Mkt Cap": T.fmt_big, "Volume": T.fmt_big}
    vt = st.tabs(list(views) + [L("Charts", "الرسوم")])
    for tab, (vname, cols) in zip(vt, views.items()):
        with tab:
            cols = [c for c in cols if c in df.columns]
            show = df[cols].copy()
            for c, fn in fmt.items():
                if c in show:
                    show[c] = show[c].map(fn)
            pct_cols = [c for c in ("Chg %", "Perf W", "Perf M", "Perf 3M", "Perf YTD", "52W %") if c in show]
            show = show.rename(columns=N)
            st.dataframe(show.style.map(T.color_style, subset=[N[c] for c in pct_cols]).format(
                {**{N[c]: "{:+.2f}%" for c in pct_cols}, **{N[c]: "{:,.2f}" for c in ("Price", "P/E", "Fwd P/E", "P/B", "EPS") if c in cols},
                 **({N["Div %"]: "{:.2f}%"} if "Div %" in cols else {}), **({N["RSI"]: "{:.0f}"} if "RSI" in cols else {}),
                 **({N["Volatility"]: "{:.1f}%"} if "Volatility" in cols else {})}, na_rep="—"),
                hide_index=True, height=520)
    with vt[-1]:
        if "_spark" in df:
            items = []
            for _, r in df.head(36).iterrows():
                sp = r["_spark"] if isinstance(r["_spark"], np.ndarray) else None
                items.append(T.tile(f'{r["Symbol"]} · {str(r["Name"])[:20]}', T.fmt_price(r["Price"]), None, r["Chg %"], sp))
            ui.html(T.tiles(items))
    a, b, c = st.columns([2, 1, 1])
    pick = a.selectbox(L("Selected stock", "السهم المختار"), df["Symbol"].tolist())
    if b.button(L("Open stock", "افتح السهم"), icon=":material/candlestick_chart:", key="sc_open"):
        ui.open_stock(pick)
    c.download_button(L("Export CSV", "تصدير CSV"), df.drop(columns=["_spark"], errors="ignore").to_csv(index=False).encode(),
                      "screener.csv", "text/csv", icon=":material/download:")
    if res.get("err"):
        with st.expander(L("Technical details", "تفاصيل فنية")):
            st.code(res["err"])
    ui.foot()


# =====================================================================
# SCANNER
# =====================================================================
def page_scanner():
    ui.header("radar", "Opportunity Scanner", "صائد الفرص",
              "The bot scans US stocks for technical setups and builds a trade plan (entry, stop, target) for each.",
              "البوت يفحص الأسهم الأمريكية بحثاً عن فرص فنية ويبني لكل فرصة خطة: دخول ووقف وهدف.")
    bysec = U.by_sector()
    universes = {"all": (L("Top 175 US stocks", "أكبر 175 سهم أمريكي"), U.US_UNIVERSE),
                 **{f"s:{k}": (f"{L('Sector', 'قطاع')}: {sector_name(k)}", v) for k, v in bysec.items()},
                 "wl": (L("My watchlist", "قائمة المتابعة"), ss.watchlist), "custom": (L("Custom list", "قائمة مخصصة"), None)}
    c1, c2, c3 = st.columns([1.4, 1, 1])
    uk = c1.selectbox(L("Universe", "نطاق البحث"), list(universes), format_func=lambda k: universes[k][0])
    preset = c2.selectbox(L("Setup filter", "نوع الفرصة"), list(engine.SCAN_PRESETS),
                          format_func=lambda k: L(engine.SCAN_PRESETS[k][0], engine.SCAN_PRESETS[k][1]))
    if universes[uk][1] is None:
        txt = c3.text_input(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), "AAPL, MSFT, NVDA, TSLA, AMD")
        symbols = [s.strip().upper() for s in txt.split(",") if s.strip()]
    else:
        symbols = universes[uk][1]
        c3.metric(L("Symbols", "عدد الرموز"), len(symbols))
    if st.button(L("Run scan", "ابدأ البحث"), type="primary", icon=":material/radar:"):
        with st.spinner(L(f"Scanning {len(symbols)} symbols...", f"جاري فحص {len(symbols)} رمز...")):
            dmap = data.history_many(tuple(symbols), "1y")
            ss.scan = {"res": engine.scan(dmap, spy_daily()), "time": datetime.now(), "count": len(dmap)}
    sc = ss.get("scan")
    if not sc:
        st.info(L("Choose a universe and press Run scan.", "اختر النطاق واضغط ابدأ البحث."), icon=":material/info:")
        return
    res = sc["res"]
    if res.empty:
        st.warning(L("No data returned. Try again in a minute.", "لم تصل بيانات. حاول بعد دقيقة."))
        return
    tag = engine.SCAN_PRESETS[preset][2]
    view = res[res["_tags"].str.contains(tag)] if tag else res
    m = st.columns(5)
    m[0].metric(L("Scanned", "تم فحصها"), sc["count"])
    m[1].metric(L("Bullish (score ≥ 3)", "إيجابية (نقاط ≥ 3)"), int((res["Score"] >= 3).sum()))
    m[2].metric(L("Bearish (score < 0)", "سلبية (نقاط < 0)"), int((res["Score"] < 0).sum()))
    m[3].metric(L("Matches", "مطابقة"), len(view))
    m[4].metric(L("Scan time", "وقت البحث"), f"{sc['time']:%H:%M}")
    lo, hi = int(res["Score"].min()), int(res["Score"].max())
    min_score = st.slider(L("Minimum score", "أقل عدد نقاط"), lo, hi, max(lo, min(2, hi))) if hi > lo else lo
    view = view[view["Score"] >= min_score].copy()
    view["Sector"] = view["Sector"].map(sector_name)
    view["Setup"] = view["Setup_ar"] if is_ar() else view["Setup"]
    view["Signals"] = view["Signals_ar"] if is_ar() else view["Signals"]
    view["Trend"] = view["Trend"].map(lambda t: L(t, {"Up": "صاعد", "Down": "هابط", "Mixed": "متذبذب"}[t]))
    cols = ["Symbol", "Sector", "Price", "Chg %", "1M %", "3M %", "RSI", "ADX", "Vol ×", "Trend", "Score", "Setup",
            "Entry", "Stop", "Target", "R:R", "Signals"]
    N = {"Symbol": L("Ticker", "الرمز"), "Sector": L("Sector", "القطاع"), "Price": L("Price", "السعر"), "Chg %": L("Chg %", "التغير %"),
         "1M %": L("1M %", "شهر %"), "3M %": L("3M %", "3 أشهر %"), "Vol ×": L("Vol ×", "الحجم ×"), "Trend": L("Trend", "الاتجاه"),
         "Score": L("Score", "النقاط"), "Setup": L("Setup", "نوع الفرصة"), "Entry": L("Entry", "الدخول"), "Stop": L("Stop", "الوقف"),
         "Target": L("Target", "الهدف"), "Signals": L("Signals", "الإشارات")}
    show = view[cols].rename(columns=N)
    st.dataframe(show.style.map(T.color_style, subset=[N["Chg %"], N["1M %"], N["3M %"]]).format(
        {N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["1M %"]: "{:+.1f}%", N["3M %"]: "{:+.1f}%", "RSI": "{:.0f}",
         "ADX": "{:.0f}", N["Vol ×"]: "{:.1f}", N["Entry"]: "{:,.2f}", N["Stop"]: "{:,.2f}", N["Target"]: "{:,.2f}", "R:R": "{:.1f}"},
        na_rep="—"), hide_index=True, height=440)
    a, b, c = st.columns([2, 1, 1])
    pick = a.selectbox(L("Selected symbol", "الرمز المختار"), view["Symbol"].tolist() or res["Symbol"].tolist())
    if b.button(L("Open chart", "افتح الرسم"), icon=":material/candlestick_chart:"):
        ui.open_stock(pick)
    if c.button("Catalyst Pro", icon=":material/bolt:", key="scan_cat"):
        ss.symbol = pick
        ui.goto("catalyst")
    v1, v2 = st.columns([1.6, 1])
    v1.plotly_chart(charts.scan_scatter(res, L("Momentum map: 1-month return vs RSI (bubble = volume, color = score)",
                                              "خريطة الزخم: عائد الشهر مقابل RSI (الحجم = حجم التداول، اللون = النقاط)")))
    by_sec = res.groupby("Sector")["Score"].mean().sort_values()
    v2.plotly_chart(charts.hbar([sector_name(s) for s in by_sec.index], list(by_sec.values),
                                L("Average score by sector", "متوسط النقاط حسب القطاع"), 460, suffix=""))
    st.download_button(L("Export CSV", "تصدير CSV"), res.drop(columns=["_tags"]).to_csv(index=False).encode(), "scan.csv",
                       "text/csv", icon=":material/download:")
    ui.foot()


# =====================================================================
# CATALYST PRO
# =====================================================================
def page_catalyst():
    ui.header("bolt", "Catalyst Pro", "المحفزات الاحترافية",
              "Technical, fundamental and event catalysts combined into one score and a complete trade plan.",
              "تجميع المحفزات الفنية والمالية والأحداث في تقييم واحد وخطة تداول كاملة.")
    c1, c2, c3 = st.columns([1.2, 1, 1])
    sym = c1.text_input(L("Symbol", "الرمز"), ss.symbol).strip().upper() or "AAPL"
    ss.symbol = sym
    ss.acct["size"] = c2.number_input(L("Account size ($)", "حجم المحفظة ($)"), 100, 100_000_000, int(ss.acct["size"]), step=1000)
    ss.acct["risk"] = c3.number_input(L("Risk per trade (%)", "المخاطرة لكل صفقة (%)"), 0.1, 10.0, float(ss.acct["risk"]), step=0.25)
    with st.spinner(L(f"Analyzing {sym}...", f"جاري تحليل {sym}...")):
        daily = data.history(sym, "2y")
        if daily.empty or len(daily) < 60:
            st.error(L(f"Not enough data for {sym}.", f"لا توجد بيانات كافية للرمز {sym}."))
            return
        d = ta.add_all(daily)
        inf = data.info(sym)
        f = data.fundamentals(sym)
        nws = data.news(sym, 20)
        tech = engine.technical_checks(d, spy_daily())
        fund = engine.fundamental_checks(inf, f["earnings_hist"])
        rr = f["ratings"]
        if isinstance(rr, pd.DataFrame) and not rr.empty:
            rr = rr[rr.index >= pd.Timestamp.now() - pd.Timedelta(days=30)]
        events = engine.event_checks(f["earnings_date"], rr, nws, inf, d)
        score = engine.catalyst_score(tech, fund, events)
        p = engine.trade_plan(d, ss.acct["size"], ss.acct["risk"])

    name = inf.get("shortName") or U.name_of(sym)
    kind = "up" if score["total"] >= 55 else ("down" if score["total"] < 45 else "neu")
    bias_kind = "up" if p["bias"].startswith("Long") else ("down" if "Avoid" in p["bias"] else "neu")
    ui.html(f'<h3 style="margin:.2rem 0">{T.esc(name)} ({sym})</h3>'
            + T.badge(L(score["label"], score["label_ar"]), kind, "insights")
            + T.badge(f'{L("Bias", "التوجه")}: {L(p["bias"], p["bias_ar"])}', bias_kind, "explore")
            + T.badge(f'{L("Setup", "الفرصة")}: {L(p["setup"], p["setup_ar"])}', "acc", "target"))
    g1, g2, g3, g4 = st.columns([1.3, 1, 1, 1])
    g1.plotly_chart(charts.score_gauge(score["total"], L("Catalyst score", "تقييم المحفزات")))
    scf = lambda v: "n/a" if v is None else f"{v:.0f}/100"
    g2.metric(L("Technical (50%)", "فني (50%)"), scf(score["technical"]), f"{sum(x['Pass'] for x in tech)}/{len(tech)}", delta_color="off")
    g3.metric(L("Fundamental (30%)", "مالي (30%)"), scf(score["fundamental"]),
              f"{sum(x['Pass'] for x in fund)}/{len(fund)}" if fund else L("no data", "لا بيانات"), delta_color="off")
    g4.metric(L("Events (20%)", "أحداث (20%)"), scf(score["event"]), f"{len(events)}", delta_color="off")

    ui.sec("flag", "Trade plan", "خطة التداول")
    cards = [(L("Current price", "السعر الحالي"), f"${p['price']:,.2f}", T.BORDER),
             (L("Entry zone", "منطقة الدخول"), f"${p['zone'][0]:,.2f} – ${p['zone'][1]:,.2f}", T.ACCENT),
             (L("Stop loss", "وقف الخسارة"), f"${p['stop']:,.2f}", T.DOWN), (L("Target 1 (2R)", "الهدف الأول"), f"${p['t1']:,.2f}", T.UP),
             (L("Target 2 (3R)", "الهدف الثاني"), f"${p['t2']:,.2f}", T.UP), (L("Risk / share", "المخاطرة للسهم"), f"${p['risk_per_share']:,.2f}", T.BORDER),
             (L("Position size", "حجم الصفقة"), f"{p['shares']:,} {L('sh', 'سهم')}", T.GOLD),
             (L("Position value", "قيمة الصفقة"), f"${p['position_value']:,.0f}", T.GOLD),
             (L("Max loss", "أقصى خسارة"), f"${p['shares'] * p['risk_per_share']:,.0f}", T.DOWN),
             ("ATR (14)", f"${p['atr']:,.2f} ({p['atr_pct']:.1f}%)", T.BORDER), (L("Support", "الدعم"), f"${p['support']:,.2f}", T.BORDER),
             (L("Resistance", "المقاومة"), f"${p['resistance']:,.2f}", T.BORDER)]
    ui.html('<div class="plan">' + "".join(f'<div class="p" style="border-inline-start-color:{c}"><div class="l">{l}</div><div class="v">{v}</div></div>'
                                           for l, v, c in cards) + "</div>")
    left, right = st.columns([1.6, 1])
    with left:
        levels = [(L("Entry", "دخول"), p["entry"], T.ACCENT, "solid"), (L("Stop", "وقف"), p["stop"], T.DOWN, "dash"),
                  ("T1", p["t1"], T.UP, "dot"), ("T2", p["t2"], T.UP, "dash")]
        st.plotly_chart(charts.price_chart(d.tail(126), "Candles", ["SMA 20", "SMA 50"], [], False, levels=levels, height=520))
    with right:
        ui.sec("schedule", "Entry timing", "توقيت الدخول")
        earn = f["earnings_date"]
        ed = (pd.Timestamp(earn).normalize() - pd.Timestamp.now().normalize()).days if earn is not None else None
        timing = [(f"<b>{L('Trigger', 'شرط الدخول')}:</b> {T.esc(L(p['trigger'], p['trigger_ar']))}", "flag"),
                  (f"<b>{L('Market now', 'السوق الآن')}:</b> {T.market_status(is_ar())}", "schedule"),
                  (L("<b>Best window:</b> avoid the first 30 minutes after the 9:30 ET open; confirm on the daily close or after 10:00 ET with above-average volume.",
                     "<b>أفضل وقت:</b> تجنّب أول 30 دقيقة بعد افتتاح 9:30 بتوقيت نيويورك (4:30 عصراً بتوقيت السعودية)، وأكّد على الإغلاق اليومي أو بعد 10:00 مع حجم أعلى من المتوسط."), "timer"),
                  (L("<b>Holding period:</b> ", "<b>مدة الاحتفاظ:</b> ") + (L("2–6 weeks (swing)", "2–6 أسابيع (سوينغ)") if p["setup"] in ("Breakout", "Pullback to SMA20")
                                                                          else L("1–2 weeks (short swing)", "1–2 أسبوع")), "hourglass")]
        if ed is not None and 0 <= ed <= 14:
            timing.append((f"<b class='down'>{L(f'Earnings in {ed} days', f'إعلان أرباح بعد {ed} يوم')}</b>: "
                           f"{L('half size, or wait until after the report.', 'نصف الحجم أو انتظر بعد الإعلان.')}", "warning"))
        ui.html("".join(f'<div class="check">{T.icon(ic, T.GOLD)}<div>{t}</div></div>' for t, ic in timing))
        ui.sec("logout", "Exit rules", "قواعد الخروج")
        ui.html("".join(f'<div class="check">{T.icon("chevron_right", T.MUTED)}<div>{T.esc(L(e, a))}</div></div>' for e, a in p["exits"]))

    def checklist(items):
        return "".join(f'<div class="check">{T.icon("check_circle", T.UP) if c["Pass"] else T.icon("cancel", T.DOWN)}'
                       f'<div><b>{T.esc(L(c["Check"], c["Check_ar"]))}</b> <span class="muted">· {T.esc(c["Detail"])}</span></div></div>'
                       for c in items)
    c1, c2 = st.columns(2)
    with c1:
        ui.sec("query_stats", "Technical catalysts", "المحفزات الفنية")
        ui.html(checklist(tech))
    with c2:
        ui.sec("request_quote", "Fundamental catalysts", "المحفزات المالية")
        ui.html(checklist(fund)) if fund else st.caption(L("No fundamental data (ETF, index or crypto).", "لا توجد بيانات مالية (صندوق أو مؤشر أو عملة رقمية)."))
    ui.sec("event", "Event catalysts", "محفزات الأحداث")
    if events:
        rows = []
        for e in events:
            en, ar, k, ic = engine.IMPACT[e["Impact"]]
            rows.append(f'<div class="check">{T.badge(L(en, ar), k, ic)}<div><b>{T.esc(L(e["Event"], e["Event_ar"]))}</b> '
                        f'<span class="muted">· {T.esc(L(e["Detail"], e["Detail_ar"]))}</span></div></div>')
        ui.html("".join(rows))
    else:
        st.caption(L("No special events detected right now.", "لا توجد أحداث خاصة حالياً."))
    ui.sec("newspaper", "Latest news", "آخر الأخبار")
    ui.news_list(nws, 6)
    ui.foot()
