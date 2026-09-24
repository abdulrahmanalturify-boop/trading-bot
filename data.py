"""
data.py - All data loading (cached). Sources: Yahoo Finance (yfinance), FRED (economic data),
Google Translate (Arabic news via deep-translator).
"""
import io
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

import engine


# ---------------------------------------------------------------- helpers
def _flat(df):
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df.dropna(subset=["Close"])


def _split(df, symbols):
    out = {}
    if df is None or df.empty:
        return out
    if not isinstance(df.columns, pd.MultiIndex):
        if len(symbols) == 1:
            out[symbols[0]] = df.dropna(subset=["Close"])
        return out
    lvl0 = set(df.columns.get_level_values(0))
    for s in symbols:
        try:
            sub = df[s] if s in lvl0 else df.xs(s, axis=1, level=1)
        except KeyError:
            continue
        sub = sub.dropna(subset=["Close"])
        if not sub.empty:
            out[s] = sub
    return out


# ---------------------------------------------------------------- prices
@st.cache_data(ttl=300, show_spinner=False)
def history(symbol, period="2y", interval="1d"):
    try:
        return _flat(yf.download(symbol, period=period, interval=interval, auto_adjust=True,
                                 progress=False))
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def history_many(symbols: tuple, period="1y", interval="1d"):
    if not symbols:
        return {}
    try:
        df = yf.download(list(symbols), period=period, interval=interval, auto_adjust=True,
                         progress=False, threads=True)
        return _split(df, list(symbols))
    except Exception:
        return {}


@st.cache_data(ttl=21600, show_spinner=False)
def info(symbol):
    try:
        return dict(yf.Ticker(symbol).info or {})
    except Exception:
        return {}


# ---------------------------------------------------------------- search & screeners
@st.cache_data(ttl=3600, show_spinner=False)
def search(query):
    try:
        quotes = yf.Search(query, max_results=10, news_count=0).quotes
    except Exception:
        return []
    out = []
    for q in quotes or []:
        sym = q.get("symbol")
        if not sym:
            continue
        out.append({"symbol": sym, "name": q.get("longname") or q.get("shortname") or sym,
                    "exchange": q.get("exchDisp") or q.get("exchange", ""),
                    "type": q.get("typeDisp") or q.get("quoteType", "")})
    return out


