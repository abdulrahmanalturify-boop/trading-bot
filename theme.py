"""
theme.py - Brand identity v3 (A.Alturaifi Pro): palette, fonts, logo, CSS, animated hero, ticker tape,
company logo circles, Material icons and HTML components. No emoji anywhere.
Fonts: Plus Jakarta Sans (Latin) + Readex Pro (Arabic).
"""
import base64
import hashlib
import html
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

BG, CARD, CARD2, BORDER = "#0A0E17", "#111723", "#161D2B", "#222B3B"
TEXT, MUTED = "#E9EDF5", "#8A94A7"
UP, DOWN = "#0ECB81", "#F6465D"
ACCENT, VIOLET, CYAN, GOLD, PURPLE = "#3D7BFF", "#8B5CF6", "#22D3EE", "#F5B94A", "#A78BFA"

# ---------------------------------------------------------------- logo
_MARK = """<defs><linearGradient id="bgA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3D7BFF"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>
<rect x="0" y="0" width="64" height="64" rx="16" fill="url(#bgA)"/>
<path d="M17 48 L29.5 15.5 Q32 11 34.5 15.5 L47 48" fill="none" stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M22 37 L30 31 L35 34 L48 24" fill="none" stroke="#22D3EE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M43 23.2 L48.6 23.6 L48.2 29.2" fill="none" stroke="#22D3EE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>"""

