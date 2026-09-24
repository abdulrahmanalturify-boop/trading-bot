"""
theme.py - Colors, CSS, number formatting and small HTML components (tiles, sparklines, news cards).
"""
import html
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

BG, CARD, CARD2, BORDER = "#0B0E14", "#131821", "#1A2130", "#242C3B"
TEXT, MUTED = "#E6E8EB", "#8A93A3"
UP, DOWN, ACCENT, GOLD, PURPLE = "#00C087", "#FF4D4F", "#2F7BFF", "#F5C542", "#B07CFF"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Cairo:wght@400;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea {{ font-family: 'Inter', 'Cairo', sans-serif; }}
.block-container {{ padding-top: 1.1rem; padding-bottom: 2.5rem; max-width: 1500px; }}
h1 {{ font-size: 1.7rem !important; font-weight: 700 !important; }}
h2, h3 {{ font-weight: 600 !important; }}
[data-testid="stMetric"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:10px 14px; }}
[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
.up {{ color:{UP}; }} .down {{ color:{DOWN}; }} .muted {{ color:{MUTED}; }}
.card {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:14px 16px; margin-bottom:10px; }}
.section {{ font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; margin:18px 0 8px; font-weight:600; }}
.tiles {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(192px,1fr)); gap:10px; }}
.tile {{ background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:10px 12px; transition:border .15s; }}
.tile:hover {{ border-color:{ACCENT}; }}
.t-name {{ color:{MUTED}; font-size:.78rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.t-row {{ display:flex; justify-content:space-between; align-items:flex-end; gap:6px; }}
.t-val {{ font-size:1.12rem; font-weight:700; margin-top:2px; }}
.t-chg {{ font-size:.8rem; font-weight:600; margin-top:2px; }}
.t-sub {{ color:{MUTED}; font-size:.7rem; margin-top:2px; }}
.q-name {{ color:{MUTED}; font-size:.95rem; }}
.q-price {{ font-size:2.5rem; font-weight:700; line-height:1.15; }}
.q-chg {{ font-size:1.05rem; font-weight:600; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:8px; margin:8px 0; }}
.stat {{ background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:7px 10px; }}
.stat .l {{ color:{MUTED}; font-size:.72rem; }} .stat .v {{ font-weight:600; font-size:.92rem; }}
.range {{ position:relative; height:6px; background:{BORDER}; border-radius:3px; margin:10px 0 4px; }}
.range .dot {{ position:absolute; top:-4px; width:14px; height:14px; border-radius:50%; background:{ACCENT}; border:2px solid {BG}; }}
.badge {{ display:inline-block; padding:2px 9px; border-radius:20px; font-size:.75rem; font-weight:600; margin:2px 3px 2px 0; }}
.b-up {{ background:{UP}22; color:{UP}; }} .b-down {{ background:{DOWN}22; color:{DOWN}; }}
.b-neu {{ background:{MUTED}22; color:{MUTED}; }} .b-acc {{ background:{ACCENT}22; color:{ACCENT}; }}
.plan {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:8px; }}
.plan .p {{ background:{CARD2}; border-radius:8px; padding:9px 12px; border-left:3px solid {ACCENT}; }}
.plan .p .l {{ color:{MUTED}; font-size:.72rem; }} .plan .p .v {{ font-size:1.05rem; font-weight:700; }}
.rtl {{ direction:rtl; text-align:right; font-family:'Cairo', sans-serif; }}
.news {{ background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:12px 14px; margin-bottom:8px; }}
.news a {{ color:{TEXT}; text-decoration:none; font-weight:600; font-size:1rem; line-height:1.6; }}
.news a:hover {{ color:{ACCENT}; }}
.news .meta {{ color:{MUTED}; font-size:.78rem; margin-top:4px; }}
.news .sum {{ color:{MUTED}; font-size:.86rem; margin-top:6px; line-height:1.7; }}
.tag {{ background:{ACCENT}22; color:{ACCENT}; border-radius:4px; padding:1px 7px; font-size:.72rem; margin:0 6px; }}
.status {{ font-size:.8rem; padding:6px 10px; border-radius:8px; background:{CARD}; border:1px solid {BORDER}; margin-bottom:8px; }}
.wl {{ font-size:.82rem; text-align:right; padding-top:6px; line-height:1.25; }}
/* brand */
.brand {{ display:flex; align-items:center; gap:10px; margin:0 0 12px; }}
.brand .logo {{ width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center;
  font-weight:800; font-size:1.25rem; color:#fff; background:linear-gradient(135deg, {ACCENT}, {UP}); }}
.brand .name {{ font-weight:700; font-size:1.05rem; letter-spacing:.01em; }}
.brand .tag-line {{ color:{MUTED}; font-size:.72rem; }}
.brand-sub {{ color:{ACCENT}; font-size:.8rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }}
.check {{ padding:6px 0; border-bottom:1px solid {BORDER}; font-size:.9rem; }}
</style>
"""


# ---------------------------------------------------------------- formatting
def fmt_price(x):
    if x is None or pd.isna(x):
        return "—"
    x = float(x)
    if abs(x) >= 1000:
        return f"{x:,.2f}"
    if abs(x) >= 1:
        return f"{x:,.2f}"
    return f"{x:.4f}"


def fmt_big(x):
    if x is None or pd.isna(x):
        return "—"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(x) >= div:
            return f"{x / div:.2f}{unit}"
    return f"{x:,.0f}"


def fmt_pct(x, signed=True):
    if x is None or pd.isna(x):
        return "—"
    return f"{x:+.2f}%" if signed else f"{x:.2f}%"


def cls(v, invert=False):
    if v is None or pd.isna(v) or v == 0:
        return "muted"
    good = v > 0
    if invert:
        good = not good
    return "up" if good else "down"


def color_style(v):
    try:
        return f"color: {UP}" if v > 0 else (f"color: {DOWN}" if v < 0 else "")
    except TypeError:
        return ""


def esc(s):
    return html.escape(str(s))


# ---------------------------------------------------------------- components
def sparkline(values, color, w=84, h=30):
    v = np.asarray([x for x in values if pd.notna(x)], dtype=float)
    if len(v) < 2:
        return ""
    lo, hi = v.min(), v.max()
    rng = hi - lo if hi > lo else 1.0
    xs = np.linspace(1, w - 1, len(v))
    ys = h - 2 - (v - lo) / rng * (h - 4)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.6" points="{pts}"/></svg>')


def tile(name, value, chg=None, pct=None, spark=None, sub="", invert=False):
    c = cls(pct if pct is not None else chg, invert)
    color = {"up": UP, "down": DOWN}.get(c, MUTED)
    chg_txt = ""
    if pct is not None and chg is not None:
        chg_txt = f"{chg:+,.2f} ({pct:+.2f}%)"
    elif pct is not None:
        chg_txt = f"{pct:+.2f}%"
    elif chg is not None:
        chg_txt = f"{chg:+,.2f}"
    svg = sparkline(spark, color) if spark is not None else ""
    return (f'<div class="tile"><div class="t-name">{esc(name)}</div>'
            f'<div class="t-row"><div><div class="t-val">{value}</div>'
            f'<div class="t-chg {c}">{chg_txt}</div></div>{svg}</div>'
            + (f'<div class="t-sub">{esc(sub)}</div>' if sub else "") + "</div>")


def tiles(items):
    return '<div class="tiles">' + "".join(items) + "</div>"


def badge(text, kind="neu"):
    return f'<span class="badge b-{kind}">{esc(text)}</span>'


def time_ago(ts, lang="en"):
    if ts is None or pd.isna(ts):
        return ""
    mins = (pd.Timestamp.now(tz="UTC") - ts).total_seconds() / 60
    if lang == "ar":
        if mins < 60:
            return f"قبل {int(max(mins, 1))} دقيقة"
        if mins < 1440:
            return f"قبل {int(mins // 60)} ساعة"
        return f"قبل {int(mins // 1440)} يوم"
    if mins < 60:
        return f"{int(max(mins, 1))}m ago"
    if mins < 1440:
        return f"{int(mins // 60)}h ago"
    return f"{int(mins // 1440)}d ago"


def news_html(n, title, summary, tag=None, arabic=True):
    tag_html = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    summary = summary or ""
    short = esc(summary[:260]) + ("…" if len(summary) > 260 else "")
    direction = ' class="news rtl"' if arabic else ' class="news"'
    return (f'<div{direction}>{tag_html}<a href="{esc(n["link"])}" target="_blank">{esc(title)}</a>'
            f'<div class="meta">{esc(n["source"])} · {time_ago(n["time"], "ar" if arabic else "en")}</div>'
            + (f'<div class="sum">{short}</div>' if short else "") + "</div>")


def market_status():
    now = datetime.now(ZoneInfo("America/New_York"))
    t = now.hour * 60 + now.minute
    if now.weekday() >= 5:
        state, dot = "Closed (Weekend)", "🔴"
    elif 570 <= t < 960:
        state, dot = "Market Open", "🟢"
    elif 240 <= t < 570:
        state, dot = "Pre-Market", "🟡"
    elif 960 <= t < 1200:
        state, dot = "After-Hours", "🟡"
    else:
        state, dot = "Closed", "🔴"
    return f"{dot} <b>{state}</b> · {now:%a %H:%M} ET"
