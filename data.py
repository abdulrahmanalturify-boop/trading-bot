"""
data.py - Data loading. Sources: Yahoo Finance (yfinance), FRED (economic data), Google Translate.
Rule: failures are NEVER cached (the cached inner function raises, the wrapper returns an empty value),
so a temporary error doesn't stick for hours.
"""
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

import universe as U

try:
    from yfinance import EquityQuery
except Exception:  # very old yfinance
    EquityQuery = None


class Empty(Exception):
    pass


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
def _history(symbol, period, interval):
    df = _flat(yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False))
    if df.empty:
        raise Empty(symbol)
    return df


def history(symbol, period="2y", interval="1d"):
    try:
        return _history(symbol, period, interval)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def _history_many(symbols, period, interval):
    out = _split(yf.download(list(symbols), period=period, interval=interval, auto_adjust=True,
                             progress=False, threads=True), list(symbols))
    if not out:
        raise Empty("batch")
    return out


def history_many(symbols, period="1y", interval="1d"):
    symbols = tuple(dict.fromkeys(s for s in symbols if s))
    if not symbols:
        return {}
    try:
        return _history_many(symbols, period, interval)
    except Exception:
        return {}


def changes(symbols, period="5d"):
    """symbol -> (last price, % change vs previous close)."""
    out = {}
    for s, df in history_many(symbols, period).items():
        if len(df) >= 2:
            out[s] = (float(df["Close"].iloc[-1]), float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100))
    return out


@st.cache_data(ttl=21600, show_spinner=False)
def _info(symbol):
    i = dict(yf.Ticker(symbol).info or {})
    if len(i) < 3:
        raise Empty(symbol)
    return i


def info(symbol):
    try:
        return _info(symbol)
    except Exception:
        return {}


# ---------------------------------------------------------------- search & screeners
@st.cache_data(ttl=3600, show_spinner=False)
def _search(query):
    out = []
    for q in yf.Search(query, max_results=10, news_count=0).quotes or []:
        sym = q.get("symbol")
        if sym:
            out.append({"symbol": sym, "name": q.get("longname") or q.get("shortname") or sym,
                        "exchange": q.get("exchDisp") or q.get("exchange", ""),
                        "type": q.get("typeDisp") or q.get("quoteType", "")})
    if not out:
        raise Empty(query)
    return out


def search(query):
    try:
        return _search(query)
    except Exception:
        return []


