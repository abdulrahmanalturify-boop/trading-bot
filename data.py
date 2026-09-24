"""
data.py - Data loading. Sources: Yahoo Finance (yfinance), FRED (economic data), Google Translate.
Rule: failures are NEVER cached (the cached inner function raises, the wrapper returns an empty value),
so a temporary error doesn't stick for hours.
"""
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import numpy as np
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
        if op == "or_eq":
            opts = list(vals[0])
            parts.append(EquityQuery("eq", [field, opts[0]]) if len(opts) == 1
                         else EquityQuery("or", [EquityQuery("eq", [field, v]) for v in opts]))
        else:
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


_TR_FAIL = {"t": 0.0}


def _gtx(text, target):
    r = requests.get("https://translate.googleapis.com/translate_a/single", timeout=8,
                     params={"client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": text},
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return "".join(seg[0] for seg in r.json()[0] if seg and seg[0])


def _mymemory(text, target):
    r = requests.get("https://api.mymemory.translated.net/get", timeout=8, params={"q": text[:480], "langpair": f"en|{target}"})
    r.raise_for_status()
    out = r.json().get("responseData", {}).get("translatedText")
    if not out or "MYMEMORY WARNING" in out:
        raise Empty("mymemory")
    return out


def _deep(text, target):
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source="auto", target=target).translate(text[:4500])


def _translate_one(text, target):
    last = None
    for fn in (_gtx, _deep, _mymemory):
        try:
            out = fn(text, target)
            if out and out.strip():
                return out
        except Exception as e:
            last = e
    raise last or Empty("translate")


def _chunks(texts, limit=1400):
    batch, size = [], 0
    for i, t in enumerate(texts):
        t = (t or "").replace("\n", " ").strip()
        if batch and size + len(t) > limit:
            yield batch
            batch, size = [], 0
        batch.append((i, t))
        size += len(t) + 1
    if batch:
        yield batch


@st.cache_data(ttl=86400, show_spinner=False)
def _translate(texts, target):
    out = list(texts)
    ok = 0

    def do_batch(batch):
        joined = "\n".join(t for _, t in batch)
        try:
            res = _translate_one(joined, target).split("\n")
            if len(res) == len(batch):
                return [(i, r) for (i, _), r in zip(batch, res)]
        except Exception:
            pass
        pairs = []
        for i, t in batch:
            try:
                pairs.append((i, _translate_one(t, target) if t else t))
            except Exception:
                pairs.append((i, None))
        return pairs

    with ThreadPoolExecutor(max_workers=4) as ex:
        for pairs in ex.map(do_batch, list(_chunks(texts))):
            for i, r in pairs:
                if r:
                    out[i] = r
                    ok += 1
    if texts and ok == 0:
        raise Empty("translate")
    return out


def translate(texts, target="ar"):
    """Translates a list of strings (Google gtx -> deep-translator -> MyMemory). Never raises."""
    import time
    texts = tuple(texts)
    if not texts or time.time() - _TR_FAIL["t"] < 600:
        return list(texts)
    try:
        return _translate(texts, target)
    except Exception:
        _TR_FAIL["t"] = time.time()
        return list(texts)


def translate_long(text, target="ar"):
    """Long text (company descriptions): split into sentences-ish chunks."""
    if not text:
        return text
    parts, cur = [], ""
    for sent in text.replace("\n", " ").split(". "):
        if len(cur) + len(sent) > 900 and cur:
            parts.append(cur)
            cur = ""
        cur += sent + ". "
    if cur:
        parts.append(cur)
    return " ".join(translate(parts, target))


# ---------------------------------------------------------------- company logos
# The server checks once (cached 7 days) which logo URL works, then pages use that URL directly:
# no broken-image icons and much lighter pages than embedding the images.
_LOGO_MEM = {}
_LOGO_CB = {"fails": 0, "until": 0.0}


def _is_img(b):
    return len(b) > 200 and (b[:4] == b"\x89PNG" or b[:3] == b"\xff\xd8\xff" or b[:4] == b"RIFF")


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def _logo_src(sym):
    net_err = 0
    for url in (f"https://assets.parqet.com/logos/symbol/{sym}?format=png&size=100",
                f"https://financialmodelingprep.com/image-stock/{sym}.png"):
        try:
            r = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200 and _is_img(r.content):
                return url
        except Exception:
            net_err += 1
    if net_err == 2:
        raise Empty(sym)      # network trouble: try again later (not cached)
    return None               # this company has no logo: remember that