@st.cache_data(ttl=600, show_spinner=False)
def screen(name, count=25):
    try:
        try:
            res = yf.screen(name, count=count)
        except TypeError:
            res = yf.screen(name)
        quotes = res.get("quotes", []) if isinstance(res, dict) else []
    except Exception:
        return pd.DataFrame()
    rows = []
    for q in quotes:
        rows.append({
            "Symbol": q.get("symbol"),
            "Name": q.get("shortName") or q.get("longName") or q.get("symbol"),
            "Price": q.get("regularMarketPrice"),
            "Chg %": q.get("regularMarketChangePercent"),
            "Volume": q.get("regularMarketVolume"),
            "Avg Vol (3M)": q.get("averageDailyVolume3Month"),
            "Mkt Cap": q.get("marketCap"),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- news
def parse_news(items):
    out = []
    for it in items or []:
        c = it.get("content", it) if isinstance(it, dict) else {}
        title = c.get("title")
        if not title:
            continue
        link = ((c.get("canonicalUrl") or {}).get("url") or (c.get("clickThroughUrl") or {}).get("url")
                or c.get("link") or "")
        prov = c.get("provider")
        source = prov.get("displayName", "") if isinstance(prov, dict) else (c.get("publisher") or "")
        pub = c.get("pubDate") or c.get("displayTime") or c.get("providerPublishTime")
        ts = (pd.to_datetime(pub, unit="s", utc=True) if isinstance(pub, (int, float))
              else pd.to_datetime(pub, utc=True, errors="coerce"))
        out.append({"title": title, "link": link, "source": source, "time": ts,
                    "summary": c.get("summary") or ""})
    return out


@st.cache_data(ttl=1800, show_spinner=False)
def news(symbol, count=20):
    try:
        t = yf.Ticker(symbol)
        try:
            raw = t.get_news(count=count)
        except Exception:
            raw = t.news
        return parse_news(raw)
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def market_news():
    seen, out = set(), []
    for s in ("^GSPC", "SPY", "QQQ", "^DJI", "DIA", "^IXIC"):
        for n in news(s):
            key = n["title"].strip().lower()
            if key not in seen:
                seen.add(key)
                out.append(n)
    out.sort(key=lambda n: n["time"] if pd.notna(n["time"]) else pd.Timestamp("1970-01-01", tz="UTC"),
             reverse=True)
    return out


@st.cache_data(ttl=21600, show_spinner=False)
def translate(texts: tuple, target="ar"):
    """Translates a tuple of strings to Arabic. Falls back to the original text on any error."""
    try:
        from deep_translator import GoogleTranslator
    except Exception:
        return list(texts)

    def one(t):
        if not t:
            return t
        try:
            return GoogleTranslator(source="auto", target=target).translate(t[:4500]) or t
        except Exception:
            return t

    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(one, texts))


# ---------------------------------------------------------------- fundamentals & catalysts
@st.cache_data(ttl=21600, show_spinner=False)
def fundamentals(symbol):
    t = yf.Ticker(symbol)
    out = {"earnings_date": None, "ratings": pd.DataFrame(), "targets": {}, "rec_summary": pd.DataFrame(),
           "earnings_hist": pd.DataFrame(), "income_q": pd.DataFrame(), "insiders": pd.DataFrame()}

    def attempt(key, fn):
        try:
            val = fn()
            if val is not None:
                out[key] = val
        except Exception:
            pass

    def earn_date():
        cal = t.calendar
        dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
        dates = [pd.Timestamp(x) for x in (dates or []) if x is not None]
        return min(dates) if dates else None

    def ratings():
        r = t.upgrades_downgrades
        if r is None or r.empty:
            return pd.DataFrame()
        r = r.copy()
        idx = pd.to_datetime(r.index, errors="coerce")
        if getattr(idx, "tz", None) is not None:
            idx = idx.tz_localize(None)
        r.index = idx
        return r[r.index >= pd.Timestamp.now() - pd.Timedelta(days=90)].sort_index(ascending=False)

    def earnings_hist():
        e = t.get_earnings_dates(limit=12)
        if e is None or e.empty:
            return pd.DataFrame()
        return e.dropna(subset=[c for c in e.columns if "Reported" in c] or None)

    attempt("earnings_date", earn_date)
    attempt("ratings", ratings)
    attempt("targets", lambda: dict(t.analyst_price_targets or {}))
    attempt("rec_summary", lambda: t.recommendations_summary)
    attempt("earnings_hist", earnings_hist)
    attempt("income_q", lambda: t.quarterly_income_stmt)
    attempt("insiders", lambda: t.insider_transactions)
    return out


# ---------------------------------------------------------------- macro (FRED)
@st.cache_data(ttl=43200, show_spinner=False)
def fred(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        idx = pd.DatetimeIndex(pd.to_datetime(df.iloc[:, 0], errors="coerce"))
        s = pd.Series(pd.to_numeric(df.iloc[:, 1], errors="coerce").values, index=idx)
        return s[s.index.notna()].dropna()
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=43200, show_spinner=False)
def macro():
    ids = list(engine.MACRO_SERIES)
    with ThreadPoolExecutor(max_workers=8) as ex:
        raw = dict(zip(ids, ex.map(fred, ids)))
    out = {}
    for sid, (name, how, unit, bad) in engine.MACRO_SERIES.items():
        s = engine.macro_transform(raw[sid], how).dropna()
        if len(s) < 2:
            continue
        out[sid] = {"name": name, "value": float(s.iloc[-1]), "prev": float(s.iloc[-2]),
                    "date": s.index[-1], "unit": unit, "higher_is_bad": bad, "hist": s.tail(36)}
    return out
