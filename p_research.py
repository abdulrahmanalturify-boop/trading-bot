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
import taxonomy as X
import theme as T
import ui
import universe as U
from i18n import L, industry_name, is_ar, sector_name, sig, theme_name

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
    sec = inf.get("sector") or (U.sector_of(sym) if U.known(sym) else "")
    ind = inf.get("industry") or (U.industry_of(sym) if U.known(sym) else "")
    badges = (T.badge(sector_name(sec), "acc", "category") if sec else "") + (T.badge(industry_name(ind), "vio", "factory") if ind else "")
    for tk, sk in X.themes_of(sym)[:2]:
        badges += T.badge(theme_name(tk, sk), "gold", X.THEMES[tk][2])
    uri = data.logos([sym]).get(sym)
    ui.html(f'<div style="display:flex;gap:14px;align-items:center">{T.logo_circle(sym, uri, 58)}<div>'
            f'<div class="q-name"><b style="color:#fff;font-size:1.15rem">{T.esc(name)}</b> · {sym} · {T.esc(exch)}</div><div>{badges}</div></div></div>'
            f'<div style="margin-top:6px"><span class="q-price">{T.fmt_price(last)}</span> <span class="muted">{inf.get("currency", "USD")}</span></div>'
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


def company_tab(sym):
    p = data.profile(sym)
    ui.sec("apartment", "Company description", "نبذة عن الشركة")
    summary = p["summary"]
    if summary:
        if is_ar():
            with st.spinner("جاري ترجمة النبذة..."):
                tr = data.translate_long(summary)
            ui.html(f'<div class="card rtl"><div class="desc">{T.esc(tr)}</div></div>')
            if tr == summary:
                st.caption("خدمة الترجمة مشغولة حالياً؛ نعرض النص الأصلي.")
            with st.expander("النص الأصلي بالإنجليزي"):
                st.write(summary)
        else:
            ui.html(f'<div class="card"><div class="desc">{T.esc(summary)}</div></div>')
    else:
        st.caption(L("No description available for this symbol.", "لا توجد نبذة متاحة لهذا الرمز."))

    ui.sec("category", "Classification", "التصنيف")
    th = X.themes_of(sym)
    sub = X.SUBIND.get(sym)
    items = [("category", L("Sector", "القطاع"), sector_name(p["sector"]) if p["sector"] else "—"),
             ("factory", L("Industry", "الصناعة"), industry_name(p["industry"]) if p["industry"] else "—"),
             ("account_tree", L("Sub-industry", "الصناعة الفرعية"), L(sub[0], sub[1]) if sub else "—"),
             ("lightbulb", L("Themes", "الثيمات الاستثمارية"), " · ".join(dict.fromkeys(theme_name(t) for t, _ in th)) or "—"),
             ("label", L("Sub-themes", "الثيمات الفرعية"), " · ".join(theme_name(t, s_) for t, s_ in th) or "—"),
             ("location_city", L("Headquarters", "المقر الرئيسي"), p["hq"] or "—"),
             ("groups", L("Employees", "الموظفون"), f"{p['employees']:,}" if p["employees"] else "—"),
             ("person", L("CEO", "الرئيس التنفيذي"), p["ceo"] or "—"),
             ("storefront", L("Exchange", "السوق"), p["exchange"] or "—")]
    web = f'<a href="{T.esc(p["website"])}" target="_blank" style="color:#7EA6FF">{T.esc(p["website"])}</a>' if p["website"] else "—"
    ui.html('<div class="prof">' + "".join(f'<div class="it"><div class="l">{T.icon(ic)}{T.esc(l)}</div><div class="v">{T.esc(v)}</div></div>'
                                           for ic, l, v in items)
            + f'<div class="it"><div class="l">{T.icon("language")}{L("Website", "الموقع الإلكتروني")}</div><div class="v">{web}</div></div></div>')
    if p["officers"]:
        ui.sec("badge", "Key executives", "كبار التنفيذيين")
        off = pd.DataFrame([{L("Name", "الاسم"): o.get("name"), L("Title", "المنصب"): o.get("title"),
                             L("Age", "العمر"): o.get("age")} for o in p["officers"]])
        st.dataframe(off, hide_index=True)
    if p["industry"]:
        peers = [s for s, v in U.STOCKS.items() if v[2] == p["industry"] and s != sym][:8]
        if peers:
            ui.sec("hub", "Peers in the same industry", "شركات منافسة في نفس الصناعة")
            ch = data.changes(peers)
            df = pd.DataFrame([{"Symbol": s, "Name": U.name_of(s), "Price": ch.get(s, (np.nan, np.nan))[0], "Chg %": ch.get(s, (np.nan, np.nan))[1]} for s in peers])
            ui.html(f'<div class="card">{ui.row_list(df, data.logos(peers))}</div>')


def _max_pain(calls, puts):
    strikes = sorted(set(calls.get("strike", pd.Series(dtype=float))) | set(puts.get("strike", pd.Series(dtype=float))))
    if not strikes:
        return None
    co, po = calls.fillna(0), puts.fillna(0)
    pain = [(k * 0 + (co["openInterest"] * np.maximum(k - co["strike"], 0)).sum() + (po["openInterest"] * np.maximum(po["strike"] - k, 0)).sum(), k)
            for k in strikes]
    return min(pain)[1]


def _chain_html(calls, puts, price, n):
    c = calls.set_index("strike") if not calls.empty else pd.DataFrame()
    p = puts.set_index("strike") if not puts.empty else pd.DataFrame()
    strikes = sorted(set(c.index) | set(p.index))
    if not strikes:
        return ""
    atm = min(range(len(strikes)), key=lambda i: abs(strikes[i] - price))
    if n:
        strikes = strikes[max(0, atm - n): atm + n + 1]
    cols = ["bid", "ask", "lastPrice", "percentChange", "volume", "openInterest", "impliedVolatility"]
    hdr = [L("Bid", "العرض"), L("Ask", "الطلب"), L("Last", "آخر"), L("Chg%", "التغير%"), L("Vol", "الحجم"), L("OI", "العقود المفتوحة"), "IV"]

    def cell(df, k, col, side):
        if df.empty or k not in df.index:
            return "<td>—</td>"
        v = df.loc[k, col]
        if isinstance(v, pd.Series):
            v = v.iloc[0]
        itm = (side == "c" and k < price) or (side == "p" and k > price)
        klass = f' class="itm-{side}"' if itm else ""
        if pd.isna(v):
            txt = "—"
        elif col == "impliedVolatility":
            txt = f"{v * 100:.1f}%"
        elif col == "percentChange":
            txt = f'<span class="{T.cls(v)}">{v:+.1f}%</span>'
        elif col in ("volume", "openInterest"):
            txt = f"{int(v):,}"
        else:
            txt = f"{v:,.2f}"
        return f"<td{klass}>{txt}</td>"
    rows = []
    above = False
    for k in strikes:
        atm_cls = ""
        if not above and k >= price:
            atm_cls, above = ' class="atm"', True
        rows.append(f"<tr{atm_cls}>" + "".join(cell(c, k, col, "c") for col in reversed(cols)) + f'<td class="k">{k:,.2f}</td>'
                    + "".join(cell(p, k, col, "p") for col in cols) + "</tr>")
    head = (f'<tr><th class="side" colspan="7" style="color:{T.UP}">{L("CALLS", "عقود الشراء CALL")}</th><th class="side">{L("Strike", "سعر التنفيذ")}</th>'
            f'<th class="side" colspan="7" style="color:{T.DOWN}">{L("PUTS", "عقود البيع PUT")}</th></tr><tr>'
            + "".join(f"<th>{h}</th>" for h in reversed(hdr)) + f'<th style="text-align:center">$</th>' + "".join(f"<th>{h}</th>" for h in hdr) + "</tr>")
    return f'<div class="chainwrap"><table class="chain"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'


def options_tab(sym, price):
    exps = data.expirations(sym)
    if not exps:
        st.info(L("No listed options for this symbol.", "لا توجد عقود خيارات مدرجة لهذا الرمز."), icon=":material/info:")
        return
    today = pd.Timestamp.now().normalize()

    def lab(e):
        d = (pd.Timestamp(e) - today).days
        return f"{pd.Timestamp(e):%b %d, %Y} · {d}{L('d', ' يوم')}"
    c1, c2, c3 = st.columns([1.4, 1, 1])
    exp = c1.selectbox(L("Expiration", "تاريخ الانتهاء"), exps[:24], format_func=lab)
    rng = c2.segmented_control(L("Strikes", "أسعار التنفيذ"), [8, 15, 30, 0], default=15, key="op_rng",
                               format_func=lambda n: L("All", "الكل") if n == 0 else f"±{n}") or 15
    view = c3.segmented_control(L("View", "العرض"), ["chain", "calls", "puts"], default="chain", key="op_view",
                                format_func=lambda v: {"chain": L("T-Chain", "الجدول الكامل"), "calls": "Calls", "puts": "Puts"}[v]) or "chain"
    with st.spinner(L("Loading option chain...", "جاري تحميل سلسلة الخيارات...")):
        calls, puts = data.option_chain(sym, exp)
    if calls.empty and puts.empty:
        st.warning(L("Option chain unavailable right now.", "سلسلة الخيارات غير متاحة حالياً."))
        return
    dte = max((pd.Timestamp(exp) - today).days, 0)
    atm_k = min(set(calls["strike"]) | set(puts["strike"]), key=lambda k: abs(k - price))

    def mid(df, k):
        r = df[df["strike"] == k]
        if r.empty:
            return np.nan
        r = r.iloc[0]
        return (r["bid"] + r["ask"]) / 2 if r["bid"] > 0 and r["ask"] > 0 else r["lastPrice"]
    straddle = np.nansum([mid(calls, atm_k), mid(puts, atm_k)])
    atm_iv = np.nanmean([calls.loc[calls["strike"] == atm_k, "impliedVolatility"].mean(), puts.loc[puts["strike"] == atm_k, "impliedVolatility"].mean()])
    pc_vol = puts["volume"].fillna(0).sum() / max(calls["volume"].fillna(0).sum(), 1)
    pc_oi = puts["openInterest"].fillna(0).sum() / max(calls["openInterest"].fillna(0).sum(), 1)
    mp = _max_pain(calls, puts)
    m = st.columns(6)
    m[0].metric(L("Underlying", "سعر السهم"), f"${price:,.2f}", L(f"{dte} days to expiry", f"{dte} يوم للانتهاء"), delta_color="off")
    m[1].metric(L("ATM implied vol.", "التذبذب الضمني"), f"{atm_iv * 100:.1f}%" if pd.notna(atm_iv) else "—")
    m[2].metric(L("Expected move", "الحركة المتوقعة"), f"±${straddle:,.2f}", f"±{straddle / price * 100:.1f}%", delta_color="off")
    m[3].metric(L("Put/Call volume", "نسبة PUT/CALL حجم"), f"{pc_vol:.2f}")
    m[4].metric(L("Put/Call open int.", "نسبة PUT/CALL عقود"), f"{pc_oi:.2f}")
    m[5].metric(L("Max pain", "نقطة الألم القصوى"), f"${mp:,.2f}" if mp else "—")
    st.caption(L("Expected move = at-the-money straddle price. Max pain = strike where option holders lose the most at expiration. "
                 "Shaded cells are in the money.",
                 "الحركة المتوقعة = سعر الستراديل عند سعر السوق. نقطة الألم القصوى = السعر الذي يخسر عنده حاملو العقود أكثر شيء عند الانتهاء. "
                 "الخانات المظللة داخل السعر (In the money)."))
    if view == "chain":
        ui.html(_chain_html(calls, puts, price, rng))
    else:
        df = calls if view == "calls" else puts
        cols = ["contractSymbol", "strike", "lastPrice", "bid", "ask", "percentChange", "volume", "openInterest", "impliedVolatility", "inTheMoney"]
        df = df[[c for c in cols if c in df]].copy()
        if rng:
            i = (df["strike"] - price).abs().idxmin()
            pos = df.index.get_loc(i)
            df = df.iloc[max(0, pos - rng): pos + rng + 1]
        df["impliedVolatility"] = df["impliedVolatility"] * 100
        st.dataframe(df.style.map(T.color_style, subset=["percentChange"]).format(
            {"strike": "{:,.2f}", "lastPrice": "{:,.2f}", "bid": "{:,.2f}", "ask": "{:,.2f}", "percentChange": "{:+.1f}%", "impliedVolatility": "{:.1f}%",
             "volume": "{:,.0f}", "openInterest": "{:,.0f}"}, na_rep="—"), hide_index=True, height=520)
    a, b = st.columns(2)
    win = lambda d: d[(d["strike"] > price * 0.7) & (d["strike"] < price * 1.3)]
    a.plotly_chart(charts.oi_by_strike(win(calls), win(puts), price, L("Open interest by strike", "العقود المفتوحة حسب سعر التنفيذ"),
                                       (L("Calls", "شراء"), L("Puts", "بيع"))))
    b.plotly_chart(charts.iv_smile(win(calls), win(puts), price, L("Implied volatility smile", "منحنى التذبذب الضمني"),
                                   (L("Calls IV", "تذبذب الشراء"), L("Puts IV", "تذبذب البيع"))))
    ui.sec("local_fire_department", "Most active contracts", "العقود الأكثر تداولاً")
    act = pd.concat([calls.assign(Type="CALL"), puts.assign(Type="PUT")])
    act = act.sort_values("volume", ascending=False).head(10)[["Type", "contractSymbol", "strike", "lastPrice", "percentChange", "volume", "openInterest", "impliedVolatility"]]
    act["impliedVolatility"] = act["impliedVolatility"] * 100
    st.dataframe(act.style.map(T.color_style, subset=["percentChange"]).format(
        {"strike": "{:,.2f}", "lastPrice": "{:,.2f}", "percentChange": "{:+.1f}%", "impliedVolatility": "{:.1f}%", "volume": "{:,.0f}",
         "openInterest": "{:,.0f}"}, na_rep="—"), hide_index=True)


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
            if st.button(L("Add to watchlist", "أضف للمتابعة"), icon=":material/star:", width="stretch"):
                ss.watchlist.append(sym)
                st.rerun()
        else:
            st.button(L("In watchlist", "في المتابعة"), icon=":material/star:", disabled=True, width="stretch")
        if st.button("Catalyst Pro", icon=":material/bolt:", width="stretch"):
            ui.goto("catalyst")
    key_stats(daily, inf)
    tabs = st.tabs([L(":material/candlestick_chart: Chart", ":material/candlestick_chart: الرسم البياني"),
                    L(":material/apartment: Company", ":material/apartment: عن الشركة"),
                    L(":material/speed: Technicals", ":material/speed: التحليل الفني"),
                    L(":material/request_quote: Financials", ":material/request_quote: المالية"),
                    L(":material/groups: Analysts", ":material/groups: المحللون"),
                    L(":material/tune: Options", ":material/tune: الخيارات"),
                    L(":material/newspaper: News", ":material/newspaper: الأخبار")])
    with tabs[0]:
        chart_tab(sym, daily)
    with tabs[1]:
        company_tab(sym)
    with tabs[2]:
        technicals_tab(daily)
    with tabs[3]:
        financials_tab(sym, inf)
    with tabs[4]:
        analysts_tab(sym, inf, price)
    with tabs[5]:
        options_tab(sym, float(price))
    with tabs[6]:
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
    "ai": ("AI leaders", "قادة الذكاء الاصطناعي", {"theme": "ai"}),
    "nuclear": ("Clean energy & nuclear", "الطاقة النظيفة والنووية", {"theme": "power"}),
}