def _one_logo(s):
    try:
        u = _logo_src(s)
    except Exception:                      # host unreachable: retry later, open the breaker after repeated failures
        _LOGO_CB["fails"] += 1
        if _LOGO_CB["fails"] >= 6:
            _LOGO_CB["until"] = time.time() + 600
            _LOGO_CB["fails"] = 0
        return None
    _LOGO_CB["fails"] = 0
    _LOGO_MEM[s] = u                       # a URL, or None when the company has no logo
    return u


def logos(symbols):
    """symbol -> verified logo URL (or None). Indices, FX, futures and crypto get no logo."""
    syms = [s for s in dict.fromkeys(symbols) if s and not any(c in s for c in "^=") and not s.endswith("-USD")]
    if time.time() < _LOGO_CB["until"]:           # logo hosts unreachable: use what we already know
        return {s: _LOGO_MEM.get(s) for s in syms}
    out = {s: _LOGO_MEM[s] for s in syms if s in _LOGO_MEM}
    todo = [s for s in syms if s not in out]
    if todo:
        with ThreadPoolExecutor(max_workers=12) as ex:
            for s, u in zip(todo, ex.map(_one_logo, todo)):
                out[s] = u
    return out


def logo_url(sym):
    """Direct URL (used inside tables, loaded by the browser)."""
    return f"https://assets.parqet.com/logos/symbol/{sym}?format=png&size=64"


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


# ---------------------------------------------------------------- company profile
def profile(symbol):
    i = info(symbol)
    officers = i.get("companyOfficers") or []
    ceo = next((o.get("name") for o in officers if "CEO" in str(o.get("title", "")).upper()), None) or (officers[0].get("name") if officers else None)
    hq = ", ".join(x for x in (i.get("city"), i.get("state"), i.get("country")) if x)
    return {"name": i.get("longName") or i.get("shortName") or U.name_of(symbol), "summary": i.get("longBusinessSummary") or "",
            "sector": i.get("sector") or (U.sector_of(symbol) if U.known(symbol) else None),
            "industry": i.get("industry") or (U.industry_of(symbol) if U.known(symbol) else None),
            "website": i.get("website"), "employees": i.get("fullTimeEmployees"), "hq": hq, "ceo": ceo,
            "exchange": i.get("fullExchangeName") or i.get("exchange"), "currency": i.get("currency", "USD"),
            "officers": officers[:6]}


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def _classify(symbol):
    i = dict(yf.Ticker(symbol).info or {})
    if len(i) < 3:
        raise Empty(symbol)                       # nothing came back: don't cache
    return i.get("sector"), i.get("industry")     # may be (None, None) for funds: cached


def classify(symbols, limit=40):
    """sector/industry for any ticker (static lists first, Yahoo for the rest, cached 7 days)."""
    from sp500 import SP500
    out, todo = {}, []
    for s in symbols:
        if U.known(s):
            out[s] = (U.sector_of(s), U.industry_of(s))
        elif s in SP500:
            out[s] = (SP500[s][1], SP500[s][2])
        else:
            todo.append(s)

    def one(s):
        try:
            return s, _classify(s)
        except Exception:
            return s, (None, None)
    with ThreadPoolExecutor(max_workers=6) as ex:
        for s, v in ex.map(one, todo[:limit]):
            out[s] = v
    return out


# ---------------------------------------------------------------- options
@st.cache_data(ttl=1800, show_spinner=False)
def _expirations(symbol):
    exps = list(yf.Ticker(symbol).options or [])
    if not exps:
        raise Empty(symbol)
    return exps


def expirations(symbol):
    try:
        return _expirations(symbol)
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def _chain(symbol, exp):
    oc = yf.Ticker(symbol).option_chain(exp)
    calls, puts = oc.calls.copy(), oc.puts.copy()
    if calls.empty and puts.empty:
        raise Empty(symbol)
    return calls, puts


def option_chain(symbol, exp):
    try:
        return _chain(symbol, exp)
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


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


BLS_MAP = {"CPIAUCSL": "CUSR0000SA0", "CPILFESL": "CUSR0000SA0L1E", "UNRATE": "LNS14000000", "PAYEMS": "CES0000000001",
           "PPIFIS": "WPSFD4", "JTSJOL": "JTS000000000000000JOL"}


