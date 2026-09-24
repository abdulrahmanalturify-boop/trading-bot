"""
p_markets.py - Overview (TradingView-style heatmap, sector rotation, market breadth) · Futures · Options market ·
Economy · What's Trending · News
"""
import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import heatmap as HM
import ta
import taxonomy as X
import theme as T
import ui
import universe as U
from i18n import L, industry_name, is_ar, lang, sector_name, theme_name
from sp500 import DOW30, SP500, gics_name

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


def _chg(df, n):
    """% change over n bars ('ytd' = since the first close of the year)."""
    if df is None or df.empty:
        return np.nan
    c = df["Close"].dropna()
    if n == "ytd":
        y = c[c.index.year == c.index[-1].year]
        return (c.iloc[-1] / y.iloc[0] - 1) * 100 if len(y) > 1 else np.nan
    return (c.iloc[-1] / c.iloc[-1 - n] - 1) * 100 if len(c) > n else np.nan


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
# HEATMAP (TradingView style, inside Overview)
# =====================================================================
HM_PERIODS = {"1D": ("Change 1D, %", "التغير يوم، %"), "1W": ("Change 1W, %", "التغير أسبوع، %"), "1M": ("Change 1M, %", "التغير شهر، %"),
              "3M": ("Change 3M, %", "التغير 3 أشهر، %"), "YTD": ("Change YTD, %", "منذ بداية العام، %"), "1Y": ("Change 1Y, %", "التغير سنة، %"),
              "PRE": ("Pre-market, %", "ما قبل الافتتاح، %"), "POST": ("After-hours, %", "ما بعد الإغلاق، %")}
HM_SIZES = {"cap": ("Market cap", "القيمة السوقية"), "dvol": ("Dollar volume", "قيمة التداول"), "equal": ("Equal size", "حجم متساوٍ")}


def hm_universes():
    u = {"sp500": (L("S&P 500 Index", "مؤشر إس آند بي 500"), list(SP500)),
         "dow": (L("Dow Jones 30", "داو جونز 30"), DOW30),
         "top": (L("Top 175 US stocks", "أكبر 175 سهم أمريكي"), list(U.US_UNIVERSE))}
    for tk, (en, ar, _, _) in X.THEMES.items():
        u[f"t:{tk}"] = (L(f"Theme · {en}", f"ثيم · {ar}"), X.theme_tickers(tk))
    return u


def _meta(sym):
    """(name, sector, industry, industry naming) from the static lists."""
    if sym in SP500:
        n, sec, sub = SP500[sym]
        return n, sec, sub, "gics"
    if U.known(sym):
        return U.name_of(sym), U.sector_of(sym), U.industry_of(sym), "yahoo"
    return sym, "Other", "Other", "yahoo"


def heatmap_frame(ukey, period, sizing):
    syms = hm_universes()[ukey][1]
    q, source = data.market_quotes(syms)
    if q.empty:
        return pd.DataFrame(), source
    q = q.drop_duplicates("Symbol").set_index("Symbol")
    rows = []
    for s in syms:
        if s not in q.index:
            continue
        r = q.loc[s]
        name, sec, ind, kind = _meta(s)
        rows.append({"Symbol": s, "Name": r.get("Name") if isinstance(r.get("Name"), str) and r.get("Name") != s else name,
                     "Sector": sec, "Industry": ind, "Kind": kind, "Price": r.get("Price"), "1D": r.get("Chg %"),
                     "1Y": r.get("52W %"), "PRE": r.get("PRE"), "POST": r.get("POST"), "Cap": r.get("Mkt Cap"),
                     "Volume": r.get("Volume")})
    df = pd.DataFrame(rows)
    if df.empty:
        return df, source
    if period in ("1W", "1M", "3M", "YTD") or (period == "1Y" and df["1Y"].isna().all()):
        perf = data.perf_table(df["Symbol"].tolist())
        if not perf.empty:
            df = df.drop(columns=[c for c in ("1W", "1M", "3M", "YTD") if c in df]).merge(
                perf[["Symbol", "1W", "1M", "3M", "YTD"] + (["1Y"] if period == "1Y" else [])].rename(columns={"1Y": "1Y_h"}), on="Symbol", how="left")
            if "1Y_h" in df:
                df["1Y"] = df["1Y"].fillna(df["1Y_h"])
    df["Val"] = pd.to_numeric(df.get(period), errors="coerce") if period in df else np.nan
    cap = pd.to_numeric(df["Cap"], errors="coerce")
    static = df["Symbol"].map(lambda s: U.STOCKS[s][3] * 1e9 if s in U.STOCKS else np.nan)
    cap = cap.fillna(static).fillna(cap.median() if cap.notna().any() else 2e10).fillna(2e10)
    if sizing == "cap":
        df["Size"] = cap
    elif sizing == "dvol":
        dv = pd.to_numeric(df["Volume"], errors="coerce") * pd.to_numeric(df["Price"], errors="coerce")
        df["Size"] = dv.fillna(dv.median() if dv.notna().any() else 1.0).clip(lower=1.0)
    else:
        df["Size"] = 1.0
    df["Cap"] = cap
    return df, source


