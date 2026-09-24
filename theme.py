"""
theme.py - Brand identity (A.Alturaifi Pro): colors, fonts, CSS, logo, animated hero, ticker tape,
Material icons and small HTML components. No emoji anywhere.
"""
import html
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

BG, CARD, CARD2, BORDER = "#070B14", "#0E1421", "#131B2B", "#1E2839"
TEXT, MUTED = "#E8ECF3", "#8B96AA"
UP, DOWN, ACCENT, GOLD, PURPLE = "#16C784", "#EA3943", "#3B82F6", "#D4AF37", "#A78BFA"

# ---------------------------------------------------------------- logo (SVG, used by st.logo)
LOGO_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F3D27A"/><stop offset="1" stop-color="#B8891E"/></linearGradient></defs>
<rect x="2" y="2" width="60" height="60" rx="14" fill="#0E1421" stroke="url(#g)" stroke-width="3"/>
<path d="M14 48 L28 16 L32 16 L46 48" fill="none" stroke="url(#g)" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
<path d="M19 38 L27 32 L33 35 L47 22" fill="none" stroke="#16C784" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="47" cy="22" r="3.5" fill="#16C784"/></svg>"""

LOGO_WORDMARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 64" width="380" height="64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F3D27A"/><stop offset="1" stop-color="#B8891E"/></linearGradient></defs>
<rect x="2" y="2" width="60" height="60" rx="14" fill="#0E1421" stroke="url(#g)" stroke-width="3"/>
<path d="M14 48 L28 16 L32 16 L46 48" fill="none" stroke="url(#g)" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
<path d="M19 38 L27 32 L33 35 L47 22" fill="none" stroke="#16C784" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="47" cy="22" r="3.5" fill="#16C784"/>
<text x="76" y="37" font-family="Helvetica, Arial, sans-serif" font-size="26" font-weight="700" fill="#E8ECF3" letter-spacing="0.5">A.ALTURAIFI<tspan dx="9" font-weight="800" fill="url(#g)">PRO</tspan></text>
<text x="77" y="55" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#8B96AA" letter-spacing="2.4">US MARKETS · RESEARCH · TRADING</text>
</svg>"""

# ---------------------------------------------------------------- CSS
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0&display=block');
html, body, .stApp, .stMarkdown, button, input, textarea, select, [data-testid="stMetricValue"] {{
  font-family: 'Inter', 'IBM Plex Sans Arabic', system-ui, sans-serif; }}
.stApp {{ background: {BG}; }}
.stApp::before {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background:
    radial-gradient(900px 500px at 10% -10%, rgba(59,130,246,.13), transparent 60%),
    radial-gradient(800px 480px at 95% 0%, rgba(212,175,55,.09), transparent 60%),
    radial-gradient(700px 500px at 50% 110%, rgba(22,199,132,.06), transparent 60%);
  animation: aurora 22s ease-in-out infinite alternate; }}
.stApp::after {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.35;
  background-image: linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 48px 48px; animation: gridmove 40s linear infinite; }}
@keyframes aurora {{ 0% {{ transform: translate3d(0,0,0) scale(1); }} 100% {{ transform: translate3d(-3%,2%,0) scale(1.08); }} }}
@keyframes gridmove {{ 0% {{ background-position: 0 0, 0 0; }} 100% {{ background-position: 48px 48px, 48px 48px; }} }}
header[data-testid="stHeader"] {{ background: rgba(7,11,20,.82); backdrop-filter: blur(14px);
  border-bottom: 1px solid {BORDER}; }}
[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"] {{ display:none; }}
.block-container {{ padding-top: 4.2rem; padding-bottom: 3rem; max-width: 1560px; position:relative; z-index:1; }}
h1 {{ font-size: 1.75rem !important; font-weight: 800 !important; letter-spacing: -.01em; }}
h2, h3 {{ font-weight: 700 !important; }}
.ms {{ font-family:'Material Symbols Rounded'; font-weight:400; font-style:normal; font-size:1.15em; line-height:1;
  display:inline-block; vertical-align:-0.2em; letter-spacing:normal; text-transform:none; white-space:nowrap;
  -webkit-font-feature-settings:'liga'; font-feature-settings:'liga'; }}
[data-testid="stMetric"] {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER};
  border-radius:12px; padding:12px 16px; }}