@st.cache_data(ttl=43200, show_spinner=False)
def _bls(series_ids):
    y = date.today().year
    r = requests.post("https://api.bls.gov/publicAPI/v1/timeseries/data/", timeout=20,
                      json={"seriesid": list(series_ids), "startyear": str(y - 3), "endyear": str(y)},
                      headers={"Content-type": "application/json"})
    r.raise_for_status()
    js = r.json()
    if js.get("status") != "REQUEST_SUCCEEDED":
        raise Empty(str(js.get("message"))[:120])
    out = {}
    for ser in js.get("Results", {}).get("series", []):
        pts = {}
        for d in ser.get("data", []):
            per = d.get("period", "")
            if per.startswith("M") and per != "M13":
                v = pd.to_numeric(d.get("value"), errors="coerce")
                pts[pd.Timestamp(int(d["year"]), int(per[1:]), 1)] = v
        if pts:
            out[ser["seriesID"]] = pd.Series(pts).sort_index().dropna()
    if not out:
        raise Empty("bls")
    return out


@st.cache_data(ttl=900, show_spinner=False)
def macro():
    """Returns (indicators, errors, source status). Order: FRED (API key or CSV) -> BLS for the labor/inflation series.
    Successful series are cached 12h; the combined result is re-checked every 15 minutes."""
    ids = list(U.MACRO_SERIES)
    with ThreadPoolExecutor(max_workers=9) as ex:
        results = dict(zip(ids, ex.map(fred, ids)))
    raw, src, errors = {}, {}, []
    for sid, (s, err) in results.items():
        if err:
            errors.append(err)
        else:
            raw[sid], src[sid] = s, "FRED"
    status = {"FRED": f"{len(raw)}/{len(ids)}"}
    need = [sid for sid in ids if sid not in raw and sid in BLS_MAP]
    if need:
        try:
            got = _bls(tuple(BLS_MAP[x] for x in need))
            for sid in need:
                if BLS_MAP[sid] in got:
                    raw[sid], src[sid] = got[BLS_MAP[sid]], "BLS"
            status["BLS"] = f"{sum(1 for v in src.values() if v == 'BLS')}/{len(need)}"
        except Exception as e:
            status["BLS"] = f"failed: {type(e).__name__} {str(e)[:80]}"
    out = {}
    for sid, (en, ar, how, unit, bad) in U.MACRO_SERIES.items():
        if sid not in raw:
            continue
        s = transform(raw[sid], how).dropna()
        if len(s) < 2:
            continue
        out[sid] = {"en": en, "ar": ar, "value": float(s.iloc[-1]), "prev": float(s.iloc[-2]), "date": s.index[-1],
                    "unit": unit, "higher_is_bad": bad, "hist": s.tail(36), "source": src[sid]}
    return out, errors, status


@st.cache_data(ttl=3600, show_spinner=False)
def _econ_calendar(start, end):
    cal = yf.Calendars(start=start, end=end)
    frames = []
    for offset in range(0, 600, 100):
        df = cal.get_economic_events_calendar(limit=100, offset=offset, force=True)
        if df is None or df.empty:
            break
        frames.append(df.reset_index())
        if len(df) < 100:
            break
    if not frames:
        raise Empty("calendar")
    return pd.concat(frames, ignore_index=True).drop_duplicates()


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


def econ_releases(days_back=45):
    """Latest US release per event (actual vs expected vs previous)."""
    df = econ_calendar(days_back, 0)
    if df.empty:
        return df
    ev = next((c for c in df.columns if c.lower() in ("event", "econ release")), df.columns[0])
    act = next((c for c in df.columns if c.lower() == "actual"), None)
    tcol = next((c for c in df.columns if "Time" in c or "Date" in c), None)
    if act is None:
        return pd.DataFrame()
    df = df[pd.to_numeric(df[act], errors="coerce").notna()].copy()
    if tcol:
        df[tcol] = pd.to_datetime(df[tcol], errors="coerce", utc=True)
        df = df.sort_values(tcol, ascending=False)
    return df.drop_duplicates(subset=[ev]).rename(columns={ev: "Event"})


# ---------------------------------------------------------------- batch quotes (one request per 150 symbols)
QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote?"