def _quotes_df(quotes):
    rows = []
    for q in quotes or []:
        rows.append({
            "Symbol": q.get("symbol"), "Name": q.get("shortName") or q.get("longName") or q.get("symbol"),
            "Price": q.get("regularMarketPrice"), "Chg %": q.get("regularMarketChangePercent"),
            "Volume": q.get("regularMarketVolume"), "Avg Vol": q.get("averageDailyVolume3Month"),
            "Mkt Cap": q.get("marketCap"), "P/E": q.get("trailingPE"), "Fwd P/E": q.get("forwardPE"),
            "P/B": q.get("priceToBook"), "EPS": q.get("epsTrailingTwelveMonths"),
            "Div %": (q.get("trailingAnnualDividendYield") or 0) * 100 if q.get("trailingAnnualDividendYield") is not None else None,
            "52W High": q.get("fiftyTwoWeekHigh"), "52W Low": q.get("fiftyTwoWeekLow"),
            "52W %": q.get("fiftyTwoWeekChangePercent"), "SMA50": q.get("fiftyDayAverage"),
            "SMA200": q.get("twoHundredDayAverage"), "Rating": q.get("averageAnalystRating"),
            "Exchange": q.get("fullExchangeName") or q.get("exchange"),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=600, show_spinner=False)
def _screen(name, count):
    try:
        res = yf.screen(name, count=count)
    except TypeError:
        res = yf.screen(name)
    df = _quotes_df(res.get("quotes", []) if isinstance(res, dict) else [])
    if df.empty:
        raise Empty(name)
    return df


def screen(name, count=25):
    try:
        return _screen(name, count)
    except Exception:
        return pd.DataFrame()


def build_query(filters):
    """filters: list of (op, field, *values). Region US is always added."""
    parts = [EquityQuery("eq", ["region", "us"])]
    for f in filters:
        op, field, *vals = f
        parts.append(EquityQuery(op, [field, *vals]))
    return parts[0] if len(parts) == 1 else EquityQuery("and", parts)


@st.cache_data(ttl=900, show_spinner=False)
def _screen_custom(filters_json, sort_field, sort_asc, size):
    q = build_query(json.loads(filters_json))
    res = yf.screen(q, sortField=sort_field, sortAsc=sort_asc, size=size)
    df = _quotes_df(res.get("quotes", []) if isinstance(res, dict) else [])
    if df.empty:
        raise Empty("custom")
    return df


def screen_custom(filters, sort_field="intradaymarketcap", sort_asc=False, size=100):
    """Returns (DataFrame, error message or None)."""
    if EquityQuery is None:
        return pd.DataFrame(), "EquityQuery not available in this yfinance version"
    try:
        return _screen_custom(json.dumps(filters), sort_field, sort_asc, size), None
    except Empty:
        return pd.DataFrame(), None
    except Exception as e:
        return pd.DataFrame(), str(e)[:160]


@st.cache_data(ttl=43200, show_spinner=False)
def _sector_caps(sector):
    q = build_query([("eq", "sector", sector)])
    res = yf.screen(q, sortField="intradaymarketcap", sortAsc=False, size=100)
    caps = {x.get("symbol"): x.get("marketCap") for x in res.get("quotes", []) if x.get("marketCap")}
    if not caps:
        raise Empty(sector)
    return caps


@st.cache_data(ttl=600, show_spinner=False)
def market_caps():
    """Live market caps for the heatmap (falls back to static estimates). Re-checked every 10 minutes."""
    caps = {s: v[3] * 1e9 for s, v in U.STOCKS.items()}
    if EquityQuery is None:
        return caps, False
    live = False
    for sec in U.SECTORS:
        try:
            for s, c in _sector_caps(sec).items():
                if s in caps:
                    caps[s] = c
                    live = True
        except Exception:
            continue
    return caps, live


# ---------------------------------------------------------------- news
def _tickers_of(it, c, title):
    found = []
    for s in it.get("relatedTickers") or c.get("relatedTickers") or []:
        if isinstance(s, str):
            found.append(s)
    fin = c.get("finance") or {}
    for t in fin.get("stockTickers") or []:
        s = t.get("symbol") if isinstance(t, dict) else None
        if s:
            found.append(s)
    found += U.detect_tickers(title)
    clean = [s for s in dict.fromkeys(found) if s and "^" not in s and "=" not in s]
    return clean[:6]


def parse_news(items):
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        c = it.get("content", it)
        title = c.get("title")
        if not title:
            continue
        link = ((c.get("canonicalUrl") or {}).get("url") or (c.get("clickThroughUrl") or {}).get("url")
                or c.get("link") or it.get("link") or "")
        prov = c.get("provider")
        source = prov.get("displayName", "") if isinstance(prov, dict) else (c.get("publisher") or it.get("publisher") or "")
        pub = c.get("pubDate") or c.get("displayTime") or c.get("providerPublishTime") or it.get("providerPublishTime")
        ts = (pd.to_datetime(pub, unit="s", utc=True) if isinstance(pub, (int, float))
              else pd.to_datetime(pub, utc=True, errors="coerce"))
        out.append({"title": title, "link": link, "source": source, "time": ts,
                    "summary": c.get("summary") or c.get("description") or "", "tickers": _tickers_of(it, c, title)})
    return out


@st.cache_data(ttl=1200, show_spinner=False)
def _news(symbol, count):
    t = yf.Ticker(symbol)
    try:
        raw = t.get_news(count=count)
    except Exception:
        raw = t.news
    out = parse_news(raw)
    if not out:
        raise Empty(symbol)
    for n in out:
        if symbol not in n["tickers"] and "^" not in symbol:
            n["tickers"] = [symbol] + n["tickers"][:5]
    return out


def news(symbol, count=20):
    try:
        return _news(symbol, count)
    except Exception:
        return []


@st.cache_data(ttl=1200, show_spinner=False)
def _search_news(query, count):
    out = parse_news(yf.Search(query, max_results=1, news_count=count).news)
    if not out:
        raise Empty(query)
    return out


def search_news(query, count=20):
    try:
        return _search_news(query, count)
    except Exception:
        return []


def _sort_news(items):
    seen, out = set(), []
    for n in items:
        k = n["title"].strip().lower()
        if k not in seen:
            seen.add(k)
            out.append(n)
    out.sort(key=lambda n: n["time"] if pd.notna(n["time"]) else pd.Timestamp("1970-01-01", tz="UTC"), reverse=True)
    return out


def market_news():
    items = search_news("stock market", 25) + search_news("Wall Street stocks", 20)
    for s in ("SPY", "QQQ", "^GSPC"):
        items += news(s, 15)
    return _sort_news(items)


def trending_stories(k=3):
    """Top stories = recent market news that mention the most companies."""
    items = market_news()
    recent = [n for n in items[:40] if n["tickers"]]
    recent.sort(key=lambda n: (len(n["tickers"]) >= 2, n["time"] if pd.notna(n["time"]) else pd.Timestamp("1970-01-01", tz="UTC")),
                reverse=True)
    picked = recent[:k]
    if len(picked) < k:
        picked += [n for n in items if n not in picked][: k - len(picked)]
    return picked


@st.cache_data(ttl=21600, show_spinner=False)
def _translate(texts, target):
    from deep_translator import GoogleTranslator

    def one(t):
        if not t:
            return t
        try:
            return GoogleTranslator(source="auto", target=target).translate(t[:4500]) or t
        except Exception:
            return t

    with ThreadPoolExecutor(max_workers=8) as ex:
        out = list(ex.map(one, texts))
    if texts and all(a == b for a, b in zip(out, texts) if a):
        raise Empty("translate")
    return out


def translate(texts, target="ar"):
    texts = tuple(texts)
    try:
        return _translate(texts, target)
    except Exception:
        return list(texts)


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
        rep = [c for c in e.columns if "Reported" in c]
        return e.dropna(subset=rep) if rep else e

    attempt("earnings_date", earn_date)
    attempt("ratings", ratings)
    attempt("targets", lambda: dict(t.analyst_price_targets or {}))
    attempt("rec_summary", lambda: t.recommendations_summary)
    attempt("earnings_hist", earnings_hist)
    attempt("income_q", lambda: t.quarterly_income_stmt)
    attempt("insiders", lambda: t.insider_transactions)
    return out


# ---------------------------------------------------------------- economy
def _fred_key():
    try:
        return st.secrets.get("FRED_API_KEY")
    except Exception:
        return None


@st.cache_data(ttl=43200, show_spinner=False)
def _fred(series_id, key):
    start = (date.today() - timedelta(days=365 * 6)).isoformat()
    if key:
        r = requests.get("https://api.stlouisfed.org/fred/series/observations", timeout=20,
                         params={"series_id": series_id, "api_key": key, "file_type": "json", "observation_start": start})
        r.raise_for_status()
        obs = r.json().get("observations", [])
        s = pd.Series({pd.Timestamp(o["date"]): pd.to_numeric(o["value"], errors="coerce") for o in obs}, dtype=float)
    else:
        last_err = None
        for attempt in range(2):
            try:
                r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", timeout=12,
                                 params={"id": series_id, "cosd": start},
                                 headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "text/csv"})
                r.raise_for_status()
                break
            except Exception as e:
                last_err = e
        else:
            raise last_err
        df = pd.read_csv(io.StringIO(r.text))
        idx = pd.DatetimeIndex(pd.to_datetime(df.iloc[:, 0], errors="coerce"))
        s = pd.Series(pd.to_numeric(df.iloc[:, 1], errors="coerce").values, index=idx)
    s = s[s.index.notna()].dropna().sort_index()
    if len(s) < 3:
        raise Empty(series_id)
    return s