def heatmap_section():
    ui.sec("grid_view", "Stock heatmap", "خريطة الأسهم الحرارية")
    unis = hm_universes()
    c = st.columns([1.35, 1, 1.05, 1.25])
    ukey = c[0].selectbox(L("Index", "المؤشر"), list(unis), key="hm_uni", format_func=lambda k: unis[k][0])
    sizing = c[1].selectbox(L("Size", "الحجم"), list(HM_SIZES), key="hm_size", format_func=lambda k: L(*HM_SIZES[k]))
    period = c[2].selectbox(L("Color", "اللون"), list(HM_PERIODS), key="hm_per", format_func=lambda k: L(*HM_PERIODS[k]))
    theme_uni = ukey.startswith("t:")
    with st.spinner(L("Building the heatmap...", "جاري بناء الخريطة...")):
        df, source = heatmap_frame(ukey, period, sizing)
    if df.empty:
        c[3].selectbox(L("Sector", "القطاع"), ["all"], key="hm_sec_empty", format_func=lambda s: L("All sectors", "كل القطاعات"))
        st.warning(L("Market data is temporarily unavailable.", "بيانات السوق غير متاحة مؤقتاً."))
        return None
    sectors = ["all"] + sorted(df["Sector"].unique(), key=lambda s: -df.loc[df["Sector"] == s, "Cap"].sum())
    if ss.get("hm_sec") not in sectors:
        ss["hm_sec"] = "all"
    sec = c[3].selectbox(L("Sector", "القطاع"), sectors, key="hm_sec",
                         format_func=lambda s: L("All sectors", "كل القطاعات") if s == "all" else sector_name(s))
    view = df if sec == "all" else df[df["Sector"] == sec]
    if theme_uni and sec == "all":                         # themes are grouped by sub-theme
        tk = ukey[2:]
        first = {}
        for sk, (_, _, tickers) in X.THEMES[tk][3].items():
            for t_ in tickers:
                first.setdefault(t_, sk)
        view = view.assign(Group=view["Symbol"].map(first))
        label = lambda g: theme_name(tk, g)
    elif sec == "all":
        view = view.assign(Group=view["Sector"])
        label = sector_name
    else:
        view = view.assign(Group=view["Industry"])
        kind_of = view.groupby("Industry")["Kind"].first().to_dict()
        label = lambda g: gics_name(g) if kind_of.get(g) == "gics" else industry_name(g)
    if view["Val"].isna().all():
        st.info(L("This measure isn't available right now (for example pre-market data outside trading hours). Showing today's change.",
                  "هذا المقياس غير متاح حالياً (مثل بيانات ما قبل الافتتاح خارج أوقات التداول). نعرض تغير اليوم."), icon=":material/info:")
        view = view.assign(Val=view["1D"])
        period = "1D"
    rng = HM.RANGE.get(period, 3)
    tiles, groups = HM.layout(view, "Group", "Size")
    big = HM.big_symbols(tiles, 38)
    lg = {s: u for s, u in data.logos(big[:140]).items() if u}
    lg.update(data.known_logos(HM.big_symbols(tiles, 20)))

    def tip(t):
        v = t.get("Val")
        chg = f"{v:+.2f}%" if v is not None and np.isfinite(v) else "—"
        return f'{t["Symbol"]} · {t.get("Name", "")}\n{T.fmt_price(t.get("Price"))} · {chg} · {L("Mkt cap", "القيمة")} {T.fmt_big(t.get("Cap"))}'
    ui.html(HM.render(tiles, groups, lg, rng, lang(), label, tip, rtl=is_ar()))
    ui.html(HM.legend(rng))
    up, dn = int((view["Val"] > 0).sum()), int((view["Val"] < 0).sum())
    w = np.average(view["Val"].fillna(0), weights=view["Size"]) if view["Size"].sum() > 0 else 0
    st.caption(L(f"{len(view)} companies · {up} up · {dn} down · weighted change {w:+.2f}% · size = {L(*HM_SIZES[sizing])} · "
                 "click any company to open its page" + ("" if source == "live" else " · delayed data"),
                 f"{len(view)} شركة · {up} صاعدة · {dn} نازلة · التغير المرجّح {w:+.2f}% · الحجم = {L(*HM_SIZES[sizing])} · "
                 "اضغط على أي شركة لفتح صفحتها" + ("" if source == "live" else " · بيانات متأخرة")))
    ui.open_picker(view.sort_values("Size", ascending=False)["Symbol"].tolist(), "hm", "Open a company from the map", "افتح شركة من الخريطة")
    return df if ukey == "sp500" else None