@st.cache_data(ttl=90, show_spinner=False)
def _quotes(symbols):
    from yfinance.data import YfData
    yd = YfData()
    out = []
    for i in range(0, len(symbols), 150):
        js = yd.get_raw_json(QUOTE_URL, params={"symbols": ",".join(symbols[i:i + 150]), "formatted": "false",
                                                "lang": "en-US", "region": "US"})
        out += ((js or {}).get("quoteResponse") or {}).get("result") or []
    if not out:
        raise Empty("quotes")
    return out


def _ratio(a, b):
    try:
        return (float(a) / float(b) - 1) * 100 if a and b else np.nan
    except (TypeError, ValueError):
        return np.nan


def quotes_df(symbols):
    """Live snapshot for many symbols at once."""
    try:
        raw = _quotes(tuple(dict.fromkeys(symbols)))
    except Exception:
        return pd.DataFrame()
    rows = []
    for q in raw:
        p = q.get("regularMarketPrice")
        rows.append({"Symbol": q.get("symbol"), "Name": q.get("shortName") or q.get("longName") or q.get("symbol"),
                     "Price": p, "Chg %": q.get("regularMarketChangePercent"), "Mkt Cap": q.get("marketCap"),
                     "Volume": q.get("regularMarketVolume"), "Avg Vol": q.get("averageDailyVolume3Month"),
                     "52W %": q.get("fiftyTwoWeekChangePercent"), "vs50 %": _ratio(p, q.get("fiftyDayAverage")),
                     "vs200 %": _ratio(p, q.get("twoHundredDayAverage")), "Hi52 %": _ratio(p, q.get("fiftyTwoWeekHigh")),
                     "Lo52 %": _ratio(p, q.get("fiftyTwoWeekLow")), "PRE": q.get("preMarketChangePercent"),
                     "POST": q.get("postMarketChangePercent"), "P/E": q.get("trailingPE")})
    df = pd.DataFrame(rows)
    for c in ("Price", "Chg %", "Mkt Cap", "Volume", "Avg Vol", "52W %", "PRE", "POST", "P/E"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df["52W %"].notna().sum() > 5 and df["52W %"].abs().median() < 1.5:     # some API versions send fractions
        df["52W %"] = df["52W %"] * 100
    return df


def market_quotes(symbols):
    """(DataFrame, source): batch quotes, or daily history as a fallback."""
    df = quotes_df(symbols)
    if not df.empty and df["Chg %"].notna().sum() >= max(1, len(symbols) // 2):
        return df, "live"
    ch = changes(tuple(symbols))
    if not ch:
        return pd.DataFrame(), "none"
    df = pd.DataFrame([{"Symbol": s, "Price": p, "Chg %": c} for s, (p, c) in ch.items()])
    df["Mkt Cap"] = df["Symbol"].map(lambda s: U.STOCKS[s][3] * 1e9 if s in U.STOCKS else np.nan)
    return df, "history"


@st.cache_data(ttl=1800, show_spinner=False)
def _perf(symbols):
    hist = _history_many(symbols, "1y", "1d")
    rows = []
    for s, df in hist.items():
        c = df["Close"].dropna()
        if len(c) < 6:
            continue
        f = lambda n: (c.iloc[-1] / c.iloc[-n - 1] - 1) * 100 if len(c) > n else np.nan
        ytd = c[c.index.year == c.index[-1].year]
        rows.append({"Symbol": s, "1W": f(5), "1M": f(21), "3M": f(63),
                     "YTD": (c.iloc[-1] / ytd.iloc[0] - 1) * 100 if len(ytd) > 1 else np.nan,
                     "1Y": (c.iloc[-1] / c.iloc[0] - 1) * 100})
    if not rows:
        raise Empty("perf")
    return pd.DataFrame(rows)


def perf_table(symbols):
    """1W / 1M / 3M / YTD / 1Y % change per symbol (cached 30 min)."""
    try:
        return _perf(tuple(dict.fromkeys(symbols)))
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------- financial statements
STMT_KEYS = ("inc_a", "inc_q", "bal_a", "bal_q", "cf_a", "cf_q")


@st.cache_data(ttl=21600, show_spinner=False)
def _statements(symbol):
    t = yf.Ticker(symbol)
    fns = {"inc_a": lambda: t.income_stmt, "inc_q": lambda: t.quarterly_income_stmt, "bal_a": lambda: t.balance_sheet,
           "bal_q": lambda: t.quarterly_balance_sheet, "cf_a": lambda: t.cashflow, "cf_q": lambda: t.quarterly_cashflow}
    out = {}
    for k, fn in fns.items():
        try:
            v = fn()
            out[k] = v if isinstance(v, pd.DataFrame) else pd.DataFrame()
        except Exception:
            out[k] = pd.DataFrame()
    if all(v.empty for v in out.values()):
        raise Empty(symbol)
    return out


def statements(symbol):
    try:
        return _statements(symbol)
    except Exception:
        return {k: pd.DataFrame() for k in STMT_KEYS}


# ---------------------------------------------------------------- options market snapshot
@st.cache_data(ttl=600, show_spinner=False)
def _opt_snapshot(symbol):
    t = yf.Ticker(symbol)
    exps = list(t.options or [])
    if not exps:
        raise Empty(symbol)
    today = pd.Timestamp.now().normalize()
    exp = next((e for e in exps if (pd.Timestamp(e) - today).days >= 1), exps[0])
    oc = t.option_chain(exp)
    calls, puts = oc.calls.copy(), oc.puts.copy()
    if calls.empty and puts.empty:
        raise Empty(symbol)
    und = getattr(oc, "underlying", None) or {}
    price = und.get("regularMarketPrice") if isinstance(und, dict) else None
    if not price:
        h = t.history(period="5d")
        price = float(h["Close"].iloc[-1]) if not h.empty else None
    if not price:
        raise Empty(symbol)
    for df in (calls, puts):
        for c in ("volume", "openInterest", "bid", "ask", "lastPrice", "impliedVolatility", "strike"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce")
    strikes = sorted(set(calls["strike"].dropna()) | set(puts["strike"].dropna()))
    atm = min(strikes, key=lambda k: abs(k - price))

    def mid(df):
        r = df[df["strike"] == atm]
        if r.empty:
            return np.nan
        r = r.iloc[0]
        return (r["bid"] + r["ask"]) / 2 if (r["bid"] or 0) > 0 and (r["ask"] or 0) > 0 else r["lastPrice"]
    iv = np.nanmean([calls.loc[calls["strike"] == atm, "impliedVolatility"].mean(),
                     puts.loc[puts["strike"] == atm, "impliedVolatility"].mean()])
    cv, pv = float(calls["volume"].fillna(0).sum()), float(puts["volume"].fillna(0).sum())
    coi, poi = float(calls["openInterest"].fillna(0).sum()), float(puts["openInterest"].fillna(0).sum())
    unusual = []
    for kind, df in (("CALL", calls), ("PUT", puts)):
        d = df[(df["volume"].fillna(0) >= 500) & (df["volume"].fillna(0) > df["openInterest"].fillna(0))]
        for _, r in d.iterrows():
            unusual.append({"Symbol": symbol, "Type": kind, "Strike": float(r["strike"]), "Expiry": exp, "Volume": float(r["volume"]),
                            "OI": float(r["openInterest"]) if pd.notna(r["openInterest"]) else 0.0, "Last": float(r["lastPrice"]),
                            "IV %": float(r["impliedVolatility"]) * 100 if pd.notna(r["impliedVolatility"]) else np.nan})
    straddle = float(np.nansum([mid(calls), mid(puts)]))
    return {"symbol": symbol, "price": float(price), "expiry": exp, "dte": max((pd.Timestamp(exp) - today).days, 0),
            "atm": float(atm), "iv": float(iv) * 100 if pd.notna(iv) else np.nan, "move": straddle,
            "move_pct": straddle / float(price) * 100, "call_vol": cv, "put_vol": pv, "pc_vol": pv / max(cv, 1),
            "pc_oi": poi / max(coi, 1), "call_oi": coi, "put_oi": poi, "unusual": unusual, "n_exp": len(exps)}


def options_snapshot(symbols):
    """Nearest-expiry options stats for several underlyings (cached 10 min each)."""
    def one(s):
        try:
            return _opt_snapshot(s)
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=6) as ex:
        return [r for r in ex.map(one, symbols) if r]


def known_logos(symbols):
    """Logos already verified by earlier pages (no network)."""
    return {s: _LOGO_MEM[s] for s in symbols if _LOGO_MEM.get(s)}