def _apply_preset():
    p = PRESETS[ss.sc_preset][2]
    for k in F:
        ss[f"sf_{k}"] = p.get(k, 0)
    ss["sf_theme"] = p.get("theme", "Any")
    ss["sf_subtheme"] = "Any"


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


def _theme_opts():
    return ["Any"] + list(X.THEMES)


def page_screener():
    ui.header("filter_alt", "Stock Screener", "فلتر الأسهم",
              "Filter the entire US market by sector, industry, investment theme, valuation, growth, dividends, short interest and technicals.",
              "فلترة السوق الأمريكي كامل حسب القطاع والصناعة والثيم الاستثماري والتقييم والنمو والتوزيعات والبيع على المكشوف والتحليل الفني.")
    top = st.columns([1.4, 1, 1, 0.8])
    top[0].selectbox(L("Preset", "قالب جاهز"), list(PRESETS), key="sc_preset", on_change=_apply_preset,
                     format_func=lambda k: L(PRESETS[k][0], PRESETS[k][1]))
    sort = top[1].selectbox(L("Order by", "ترتيب حسب"), list(SORTS), format_func=lambda k: L(SORTS[k][0], SORTS[k][1]))
    size = top[2].selectbox(L("Results", "عدد النتائج"), [50, 100, 250], index=1)
    top[3].write("")
    run = top[3].button(L("Screen", "ابحث"), type="primary", icon=":material/search:", width="stretch")

    # ---- classification row (always visible): sector · industry · theme · sub-theme
    c = st.columns(4)
    c[0].selectbox(L("Sector", "القطاع"), ["Any"] + U.SECTORS, key="sf_sector",
                   format_func=lambda s_: L("Any", "الكل") if s_ == "Any" else sector_name(s_))
    sec = ss.get("sf_sector", "Any")
    iopts = ["Any"] + (U.INDUSTRIES.get(sec, []) if sec != "Any" else [])
    if ss.get("sf_industry") not in iopts:
        ss["sf_industry"] = "Any"
    c[1].selectbox(L("Industry", "الصناعة"), iopts, key="sf_industry", disabled=sec == "Any",
                   format_func=lambda s_: L("Any", "الكل") if s_ == "Any" else industry_name(s_))
    c[2].selectbox(L("Theme", "الثيم الاستثماري"), _theme_opts(), key="sf_theme",
                   format_func=lambda t: L("Any", "الكل") if t == "Any" else theme_name(t))
    th = ss.get("sf_theme", "Any")
    sopts = ["Any"] + (list(X.THEMES[th][3]) if th != "Any" else [])
    if ss.get("sf_subtheme") not in sopts:
        ss["sf_subtheme"] = "Any"
    c[3].selectbox(L("Sub-theme", "الثيم الفرعي"), sopts, key="sf_subtheme", disabled=th == "Any",
                   format_func=lambda k: L("Any", "الكل") if k == "Any" else theme_name(th, k))

    groups = {"desc": L("Descriptive", "وصفية"), "fund": L("Fundamental", "أساسية"), "tech": L("Technical", "فنية")}
    tabs = st.tabs(list(groups.values()))
    for tab, g in zip(tabs, groups):
        with tab:
            keys = [k for k, v in F.items() if v[2] == g or (g == "tech" and v[2] == "local")]
            cols = st.columns(4)
            for i, k in enumerate(keys):
                en, ar, _, opts = F[k]
                ss.setdefault(f"sf_{k}", 0)
                cols[i % 4].selectbox(L(en, ar), list(range(len(opts))), key=f"sf_{k}", format_func=lambda i_, o=opts: L(o[i_][0], o[i_][1]))

    active = [(k, ss.get(f"sf_{k}", 0)) for k in F if ss.get(f"sf_{k}", 0)]
    chips = [T.badge(f"{L(F[k][0], F[k][1])}: {L(F[k][3][v][0], F[k][3][v][1])}", "acc", "filter_alt") for k, v in active]
    if sec != "Any":
        chips.append(T.badge(sector_name(sec), "acc", "category"))
    if ss.get("sf_industry", "Any") != "Any":
        chips.append(T.badge(industry_name(ss.sf_industry), "vio", "factory"))
    if th != "Any":
        chips.append(T.badge(theme_name(th) + ("" if ss.get("sf_subtheme", "Any") == "Any" else f" › {theme_name(th, ss.sf_subtheme)}"), "gold", X.THEMES[th][2]))
    if chips:
        ui.html(" ".join(chips))

    theme_syms = X.theme_tickers(th, None if ss.get("sf_subtheme", "Any") == "Any" else ss.sf_subtheme) if th != "Any" else None
    if run or "screen" not in ss:
        filters = []
        for k in F:
            v = ss.get(f"sf_{k}", 0)
            if v and F[k][2] != "local":
                filters += [list(f) for f in F[k][3][v][2]]
        if sec != "Any":
            filters.append(["eq", "sector", sec])
        if ss.get("sf_industry", "Any") != "Any":
            filters.append(["eq", "industry", ss.sf_industry])
        if theme_syms and sec == "Any":
            filters.append(["or_eq", "sector", sorted({U.sector_of(t) for t in theme_syms} - {"Other"})])
        with st.spinner(L("Screening the US market...", "جاري فلترة السوق الأمريكي...")):
            df, err = data.screen_custom(filters, sort, SORTS[sort][2], 250 if theme_syms else size)
            source = "live"
            if theme_syms is not None:
                have = set(df["Symbol"]) if not df.empty else set()
                df = df[df["Symbol"].isin(theme_syms)] if not df.empty else df
                missing = [t for t in theme_syms if t not in have]
                if missing:
                    ch = data.changes(missing)
                    extra = pd.DataFrame([{"Symbol": t, "Name": U.name_of(t), "Price": ch[t][0], "Chg %": ch[t][1]} for t in missing if t in ch])
                    df = pd.concat([df, extra], ignore_index=True) if not df.empty else extra
            if df.empty and theme_syms is None:
                source = "fallback"
                fb = data.changes(tuple(U.US_UNIVERSE))
                df = pd.DataFrame([{"Symbol": s_, "Name": U.name_of(s_), "Price": p_, "Chg %": c_, "Mkt Cap": U.STOCKS[s_][3] * 1e9}
                                   for s_, (p_, c_) in fb.items()])
                if sec != "Any" and not df.empty:
                    df = df[df["Symbol"].map(U.sector_of) == sec]
        ss.screen = {"df": df, "err": err, "source": source}

    res = ss.screen
    df = _local_filters(res["df"].copy()) if not res["df"].empty else res["df"]
    if res["source"] == "fallback":
        st.warning(L("Live screener unavailable right now; showing the top 175 US stocks with price filters only.",
                     "الفلتر المباشر غير متاح حالياً؛ نعرض أكبر 175 سهم أمريكي مع فلاتر السعر فقط."), icon=":material/cloud_off:")
    if df.empty:
        st.info(L("No stocks match these filters.", "لا توجد أسهم تطابق هذه الفلاتر."))
        return
    tech = _technicals(df["Symbol"].head(150).tolist())
    if not tech.empty:
        df = df.merge(tech, on="Symbol", how="left")
        if ss.get("sf_rsi", 0):
            df = df[{1: df["RSI"] < 30, 2: df["RSI"] > 70, 3: df["RSI"].between(40, 60)}[ss.sf_rsi]]
    # ---- classification columns
    with st.spinner(L("Classifying companies...", "جاري تصنيف الشركات...")):
        cls_map = data.classify(df["Symbol"].tolist(), limit=40)
    df["_sector"] = df["Symbol"].map(lambda s_: sec if sec != "Any" else (cls_map.get(s_, (None, None))[0]))
    df["_industry"] = df["Symbol"].map(lambda s_: ss.sf_industry if ss.get("sf_industry", "Any") != "Any" else (cls_map.get(s_, (None, None))[1]))
    df["Sector"] = df["_sector"].map(lambda v: sector_name(v) if v else "—")
    df["Industry"] = df["_industry"].map(lambda v: industry_name(v) if v else "—")
    df["Theme"] = df["Symbol"].map(lambda s_: " · ".join(dict.fromkeys(theme_name(t) for t, _ in X.themes_of(s_))) or "—")
    df["Sub-theme"] = df["Symbol"].map(lambda s_: " · ".join(theme_name(t, k) for t, k in X.themes_of(s_)) or "—")
    df.insert(0, "Logo", df["Symbol"].map(data.logo_url))

    m = st.columns(4)
    m[0].metric(L("Matches", "النتائج"), len(df))
    m[1].metric(L("Advancing", "صاعدة"), int((df["Chg %"] > 0).sum()))
    m[2].metric(L("Median P/E", "وسيط مكرر الربحية"), f"{df['P/E'].median():.1f}" if "P/E" in df and df["P/E"].notna().any() else "—")
    m[3].metric(L("Total market cap", "إجمالي القيمة السوقية"), T.fmt_big(df["Mkt Cap"].sum()) if "Mkt Cap" in df else "—")

    N = {"Symbol": L("Ticker", "الرمز"), "Name": L("Company", "الشركة"), "Sector": L("Sector", "القطاع"), "Industry": L("Industry", "الصناعة"),
         "Theme": L("Theme", "الثيم"), "Sub-theme": L("Sub-theme", "الثيم الفرعي"), "Mkt Cap": L("Market cap", "القيمة السوقية"),
         "Price": L("Price", "السعر"), "Chg %": L("Change", "التغير"), "Volume": L("Volume", "الحجم"), "P/E": "P/E", "Fwd P/E": "Fwd P/E",
         "P/B": "P/B", "EPS": "EPS", "Div %": L("Dividend", "التوزيعات"), "52W %": L("52W perf", "أداء سنوي"), "Rating": L("Analyst rating", "تقييم المحللين"),
         "Perf W": L("Perf week", "أسبوع"), "Perf M": L("Perf month", "شهر"), "Perf 3M": L("Perf quarter", "3 أشهر"), "Perf YTD": L("Perf YTD", "منذ بداية العام"),
         "RSI": "RSI", "Volatility": L("Volatility", "التذبذب"), "Logo": ""}
    views = {L("Overview", "نظرة عامة"): ["Logo", "Symbol", "Name", "Sector", "Industry", "Mkt Cap", "P/E", "Price", "Chg %", "Volume"],
             L("Classification", "التصنيف"): ["Logo", "Symbol", "Name", "Sector", "Industry", "Theme", "Sub-theme"],
             L("Valuation", "التقييم"): ["Logo", "Symbol", "Mkt Cap", "P/E", "Fwd P/E", "P/B", "EPS", "Div %", "Rating"],
             L("Performance", "الأداء"): ["Logo", "Symbol", "Price", "Chg %", "Perf W", "Perf M", "Perf 3M", "Perf YTD", "52W %", "RSI", "Volatility"]}
    vt = st.tabs(list(views) + [L("Charts", "الرسوم")])
    for tab, (vname, cols) in zip(vt, views.items()):
        with tab:
            cols = [c_ for c_ in cols if c_ in df.columns]
            show = df[cols].copy()
            for c_ in ("Mkt Cap", "Volume"):
                if c_ in show:
                    show[c_] = show[c_].map(T.fmt_big)
            pct_cols = [c_ for c_ in ("Chg %", "Perf W", "Perf M", "Perf 3M", "Perf YTD", "52W %") if c_ in show]
            show = show.rename(columns=N)
            fmt = {**{N[c_]: "{:+.2f}%" for c_ in pct_cols}, **{N[c_]: "{:,.2f}" for c_ in ("Price", "P/E", "Fwd P/E", "P/B", "EPS") if c_ in cols}}
            if "Div %" in cols:
                fmt[N["Div %"]] = "{:.2f}%"
            if "RSI" in cols:
                fmt["RSI"] = "{:.0f}"
            if "Volatility" in cols:
                fmt[N["Volatility"]] = "{:.1f}%"
            st.dataframe(show.style.map(T.color_style, subset=[N[c_] for c_ in pct_cols]).format(fmt, na_rep="—"), hide_index=True, height=540,
                         column_config={"": st.column_config.ImageColumn("", width="small")})
    with vt[-1]:
        if "_spark" in df:
            lg = data.logos(df["Symbol"].head(36).tolist())
            items = []
            for _, r in df.head(36).iterrows():
                sp = r["_spark"] if isinstance(r["_spark"], np.ndarray) else None
                head = f'<div style="margin-bottom:4px">{T.company(r["Symbol"], str(r["Name"])[:22], lg.get(r["Symbol"]), 26)}</div>'
                items.append(T.tile("", T.fmt_price(r["Price"]), None, r["Chg %"], sp, head_html=head))
            ui.html(T.tiles(items))
    a, b, c_ = st.columns([2, 1, 1])
    pick = a.selectbox(L("Selected stock", "السهم المختار"), df["Symbol"].tolist())
    if b.button(L("Open stock", "افتح السهم"), icon=":material/candlestick_chart:", key="sc_open", width="stretch"):
        ui.open_stock(pick)
    c_.download_button(L("Export CSV", "تصدير CSV"), df.drop(columns=["_spark", "Logo", "_sector", "_industry"], errors="ignore").to_csv(index=False).encode(),
                       "screener.csv", "text/csv", icon=":material/download:", width="stretch")
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