LOGO_ICON = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{_MARK}</svg>'
LOGO_WORDMARK = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 64" width="300" height="64">{_MARK}
<defs><linearGradient id="tx" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5B8CFF"/><stop offset="1" stop-color="#A78BFA"/></linearGradient></defs>
<text x="78" y="43" font-family="Plus Jakarta Sans, Helvetica Neue, Helvetica, Arial, sans-serif" font-size="31" font-weight="800" fill="#FFFFFF" letter-spacing="-0.5">Alturaifi<tspan dx="9" fill="url(#tx)" font-weight="800" letter-spacing="1">PRO</tspan></text>
</svg>"""

FONT_LATIN, FONT_AR = "'Plus Jakarta Sans'", "'Readex Pro'"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Readex+Pro:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0&display=block');
html, body, .stApp, .stMarkdown, button, input, textarea, select, label, [data-testid="stMetricValue"], [data-baseweb] {{
  font-family: {FONT_LATIN}, {FONT_AR}, system-ui, sans-serif; }}
.stApp {{ background: {BG}; }}
.stApp::before {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background: radial-gradient(900px 520px at 8% -12%, rgba(61,123,255,.16), transparent 60%),
              radial-gradient(760px 480px at 96% -6%, rgba(139,92,246,.13), transparent 60%),
              radial-gradient(700px 480px at 50% 112%, rgba(34,211,238,.06), transparent 60%);
  animation: aurora 22s ease-in-out infinite alternate; }}
.stApp::after {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.32;
  background-image: linear-gradient(rgba(255,255,255,.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.022) 1px, transparent 1px);
  background-size: 52px 52px; animation: gridmove 44s linear infinite; }}
@keyframes aurora {{ 0% {{ transform: translate3d(0,0,0) scale(1); }} 100% {{ transform: translate3d(-3%,2%,0) scale(1.08); }} }}
@keyframes gridmove {{ 0% {{ background-position:0 0,0 0; }} 100% {{ background-position:52px 52px,52px 52px; }} }}
header[data-testid="stHeader"] {{ background: rgba(10,14,23,.86); backdrop-filter: blur(14px); border-bottom: 1px solid {BORDER}; }}
[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"] {{ display:none; }}
.block-container {{ padding-top: 4.4rem; padding-bottom: 3rem; max-width: 1560px; position:relative; z-index:1; }}
h1 {{ font-size: 1.8rem !important; font-weight: 800 !important; letter-spacing: -.02em; }}
h2, h3 {{ font-weight: 700 !important; letter-spacing: -.01em; }}
.ms {{ font-family:'Material Symbols Rounded'; font-weight:400; font-style:normal; font-size:1.15em; line-height:1; display:inline-block;
  vertical-align:-0.2em; letter-spacing:normal; text-transform:none; white-space:nowrap; font-feature-settings:'liga'; }}
[data-testid="stMetric"] {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 16px; }}
[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
[data-testid="stMetricValue"] {{ font-weight:700; letter-spacing:-.01em; }}
[data-testid="stExpander"] details {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; }}
[data-testid="stTabs"] button[role="tab"] {{ font-weight:650; }}
.stButton > button, .stDownloadButton > button {{ border-radius:10px; font-weight:650; }}
.up {{ color:{UP}; }} .down {{ color:{DOWN}; }} .muted {{ color:{MUTED}; }} .acc {{ color:{ACCENT}; }}
.num {{ font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; }}
.card {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; margin-bottom:12px; }}
.sec {{ display:flex; align-items:center; gap:8px; font-size:.8rem; letter-spacing:.1em; text-transform:uppercase; color:{MUTED};
  margin:24px 0 10px; font-weight:700; }}
.sec .ms {{ color:{ACCENT}; font-size:1.3rem; }}
.sec::after {{ content:""; flex:1; height:1px; background:linear-gradient(90deg, {BORDER}, transparent); }}
.page-title {{ display:flex; align-items:center; gap:12px; margin:4px 0 2px; }}
.page-title .ms {{ font-size:1.9rem; color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:12px; padding:7px; }}
.page-title h1 {{ margin:0 !important; padding:0 !important; }}
.page-sub {{ color:{MUTED}; font-size:.92rem; margin:2px 0 12px; }}
/* tiles */
.tiles {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(196px,1fr)); gap:10px; }}
.tile {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:11px 13px; transition: transform .15s, border-color .15s; }}
.tile:hover {{ border-color:{ACCENT}; transform: translateY(-2px); }}
.t-name {{ color:{MUTED}; font-size:.78rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.t-row {{ display:flex; justify-content:space-between; align-items:flex-end; gap:6px; direction:ltr; }}
.t-val {{ font-size:1.15rem; font-weight:750; margin-top:2px; font-variant-numeric: tabular-nums; }}
.t-chg {{ font-size:.8rem; font-weight:650; margin-top:2px; white-space:nowrap; font-variant-numeric: tabular-nums; }}
.t-sub {{ color:{MUTED}; font-size:.7rem; margin-top:3px; }}
/* hero */
.hero {{ position:relative; height:290px; border-radius:20px; overflow:hidden; border:1px solid {BORDER}; margin-bottom:14px;
  background: linear-gradient(120deg, #060c1c, #0c1d3f, #1c1543, #071a33); background-size:300% 300%; animation: sky 20s ease-in-out infinite; }}
@keyframes sky {{ 0% {{ background-position:0% 50%; }} 50% {{ background-position:100% 50%; }} 100% {{ background-position:0% 50%; }} }}
.hero svg.city {{ position:absolute; left:0; right:0; bottom:0; width:100%; height:100%; }}
.hero .content {{ position:absolute; inset:0; padding:30px 34px; display:flex; flex-direction:column;
  background: linear-gradient(90deg, rgba(10,14,23,.88) 0%, rgba(10,14,23,.35) 55%, rgba(10,14,23,0) 100%); }}
.rtl .hero .content {{ background: linear-gradient(270deg, rgba(10,14,23,.88) 0%, rgba(10,14,23,.35) 55%, rgba(10,14,23,0) 100%); }}
.hero .eyebrow {{ color:{CYAN}; font-weight:700; letter-spacing:.2em; font-size:.74rem; text-transform:uppercase; }}
.hero .title {{ font-size:2.45rem; font-weight:800; line-height:1.1; margin:8px 0 6px; color:#fff; letter-spacing:-.02em; }}
.hero .title b {{ background: linear-gradient(90deg,{ACCENT},{VIOLET},{CYAN}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.hero .tagline {{ color:#C7CFDD; max-width:560px; font-size:.98rem; line-height:1.65; }}
.hero .chips {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; direction:ltr; }}
.rtl .hero .chips {{ justify-content:flex-end; }}
.hero .chip {{ background:rgba(17,23,35,.78); border:1px solid {BORDER}; backdrop-filter: blur(6px); border-radius:10px; padding:7px 12px; font-size:.82rem; font-variant-numeric: tabular-nums; }}
.hero .chip b {{ color:#fff; margin-right:6px; }}
/* ticker tape */
.tape {{ direction:ltr; overflow:hidden; white-space:nowrap; border:1px solid {BORDER}; border-radius:12px; background:rgba(17,23,35,.85);
  margin-bottom:14px; mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent); }}
.tape .track {{ display:inline-flex; gap:34px; padding:9px 0; animation: tape 70s linear infinite; }}
.tape:hover .track {{ animation-play-state: paused; }}
.tape .it {{ font-size:.84rem; font-variant-numeric: tabular-nums; }} .tape .it b {{ color:#fff; margin-right:6px; }}
@keyframes tape {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
/* company logo circle */
.lg {{ position:relative; flex:none; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; overflow:hidden;
  color:#fff; font-weight:800; letter-spacing:-.02em; vertical-align:middle; box-shadow: 0 0 0 1px rgba(255,255,255,.08); }}
.lg img {{ width:100%; height:100%; object-fit:contain; background:#fff; padding:12%; box-sizing:border-box; }}
.co {{ display:flex; align-items:center; gap:10px; min-width:0; }}
.co .nm {{ min-width:0; }} .co .tk {{ font-weight:750; color:#fff; }}
.co .sub {{ color:{MUTED}; font-size:.76rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:190px; }}
/* rows / movers */
.rowlist {{ display:flex; flex-direction:column; }}
.rw {{ display:grid; grid-template-columns: minmax(0,1fr) auto auto; gap:12px; align-items:center; padding:9px 4px; border-bottom:1px solid {BORDER}; direction:ltr; }}
.rw:last-child {{ border-bottom:none; }}
.rw:hover {{ background:rgba(61,123,255,.06); }}
.px {{ font-variant-numeric: tabular-nums; font-weight:650; text-align:right; }}
.pill {{ display:inline-block; min-width:74px; text-align:center; padding:4px 8px; border-radius:8px; font-weight:750; font-size:.82rem; font-variant-numeric: tabular-nums; }}
.pill.up {{ background:rgba(14,203,129,.14); color:{UP}; }} .pill.down {{ background:rgba(246,70,93,.14); color:{DOWN}; }}
.pill.muted {{ background:rgba(138,148,167,.14); }}
.meter {{ height:5px; border-radius:3px; background:{BORDER}; overflow:hidden; margin-top:4px; }}
.meter span {{ display:block; height:100%; background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.mcard {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:14px 14px 6px; height:100%; }}
.mcard .hd {{ display:flex; align-items:center; gap:8px; font-weight:750; margin-bottom:6px; }}
.mcard .hd .ms {{ color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:8px; padding:4px; font-size:1.05rem; }}
.lead {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:10px; }}
.lc {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px; direction:ltr; }}
.lc .top {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.lc .bot {{ display:flex; justify-content:space-between; align-items:flex-end; margin-top:10px; gap:8px; }}
.lc .rank {{ color:{MUTED}; font-size:.75rem; font-weight:700; }}
/* quote */
.q-name {{ color:{MUTED}; font-size:.95rem; }}
.q-price {{ font-size:2.6rem; font-weight:800; line-height:1.15; font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; letter-spacing:-.02em; }}
.q-chg {{ font-size:1.05rem; font-weight:700; direction:ltr; display:inline-block; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(134px,1fr)); gap:8px; margin:8px 0; }}
.stat {{ background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:8px 11px; }}
.stat .l {{ color:{MUTED}; font-size:.72rem; }} .stat .v {{ font-weight:650; font-size:.93rem; }}
.range {{ position:relative; height:6px; background:linear-gradient(90deg,{DOWN},{GOLD},{UP}); border-radius:3px; margin:10px 0 4px; opacity:.85; }}
.range .dot {{ position:absolute; top:-5px; width:16px; height:16px; border-radius:50%; background:#fff; border:3px solid {BG}; }}
.badge {{ display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:20px; font-size:.76rem; font-weight:650; margin:2px 4px 2px 0; }}
.b-up {{ background:rgba(14,203,129,.13); color:{UP}; }} .b-down {{ background:rgba(246,70,93,.13); color:{DOWN}; }}
.b-neu {{ background:rgba(138,148,167,.13); color:{MUTED}; }} .b-acc {{ background:rgba(61,123,255,.14); color:#7EA6FF; }}
.b-vio {{ background:rgba(139,92,246,.15); color:#B9A0FF; }} .b-gold {{ background:rgba(245,185,74,.13); color:{GOLD}; }}
.plan {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:8px; }}
.plan .p {{ background:{CARD2}; border-radius:10px; padding:10px 13px; border-inline-start:3px solid {ACCENT}; }}
.plan .p .l {{ color:{MUTED}; font-size:.72rem; }} .plan .p .v {{ font-size:1.05rem; font-weight:700; direction:ltr; display:inline-block; }}
/* profile */
.prof {{ display:grid; grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap:10px; }}
.prof .it {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:10px 12px; }}
.prof .it .l {{ color:{MUTED}; font-size:.72rem; display:flex; gap:6px; align-items:center; }}
.prof .it .v {{ font-weight:650; margin-top:3px; }}
.desc {{ line-height:1.9; font-size:.97rem; color:#D5DBE6; }}
/* news */
.news {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; margin-bottom:10px; transition:border-color .15s; }}
.news:hover {{ border-color:{ACCENT}; }}
.news a {{ color:{TEXT}; text-decoration:none; font-weight:650; font-size:1rem; line-height:1.65; }}
.news a:hover {{ color:#7EA6FF; }}
.news .meta {{ color:{MUTED}; font-size:.78rem; margin-top:4px; }}
.news .sum {{ color:{MUTED}; font-size:.88rem; margin-top:6px; line-height:1.75; }}
.aff {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
.aff .lbl {{ color:{MUTED}; font-size:.74rem; margin-inline-end:4px; }}
.tkc {{ direction:ltr; display:inline-flex; gap:6px; align-items:center; border-radius:20px; padding:3px 10px 3px 3px; font-size:.78rem; font-weight:700;
  border:1px solid {BORDER}; background:{BG}; font-variant-numeric: tabular-nums; }}
.tkc.up {{ border-color:rgba(14,203,129,.45); }} .tkc.down {{ border-color:rgba(246,70,93,.45); }}
.story {{ position:relative; background: linear-gradient(135deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; height:100%; }}
.story .rank {{ position:absolute; top:10px; inset-inline-end:14px; font-size:1.9rem; font-weight:800; color:rgba(61,123,255,.25); }}
.story a {{ color:#fff; text-decoration:none; font-weight:700; font-size:1.02rem; line-height:1.6; display:block; margin-inline-end:36px; }}
.story a:hover {{ color:#7EA6FF; }}
.status {{ display:inline-flex; align-items:center; gap:7px; font-size:.8rem; padding:6px 12px; border-radius:20px; background:{CARD}; border:1px solid {BORDER}; }}
.dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
.dot.live {{ background:{UP}; animation: pulse 1.8s infinite; }} .dot.pre {{ background:{GOLD}; }} .dot.closed {{ background:{DOWN}; }}
@keyframes pulse {{ 0% {{ box-shadow:0 0 0 0 rgba(14,203,129,.6); }} 70% {{ box-shadow:0 0 0 8px rgba(14,203,129,0); }} 100% {{ box-shadow:0 0 0 0 rgba(14,203,129,0); }} }}
.wl {{ font-size:.82rem; text-align:right; padding-top:6px; line-height:1.25; direction:ltr; }}
.check {{ padding:8px 0; border-bottom:1px solid {BORDER}; font-size:.9rem; display:flex; gap:8px; align-items:flex-start; }}
.check .ms {{ font-size:1.2rem; }}
.summary li {{ margin-bottom:6px; line-height:1.8; }}
.kpi {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 14px; height:100%; }}
.kpi .l {{ color:{MUTED}; font-size:.75rem; display:flex; gap:6px; align-items:center; }}
.kpi .v {{ font-size:1.2rem; font-weight:800; margin-top:6px; display:flex; align-items:center; gap:8px; direction:ltr; }}
.kpi .s {{ font-size:.8rem; margin-top:4px; }}
/* options T-chain */
.chain {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.8rem; direction:ltr; font-variant-numeric: tabular-nums; }}
.chain th {{ position:sticky; top:0; background:{CARD2}; color:{MUTED}; font-weight:650; padding:7px 6px; text-align:right; border-bottom:1px solid {BORDER}; }}
.chain th.side {{ text-align:center; color:#fff; font-size:.84rem; }}
.chain td {{ padding:6px 6px; text-align:right; border-bottom:1px solid rgba(34,43,59,.6); }}
.chain td.k {{ text-align:center; font-weight:800; color:#fff; background:{CARD2}; }}
.chain tr:hover td {{ background:rgba(61,123,255,.08); }}
.chain td.itm-c {{ background:rgba(14,203,129,.06); }} .chain td.itm-p {{ background:rgba(246,70,93,.06); }}
.chain tr.atm td {{ border-top:2px solid {ACCENT}; }}
.chainwrap {{ max-height:560px; overflow:auto; border:1px solid {BORDER}; border-radius:14px; }}
/* academy */
.courses {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:14px; }}
.course {{ display:block; text-decoration:none !important; color:{TEXT} !important; background:{CARD}; border:1px solid {BORDER}; border-radius:18px; overflow:hidden;
  transition: transform .18s, border-color .18s, box-shadow .18s; }}
.course:hover {{ transform: translateY(-4px); border-color:{ACCENT}; box-shadow: 0 12px 30px rgba(61,123,255,.18); }}
.course .art {{ height:150px; position:relative; overflow:hidden; }}
.course .art svg {{ width:100%; height:100%; display:block; }}
.course .body {{ padding:14px 16px 16px; }}
.course .ttl {{ font-weight:800; font-size:1.05rem; line-height:1.4; }}
.course .tag {{ color:{MUTED}; font-size:.85rem; margin-top:6px; line-height:1.6; }}
.course .meta {{ display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }}
.course .play {{ position:absolute; inset-inline-end:14px; bottom:12px; width:40px; height:40px; border-radius:50%; background:rgba(255,255,255,.95);
  display:flex; align-items:center; justify-content:center; color:{BG}; }}
.lesson {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:18px; padding:22px 24px; }}
.lesson h3 {{ margin-top:0 !important; }}
.lesson p, .lesson li {{ line-height:1.9; font-size:1rem; color:#D5DBE6; }}
.take {{ border-inline-start:3px solid {CYAN}; background:rgba(34,211,238,.07); padding:10px 14px; border-radius:10px; margin-top:12px; }}
.steps {{ display:flex; gap:6px; margin:6px 0 14px; }}
.steps span {{ flex:1; height:6px; border-radius:3px; background:{BORDER}; }} .steps span.on {{ background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.gl {{ border-bottom:1px solid {BORDER}; padding:12px 2px; }} .gl b {{ font-size:1rem; }} .gl .d {{ color:#C9D0DC; line-height:1.8; margin-top:4px; }}
.foot {{ color:{MUTED}; font-size:.75rem; text-align:center; margin-top:40px; padding-top:14px; border-top:1px solid {BORDER}; }}
</style>
"""

