"""
p_research.py - Stock · Screener (Finviz-style) · Scanner · Catalyst Pro
"""
import time
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
    ui.chart(charts.price_chart(d, ctype, overlays, panels, intraday), key="st_chart")


def _counts(t):
    return [(f'{sig("Sell")} {int((t["Signal"] == "Sell").sum())}', "neg"), (f'{sig("Neutral")} {int((t["Signal"] == "Neutral").sum())}', "neu"),
            (f'{sig("Buy")} {int((t["Signal"] == "Buy").sum())}', "pos")]


def technicals_tab(daily):
    d = ta.add_all(daily)
    table, total, label, parts = ta.technical_summary(d)
    if table.empty:
        st.info(L("Not enough data for technical analysis.", "لا توجد بيانات كافية للتحليل الفني."))
        return
    labels = [sig(x) for x in ("Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy")]
    is_ma = table["Indicator"].str.startswith(("EMA", "SMA"))
    osc, mas = parts.get("Oscillators", 0), parts.get("Moving Averages", 0)
    c1, c2, c3 = st.columns(3)
    c1.markdown(T.rating_meter(osc, sig(ta.label_for(osc)), L("Oscillators", "المذبذبات"), _counts(table[~is_ma]), labels), unsafe_allow_html=True)
    c2.markdown(T.rating_meter(total, sig(label), L("Summary", "الملخص"), _counts(table), labels), unsafe_allow_html=True)
    c3.markdown(T.rating_meter(mas, sig(ta.label_for(mas)), L("Moving averages", "المتوسطات المتحركة"), _counts(table[is_ma]), labels),
                unsafe_allow_html=True)

    # ---- performance strip
    ui.sec("trending_up", "Performance", "الأداء")
    c = daily["Close"]
    cells = []
    for lab, n in (("1D", 1), ("1W", 5), ("1M", 21), ("3M", 63), ("6M", 126), ("YTD", "ytd"), ("1Y", 252)):
        if n == "ytd":
            y = c[c.index.year == c.index[-1].year]
            v = (c.iloc[-1] / y.iloc[0] - 1) * 100 if len(y) > 1 else np.nan
        else:
            v = (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100 if len(c) > n else np.nan
        if pd.notna(v):
            cells.append(f'<div class="pc2 {T.cls(v)}"><div class="l">{lab}</div><div class="v">{v:+.2f}%</div></div>')
    ui.html('<div class="perfrow">' + "".join(cells) + "</div>")

    # ---- key readings
    last = d.iloc[-1]
    price = float(last["Close"])

    def m(label_, value, kind="neu"):
        return f'<div class="m {kind}"><div class="l">{label_}</div><div class="v">{value}</div></div>'
    rsi = last.get("RSI", np.nan)
    rsi_kind = "pos" if rsi < 30 else ("neg" if rsi > 70 else "neu")
    rsi_note = L("oversold", "تشبع بيعي") if rsi < 30 else (L("overbought", "تشبع شرائي") if rsi > 70 else L("neutral", "محايد"))
    adx = last.get("ADX", np.nan)
    vol_x = last["Volume"] / last["VolAvg20"] if "VolAvg20" in d and last.get("VolAvg20") else np.nan
    s50, s200 = last.get("SMA50", np.nan), last.get("SMA200", np.nan)
    d50 = (price / s50 - 1) * 100 if pd.notna(s50) else np.nan
    d200 = (price / s200 - 1) * 100 if pd.notna(s200) else np.nan
    cards = [m("RSI (14)", f"{rsi:.1f} · {rsi_note}", rsi_kind),
             m(L("Trend strength (ADX)", "قوة الاتجاه ADX"), f"{adx:.0f} · " + (L("strong", "قوي") if adx > 25 else L("weak", "ضعيف")), "neu") if pd.notna(adx) else "",
             m(L("vs SMA 50", "مقابل متوسط 50"), f"{d50:+.2f}%", T.cls(d50)) if pd.notna(d50) else "",
             m(L("vs SMA 200", "مقابل متوسط 200"), f"{d200:+.2f}%", T.cls(d200)) if pd.notna(d200) else "",
             m("ATR (14)", f"{last['ATR']:.2f} · {last['ATR'] / price * 100:.1f}%") if pd.notna(last.get("ATR", np.nan)) else "",
             m(L("Bollinger width", "عرض بولنجر"), f"{last['BB_width'] * 100:.1f}%") if pd.notna(last.get("BB_width", np.nan)) else "",
             m(L("Volume vs 20-day avg", "الحجم مقابل متوسط 20"), f"{vol_x:.2f}×", "pos" if vol_x > 1.2 else "neu") if pd.notna(vol_x) else "",
             m("MACD", f"{last['MACD']:.2f} / {last['MACD_signal']:.2f}", T.cls(last["MACD"] - last["MACD_signal"])) if pd.notna(last.get("MACD", np.nan)) else ""]
    ui.html('<div class="mx">' + "".join(cards) + "</div>")

    left, right = st.columns([1.35, 1])
    with left:
        ui.sec("tune", "Indicator signals", "إشارات المؤشرات")
        items = []
        for _, r in table.iterrows():
            k = {"Buy": "pos", "Sell": "neg"}.get(r["Signal"], "neu")
            items.append(f'<div class="sg"><div><div class="n">{T.esc(r["Indicator"])}</div><div class="v">{r["Value"]:,.2f}</div></div>'
                         f'<span class="pill {k}" style="min-width:64px">{T.esc(sig(r["Signal"]))}</span></div>')
        ui.html('<div class="sigs">' + "".join(items) + "</div>")
    with right:
        ui.sec("stacked_line_chart", "Price ladder: pivots & support / resistance", "سلّم الأسعار: الارتكاز والدعوم والمقاومات")
        piv = ta.pivot_points(daily)
        levels = [(k, v, "res" if k.startswith("R") else ("sup" if k.startswith("S") else "piv")) for k, v in piv.items()]
        sw = ta.swing_levels(daily)
        res_ = sorted([x for x in sw if x > price])[:3]
        sup_ = sorted([x for x in sw if x < price], reverse=True)[:3]
        levels += [(L(f"Res {i + 1}", f"مقاومة {i + 1}"), v, "res") for i, v in enumerate(res_)]
        levels += [(L(f"Sup {i + 1}", f"دعم {i + 1}"), v, "sup") for i, v in enumerate(sup_)]
        ui.html(T.ladder(levels, price, L("Price", "السعر")))
        st.caption(L("R = resistance above the price, S = support below it, P = pivot. Distance is from the current price.",
                     "R = مقاومة فوق السعر، S = دعم تحت السعر، P = نقطة الارتكاز. المسافة محسوبة من السعر الحالي."))


# ---------------------------------------------------------------- financials
FIN_METRICS = {
    "rev": ("Revenue", "الإيرادات", "money"), "gp": ("Gross profit", "إجمالي الربح", "money"),
    "op": ("Operating income", "الدخل التشغيلي", "money"), "ni": ("Net income", "صافي الدخل", "money"),
    "ebitda": ("EBITDA", "EBITDA", "money"), "eps": ("EPS (diluted)", "ربحية السهم", "eps"),
    "gm": ("Gross margin", "الهامش الإجمالي", "pct"), "om": ("Operating margin", "الهامش التشغيلي", "pct"),
    "nm": ("Net margin", "صافي الهامش", "pct"), "roe": ("Return on equity", "العائد على حقوق الملكية", "pct"),
    "roa": ("Return on assets", "العائد على الأصول", "pct"), "ocf": ("Operating cash flow", "التدفق النقدي التشغيلي", "money"),
    "capex": ("Capital expenditure", "الإنفاق الرأسمالي", "money"), "fcf": ("Free cash flow", "التدفق النقدي الحر", "money"),
    "div": ("Dividends paid", "التوزيعات المدفوعة", "money"), "buyback": ("Share buybacks", "إعادة شراء الأسهم", "money"),
    "cash": ("Cash & equivalents", "النقد وما يعادله", "money"), "debt": ("Total debt", "إجمالي الديون", "money"),
    "equity": ("Shareholders' equity", "حقوق المساهمين", "money"), "de": ("Debt / equity", "الديون / حقوق الملكية", "ratio"),
    "cr": ("Current ratio", "نسبة التداول", "ratio"),
}


def _stmt_row(df, *names):
    if not isinstance(df, pd.DataFrame) or df.empty:
        return None
    for n in names:
        if n in df.index:
            s = df.loc[n]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[0]
            s = pd.to_numeric(s, errors="coerce")
            s.index = pd.to_datetime(s.index, errors="coerce")
            s = s[s.index.notna()].sort_index()
            return s if s.notna().any() else None
    return None


def fin_series(stm, freq="a"):
    inc, bal, cf = stm.get(f"inc_{freq}"), stm.get(f"bal_{freq}"), stm.get(f"cf_{freq}")
    r = lambda df, *n: _stmt_row(df, *n)
    out = {"rev": r(inc, "Total Revenue", "Operating Revenue"), "gp": r(inc, "Gross Profit"),
           "op": r(inc, "Operating Income", "EBIT"), "ni": r(inc, "Net Income", "Net Income Common Stockholders"),
           "ebitda": r(inc, "EBITDA", "Normalized EBITDA"), "eps": r(inc, "Diluted EPS", "Basic EPS"),
           "ocf": r(cf, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities"),
           "capex": r(cf, "Capital Expenditure"), "fcf": r(cf, "Free Cash Flow"),
           "div": r(cf, "Cash Dividends Paid", "Common Stock Dividend Paid"),
           "buyback": r(cf, "Repurchase Of Capital Stock", "Common Stock Payments"),
           "cash": r(bal, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"),
           "debt": r(bal, "Total Debt"), "equity": r(bal, "Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest")}
    assets = r(bal, "Total Assets")
    ca, cl = r(bal, "Current Assets"), r(bal, "Current Liabilities")
    if out["fcf"] is None and out["ocf"] is not None and out["capex"] is not None:
        out["fcf"] = out["ocf"] + out["capex"]
    ann = 4 if freq == "q" else 1
    rev, ni, eq = out["rev"], out["ni"], out["equity"]
    if rev is not None:
        for k, src in (("gm", "gp"), ("om", "op"), ("nm", "ni")):
            if out[src] is not None:
                out[k] = (out[src] / rev.replace(0, np.nan) * 100).dropna()
    if ni is not None and eq is not None:
        out["roe"] = (ni * ann / eq.replace(0, np.nan) * 100).dropna()
    if ni is not None and assets is not None:
        out["roa"] = (ni * ann / assets.replace(0, np.nan) * 100).dropna()
    if out["debt"] is not None and eq is not None:
        out["de"] = (out["debt"] / eq.replace(0, np.nan)).dropna()
    if ca is not None and cl is not None:
        out["cr"] = (ca / cl.replace(0, np.nan)).dropna()
    return {k: v for k, v in out.items() if v is not None and v.notna().any()}


def _period_labels(idx, freq):
    out = []
    for d in idx:
        lab = (f"FY{d.year}" if freq == "a" else f"Q{(d.month - 1) // 3 + 1} {d.year}") if pd.notna(d) else "—"
        while lab in out:
            lab += "'"
        out.append(lab)
    return out


def _fmt_metric(v, kind):
    if v is None or pd.isna(v):
        return "—"
    if kind == "money":
        return ("-" if v < 0 else "") + "$" + T.fmt_big(abs(v))
    if kind == "pct":
        return f"{v:.1f}%"
    if kind == "eps":
        return f"${v:.2f}"
    return f"{v:.2f}"


def financials_tab(sym, inf):
    def pct(k):
        v = inf.get(k)
        return (f"{v * 100:.2f}%", T.cls(v)) if isinstance(v, (int, float)) else ("—", "neu")

    def num(k, dec=2):
        v = inf.get(k)
        return (f"{v:,.{dec}f}", "neu") if isinstance(v, (int, float)) else ("—", "neu")
    big = lambda k: (T.fmt_big(inf.get(k)), "neu")
    groups = {
        ("Valuation", "التقييم", "price_check"): [
            (L("Market cap", "القيمة السوقية"), big("marketCap")), (L("Enterprise value", "قيمة المنشأة"), big("enterpriseValue")),
            ("P/E (TTM)", num("trailingPE")), (L("Forward P/E", "المكرر المستقبلي"), num("forwardPE")), ("PEG", num("trailingPegRatio")),
            ("P/S", num("priceToSalesTrailing12Months")), ("P/B", num("priceToBook")), ("EV/EBITDA", num("enterpriseToEbitda"))],
        ("Profitability", "الربحية", "savings"): [
            (L("Gross margin", "الهامش الإجمالي"), pct("grossMargins")), (L("Operating margin", "الهامش التشغيلي"), pct("operatingMargins")),
            (L("Profit margin", "صافي الهامش"), pct("profitMargins")), ("ROE", pct("returnOnEquity")), ("ROA", pct("returnOnAssets"))],
        ("Growth", "النمو", "trending_up"): [
            (L("Revenue growth", "نمو الإيرادات"), pct("revenueGrowth")), (L("Earnings growth", "نمو الأرباح"), pct("earningsGrowth")),
            (L("Qtr earnings growth", "نمو الأرباح الفصلي"), pct("earningsQuarterlyGrowth")),
            (L("Revenue (TTM)", "الإيرادات"), big("totalRevenue")), ("EBITDA", big("ebitda"))],
        ("Balance sheet", "الميزانية", "account_balance_wallet"): [
            (L("Total cash", "النقد"), big("totalCash")), (L("Total debt", "الديون"), big("totalDebt")),
            (L("Debt/Equity", "الديون/الملكية"), num("debtToEquity", 1)), (L("Current ratio", "نسبة التداول"), num("currentRatio")),
            (L("Free cash flow", "التدفق النقدي الحر"), (T.fmt_big(inf.get("freeCashflow")), T.cls(inf.get("freeCashflow"))))],
    }
    cols = st.columns(4)
    for col, ((gen, gar, ic), items) in zip(cols, groups.items()):
        with col:
            ui.sec(ic, gen, gar)
            ui.html('<div class="mx" style="grid-template-columns:1fr">' + "".join(
                f'<div class="m {k}"><div class="l">{l}</div><div class="v">{v}</div></div>' for l, (v, k) in items) + "</div>")

    with st.spinner(L("Loading financial statements...", "جاري تحميل القوائم المالية...")):
        stm = data.statements(sym)
    if all(v.empty for v in stm.values()):
        st.info(L("Financial statements are not available for this symbol.", "القوائم المالية غير متاحة لهذا الرمز."))
        return

    # ---- interactive explorer: click a metric, see its history
    ui.sec("insights", "Interactive metric explorer", "مستكشف المؤشرات التفاعلي")
    a, b = st.columns([5, 1.2], vertical_alignment="bottom")
    freq = b.segmented_control(L("Period", "الفترة"), ["a", "q"], default="a", key="fin_freq",
                               format_func=lambda k: L("Annual", "سنوي") if k == "a" else L("Quarterly", "ربعي")) or "a"
    series = fin_series(stm, freq)
    avail = [k for k in FIN_METRICS if k in series]
    if not avail:
        st.caption(L("No statement data for this period.", "لا توجد بيانات لهذه الفترة."))
    else:
        if ss.get("fin_metric") not in avail:
            ss["fin_metric"] = "rev" if "rev" in avail else avail[0]
        pick = a.pills(L("Choose a metric", "اختر المؤشر"), avail, key="fin_metric", selection_mode="single",
                       format_func=lambda k: L(FIN_METRICS[k][0], FIN_METRICS[k][1])) or avail[0]
        s_ = series[pick]
        en, ar, kind = FIN_METRICS[pick]
        labels_ = _period_labels(s_.index, freq)
        vals = [float(v) if pd.notna(v) else np.nan for v in s_.values]
        note = L(" (annualized)", " (سنوي)") if pick in ("roe", "roa") and freq == "q" else ""
        ui.chart(charts.metric_bars(labels_, vals, L(en, ar) + note, kind), key="fin_chart")
        last_v = vals[-1]
        prev_v = vals[-2] if len(vals) > 1 else np.nan
        yoy_v = vals[-5] if freq == "q" and len(vals) > 4 else (prev_v if freq == "a" else np.nan)

        def chg(x, y):
            if pd.isna(x) or pd.isna(y) or y == 0:
                return None
            return (x - y) if kind in ("pct", "ratio") else (x / abs(y) - 1) * 100 if y > 0 else (x - y) / abs(y) * 100
        c_prev, c_yoy = chg(last_v, prev_v), chg(last_v, yoy_v)
        unit = L(" pts", " نقطة") if kind in ("pct", "ratio") else "%"
        k1, k2, k3 = st.columns(3)
        k1.markdown(T.kpi("flag", L("Latest", "الأحدث") + f" · {labels_[-1]}", _fmt_metric(last_v, kind), "", T.cls(last_v) if kind != "ratio" else None),
                    unsafe_allow_html=True)
        k2.markdown(T.kpi("swap_vert", L("vs previous period", "مقابل الفترة السابقة"), f"{c_prev:+.1f}{unit}" if c_prev is not None else "—", "",
                          T.cls(c_prev) if c_prev is not None else None), unsafe_allow_html=True)
        k3.markdown(T.kpi("event_repeat", L("vs a year earlier", "مقابل قبل سنة"), f"{c_yoy:+.1f}{unit}" if c_yoy is not None else "—", "",
                          T.cls(c_yoy) if c_yoy is not None else None), unsafe_allow_html=True)

    # ---- cash flow
    ui.sec("payments", "Cash flow", "التدفقات النقدية")
    ca = fin_series(stm, "a")
    ocf, capex, fcf = ca.get("ocf"), ca.get("capex"), ca.get("fcf")
    if ocf is None and fcf is None:
        st.caption(L("Cash flow statement is not available for this symbol.", "قائمة التدفقات النقدية غير متاحة لهذا الرمز."))
    else:
        base = (fcf if fcf is not None else ocf).dropna()
        idx = base.index
        get = lambda s, d: float(s.get(d, np.nan)) if s is not None else np.nan
        last_d = idx[-1]
        rev = ca.get("rev")
        f_last, o_last = get(fcf, last_d), get(ocf, last_d)
        cap = inf.get("marketCap")
        ni_last = get(ca.get("ni"), last_d)
        k = st.columns(5)
        k[0].markdown(T.kpi("account_balance", L("Operating cash flow", "التدفق التشغيلي"), _fmt_metric(o_last, "money"), f"FY{last_d.year}", T.cls(o_last)),
                      unsafe_allow_html=True)
        k[1].markdown(T.kpi("savings", L("Free cash flow", "التدفق النقدي الحر"), _fmt_metric(f_last, "money"), f"FY{last_d.year}", T.cls(f_last)),
                      unsafe_allow_html=True)
        fm = f_last / get(rev, last_d) * 100 if rev is not None and get(rev, last_d) else np.nan
        k[2].markdown(T.kpi("percent", L("FCF margin", "هامش التدفق الحر"), f"{fm:.1f}%" if pd.notna(fm) else "—", L("of revenue", "من الإيرادات"),
                            T.cls(fm) if pd.notna(fm) else None), unsafe_allow_html=True)
        fy = f_last / cap * 100 if cap and pd.notna(f_last) else np.nan
        k[3].markdown(T.kpi("sell", L("FCF yield", "عائد التدفق الحر"), f"{fy:.2f}%" if pd.notna(fy) else "—", L("FCF / market cap", "التدفق / القيمة السوقية"),
                            T.cls(fy) if pd.notna(fy) else None), unsafe_allow_html=True)
        cc = o_last / ni_last if pd.notna(ni_last) and ni_last > 0 and pd.notna(o_last) else np.nan
        k[4].markdown(T.kpi("sync_alt", L("Cash conversion", "جودة الأرباح النقدية"), f"{cc:.2f}×" if pd.notna(cc) else "—",
                            L("operating cash / net income", "النقد التشغيلي / صافي الدخل"), ("pos" if cc >= 1 else "neg") if pd.notna(cc) else None),
                      unsafe_allow_html=True)
        left, right = st.columns([1.25, 1])
        with left:
            per = _period_labels(idx, "a")
            margin = [get(fcf, d) / get(rev, d) * 100 if rev is not None and get(rev, d) else None for d in idx] if fcf is not None else None
            ui.chart(charts.cash_trend(per, [get(ocf, d) for d in idx], [get(capex, d) for d in idx], [get(fcf, d) for d in idx], margin,
                                       L("Cash flow trend", "اتجاه التدفقات النقدية"),
                                       (L("Operating cash flow", "التدفق التشغيلي"), L("Capital expenditure", "الإنفاق الرأسمالي"),
                                        L("Free cash flow", "التدفق النقدي الحر"), L("FCF margin", "هامش التدفق الحر"))), key="cf_trend")
        with right:
            items = []
            if pd.notna(o_last):
                items.append((L("Operating CF", "التشغيلي"), o_last, "relative"))
            cx = get(capex, last_d)
            if pd.notna(cx):
                items.append((L("CapEx", "الإنفاق الرأسمالي"), cx, "relative"))
            items.append((L("Free CF", "التدفق الحر"), 0, "total"))
            for key_, en_, ar_ in (("div", "Dividends", "التوزيعات"), ("buyback", "Buybacks", "إعادة الشراء")):
                v = get(ca.get(key_), last_d)
                if pd.notna(v) and v != 0:
                    items.append((L(en_, ar_), v, "relative"))
            items.append((L("Left over", "المتبقي"), 0, "total"))
            if len(items) > 2:
                ui.chart(charts.cash_waterfall(items, L(f"Where the cash went · FY{last_d.year}", f"أين ذهب النقد · {last_d.year}")), key="cf_wf")
    with st.expander(L("Full financial statements", "القوائم المالية الكاملة"), icon=":material/table_view:"):
        f2 = st.segmented_control(L("Period ", "الفترة "), ["a", "q"], default="a", key="fin_freq2",
                                  format_func=lambda k: L("Annual", "سنوي") if k == "a" else L("Quarterly", "ربعي")) or "a"
        tabs = st.tabs([L("Income statement", "قائمة الدخل"), L("Balance sheet", "الميزانية العمومية"), L("Cash flow", "التدفقات النقدية")])
        for tab, key_ in zip(tabs, ("inc", "bal", "cf")):
            with tab:
                df = stm.get(f"{key_}_{f2}")
                if not isinstance(df, pd.DataFrame) or df.empty:
                    st.caption("—")
                    continue
                num = df.apply(pd.to_numeric, errors="coerce")
                show = num / 1e9
                raw = [i for i in num.index if any(w in str(i) for w in ("EPS", "Per Share", "Rate"))]
                show.loc[raw] = num.loc[raw]
                show.columns = _period_labels(pd.to_datetime(show.columns, errors="coerce"), f2)
                st.dataframe(show.style.format("{:,.2f}", na_rep="—"), height=420)
                st.caption(L("Values in billions of USD (EPS and rates as reported).", "القيم بالمليار دولار (ربحية السهم والنسب كما هي)."))


def analysts_tab(sym, inf, price):
    f = data.fundamentals(sym)
    c1, c2 = st.columns(2)
    with c1:
        if f["targets"]:
            ui.chart(charts.target_chart(price, f["targets"], L("12-month price targets", "السعر المستهدف (12 شهر)")), key="an_tgt")
            mean = f["targets"].get("mean")
            if mean:
                up = (mean / price - 1) * 100
                ui.html(T.kpi("flag", L("Upside to mean target", "مساحة الصعود للهدف"), f"{up:+.1f}%",
                              f"{inf.get('numberOfAnalystOpinions', 0) or 0} {L('analysts', 'محلل')}", T.cls(up)))
        rec = f["rec_summary"]
        if isinstance(rec, pd.DataFrame) and not rec.empty:
            ui.chart(charts.rec_chart(rec, L("Analyst recommendations", "توصيات المحللين")), key="an_rec")
    with c2:
        eh = f["earnings_hist"]
        if isinstance(eh, pd.DataFrame) and not eh.empty:
            fig = charts.eps_chart(eh, L("EPS: estimate vs actual", "ربحية السهم: المتوقع مقابل الفعلي"))
            if fig is not None:
                ui.chart(fig, key="an_eps")
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
    num = lambda df, c: pd.to_numeric(df[c], errors="coerce").fillna(0).to_numpy() if c in df else np.zeros(len(df))
    ck, coi, pk, poi = num(calls, "strike"), num(calls, "openInterest"), num(puts, "strike"), num(puts, "openInterest")
    pain = [(float((coi * np.maximum(k - ck, 0)).sum() + (poi * np.maximum(pk - k, 0)).sum()), k) for k in strikes]
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
    ui.safe(_options_tab, sym, price)


def _options_tab(sym, price):
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
        df = df[[c for c in cols if c in df]].reset_index(drop=True)
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
    ui.chart(charts.oi_by_strike(win(calls), win(puts), price, L("Open interest by strike", "العقود المفتوحة حسب سعر التنفيذ"),
                                 (L("Calls", "شراء"), L("Puts", "بيع"))), key=f"oi_{sym}", container=a)
    ui.chart(charts.iv_smile(win(calls), win(puts), price, L("Implied volatility smile", "منحنى التذبذب الضمني"),
                             (L("Calls IV", "تذبذب الشراء"), L("Puts IV", "تذبذب البيع"))), key=f"iv_{sym}", container=b)
    ui.sec("local_fire_department", "Most active contracts", "العقود الأكثر تداولاً")
    act = pd.concat([calls.assign(Type="CALL"), puts.assign(Type="PUT")], ignore_index=True)
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
        ui.safe(chart_tab, sym, daily)
    with tabs[1]:
        ui.safe(company_tab, sym)
    with tabs[2]:
        ui.safe(technicals_tab, daily)
    with tabs[3]:
        ui.safe(financials_tab, sym, inf)
    with tabs[4]:
        ui.safe(analysts_tab, sym, inf, price)
    with tabs[5]:
        options_tab(sym, float(price))
    with tabs[6]:
        ui.safe(ui.news_list, data.news(sym, 20), 15)
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


# backup screener: when Yahoo's live screener refuses the server (e.g. HTTP 401), filter our own universe with live batch quotes
LOCAL_FIELDS = {"intradaymarketcap": "Mkt Cap", "intradayprice": "Price", "avgdailyvol3m": "Avg Vol", "peratio.lasttwelvemonths": "P/E",
                "pricebookratio.quarterly": "P/B", "forward_dividend_yield": "Div %", "percentchange": "Chg %",
                "fiftytwowkpercentchange": "52W %"}
LOCAL_SORT = {"intradaymarketcap": "Mkt Cap", "percentchange": "Chg %", "dayvolume": "Volume", "peratio.lasttwelvemonths": "P/E",
              "forward_dividend_yield": "Div %", "fiftytwowkpercentchange": "52W %"}
_LIVE_DOWN = {"until": 0.0, "err": ""}


def _field_label(field):
    for en, ar, _, opts in F.values():
        if any(f[1] == field for o in opts for f in o[2]):
            return L(en, ar)
    return field


def _local_screen(filters, sort, asc, size):
    """(DataFrame, skipped filter fields) from the S&P 500 + top 175 with live quotes; (None, []) if quotes are unavailable."""
    from sp500 import SP500
    syms = list(dict.fromkeys(list(U.US_UNIVERSE) + list(SP500)))
    try:
        raw = data._quotes(tuple(syms))
    except Exception:
        return None, []
    df = data._quotes_df(raw)
    if df.empty:
        return None, []
    if df["52W %"].notna().sum() > 5 and pd.to_numeric(df["52W %"], errors="coerce").abs().median() < 1.5:
        df["52W %"] = pd.to_numeric(df["52W %"], errors="coerce") * 100
    meta = data.classify(df["Symbol"].tolist(), limit=0)
    sec_ = df["Symbol"].map(lambda x: meta.get(x, (None, None))[0])
    ind_ = df["Symbol"].map(lambda x: meta.get(x, (None, None))[1])
    keep = pd.Series(True, index=df.index)
    skipped = []
    for f in filters:
        op, field, *vals = f
        if field == "region":
            continue
        if op == "or_eq":
            keep &= (sec_ if field == "sector" else ind_).isin(list(vals[0]))
            continue
        if op == "eq" and field in ("sector", "industry"):
            keep &= (sec_ if field == "sector" else ind_) == vals[0]
            continue
        col = LOCAL_FIELDS.get(field)
        if col is None or col not in df:
            skipped.append(field)
            continue
        v = pd.to_numeric(df[col], errors="coerce")
        m = v > vals[0] if op == "gt" else (v < vals[0] if op == "lt" else ((v >= vals[0]) & (v <= vals[1]) if op == "btwn" else None))
        if m is not None:
            keep &= m.fillna(False)
    df = df[keep]
    sc = LOCAL_SORT.get(sort, "Mkt Cap")
    if sc in df:
        df = df.sort_values(sc, ascending=asc, na_position="last")
    return df.head(size).reset_index(drop=True), list(dict.fromkeys(skipped))


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
            n_want = 250 if theme_syms else size
            if time.time() < _LIVE_DOWN["until"]:          # Yahoo refused a moment ago: don't hammer it, use the backup directly
                df, err = pd.DataFrame(), _LIVE_DOWN["err"]
            else:
                df, err = data.screen_custom(filters, sort, SORTS[sort][2], n_want)
                if err:
                    _LIVE_DOWN.update(until=time.time() + 600, err=err)
            source, skipped = "live", []
            if err:
                ldf, skipped = _local_screen(filters, sort, SORTS[sort][2], n_want)
                if ldf is not None:
                    df, source = ldf, "local"
            if theme_syms is not None:
                have = set(df["Symbol"]) if not df.empty else set()
                df = df[df["Symbol"].isin(theme_syms)] if not df.empty else df
                missing = [t for t in theme_syms if t not in have]
                if missing:
                    ch = data.changes(missing)
                    extra = pd.DataFrame([{"Symbol": t, "Name": U.name_of(t), "Price": ch[t][0], "Chg %": ch[t][1]} for t in missing if t in ch])
                    df = pd.concat([df, extra], ignore_index=True) if not df.empty else extra
            if df.empty and theme_syms is None and err and source == "live":     # both the live and the backup screener are down
                source = "fallback"
                fb = data.changes(tuple(U.US_UNIVERSE))
                df = pd.DataFrame([{"Symbol": s_, "Name": U.name_of(s_), "Price": p_, "Chg %": c_, "Mkt Cap": U.STOCKS[s_][3] * 1e9}
                                   for s_, (p_, c_) in fb.items()])
                if sec != "Any" and not df.empty:
                    df = df[df["Symbol"].map(U.sector_of) == sec]
        ss.screen = {"df": df, "err": err, "source": source, "skipped": skipped}

    res = ss.screen
    df = _local_filters(res["df"].copy()) if not res["df"].empty else res["df"]
    if res["source"] == "local":
        st.info(L("Yahoo's live screener isn't answering our server right now, so these results are filtered from our own data "
                  "(S&P 500 + top 175 US stocks, live prices). Everything else on the page works normally.",
                  "فلتر ياهو المباشر لا يستجيب لخادم الموقع حالياً، لذلك النتائج مفلترة من بياناتنا "
                  "(أسهم إس آند بي 500 + أكبر 175 سهم أمريكي بأسعار مباشرة). وباقي الصفحة يعمل بشكل طبيعي."), icon=":material/cloud_sync:")
        if res.get("skipped"):
            st.caption(L("Filters that need the live screener and were skipped: ", "فلاتر تحتاج الفلتر المباشر وتم تجاهلها: ")
                       + " · ".join(_field_label(f_) for f_ in res["skipped"]))
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
         "RSI": "RSI", "Volatility": L("Volatility", "التذبذب"), "Logo": "Logo"}
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
                         column_config={"Logo": st.column_config.ImageColumn(" ", width="small")})
    with vt[-1]:
        if "_spark" in df:
            lg = data.logos(df["Symbol"].head(36).tolist())
            items = []
            for _, r in df.head(36).iterrows():
                sp = r["_spark"] if isinstance(r["_spark"], np.ndarray) else None
                head = f'<div style="margin-bottom:4px">{T.company(r["Symbol"], str(r["Name"])[:22], lg.get(r["Symbol"]), 26, href=ui.href(r["Symbol"]))}</div>'
                items.append(T.tile("", T.fmt_price(r["Price"]), None, r["Chg %"], sp, head_html=head))
            ui.html(T.tiles(items))
    a, c_ = st.columns([3, 1], vertical_alignment="bottom")
    with a:
        ui.open_picker(df["Symbol"].tolist(), "sc", "Selected stock", "السهم المختار")
    c_.download_button(L("Export CSV", "تصدير CSV"), df.drop(columns=["_spark", "Logo", "_sector", "_industry"], errors="ignore").to_csv(index=False).encode(),
                       "screener.csv", "text/csv", icon=":material/download:", width="stretch")
    if res.get("err") and res["source"] != "live":
        with st.expander(L("Technical details (Yahoo)", "تفاصيل فنية (ياهو)")):
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
    ui.chart(charts.scan_scatter(res, L("Momentum map: 1-month return vs RSI (bubble = volume, color = score)",
                                        "خريطة الزخم: عائد الشهر مقابل RSI (الحجم = حجم التداول، اللون = النقاط)")), key="scan_sc", container=v1)
    by_sec = res.groupby("Sector")["Score"].mean().sort_values()
    ui.chart(charts.hbar([sector_name(s) for s in by_sec.index], list(by_sec.values),
                         L("Average score by sector", "متوسط النقاط حسب القطاع"), 460, suffix=""), key="scan_sec", container=v2)
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
    ui.chart(charts.score_gauge(score["total"], L("Catalyst score", "تقييم المحفزات")), key="cat_gauge", container=g1)
    scf = lambda v: "n/a" if v is None else f"{v:.0f}/100"
    g2.metric(L("Technical (50%)", "فني (50%)"), scf(score["technical"]), f"{sum(x['Pass'] for x in tech)}/{len(tech)}", delta_color="off")
    g3.metric(L("Fundamental (30%)", "مالي (30%)"), scf(score["fundamental"]),
              f"{sum(x['Pass'] for x in fund)}/{len(fund)}" if fund else L("no data", "لا بيانات"), delta_color="off")
    g4.metric(L("Events (20%)", "أحداث (20%)"), scf(score["event"]), f"{len(events)}", delta_color="off")

    ui.sec("flag", "Trade plan", "خطة التداول")
    cards = [(L("Current price", "السعر الحالي"), f"${p['price']:,.2f}", ""),
             (L("Entry zone", "منطقة الدخول"), f"${p['zone'][0]:,.2f} – ${p['zone'][1]:,.2f}", "acc"),
             (L("Stop loss", "وقف الخسارة"), f"${p['stop']:,.2f}", "neg"), (L("Target 1 (2R)", "الهدف الأول"), f"${p['t1']:,.2f}", "pos"),
             (L("Target 2 (3R)", "الهدف الثاني"), f"${p['t2']:,.2f}", "pos"), (L("Risk / share", "المخاطرة للسهم"), f"${p['risk_per_share']:,.2f}", ""),
             (L("Position size", "حجم الصفقة"), f"{p['shares']:,} {L('sh', 'سهم')}", "acc"),
             (L("Position value", "قيمة الصفقة"), f"${p['position_value']:,.0f}", ""),
             (L("Max loss", "أقصى خسارة"), f"${p['shares'] * p['risk_per_share']:,.0f}", "neg"),
             ("ATR (14)", f"${p['atr']:,.2f} ({p['atr_pct']:.1f}%)", ""), (L("Support", "الدعم"), f"${p['support']:,.2f}", ""),
             (L("Resistance", "المقاومة"), f"${p['resistance']:,.2f}", "")]
    ui.html('<div class="plan">' + "".join(f'<div class="p {k}"><div class="l">{l}</div><div class="v">{v}</div></div>'
                                           for l, v, k in cards) + "</div>")
    left, right = st.columns([1.6, 1])
    with left:
        levels = [(L("Entry", "دخول"), p["entry"], T.ACCENT, "solid"), (L("Stop", "وقف"), p["stop"], T.DOWN, "dash"),
                  ("T1", p["t1"], T.UP, "dot"), ("T2", p["t2"], T.UP, "dash")]
        ui.chart(charts.price_chart(d.tail(126), "Candles", ["SMA 20", "SMA 50"], [], False, levels=levels, height=520), key="cat_chart")
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
            timing.append((f"<b class='dnt'>{L(f'Earnings in {ed} days', f'إعلان أرباح بعد {ed} يوم')}</b>: "
                           f"{L('half size, or wait until after the report.', 'نصف الحجم أو انتظر بعد الإعلان.')}", "warning"))
        ui.html("".join(f'<div class="check">{T.ico(ic, "gold")}<div>{t}</div></div>' for t, ic in timing))
        ui.sec("logout", "Exit rules", "قواعد الخروج")
        ui.html("".join(f'<div class="check">{T.ico("logout", "acc")}<div>{T.esc(L(e, a))}</div></div>' for e, a in p["exits"]))

    def checklist(items):
        return "".join(f'<div class="check">{T.ico("check", "pos") if c["Pass"] else T.ico("close", "neg")}'
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