[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
[data-testid="stExpander"] details {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; }}
[data-testid="stTabs"] button[role="tab"] {{ font-weight:600; }}
.up {{ color:{UP}; }} .down {{ color:{DOWN}; }} .muted {{ color:{MUTED}; }} .gold {{ color:{GOLD}; }}
.card {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px;
  padding:16px 18px; margin-bottom:12px; }}
.sec {{ display:flex; align-items:center; gap:8px; font-size:.78rem; letter-spacing:.12em; text-transform:uppercase;
  color:{MUTED}; margin:22px 0 10px; font-weight:700; }}
.sec .ms {{ color:{GOLD}; font-size:1.25rem; }}
.sec::after {{ content:""; flex:1; height:1px; background:linear-gradient(90deg, {BORDER}, transparent); }}
.page-title {{ display:flex; align-items:center; gap:12px; margin:4px 0 2px; }}
.page-title .ms {{ font-size:2rem; color:{GOLD}; background:rgba(212,175,55,.1); border:1px solid rgba(212,175,55,.25);
  border-radius:12px; padding:6px; }}
.page-title h1 {{ margin:0 !important; padding:0 !important; }}
.page-sub {{ color:{MUTED}; font-size:.9rem; margin:0 0 10px; }}
/* tiles */
.tiles {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(196px,1fr)); gap:10px; }}
.tile {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:12px; padding:11px 13px;
  transition: transform .15s, border-color .15s; }}