RTL_CSS = f"""
<style>
.block-container, [data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"] {{ direction: rtl; }}
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], h1, h2, h3, h4, label, .stMarkdown {{ text-align: right; }}
.stPlotlyChart, .js-plotly-plot, [data-testid="stDataFrame"], .tape, .t-row, [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{ direction: ltr; }}
[data-testid="stMetricValue"] {{ text-align: right; }}
input, textarea {{ text-align: right; }}
html, body, .stApp, .stMarkdown, button, input, textarea, select, label, [data-baseweb] {{ font-family: {FONT_AR}, {FONT_LATIN}, system-ui, sans-serif; }}
.sec::after {{ background: linear-gradient(270deg, {BORDER}, transparent); }}
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
    return f'<div class="page-title">{icon(ic)}<h1>{esc(title)}</h1></div>' + (f'<div class="page-sub">{sub}</div>' if sub else "")


def sec(ic, text):
    return f'<div class="sec">{icon(ic)}<span>{esc(text)}</span></div>'


def logo_circle(sym, uri=None, size=32):
    """Company logo in a circle; falls back to initials on a brand-colored circle."""
    s = f"width:{size}px;height:{size}px;font-size:{max(9, int(size * 0.36))}px"
    if uri:
        return f'<span class="lg" style="{s}"><img src="{uri}" alt=""/></span>'
    h = int(hashlib.md5(str(sym).encode()).hexdigest()[:6], 16)
    hue = h % 360
    ini = esc(str(sym).replace("^", "")[:2])
    return (f'<span class="lg" style="{s};background:linear-gradient(135deg,hsl({hue},62%,46%),hsl({(hue + 40) % 360},62%,34%))">'
            f"{ini}</span>")


def company(sym, name="", uri=None, size=32, sub=None):
    sub_html = f'<div class="sub">{esc(sub if sub is not None else name)}</div>' if (sub or name) else ""
    return f'<div class="co">{logo_circle(sym, uri, size)}<div class="nm"><div class="tk">{esc(sym)}</div>{sub_html}</div></div>'


def pill(pct):
    if pct is None or pd.isna(pct):
        return '<span class="pill muted">—</span>'
    return f'<span class="pill {cls(pct)}">{pct:+.2f}%</span>'


def sparkline(values, color, w=84, h=30):
    v = np.asarray([x for x in values if pd.notna(x)], dtype=float) if values is not None else np.array([])
    if len(v) < 2:
        return ""
    lo, hi = v.min(), v.max()
    rng = hi - lo if hi > lo else 1.0
    xs = np.linspace(1, w - 1, len(v))
    ys = h - 2 - (v - lo) / rng * (h - 4)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"1,{h} " + pts + f" {w - 1},{h}"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polygon fill="{color}" opacity=".12" points="{area}"/>'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.7" points="{pts}"/></svg>')


def tile(name, value, chg=None, pct=None, spark=None, sub="", invert=False, head_html=None):
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
    head = head_html or f'<div class="t-name">{esc(name)}</div>'
    return (f'<div class="tile">{head}<div class="t-row"><div><div class="t-val">{value}</div><div class="t-chg {c}">{txt}</div></div>{svg}</div>'
            + (f'<div class="t-sub">{esc(sub)}</div>' if sub else "") + "</div>")


def tiles(items):
    return '<div class="tiles">' + "".join(items) + "</div>"


def badge(text, kind="neu", ic=None):
    return f'<span class="badge b-{kind}">{icon(ic) if ic else ""}{esc(text)}</span>'


def ticker_chip(sym, pct, uri=None):
    c = cls(pct) if pct is not None and not pd.isna(pct) else "muted"
    val = f'<span class="{c}">{pct:+.2f}%</span>' if pct is not None and not pd.isna(pct) else ""
    return f'<span class="tkc {c}">{logo_circle(sym, uri, 20)}{esc(sym)} {val}</span>'


def kpi(ic, label, value_html, sub="", sub_cls="muted"):
    return (f'<div class="kpi"><div class="l">{icon(ic)}{esc(label)}</div><div class="v">{value_html}</div>'
            f'<div class="s {sub_cls}">{sub}</div></div>')


def tape(items):
    inner = "".join(f'<span class="it"><b>{esc(n)}</b>{fmt_price(p)} <span class="{cls(c)}">{c:+.2f}%</span></span>' for n, p, c in items)
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
    short = esc(summary[:300]) + ("…" if len(summary) > 300 else "")
    tag_html = f"{badge(tag, 'acc')} " if tag else ""
    aff = f'<div class="aff"><span class="lbl">{esc(aff_label)}</span>{chips}</div>' if chips else ""
    rtl = " rtl" if ar else ""
    return (f'<div class="news{rtl}">{tag_html}<a href="{esc(n["link"])}" target="_blank">{esc(title)}</a>'
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
                out.append(f'<rect class="win" x="{x0 + c * cw + cw * 0.28:.1f}" y="{y0 + r * rh + rh * 0.3:.1f}" width="{cw * 0.44:.1f}" '
                           f'height="{rh * 0.4:.1f}" style="animation-duration:{rng.uniform(2.5, 9):.1f}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
    return "".join(out)


LINE_PTS = [(0, 210), (90, 200), (160, 215), (240, 180), (320, 190), (400, 150), (470, 165), (560, 120), (640, 140),
            (720, 100), (800, 115), (880, 80), (960, 98), (1040, 60), (1120, 75), (1200, 45), (1300, 58), (1400, 30)]
LINE_PATH = "M" + " L".join(f"{x} {y}" for x, y in LINE_PTS)
HERO_CSS = f"""<style>
.hero .win {{ fill:#9CC3FF; opacity:.7; animation-name: twinkle; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }}
.hero .star {{ fill:#fff; animation: twinkle 4s ease-in-out infinite; }}
@keyframes twinkle {{ 0%,100% {{ opacity:.85; }} 50% {{ opacity:.08; }} }}
.hero .mline {{ stroke-dasharray: 2600; stroke-dashoffset: 2600; animation: draw 9s ease-in-out infinite; }}
@keyframes draw {{ 0% {{ stroke-dashoffset:2600; }} 60%,100% {{ stroke-dashoffset:0; }} }}
.hero .mdot {{ offset-path: path('{LINE_PATH}'); offset-rotate: 0deg; animation: travel 9s ease-in-out infinite; }}
@keyframes travel {{ 0% {{ offset-distance:0%; }} 60%,100% {{ offset-distance:100%; }} }}
.hero .beam {{ animation: beam 7s ease-in-out infinite; transform-origin: 907px 20px; }}
@keyframes beam {{ 0%,100% {{ transform: rotate(-18deg); opacity:.16; }} 50% {{ transform: rotate(18deg); opacity:.3; }} }}
</style>"""


def _skyline():
    back, front = "#0f2247", "#070d1c"
    s = []
    rng = np.random.default_rng(7)
    for _ in range(40):
        s.append(f'<circle class="star" cx="{rng.uniform(0, 1400):.0f}" cy="{rng.uniform(5, 150):.0f}" r="{rng.uniform(0.6, 1.6):.1f}" '
                 f'style="animation-delay:-{rng.uniform(0, 4):.1f}s"/>')
    s.append('<defs><linearGradient id="ln" x1="0" x2="1"><stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>'
             '<stop offset=".35" stop-color="#3D7BFF"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
             '<linearGradient id="bm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9CC3FF" stop-opacity=".9"/>'
             '<stop offset="1" stop-color="#9CC3FF" stop-opacity="0"/></linearGradient>'
             '<filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    s.append('<path class="beam" d="M907 20 L760 350 L1054 350 Z" fill="url(#bm)"/>')
    s.append(f'<g fill="{back}"><rect x="640" y="150" width="70" height="200"/><rect x="720" y="120" width="55" height="230"/>'
             '<rect x="1130" y="140" width="80" height="210"/><rect x="1220" y="170" width="60" height="180"/>'
             '<rect x="520" y="175" width="60" height="175"/><rect x="1300" y="130" width="70" height="220"/>'
             '<path d="M1010 350 L1010 95 Q1075 150 1080 350 Z"/><rect x="1004" y="80" width="4" height="20"/>'
             '<path d="M880 350 L880 170 L890 170 L890 120 L898 120 L898 70 L904 70 L904 20 L907 20 L910 70 L916 70 L916 120 L924 120 '
             'L924 170 L934 170 L934 350 Z"/></g>')
    s.append(f'<path class="mline" d="{LINE_PATH}" fill="none" stroke="url(#ln)" stroke-width="2.6" filter="url(#glow)"/>')
    s.append('<circle class="mdot" r="5" fill="#22D3EE" filter="url(#glow)"/>')
    s.append(f'<g fill="{front}"><rect x="150" y="248" width="230" height="102"/><path d="M140 250 L265 205 L390 250 Z"/>'
             '<rect x="140" y="248" width="250" height="8"/><rect x="0" y="210" width="80" height="140"/><rect x="85" y="185" width="55" height="165"/>'
             '<path d="M400 350 L400 170 L412 170 L412 130 L424 130 L424 95 L432 95 L432 55 L436 55 L436 95 L444 95 L444 130 L456 130 L456 170 '
             'L468 170 L468 350 Z"/><rect x="480" y="230" width="75" height="120"/><rect x="590" y="200" width="60" height="150"/>'
             '<rect x="780" y="215" width="80" height="135"/><rect x="950" y="235" width="50" height="115"/>'
             '<rect x="1090" y="225" width="45" height="125"/><rect x="1370" y="205" width="40" height="145"/></g>')
    s.append("".join(f'<rect x="{165 + i * 28}" y="262" width="10" height="84" fill="#10234a"/>' for i in range(8)))
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
    return (f'{HERO_CSS}<div{wrap}><div class="hero">{_SKYLINE}<div class="content"><div class="eyebrow">{esc(eyebrow)}</div>'
            f'<div class="title">{title_html}</div><div class="tagline">{esc(tagline)}</div><div class="chips">{chips_html}</div></div></div></div>')


def svg_data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