# =====================================================================
# SECTOR PERFORMANCE (cards + rotation graph) · MARKET BREADTH
# =====================================================================
SEC_PERIODS = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": "ytd"}


def _rrg(hist, window=12, tail=5):
    """JdK-style Relative Rotation Graph points (weekly, smoothed): RS-Ratio (trend of relative strength) and RS-Momentum."""
    spy = hist.get("SPY")
    if spy is None or len(spy) < 120:
        return {}
    sw = spy["Close"].resample("W-FRI").last()
    out = {}
    for etf in U.SECTOR_ETFS:
        df = hist.get(etf)
        if df is None or len(df) < 120:
            continue
        rs = ((df["Close"].resample("W-FRI").last() / sw).dropna() * 100).ewm(span=4).mean()
        ratio = 100 + (rs - rs.rolling(window).mean()) / rs.rolling(window).std()
        ratio = ratio.ewm(span=3).mean()
        roc = ratio.diff()
        mom = (100 + (roc - roc.rolling(window).mean()) / roc.rolling(window).std()).ewm(span=3).mean()
        t = pd.DataFrame({"ratio": ratio, "mom": mom}).replace([np.inf, -np.inf], np.nan).dropna().tail(tail)
        if len(t) >= 2:
            out[etf] = t
    return out


def sector_section():
    ui.sec("donut_small", "Sector performance", "أداء القطاعات")
    per = st.segmented_control(L("Period", "الفترة"), list(SEC_PERIODS), default="1D", key="ov_per", label_visibility="collapsed") or "1D"
    hist = data.history_many(tuple(list(U.SECTOR_ETFS) + ["SPY"]), "2y")
    if not hist:
        st.info(L("Sector data unavailable right now.", "بيانات القطاعات غير متاحة حالياً."))
        return
    rows = []
    for etf, name in U.SECTOR_ETFS.items():
        df = hist.get(etf)
        if df is None or len(df) < 25:
            continue
        rows.append((name, etf, _chg(df, SEC_PERIODS[per]), _chg(df, 5), _chg(df, 21), df["Close"].tail(22).values))
    if not rows:
        st.info(L("Sector data unavailable right now.", "بيانات القطاعات غير متاحة حالياً."))
        return
    rows.sort(key=lambda r: -(r[2] if pd.notna(r[2]) else -1e9))
    left, right = st.columns([1, 1.15])
    with left:
        spy = _chg(hist.get("SPY"), SEC_PERIODS[per])
        best, worst = rows[0], rows[-1]
        ui.html(f'<div class="card" style="padding:12px 14px"><div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">'
                f'{T.badge(L("Leader", "الأقوى") + ": " + sector_name(best[0]), "up", "north_east")}'
                f'{T.badge(L("Laggard", "الأضعف") + ": " + sector_name(worst[0]), "down", "south_east")}'
                f'<span class="muted" style="font-size:.8rem">S&amp;P 500 {per}</span>{T.pill(spy)}</div></div>')
        ui.html('<div class="secgrid">' + "".join(T.sector_card(sector_name(n), e, v, w, m, sp) for n, e, v, w, m, sp in rows) + "</div>")
    with right:
        tails = _rrg(hist)
        if tails:
            ui.chart(charts.sector_rrg(tails, {e: sector_name(n) for e, n in U.SECTOR_ETFS.items()},
                                       L("Sector rotation vs S&P 500 (weekly, last 5 weeks)", "دوران القطاعات مقابل إس آند بي 500 (أسبوعي، آخر 5 أسابيع)"),
                                       (L("Leading", "قيادي"), L("Weakening", "يضعف"), L("Lagging", "متأخر"), L("Improving", "يتحسن"))))
            st.caption(L("Right = stronger than the market, top = gaining momentum. Sectors usually rotate clockwise: Improving → Leading → Weakening → Lagging.",
                         "اليمين = أقوى من السوق، والأعلى = زخم متزايد. القطاعات تدور عادة مع عقارب الساعة: يتحسن ← قيادي ← يضعف ← متأخر."))