.tile:hover {{ border-color:{ACCENT}; transform: translateY(-2px); }}
.t-name {{ color:{MUTED}; font-size:.78rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.t-row {{ display:flex; justify-content:space-between; align-items:flex-end; gap:6px; direction:ltr; }}
.t-val {{ font-size:1.15rem; font-weight:700; margin-top:2px; font-variant-numeric: tabular-nums; }}
.t-chg {{ font-size:.8rem; font-weight:600; margin-top:2px; white-space:nowrap; font-variant-numeric: tabular-nums; }}
.t-sub {{ color:{MUTED}; font-size:.7rem; margin-top:3px; }}
/* hero */
.hero {{ position:relative; height:300px; border-radius:18px; overflow:hidden; border:1px solid {BORDER}; margin-bottom:14px;
  background: linear-gradient(120deg, #06101f, #0b1f3d, #1b1537, #07192c); background-size:300% 300%;
  animation: sky 20s ease-in-out infinite; }}
@keyframes sky {{ 0% {{ background-position:0% 50%; }} 50% {{ background-position:100% 50%; }} 100% {{ background-position:0% 50%; }} }}
.hero svg.city {{ position:absolute; left:0; right:0; bottom:0; width:100%; height:100%; }}
.hero .content {{ position:absolute; inset:0; padding:30px 34px; display:flex; flex-direction:column; justify-content:flex-start;
  background: linear-gradient(90deg, rgba(7,11,20,.85) 0%, rgba(7,11,20,.35) 55%, rgba(7,11,20,0) 100%); }}
.rtl .hero .content {{ background: linear-gradient(270deg, rgba(7,11,20,.85) 0%, rgba(7,11,20,.35) 55%, rgba(7,11,20,0) 100%); }}
.hero .eyebrow {{ color:{GOLD}; font-weight:700; letter-spacing:.22em; font-size:.75rem; text-transform:uppercase; }}
.hero .title {{ font-size:2.4rem; font-weight:800; line-height:1.1; margin:8px 0 6px; color:#fff; }}
.hero .title b {{ background: linear-gradient(90deg,#F3D27A,#B8891E); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.hero .tagline {{ color:#C6CEDB; max-width:560px; font-size:.98rem; line-height:1.6; }}
.hero .chips {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; direction:ltr; }}
.rtl .hero .chips {{ justify-content:flex-end; }}
.hero .chip {{ background:rgba(14,20,33,.75); border:1px solid {BORDER}; backdrop-filter: blur(6px); border-radius:10px;
  padding:7px 12px; font-size:.82rem; font-variant-numeric: tabular-nums; }}
.hero .chip b {{ color:#fff; margin-right:6px; }}
/* ticker tape */
.tape {{ direction:ltr; overflow:hidden; white-space:nowrap; border:1px solid {BORDER}; border-radius:10px;
  background:rgba(14,20,33,.8); margin-bottom:14px; mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent); }}
.tape .track {{ display:inline-flex; gap:34px; padding:9px 0; animation: tape 70s linear infinite; }}
.tape:hover .track {{ animation-play-state: paused; }}
.tape .it {{ font-size:.84rem; font-variant-numeric: tabular-nums; }}
.tape .it b {{ color:#fff; margin-right:6px; }}
@keyframes tape {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
/* quote */
.q-name {{ color:{MUTED}; font-size:.95rem; }}
.q-price {{ font-size:2.6rem; font-weight:800; line-height:1.15; font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; }}
.q-chg {{ font-size:1.05rem; font-weight:700; direction:ltr; display:inline-block; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(134px,1fr)); gap:8px; margin:8px 0; }}
.stat {{ background:{CARD}; border:1px solid {BORDER}; border-radius:9px; padding:8px 11px; }}
.stat .l {{ color:{MUTED}; font-size:.72rem; }} .stat .v {{ font-weight:650; font-size:.93rem; direction:ltr; display:inline-block; }}
.range {{ position:relative; height:6px; background:linear-gradient(90deg,{DOWN},{GOLD},{UP}); border-radius:3px; margin:10px 0 4px; opacity:.8; }}
.range .dot {{ position:absolute; top:-5px; width:16px; height:16px; border-radius:50%; background:#fff; border:3px solid {BG}; }}
.badge {{ display:inline-flex; align-items:center; gap:4px; padding:2px 10px; border-radius:20px; font-size:.76rem; font-weight:650; margin:2px 4px 2px 0; }}
.b-up {{ background:rgba(22,199,132,.13); color:{UP}; }} .b-down {{ background:rgba(234,57,67,.13); color:{DOWN}; }}
.b-neu {{ background:rgba(139,150,170,.13); color:{MUTED}; }} .b-acc {{ background:rgba(59,130,246,.13); color:{ACCENT}; }}
.b-gold {{ background:rgba(212,175,55,.13); color:{GOLD}; }}
.plan {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:8px; }}
.plan .p {{ background:{CARD2}; border-radius:10px; padding:10px 13px; border-inline-start:3px solid {ACCENT}; }}
.plan .p .l {{ color:{MUTED}; font-size:.72rem; }} .plan .p .v {{ font-size:1.05rem; font-weight:700; direction:ltr; display:inline-block; }}
/* news */
.news {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:12px;
  padding:14px 16px; margin-bottom:10px; transition:border-color .15s; }}
.news:hover {{ border-color:{ACCENT}; }}
.news a {{ color:{TEXT}; text-decoration:none; font-weight:650; font-size:1rem; line-height:1.6; }}
.news a:hover {{ color:{ACCENT}; }}
.news .meta {{ color:{MUTED}; font-size:.78rem; margin-top:4px; }}
.news .sum {{ color:{MUTED}; font-size:.87rem; margin-top:6px; line-height:1.7; }}
.news .aff {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
.news .aff .lbl {{ color:{MUTED}; font-size:.74rem; margin-inline-end:4px; }}
.tk {{ direction:ltr; display:inline-flex; gap:6px; align-items:center; border-radius:8px; padding:3px 9px; font-size:.78rem;
  font-weight:700; border:1px solid {BORDER}; background:{BG}; font-variant-numeric: tabular-nums; }}
.tk.up {{ border-color:rgba(22,199,132,.45); }} .tk.down {{ border-color:rgba(234,57,67,.45); }}
.story {{ position:relative; background: linear-gradient(135deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px;
  padding:16px 18px; height:100%; }}
.story .rank {{ position:absolute; top:12px; inset-inline-end:14px; font-size:1.8rem; font-weight:800; color:rgba(212,175,55,.25); }}
.story a {{ color:#fff; text-decoration:none; font-weight:700; font-size:1.02rem; line-height:1.55; display:block; margin-inline-end:34px; }}
.story a:hover {{ color:{GOLD}; }}
.status {{ display:inline-flex; align-items:center; gap:7px; font-size:.8rem; padding:6px 12px; border-radius:20px;
  background:{CARD}; border:1px solid {BORDER}; }}
.dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
.dot.live {{ background:{UP}; box-shadow:0 0 0 0 rgba(22,199,132,.7); animation: pulse 1.8s infinite; }}
.dot.pre {{ background:{GOLD}; }} .dot.closed {{ background:{DOWN}; }}
@keyframes pulse {{ 0% {{ box-shadow:0 0 0 0 rgba(22,199,132,.6); }} 70% {{ box-shadow:0 0 0 8px rgba(22,199,132,0); }} 100% {{ box-shadow:0 0 0 0 rgba(22,199,132,0); }} }}
.wl {{ font-size:.82rem; text-align:right; padding-top:6px; line-height:1.25; direction:ltr; }}
.check {{ padding:8px 0; border-bottom:1px solid {BORDER}; font-size:.9rem; display:flex; gap:8px; align-items:flex-start; }}
.check .ms {{ font-size:1.2rem; }}
.summary li {{ margin-bottom:6px; line-height:1.7; }}
.kpi {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:12px; padding:12px 14px; height:100%; }}
.kpi .l {{ color:{MUTED}; font-size:.75rem; display:flex; gap:6px; align-items:center; }}
.kpi .v {{ font-size:1.25rem; font-weight:800; margin-top:4px; direction:ltr; display:inline-block; }}
.kpi .s {{ font-size:.8rem; margin-top:2px; }}
.mini {{ width:100%; border-collapse:collapse; font-size:.84rem; direction:ltr; }}
.mini td {{ padding:6px 4px; border-bottom:1px solid {BORDER}; font-variant-numeric: tabular-nums; }}
.mini td.r {{ text-align:right; }}
.mini tr:hover td {{ background:rgba(59,130,246,.06); }}
.foot {{ color:{MUTED}; font-size:.75rem; text-align:center; margin-top:40px; padding-top:14px; border-top:1px solid {BORDER}; }}
</style>
"""

RTL_CSS = """
<style>
.block-container, [data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"] { direction: rtl; }
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], h1, h2, h3, h4, label, .stMarkdown { text-align: right; }
.stPlotlyChart, .js-plotly-plot, [data-testid="stDataFrame"], .tape, .t-row, [data-testid="stMetricValue"],
[data-testid="stMetricDelta"] { direction: ltr; }
[data-testid="stMetricValue"] { text-align: right; }
input, textarea { text-align: right; }
html, body, .stApp, .stMarkdown, button, input, textarea { font-family: 'IBM Plex Sans Arabic', 'Inter', system-ui, sans-serif; }
.sec::after { background: linear-gradient(270deg, #1E2839, transparent); }
</style>
"""


# ---------------------------------------------------------------- formatting
def fmt_price(x):
    if x is None or pd.isna(x):
        return "—"
    x = float(x)
    return f"{x:,.2f}" if abs(x) >= 1 else f"{x:.4f}"


def fmt_big(x):
    if x is None or pd.isna(x):
        return "—"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(x) >= div:
            return f"{x / div:.2f}{unit}"
    return f"{x:,.0f}"


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


def icon(name, color=None):
    style = f' style="color:{color}"' if color else ""
    return f'<span class="ms"{style}>{name}</span>'


# ---------------------------------------------------------------- components
def page_title(ic, title, sub=""):
    return (f'<div class="page-title">{icon(ic)}<h1>{esc(title)}</h1></div>'
            + (f'<div class="page-sub">{sub}</div>' if sub else ""))


def sec(ic, text):
    return f'<div class="sec">{icon(ic)}<span>{esc(text)}</span></div>'


def sparkline(values, color, w=84, h=30):
    v = np.asarray([x for x in values if pd.notna(x)], dtype=float)
    if len(v) < 2:
        return ""
    lo, hi = v.min(), v.max()
    rng = hi - lo if hi > lo else 1.0
    xs = np.linspace(1, w - 1, len(v))
    ys = h - 2 - (v - lo) / rng * (h - 4)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"1,{h} " + pts + f" {w - 1},{h}"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polygon fill="{color}" opacity=".12" points="{area}"/>'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.7" points="{pts}"/></svg>')


def tile(name, value, chg=None, pct=None, spark=None, sub="", invert=False):
    c = cls(pct if pct is not None else chg, invert)
    color = {"up": UP, "down": DOWN}.get(c, MUTED)
    if pct is not None and chg is not None:
        txt = f"{chg:+,.2f} ({pct:+.2f}%)"
    elif pct is not None:
        txt = f"{pct:+.2f}%"
    elif chg is not None:
        txt = f"{chg:+,.2f}"
    else:
        txt = ""
    svg = sparkline(spark, color) if spark is not None else ""
    return (f'<div class="tile"><div class="t-name">{esc(name)}</div><div class="t-row"><div>'
            f'<div class="t-val">{value}</div><div class="t-chg {c}">{txt}</div></div>{svg}</div>'
            + (f'<div class="t-sub">{esc(sub)}</div>' if sub else "") + "</div>")


def tiles(items):
    return '<div class="tiles">' + "".join(items) + "</div>"


def badge(text, kind="neu", ic=None):
    return f'<span class="badge b-{kind}">{icon(ic) if ic else ""}{esc(text)}</span>'


def ticker_chip(sym, pct):
    if pct is None or pd.isna(pct):
        return f'<span class="tk">{esc(sym)}</span>'
    c = cls(pct)
    arrow = "arrow_drop_up" if pct > 0 else ("arrow_drop_down" if pct < 0 else "remove")
    return f'<span class="tk {c}">{esc(sym)} <span class="{c}">{icon(arrow)}{pct:+.2f}%</span></span>'


def kpi(ic, label, value, sub="", sub_cls="muted"):
    return (f'<div class="kpi"><div class="l">{icon(ic)}{esc(label)}</div><div class="v">{value}</div>'
            f'<div class="s {sub_cls}">{sub}</div></div>')


def mini_table(rows):
    """rows: list of (left_html, right_html)."""
    return '<table class="mini">' + "".join(f'<tr><td>{a}</td><td class="r">{b}</td></tr>' for a, b in rows) + "</table>"


def tape(items):
    inner = "".join(f'<span class="it"><b>{esc(n)}</b>{fmt_price(p)} '
                    f'<span class="{cls(c)}">{c:+.2f}%</span></span>' for n, p, c in items)
    return f'<div class="tape"><div class="track">{inner}{inner}</div></div>'


def time_ago(ts, ar=False):
    if ts is None or pd.isna(ts):
        return ""
    mins = (pd.Timestamp.now(tz="UTC") - ts).total_seconds() / 60
    if ar:
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


def news_card(n, title, summary, chips="", aff_label="", ar=False, tag=None):
    summary = summary or ""
    short = esc(summary[:280]) + ("…" if len(summary) > 280 else "")
    tag_html = f'{badge(tag, "acc")} ' if tag else ""
    aff = f'<div class="aff"><span class="lbl">{esc(aff_label)}</span>{chips}</div>' if chips else ""
    return (f'<div class="news">{tag_html}<a href="{esc(n["link"])}" target="_blank">{esc(title)}</a>'
            f'<div class="meta">{icon("schedule")} {esc(n["source"])} · {time_ago(n["time"], ar)}</div>'
            + (f'<div class="sum">{short}</div>' if short else "") + aff + "</div>")


def market_status(ar=False):
    now = datetime.now(ZoneInfo("America/New_York"))
    t = now.hour * 60 + now.minute
    if now.weekday() >= 5:
        state, dot = ("السوق مغلق (عطلة)" if ar else "Closed · Weekend"), "closed"
    elif 570 <= t < 960:
        state, dot = ("السوق مفتوح" if ar else "Market Open"), "live"
    elif 240 <= t < 570:
        state, dot = ("ما قبل الافتتاح" if ar else "Pre-Market"), "pre"
    elif 960 <= t < 1200:
        state, dot = ("ما بعد الإغلاق" if ar else "After-Hours"), "pre"
    else:
        state, dot = ("السوق مغلق" if ar else "Market Closed"), "closed"
    return f'<span class="status"><span class="dot {dot}"></span><b>{state}</b><span class="muted">· {now:%H:%M} ET</span></span>'


# ---------------------------------------------------------------- animated skyline hero
def _windows(x0, y0, w, h, cols, rows, seed):
    rng = np.random.default_rng(seed)
    out = []
    cw, rh = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            if rng.random() < 0.55:
                out.append(f'<rect class="win" x="{x0 + c * cw + cw * 0.28:.1f}" y="{y0 + r * rh + rh * 0.3:.1f}" '
                           f'width="{cw * 0.44:.1f}" height="{rh * 0.4:.1f}" '
                           f'style="animation-duration:{rng.uniform(2.5, 9):.1f}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
    return "".join(out)


LINE_PTS = [(0, 210), (90, 200), (160, 215), (240, 180), (320, 190), (400, 150), (470, 165), (560, 120), (640, 140),
            (720, 100), (800, 115), (880, 80), (960, 98), (1040, 60), (1120, 75), (1200, 45), (1300, 58), (1400, 30)]
LINE_PATH = "M" + " L".join(f"{x} {y}" for x, y in LINE_PTS)

HERO_CSS = f"""<style>
.hero .win {{ fill:#F3D27A; opacity:.75; animation-name: twinkle; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }}
.hero .star {{ fill:#fff; animation: twinkle 4s ease-in-out infinite; }}
@keyframes twinkle {{ 0%,100% {{ opacity:.85; }} 50% {{ opacity:.08; }} }}
.hero .mline {{ stroke-dasharray: 2600; stroke-dashoffset: 2600; animation: draw 9s ease-in-out infinite; }}
@keyframes draw {{ 0% {{ stroke-dashoffset:2600; }} 60%,100% {{ stroke-dashoffset:0; }} }}
.hero .mdot {{ offset-path: path('{LINE_PATH}'); offset-rotate: 0deg; animation: travel 9s ease-in-out infinite; }}
@keyframes travel {{ 0% {{ offset-distance:0%; }} 60%,100% {{ offset-distance:100%; }} }}
.hero .beam {{ animation: beam 7s ease-in-out infinite; transform-origin: 907px 20px; }}
@keyframes beam {{ 0%,100% {{ transform: rotate(-18deg); opacity:.18; }} 50% {{ transform: rotate(18deg); opacity:.32; }} }}
</style>"""


def _skyline():
    back = "#0f2140"
    front = "#070d1a"
    s = []
    rng = np.random.default_rng(7)
    for _ in range(40):
        s.append(f'<circle class="star" cx="{rng.uniform(0, 1400):.0f}" cy="{rng.uniform(5, 150):.0f}" '
                 f'r="{rng.uniform(0.6, 1.6):.1f}" style="animation-delay:-{rng.uniform(0, 4):.1f}s"/>')
    s.append('<defs><linearGradient id="ln" x1="0" x2="1"><stop offset="0" stop-color="#16C784" stop-opacity="0"/>'
             '<stop offset=".3" stop-color="#16C784"/><stop offset="1" stop-color="#F3D27A"/></linearGradient>'
             '<linearGradient id="bm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F3D27A" stop-opacity=".9"/>'
             '<stop offset="1" stop-color="#F3D27A" stop-opacity="0"/></linearGradient>'
             '<filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/>'
             '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    s.append('<path class="beam" d="M907 20 L760 350 L1054 350 Z" fill="url(#bm)"/>')
    s.append(f'<g fill="{back}">'
             '<rect x="640" y="150" width="70" height="200"/><rect x="720" y="120" width="55" height="230"/>'
             '<rect x="1130" y="140" width="80" height="210"/><rect x="1220" y="170" width="60" height="180"/>'
             '<rect x="520" y="175" width="60" height="175"/><rect x="1300" y="130" width="70" height="220"/>'
             '<path d="M1010 350 L1010 95 Q1075 150 1080 350 Z"/><rect x="1004" y="80" width="4" height="20"/>'
             '<path d="M880 350 L880 170 L890 170 L890 120 L898 120 L898 70 L904 70 L904 20 L907 20 '
             'L910 70 L916 70 L916 120 L924 120 L924 170 L934 170 L934 350 Z"/></g>')
    s.append(f'<path class="mline" d="{LINE_PATH}" fill="none" stroke="url(#ln)" stroke-width="2.5" filter="url(#glow)"/>')
    s.append('<circle class="mdot" r="5" fill="#F3D27A" filter="url(#glow)"/>')
    s.append(f'<g fill="{front}">'
             '<rect x="150" y="248" width="230" height="102"/><path d="M140 250 L265 205 L390 250 Z"/>'
             '<rect x="140" y="248" width="250" height="8"/>'
             '<rect x="0" y="210" width="80" height="140"/><rect x="85" y="185" width="55" height="165"/>'
             '<path d="M400 350 L400 170 L412 170 L412 130 L424 130 L424 95 L432 95 L432 55 L436 55 L436 95 L444 95 L444 130 '
             'L456 130 L456 170 L468 170 L468 350 Z"/>'
             '<rect x="480" y="230" width="75" height="120"/><rect x="590" y="200" width="60" height="150"/>'
             '<rect x="780" y="215" width="80" height="135"/><rect x="950" y="235" width="50" height="115"/>'
             '<rect x="1090" y="225" width="45" height="125"/><rect x="1370" y="205" width="40" height="145"/></g>')
    s.append("".join(f'<rect x="{165 + i * 28}" y="262" width="10" height="84" fill="#10213d"/>' for i in range(8)))
    s.append(_windows(0, 220, 80, 120, 4, 6, 1) + _windows(85, 195, 55, 150, 3, 7, 2) + _windows(400, 180, 68, 165, 3, 9, 3)
             + _windows(480, 240, 75, 105, 4, 5, 4) + _windows(590, 210, 60, 135, 3, 7, 5) + _windows(780, 225, 80, 120, 4, 6, 6)
             + _windows(950, 245, 50, 100, 2, 5, 8) + _windows(1090, 235, 45, 110, 2, 5, 9) + _windows(1370, 215, 40, 130, 2, 6, 10))
    return ('<svg class="city" viewBox="0 0 1400 350" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg">'
            + "".join(s) + "</svg>")


_SKYLINE = None


def hero(eyebrow, title_html, tagline, chips_html, rtl=False):
    global _SKYLINE
    if _SKYLINE is None:
        _SKYLINE = _skyline()
    wrap = ' class="rtl"' if rtl else ""
    return (f'{HERO_CSS}<div{wrap}><div class="hero">{_SKYLINE}<div class="content">'
            f'<div class="eyebrow">{esc(eyebrow)}</div><div class="title">{title_html}</div>'
            f'<div class="tagline">{esc(tagline)}</div><div class="chips">{chips_html}</div></div></div></div>')