def fred(series_id):
    try:
        return _fred(series_id, _fred_key()), None
    except Exception as e:
        return pd.Series(dtype=float), f"{series_id}: {type(e).__name__} {str(e)[:80]}"


def transform(s, how):
    if how == "yoy":
        freq = 52 if len(s) > 2 and (s.index[-1] - s.index[-2]).days < 10 else (4 if (s.index[-1] - s.index[-2]).days > 80 else 12)
        return (s / s.shift(freq) - 1) * 100
    if how == "mom":
        return (s / s.shift(1) - 1) * 100
    if how == "diff":
        return s.diff()
    if how == "level_k":
        return s / 1000
    if how == "level_m":
        return s / 1000
    return s


@st.cache_data(ttl=900, show_spinner=False)
def macro():
    """Returns (dict of indicators, list of errors). Successful series are cached 12h; the whole
    result is re-checked every 15 minutes so an outage never blocks the page for long."""
    ids = list(U.MACRO_SERIES)
    with ThreadPoolExecutor(max_workers=9) as ex:
        results = dict(zip(ids, ex.map(fred, ids)))
    out, errors = {}, []
    for sid, (en, ar, how, unit, bad) in U.MACRO_SERIES.items():
        raw, err = results[sid]
        if err:
            errors.append(err)
            continue
        s = transform(raw, how).dropna()
        if len(s) < 2:
            continue
        out[sid] = {"en": en, "ar": ar, "value": float(s.iloc[-1]), "prev": float(s.iloc[-2]), "date": s.index[-1],
                    "unit": unit, "higher_is_bad": bad, "hist": s.tail(36)}
    return out, errors


@st.cache_data(ttl=3600, show_spinner=False)
def _econ_calendar(start, end):
    cal = yf.Calendars(start=start, end=end)
    df = cal.get_economic_events_calendar(limit=100)
    if df is None or df.empty:
        raise Empty("calendar")
    return df.reset_index()


def econ_calendar(days_back=7, days_fwd=7):
    """Economic events (US only when a region column exists)."""
    if not hasattr(yf, "Calendars"):
        return pd.DataFrame()
    start = (date.today() - timedelta(days=days_back)).isoformat()
    end = (date.today() + timedelta(days=days_fwd)).isoformat()
    try:
        df = _econ_calendar(start, end).copy()
    except Exception:
        return pd.DataFrame()
    region = next((c for c in df.columns if c.lower() in ("region", "country", "country code")), None)
    if region:
        df = df[df[region].astype(str).str.upper().isin(["US", "USA", "UNITED STATES"])]
    return df