def breadth_section(sp=None):
    ui.sec("monitor_heart", "Market breadth · S&P 500", "اتساع السوق · إس آند بي 500")
    if sp is None:
        q, _ = data.market_quotes(list(SP500))
        sp = q.rename(columns={"Chg %": "1D"}) if not q.empty else q
        if not sp.empty:
            sp["Sector"] = sp["Symbol"].map(lambda s: SP500.get(s, ("", "Other", ""))[1])
    if sp is None or sp.empty:
        st.info(L("Breadth data unavailable right now.", "بيانات اتساع السوق غير متاحة حالياً."))
        return
    q = data.quotes_df(list(SP500)) if "vs50 %" not in sp else sp
    chg = pd.to_numeric(sp["1D"], errors="coerce").dropna()
    adv, dec = int((chg > 0).sum()), int((chg < 0).sum())
    unch = len(chg) - adv - dec
    pct = adv / max(len(chg), 1) * 100
    a, b, c = st.columns([1, 1.1, 1.2])
    with a:
        mood = L("Bullish breadth", "اتساع إيجابي") if pct > 55 else (L("Bearish breadth", "اتساع سلبي") if pct < 45 else L("Mixed", "متوازن"))
        ui.html(f'<div class="card">{T.pulse_gauge(pct, L("advancing", "صاعدة"), mood)}'
                f'<div style="margin-top:8px">{T.ad_bar(adv, dec, unch)}</div>'
                f'<div style="display:flex;justify-content:space-between;margin-top:8px;font-size:.8rem;font-weight:700;direction:ltr">'
                f'<span class="pill pos" style="min-width:0">▲ {adv}</span><span class="pill neu" style="min-width:0">= {unch}</span>'
                f'<span class="pill neg" style="min-width:0">▼ {dec}</span></div></div>')
    with b:
        items = []
        if not q.empty and "vs50 %" in q:
            v50, v200 = pd.to_numeric(q["vs50 %"], errors="coerce").dropna(), pd.to_numeric(q["vs200 %"], errors="coerce").dropna()
            hi, lo = pd.to_numeric(q["Hi52 %"], errors="coerce").dropna(), pd.to_numeric(q["Lo52 %"], errors="coerce").dropna()
            for lab, s_, col in ((L("Above 50-day average", "فوق متوسط 50 يوم"), v50 > 0, T.ACCENT),
                                 (L("Above 200-day average", "فوق متوسط 200 يوم"), v200 > 0, T.VIOLET)):
                if len(s_):
                    p_ = s_.mean() * 100
                    items.append((lab, f"{p_:.0f}%", p_, T.UP if p_ >= 50 else T.DOWN))
            if len(hi):
                nh, nl = int((hi >= -2).sum()), int((lo <= 2).sum())
                items.append((L("Near 52-week high", "قرب القمة السنوية"), str(nh), nh / len(hi) * 100 * 4, T.UP))
                items.append((L("Near 52-week low", "قرب القاع السنوي"), str(nl), nl / len(lo) * 100 * 4, T.DOWN))
        ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:800;letter-spacing:.08em">'
                f'{L("PARTICIPATION", "المشاركة")}</div>{T.progress_bars(items) if items else ""}</div>')
    with c:
        if "Sector" in sp:
            g = sp.assign(up=pd.to_numeric(sp["1D"], errors="coerce") > 0).groupby("Sector")["up"].mean().sort_values(ascending=False) * 100
            ui.html(f'<div class="card"><div class="muted" style="font-size:.75rem;font-weight:800;letter-spacing:.08em">'
                    f'{L("ADVANCING BY SECTOR", "الصاعدة حسب القطاع")}</div>' +
                    T.progress_bars([(sector_name(s_), f"{v:.0f}%", v, T.UP if v >= 50 else T.DOWN) for s_, v in g.items()]) + "</div>")
    ui.chart(charts.change_distribution(chg, L("Distribution of today's moves (S&P 500)", "توزيع حركة الأسهم اليوم (إس آند بي 500)"),
                                        L("Change %", "التغير %"), L("Stocks", "عدد الأسهم")))


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
            chips += f'<span class="chip"><b>{name}</b>{f"{p:.2f}%" if s == "^TNX" else T.fmt_price(p)} {T.pill(c)}</span>'
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
    sp = ui.safe(heatmap_section)
    ui.safe(sector_section)
    ui.safe(breadth_section, sp)
    a, b, c = st.columns(3)
    if a.button(L("Futures market", "سوق العقود الآجلة"), icon=":material/update:", width="stretch"):
        ui.goto("futures")
    if b.button(L("Options market", "سوق الخيارات"), icon=":material/tune:", width="stretch"):
        ui.goto("options")
    if c.button(L("Economy dashboard", "لوحة الاقتصاد"), icon=":material/account_balance:", width="stretch"):
        ui.goto("economy")
    ui.foot()


# =====================================================================
# FUTURES
# =====================================================================
FU_PERIODS = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": "ytd", "1Y": 251}


def _perf_matrix(rows, hdr):
    head = "".join(f"<th>{h}</th>" for h in hdr)
    body = []
    for name, sym, price, vals in rows:
        cells = "".join(f'<td><span class="cp {T.cls(v)}">{v:+.2f}%</span></td>' if pd.notna(v) else "<td>—</td>" for v in vals)
        body.append(f'<tr><td style="text-align:left"><b>{T.esc(name)}</b> <span class="muted">{T.esc(sym)}</span></td>'
                    f'<td>{T.fmt_price(price)}</td>{cells}</tr>')
    return (f'<div class="chainwrap" style="max-height:none"><table class="chain"><thead><tr><th style="text-align:left">{L("Contract", "العقد")}</th>'
            f'<th>{L("Last", "آخر سعر")}</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def page_futures():
    ui.header("update", "Futures", "العقود الآجلة",
              "US futures on stock indices, energy, metals, agriculture, interest rates, currencies and crypto.",
              "العقود الآجلة الأمريكية على مؤشرات الأسهم والطاقة والمعادن والزراعة والفائدة والعملات والعملات الرقمية.")
    syms = list(U.FUTURES_NAMES)
    with st.spinner(L("Loading futures...", "جاري تحميل العقود...")):
        hist = data.history_many(tuple(syms), "1y")
    if not hist:
        st.warning(L("Futures data is temporarily unavailable.", "بيانات العقود غير متاحة مؤقتاً."))
        return
    groups = {g[0]: g for g in U.FUTURES}
    pick = st.segmented_control(L("Market", "السوق"), ["all"] + list(groups), default="all", key="fu_grp",
                                format_func=lambda k: L("All markets", "كل الأسواق") if k == "all" else L(groups[k][0], groups[k][1])) or "all"
    for (gen, gar, ic), items in U.FUTURES.items():
        if pick not in ("all", gen):
            continue
        ui.sec(ic, gen, gar)
        tl = []
        for sym, (en, ar) in items.items():
            df = hist.get(sym)
            if df is None or len(df) < 2:
                tl.append(T.tile(L(en, ar), "—", sub=sym))
                continue
            p, pr = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
            tl.append(T.tile(L(en, ar), T.fmt_price(p), p - pr, (p / pr - 1) * 100, df["Close"].tail(22).values, sub=sym))
        ui.html(T.tiles(tl))

    ui.sec("table_chart", "Performance matrix", "مصفوفة الأداء")
    rows = []
    for (gen, gar, ic), items in U.FUTURES.items():
        if pick not in ("all", gen):
            continue
        for sym, (en, ar) in items.items():
            df = hist.get(sym)
            if df is not None and len(df) > 1:
                rows.append((L(en, ar), sym, float(df["Close"].iloc[-1]), [_chg(df, n) for n in FU_PERIODS.values()]))
    ui.html(_perf_matrix(rows, list(FU_PERIODS)))

    ui.sec("candlestick_chart", "Contract chart", "رسم العقد")
    avail = [s for s in syms if s in hist and (pick == "all" or s in U.FUTURES[groups[pick]])]
    if not avail:
        ui.foot()
        return
    ui.valid("fu_sym", avail)
    c1, c2 = st.columns([2, 1])
    sym = c1.selectbox(L("Contract", "العقد"), avail, key="fu_sym", format_func=lambda s: f"{L(*U.FUTURES_NAMES[s])} · {s}")
    rng = c2.segmented_control(L("Range", "المدى"), ["3M", "6M", "1Y"], default="6M", key="fu_rng") or "6M"
    d = ta.add_all(hist[sym]).tail({"3M": 63, "6M": 126, "1Y": 252}[rng])
    if len(d) > 2:
        ui.chart(charts.price_chart(d, "Candles", ["SMA 20", "SMA 50"], ["RSI"], height=560))
    grp = next((g for g in U.FUTURES if sym in U.FUTURES[g]), None)
    if grp:
        ui.chart(charts.norm_lines({L(*U.FUTURES_NAMES[s]): hist[s]["Close"].tail(63) for s in U.FUTURES[grp] if s in hist},
                                   L(f"{grp[0]}: relative performance (3 months)", f"{grp[1]}: الأداء النسبي (3 أشهر)")))
    st.caption(L("Continuous front-month contracts. Futures trade almost 24 hours on weekdays; prices may be delayed.",
                 "عقود الشهر الأقرب المستمرة. العقود الآجلة تتداول تقريباً 24 ساعة في أيام الأسبوع، والأسعار قد تكون متأخرة."))
    ui.foot()


# =====================================================================
# OPTIONS MARKET
# =====================================================================
def page_options():
    ui.header("tune", "Options Market", "سوق الخيارات",
              "Volatility, put/call sentiment, expected moves and unusual activity across the most traded US options.",
              "التذبذب ومعنويات PUT/CALL والحركة المتوقعة والنشاط غير المعتاد في أكثر عقود الخيارات تداولاً.")
    vix = data.history_many(tuple(U.VIX_CURVE), "1mo")
    pts = [(L(*U.VIX_CURVE[s]), float(vix[s]["Close"].iloc[-1])) for s in U.VIX_CURVE if s in vix and len(vix[s])]
    c1, c2 = st.columns([1.4, 1])
    with c1:
        if len(pts) >= 2:
            ui.chart(charts.term_structure([p[0] for p in pts], [p[1] for p in pts], L("VIX term structure", "منحنى مؤشر الخوف VIX")))
        else:
            st.caption(L("VIX curve unavailable right now.", "منحنى VIX غير متاح حالياً."))
    with c2:
        v = vix.get("^VIX")
        if v is not None and len(v) > 1:
            lv, pv = float(v["Close"].iloc[-1]), float(v["Close"].iloc[-2])
            calm = lv < 20
            contango = len(pts) >= 2 and pts[-1][1] > pts[0][1]
            k = st.columns(2)
            k[0].markdown(T.kpi("speed", L("VIX (fear index)", "مؤشر الخوف VIX"), f"{lv:.2f}", f"{(lv / pv - 1) * 100:+.2f}%",
                                "pos" if calm else "neg"), unsafe_allow_html=True)
            k[1].markdown(T.kpi("stacked_line_chart", L("Curve", "شكل المنحنى"),
                                L("Contango", "كونتانغو") if contango else L("Backwardation", "باكورديشن"),
                                L("calm market", "سوق هادئ") if contango else L("stress / hedging", "توتر وتحوّط"),
                                "pos" if contango else "neg"), unsafe_allow_html=True)
            ui.html(f'<div class="card" style="margin-top:10px;font-size:.86rem;line-height:1.8">{L("VIX below 20 usually means a calm market; above 30 means fear. When short-term VIX is above long-term (backwardation), traders are paying up for protection now.", "مؤشر VIX تحت 20 يعني غالباً سوق هادئ، وفوق 30 يعني خوف. إذا كان VIX القصير أعلى من الطويل (باكورديشن) فالمتداولون يدفعون أكثر للحماية الآن.")}</div>')

    with st.spinner(L("Loading option chains...", "جاري تحميل سلاسل الخيارات...")):
        snaps = data.options_snapshot(U.OPTION_UNDERLYINGS)
    if not snaps:
        st.warning(L("Options data is temporarily unavailable.", "بيانات الخيارات غير متاحة مؤقتاً."))
    else:
        ui.sec("insights", "Most traded underlyings · nearest expiry", "الأصول الأكثر تداولاً · أقرب انتهاء")
        lg = data.logos([s["symbol"] for s in snaps])
        cards = []
        for s in snaps:
            pc = s["pc_vol"]
            kind = "pos" if pc < 0.7 else ("neg" if pc > 1 else "neu")
            senti = L("bullish", "إيجابي") if kind == "pos" else (L("bearish", "سلبي") if kind == "neg" else L("neutral", "محايد"))
            cards.append(f'<div class="lc"><div class="top">{T.company(s["symbol"], s["expiry"], lg.get(s["symbol"]), 34, href=ui.href(s["symbol"]))}'
                         f'<span class="pill {kind}" style="min-width:0">P/C {pc:.2f}</span></div>'
                         f'<div class="bot"><div><div class="muted" style="font-size:.7rem">{L("Price", "السعر")}</div><b>{T.fmt_price(s["price"])}</b></div>'
                         f'<div><div class="muted" style="font-size:.7rem">{L("ATM IV", "التذبذب")}</div><b>{s["iv"]:.1f}%</b></div>'
                         f'<div><div class="muted" style="font-size:.7rem">{L("Exp. move", "الحركة المتوقعة")}</div><b>±{s["move_pct"]:.1f}%</b></div></div>'
                         f'<div class="muted" style="font-size:.72rem;margin-top:8px">{L("Sentiment", "المعنويات")}: {senti} · '
                         f'{T.fmt_big(s["call_vol"] + s["put_vol"])} {L("contracts", "عقد")} · {s["dte"]}{L("d", " يوم")}</div></div>')
        ui.html('<div class="lead">' + "".join(cards) + "</div>")
        a, b = st.columns(2)
        with a:
            ui.chart(charts.pc_bars([s["symbol"] for s in snaps], [s["pc_vol"] for s in snaps],
                                    L("Put/Call volume ratio (green < 0.7 bullish, red > 1 bearish)", "نسبة PUT/CALL (أخضر < 0.7 إيجابي، أحمر > 1 سلبي)")))
        with b:
            ui.chart(charts.metric_bars([s["symbol"] for s in snaps], [s["iv"] for s in snaps],
                                        L("At-the-money implied volatility", "التذبذب الضمني عند سعر السوق"), "pct", 300))
        ui.sec("local_fire_department", "Unusual options activity", "نشاط الخيارات غير المعتاد")
        un = pd.DataFrame([u for s in snaps for u in s["unusual"]])
        if un.empty:
            st.caption(L("No unusual activity (volume above open interest) right now.", "لا يوجد نشاط غير معتاد حالياً (حجم أعلى من العقود المفتوحة)."))
        else:
            un["Vol/OI"] = un["Volume"] / un["OI"].replace(0, np.nan)
            un = un.sort_values(["Vol/OI", "Volume"], ascending=False).head(25)
            un.insert(0, "Logo", un["Symbol"].map(data.logo_url))
            N = {"Symbol": L("Symbol", "الرمز"), "Type": L("Type", "النوع"), "Strike": L("Strike", "التنفيذ"), "Expiry": L("Expiry", "الانتهاء"),
                 "Volume": L("Volume", "الحجم"), "OI": L("Open int.", "العقود المفتوحة"), "Last": L("Last", "آخر سعر"), "IV %": "IV %", "Vol/OI": "Vol/OI"}
            show = un.rename(columns=N)
            st.dataframe(show.style.map(lambda v: T.signal_style(v, "CALL", "PUT"), subset=[N["Type"]]).format(
                {N["Strike"]: "{:,.2f}", N["Volume"]: "{:,.0f}", N["OI"]: "{:,.0f}", N["Last"]: "{:,.2f}", "IV %": "{:.1f}%", "Vol/OI": "{:.1f}×"}, na_rep="—"),
                hide_index=True, height=420, column_config={"Logo": st.column_config.ImageColumn(" ", width="small")})
            st.caption(L("Unusual = contracts trading more today than their total open interest (at least 500 contracts): often new positions.",
                         "غير معتاد = عقود تداولها اليوم أكبر من إجمالي العقود المفتوحة (500 عقد على الأقل): غالباً مراكز جديدة."))
    ui.sec("table_rows", "Option chain explorer", "مستعرض سلسلة الخيارات")
    import p_research
    sym = st.selectbox(L("Underlying", "الأصل"), U.OPTION_UNDERLYINGS + ["Other"], key="om_sym",
                       format_func=lambda s: L("Other symbol...", "رمز آخر...") if s == "Other" else s)
    if sym == "Other":
        sym = st.text_input(L("Symbol", "الرمز"), "SMCI", key="om_other").strip().upper() or "SPY"
    d = data.history(sym, "1mo")
    if d.empty:
        st.warning(L("No data for this symbol.", "لا توجد بيانات لهذا الرمز."))
    else:
        p_research.options_tab(sym, float(d["Close"].iloc[-1]))
    ui.foot()


# =====================================================================
# ECONOMY
# =====================================================================
BAD_UP = ("cpi", "ppi", "inflation", "unemployment", "jobless", "claims", "pce")


def page_economy():
    ui.header("account_balance", "US Economy", "الاقتصاد الأمريكي",
              "Latest releases (actual vs expected), key indicators and the economic calendar.",
              "آخر البيانات الصادرة (الفعلي مقابل المتوقع)، أهم المؤشرات، والتقويم الاقتصادي.")
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
        st.caption(L("Green = better than expected, red = worse (for inflation and jobless data, above expectations counts as worse).",
                     "الأخضر = أفضل من المتوقع، والأحمر = أسوأ (للتضخم والبطالة: الأعلى من المتوقع يعتبر أسوأ)."))
    else:
        st.caption(L("Release data is not available right now.", "بيانات الإصدارات غير متاحة حالياً."))

    ui.sec("query_stats", "Key indicators", "أهم المؤشرات")
    with st.spinner(L("Loading economic data...", "جاري تحميل البيانات الاقتصادية...")):
        mac, errors, status = data.macro()
    if mac:
        items = []
        for sid, m in mac.items():
            chg = m["value"] - m["prev"]
            unit = m["unit"]
            val = f"{m['value']:,.2f}{unit}" if unit == "%" else f"{m['value']:,.1f}{unit}"
            sub = L(f"{m['date']:%b %Y} · prior {m['prev']:,.2f} · {m['source']}", f"{m['date']:%Y-%m} · السابق {m['prev']:,.2f} · {m['source']}")
            neutral = m["higher_is_bad"] is None
            items.append(T.tile(L(m["en"], m["ar"]), val, chg, None, m["hist"].values, sub, invert=bool(m["higher_is_bad"]),
                                kind="acc" if neutral else None))
        ui.html(T.tiles(items))
        names = {L(m["en"], m["ar"]): sid for sid, m in mac.items()}
        pick = st.selectbox(L("Explore an indicator", "استعرض مؤشراً"), list(names))
        ui.chart(charts.line(mac[names[pick]]["hist"], pick, height=320, fill=True))
    else:
        st.warning(L("Indicator sources (FRED and BLS) could not be reached from the server right now. Releases above come from Yahoo. "
                     "For a permanent fix add a free FRED API key in Streamlit secrets as FRED_API_KEY.",
                     "تعذر الوصول لمصادر المؤشرات (FRED وBLS) من الخادم حالياً، والبيانات أعلاه من ياهو. "
                     "للحل الدائم أضف مفتاح FRED المجاني في إعدادات Streamlit باسم FRED_API_KEY."), icon=":material/cloud_off:")
    with st.expander(L("Data source status", "حالة مصادر البيانات"), icon=":material/lan:"):
        st.write({**status, "Yahoo calendar": "ok" if not rel.empty else "no data"})
        if errors:
            st.code("\n".join(errors[:8]))

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
        cards.append(f'<div class="lc"><div class="top">{T.company(r["Symbol"], str(r.get("Name") or "")[:26], lg.get(r["Symbol"]), 36, href=ui.href(r["Symbol"]))}'
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
            col.markdown(f'<div class="story{" rtl" if is_ar() else ""}"><div class="rank">0{i + 1}</div><a class="t" href="{T.esc(n["link"])}" target="_blank">{T.esc(t)}</a>'
                         f'<div class="muted" style="font-size:.78rem;margin-top:6px">{T.esc(n["source"])} · {T.time_ago(n["time"], is_ar())}</div>'
                         f'<div class="aff"><span class="lbl" style="width:100%">{L("Affected companies", "الشركات المتأثرة")}</span>{ch}</div></div>',
                         unsafe_allow_html=True)
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))

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
                           None if kind == "most_actives" else T.cls(r["Chg %"])), unsafe_allow_html=True)
    if not moves.empty:
        adv = int((moves["Chg %"] > 0).sum())
        k[4].markdown(T.kpi("balance", L("Breadth (top 175)", "اتساع السوق"), f"{adv}/{len(moves)}", L("advancing", "صاعدة"),
                            "pos" if adv > len(moves) / 2 else "neg"), unsafe_allow_html=True)

    ui.sec("summarize", "Market summary", "ملخص السوق")
    ui.html(f'<div class="card{" rtl" if is_ar() else ""}"><ul class="summary">' +
            "".join(f"<li>{T.esc(L(e, a))}</li>" for e, a in summary_points(px, moves, lists)) + "</ul></div>")

    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    keys = list(LISTS)
    for row in (keys[:3], keys[3:]):
        cols = st.columns(3)
        for col, kind in zip(cols, row):
            df, _ = lists[kind]
            en, ar, ic = LISTS[kind]
            body = ui.row_list(df.head(6), lg) if not df.empty else f'<div class="muted">{L("No data", "لا بيانات")}</div>'
            col.markdown(f'<div class="mcard"><div class="hd">{T.icon(ic)}<span>{T.esc(L(en, ar))}</span></div>{body}</div>', unsafe_allow_html=True)

    ui.sec("table_rows", "Full lists", "القوائم الكاملة")
    tabs = st.tabs([f":material/{v[2]}: {L(v[0], v[1])}" for v in LISTS.values()])
    for tab, kind in zip(tabs, LISTS):
        with tab:
            df, fallback = lists[kind]
            if df.empty:
                st.info(L("Data unavailable right now.", "البيانات غير متاحة حالياً."))
                continue
            ui.html(_leaderboard(df, lg))
            ui.chart(charts.movers_bubble(df, L("Change vs relative volume (bubble = market cap)", "التغير مقابل الحجم النسبي (حجم الفقاعة = القيمة السوقية)"),
                                          L("Relative volume (×)", "الحجم النسبي (×)"), L("Change %", "التغير %")), key=f"bub_{kind}")
            show = df[["Symbol", "Name", "Price", "Chg %", "Volume", "Rel Vol", "Mkt Cap"]].copy()
            show.insert(0, "Logo", show["Symbol"].map(data.logo_url))
            show["Volume"] = show["Volume"].map(T.fmt_big)
            show["Mkt Cap"] = show["Mkt Cap"].map(T.fmt_big)
            N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Price": L("Price", "السعر"), "Chg %": L("Change %", "التغير %"),
                 "Volume": L("Volume", "الحجم"), "Rel Vol": L("Rel. volume", "الحجم النسبي"), "Mkt Cap": L("Market cap", "القيمة السوقية")}
            show = show.rename(columns=N)
            st.dataframe(show.style.map(T.color_style, subset=[N["Chg %"]]).format({N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["Rel Vol"]: "{:.1f}×"}, na_rep="—"),
                         hide_index=True, height=420, column_config={"Logo": st.column_config.ImageColumn(" ", width="small")})
            if fallback:
                st.caption(L("Computed from the top 175 US stocks (screener source unavailable).", "محسوبة من أكبر 175 سهم أمريكي (مصدر القوائم غير متاح حالياً)."))
            ui.open_picker(df["Symbol"].tolist(), f"tr_{kind}", "Open a stock", "افتح سهماً")
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
