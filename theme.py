"""
theme.py - Design system v4 (A.Alturaifi Pro).
Rule used everywhere: positive = light-green box + dark-green text, negative = light-red box + dark-red text.
Fonts: Plus Jakarta Sans (Latin) + Readex Pro (Arabic). Material Symbols icons. No emoji.
"""
import base64
import hashlib
import html
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- palette
BG, CARD, CARD2, BORDER = "#0A0E17", "#111723", "#161D2B", "#222B3B"
TEXT, MUTED = "#E9EDF5", "#8A94A7"
UP, DOWN = "#22C55E", "#EF4444"                     # chart strokes on dark surfaces
ACCENT, VIOLET, CYAN, GOLD, ORANGE, PURPLE = "#3D7BFF", "#8B5CF6", "#22D3EE", "#F5B94A", "#F97316", "#A78BFA"
POS_BG, POS_FG, POS_BD = "#D1E7DD", "#0F5132", "#A3CFBB"   # light green box, dark green text
NEG_BG, NEG_FG, NEG_BD = "#F8D7DA", "#842029", "#F1AEB5"   # light red box, dark red text
ACC_BG, ACC_FG = "#DBEAFE", "#1E3A8A"
VIO_BG, VIO_FG = "#EDE9FE", "#4C1D95"
YEL_BG, YEL_FG = "#FEF3C7", "#854D0E"
ORG_BG, ORG_FG = "#FFEDD5", "#9A3412"
NEU_BG, NEU_FG = "#E2E8F0", "#334155"
FONT = "Plus Jakarta Sans, Readex Pro, system-ui, sans-serif"

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
.stApp::after {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.3;
  background-image: linear-gradient(rgba(255,255,255,.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.022) 1px, transparent 1px);
  background-size: 52px 52px; animation: gridmove 44s linear infinite; }}
@keyframes aurora {{ 0% {{ transform: translate3d(0,0,0) scale(1); }} 100% {{ transform: translate3d(-3%,2%,0) scale(1.08); }} }}
@keyframes gridmove {{ 0% {{ background-position:0 0,0 0; }} 100% {{ background-position:52px 52px,52px 52px; }} }}
header[data-testid="stHeader"] {{ background: rgba(10,14,23,.86); backdrop-filter: blur(14px); border-bottom: 1px solid {BORDER}; }}
[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"] {{ display:none; }}
.block-container {{ padding-top: 4.4rem; padding-bottom: 3rem; max-width: 1560px; position:relative; z-index:1; }}
h1 {{ font-size: 1.8rem !important; font-weight: 800 !important; letter-spacing: -.02em; }}
h2, h3 {{ font-weight: 750 !important; letter-spacing: -.01em; }}
.ms {{ font-family:'Material Symbols Rounded'; font-weight:400; font-style:normal; font-size:1.15em; line-height:1; display:inline-block;
  vertical-align:-0.2em; letter-spacing:normal; text-transform:none; white-space:nowrap; font-feature-settings:'liga'; }}
[data-testid="stMetric"] {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 16px; }}
[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
[data-testid="stMetricValue"] {{ font-weight:750; letter-spacing:-.01em; }}
[data-testid="stExpander"] details {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; }}
[data-testid="stTabs"] button[role="tab"] {{ font-weight:650; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:16px !important; }}
.stButton > button, .stDownloadButton > button {{ border-radius:10px; font-weight:650; }}
.muted {{ color:{MUTED}; }} .acc {{ color:#7EA6FF; }}
.upt {{ color:{UP}; }} .dnt {{ color:{DOWN}; }}
.num {{ font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; }}
.card {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; margin-bottom:12px; }}
.sec {{ display:flex; align-items:center; gap:8px; font-size:.8rem; letter-spacing:.1em; text-transform:uppercase; color:{MUTED}; margin:26px 0 10px; font-weight:750; }}
.sec .ms {{ color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:8px; padding:4px; font-size:1.05rem; }}
.sec::after {{ content:""; flex:1; height:1px; background:linear-gradient(90deg, {BORDER}, transparent); }}
.page-title {{ display:flex; align-items:center; gap:12px; margin:4px 0 2px; }}
.page-title .ms {{ font-size:1.9rem; color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:12px; padding:7px; }}
.page-title h1 {{ margin:0 !important; padding:0 !important; }}
.page-sub {{ color:{MUTED}; font-size:.92rem; margin:2px 0 12px; }}
/* ---------- the pastel rule ---------- */
.pos {{ background:{POS_BG} !important; color:{POS_FG} !important; }}
.neg {{ background:{NEG_BG} !important; color:{NEG_FG} !important; }}
.pill {{ display:inline-block; min-width:74px; text-align:center; padding:4px 9px; border-radius:8px; font-weight:750; font-size:.82rem;
  font-variant-numeric: tabular-nums; direction:ltr; }}
.pill.pos {{ border:1px solid {POS_BD}; }} .pill.neg {{ border:1px solid {NEG_BD}; }}
.pill.neu {{ background:rgba(138,148,167,.15); color:{MUTED}; }}
.badge {{ display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:20px; font-size:.76rem; font-weight:700; margin:2px 4px 2px 0; }}
.b-up {{ background:{POS_BG}; color:{POS_FG}; }} .b-down {{ background:{NEG_BG}; color:{NEG_FG}; }}
.b-neu {{ background:rgba(138,148,167,.16); color:#B8C0CE; }} .b-acc {{ background:{ACC_BG}; color:{ACC_FG}; }}
.b-vio {{ background:{VIO_BG}; color:{VIO_FG}; }} .b-gold {{ background:{YEL_BG}; color:{YEL_FG}; }} .b-org {{ background:{ORG_BG}; color:{ORG_FG}; }}
/* tiles */
.tiles {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(196px,1fr)); gap:10px; }}
.tile {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:11px 13px;
  transition: transform .15s, box-shadow .15s; }}
.tile:hover {{ transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,.35); }}
.tile.pos {{ background: linear-gradient(180deg, #DDF0E6, {POS_BG}) !important; border-color:{POS_BD}; }}
.tile.neg {{ background: linear-gradient(180deg, #FBE4E6, {NEG_BG}) !important; border-color:{NEG_BD}; }}
.tile.acc {{ background: linear-gradient(180deg, #E8F0FE, {ACC_BG}); border-color:#BFD3FB; color:{ACC_FG}; }}
.t-name {{ color:{MUTED}; font-size:.78rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.tile.pos .t-name {{ color:#3E6F55; }} .tile.neg .t-name {{ color:#8E4A52; }} .tile.acc .t-name {{ color:#4B5E8C; }}
.t-row {{ display:flex; justify-content:space-between; align-items:flex-end; gap:6px; direction:ltr; }}
.t-val {{ font-size:1.18rem; font-weight:800; margin-top:2px; font-variant-numeric: tabular-nums; }}
.t-chg {{ font-size:.8rem; font-weight:700; margin-top:2px; white-space:nowrap; font-variant-numeric: tabular-nums; }}
.t-sub {{ color:{MUTED}; font-size:.7rem; margin-top:3px; }}
.tile.pos .t-sub {{ color:#4F7A63; }} .tile.neg .t-sub {{ color:#98545B; }} .tile.acc .t-sub {{ color:#56689A; }}
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
.hero .chip {{ background:rgba(17,23,35,.8); border:1px solid {BORDER}; backdrop-filter: blur(6px); border-radius:10px; padding:6px 10px; font-size:.82rem;
  font-variant-numeric: tabular-nums; display:inline-flex; align-items:center; gap:7px; }}
.hero .chip b {{ color:#fff; }} .hero .chip .pill {{ min-width:0; padding:2px 7px; font-size:.75rem; }}
/* ticker tape */
.tape {{ direction:ltr; overflow:hidden; white-space:nowrap; border:1px solid {BORDER}; border-radius:12px; background:rgba(17,23,35,.85);
  margin-bottom:14px; mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent); }}
.tape .track {{ display:inline-flex; gap:26px; padding:8px 0; animation: tape 70s linear infinite; }}
.tape:hover .track {{ animation-play-state: paused; }}
.tape .it {{ font-size:.84rem; font-variant-numeric: tabular-nums; display:inline-flex; align-items:center; gap:7px; }}
.tape .it b {{ color:#fff; }} .tape .it .pill {{ min-width:0; padding:2px 7px; font-size:.74rem; }}
@keyframes tape {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
/* company logo circle + rows */
.lg {{ position:relative; flex:none; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; overflow:hidden;
  color:#fff; font-weight:800; letter-spacing:-.02em; vertical-align:middle; box-shadow: 0 0 0 1px rgba(255,255,255,.08); }}
.lg img {{ width:100%; height:100%; object-fit:contain; background:#fff; padding:12%; box-sizing:border-box; }}
.co {{ display:flex; align-items:center; gap:10px; min-width:0; }}
.co .nm {{ min-width:0; }} .co .tk {{ font-weight:800; color:#fff; }}
.co .sub {{ color:{MUTED}; font-size:.76rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:190px; }}
a.lnk {{ color:inherit !important; text-decoration:none !important; }} a.lnk:hover .tk {{ color:#7EA6FF; text-decoration:underline; }}
.rowlist {{ display:flex; flex-direction:column; }}
.rw {{ display:grid; grid-template-columns: minmax(0,1fr) auto auto; gap:12px; align-items:center; padding:9px 4px; border-bottom:1px solid {BORDER}; direction:ltr; }}
.rw:last-child {{ border-bottom:none; }} .rw:hover {{ background:rgba(61,123,255,.06); border-radius:10px; }}
.px {{ font-variant-numeric: tabular-nums; font-weight:700; text-align:right; }}
.meter {{ height:5px; border-radius:3px; background:{BORDER}; overflow:hidden; margin-top:4px; }}
.meter span {{ display:block; height:100%; background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.mcard {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:14px 14px 6px; height:100%; }}
.mcard .hd {{ display:flex; align-items:center; gap:8px; font-weight:750; margin-bottom:6px; }}
.mcard .hd .ms {{ color:#fff; background:linear-gradient(135deg,{ACCENT},{VIOLET}); border-radius:8px; padding:4px; font-size:1.05rem; }}
.mcard .hd .cnt {{ margin-inline-start:auto; color:{MUTED}; font-size:.75rem; font-weight:600; }}
.lead {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:10px; }}
.lc {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px; direction:ltr; }}
.lc .top {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.lc .bot {{ display:flex; justify-content:space-between; align-items:flex-end; margin-top:10px; gap:8px; }}
.lc .rank {{ color:{MUTED}; font-size:.75rem; font-weight:700; }}
/* quote */
.q-name {{ color:{MUTED}; font-size:.95rem; }}
.q-price {{ font-size:2.6rem; font-weight:800; line-height:1.15; font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; letter-spacing:-.02em; }}
.q-chg {{ font-size:1rem; font-weight:800; direction:ltr; display:inline-block; padding:4px 10px; border-radius:9px; }}
.q-chg.pos {{ border:1px solid {POS_BD}; }} .q-chg.neg {{ border:1px solid {NEG_BD}; }} .q-chg.neu {{ background:rgba(138,148,167,.15); color:{MUTED}; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(134px,1fr)); gap:8px; margin:8px 0; }}
.stat {{ background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:8px 11px; }}
.stat .l {{ color:{MUTED}; font-size:.72rem; }} .stat .v {{ font-weight:700; font-size:.93rem; }}
.range {{ position:relative; height:6px; background:linear-gradient(90deg,{DOWN},{GOLD},{UP}); border-radius:3px; margin:10px 0 4px; opacity:.85; }}
.range .dot {{ position:absolute; top:-5px; width:16px; height:16px; border-radius:50%; background:#fff; border:3px solid {BG}; }}
.plan {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:8px; }}
.plan .p {{ background:{CARD2}; border-radius:12px; padding:10px 13px; border:1px solid {BORDER}; }}
.plan .p .l {{ color:{MUTED}; font-size:.72rem; font-weight:600; }} .plan .p .v {{ font-size:1.05rem; font-weight:800; direction:ltr; display:inline-block; }}
.plan .p.pos, .plan .p.neg, .plan .p.acc {{ border-color:transparent; }}
.plan .p.pos .l {{ color:#3E6F55; }} .plan .p.neg .l {{ color:#8E4A52; }}
.plan .p.acc {{ background:{ACC_BG}; color:{ACC_FG}; }} .plan .p.acc .l {{ color:#4B5E8C; }}
/* profile */
.prof {{ display:grid; grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap:10px; }}
.prof .it {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:10px 12px; }}
.prof .it .l {{ color:{MUTED}; font-size:.72rem; display:flex; gap:6px; align-items:center; }}
.prof .it .v {{ font-weight:650; margin-top:3px; }}
.desc {{ line-height:1.9; font-size:.97rem; color:#D5DBE6; }}
/* news */
.news {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; margin-bottom:10px; transition:border-color .15s; }}
.news:hover {{ border-color:{ACCENT}; }}
.news a.t {{ color:{TEXT}; text-decoration:none; font-weight:700; font-size:1rem; line-height:1.65; }}
.news a.t:hover {{ color:#7EA6FF; }}
.news .meta {{ color:{MUTED}; font-size:.78rem; margin-top:4px; }}
.news .sum {{ color:{MUTED}; font-size:.88rem; margin-top:6px; line-height:1.75; }}
.aff {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
.aff .lbl {{ color:{MUTED}; font-size:.74rem; margin-inline-end:4px; }}
.tkc {{ direction:ltr; display:inline-flex; gap:6px; align-items:center; border-radius:20px; padding:3px 10px 3px 3px; font-size:.78rem; font-weight:800;
  border:1px solid {BORDER}; background:{CARD2}; color:{TEXT}; font-variant-numeric: tabular-nums; text-decoration:none !important; }}
.tkc.pos {{ border-color:{POS_BD}; }} .tkc.neg {{ border-color:{NEG_BD}; }}
.story {{ position:relative; background: linear-gradient(135deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; height:100%; }}
.story .rank {{ position:absolute; top:10px; inset-inline-end:14px; font-size:1.9rem; font-weight:800; color:rgba(61,123,255,.25); }}
.story a.t {{ color:#fff; text-decoration:none; font-weight:750; font-size:1.02rem; line-height:1.6; display:block; margin-inline-end:36px; }}
.story a.t:hover {{ color:#7EA6FF; }}
.status {{ display:inline-flex; align-items:center; gap:7px; font-size:.8rem; padding:6px 12px; border-radius:20px; background:{CARD}; border:1px solid {BORDER}; }}
.dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
.dot.live {{ background:{UP}; animation: pulse 1.8s infinite; }} .dot.pre {{ background:{GOLD}; }} .dot.closed {{ background:{DOWN}; }}
@keyframes pulse {{ 0% {{ box-shadow:0 0 0 0 rgba(34,197,94,.6); }} 70% {{ box-shadow:0 0 0 8px rgba(34,197,94,0); }} 100% {{ box-shadow:0 0 0 0 rgba(34,197,94,0); }} }}
.wl {{ font-size:.82rem; text-align:right; padding-top:4px; line-height:1.25; direction:ltr; }}
.check {{ padding:9px 0; border-bottom:1px solid {BORDER}; font-size:.9rem; display:flex; gap:10px; align-items:flex-start; }}
.ico {{ flex:none; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; }}
.ico .ms {{ font-size:1.05rem; vertical-align:0; }}
.summary li {{ margin-bottom:6px; line-height:1.8; }}
.kpi {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 14px; height:100%; }}
.kpi.pos, .kpi.neg {{ border-color:transparent; }}
.kpi .l {{ color:{MUTED}; font-size:.75rem; font-weight:650; display:flex; gap:6px; align-items:center; }}
.kpi.pos .l {{ color:#3E6F55; }} .kpi.neg .l {{ color:#8E4A52; }}
.kpi .v {{ font-size:1.25rem; font-weight:800; margin-top:6px; display:flex; align-items:center; gap:8px; direction:ltr; }}
.kpi .s {{ font-size:.8rem; margin-top:4px; font-weight:650; }}
.kpi:not(.pos):not(.neg) .v {{ color:#fff; }}
/* rating meter (technicals) */
.rmeter {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:16px; padding:16px; }}
.rmeter .rt {{ color:{MUTED}; font-size:.78rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
.rmeter .rv {{ display:inline-block; margin:8px 0 14px; padding:5px 12px; border-radius:10px; font-weight:800; font-size:1.15rem; }}
.rbar {{ position:relative; display:grid; grid-template-columns:repeat(5,1fr); gap:4px; height:10px; direction:ltr; }}
.rbar span {{ border-radius:6px; }}
.rbar i {{ position:absolute; top:-9px; width:0; height:0; border-left:8px solid transparent; border-right:8px solid transparent; border-top:10px solid #fff;
  filter: drop-shadow(0 2px 3px rgba(0,0,0,.5)); }}
.rlab {{ display:grid; grid-template-columns:repeat(5,1fr); font-size:.66rem; color:{MUTED}; margin-top:6px; text-align:center; direction:ltr; }}
.rcnt {{ display:flex; gap:6px; margin-top:12px; flex-wrap:wrap; }}
/* price ladder */
.ladder {{ display:flex; flex-direction:column; gap:5px; direction:ltr; }}
.lr {{ display:grid; grid-template-columns: 70px 1fr auto; gap:10px; align-items:center; padding:7px 10px; border-radius:10px; background:{CARD};
  border:1px solid {BORDER}; font-variant-numeric: tabular-nums; }}
.lr .ln {{ font-weight:800; font-size:.8rem; }} .lr .lp {{ font-weight:700; }}
.lr.res .ln {{ color:#F87171; }} .lr.sup .ln {{ color:#4ADE80; }} .lr.piv .ln {{ color:#93C5FD; }}
.lr.now {{ background:linear-gradient(90deg, rgba(61,123,255,.3), rgba(139,92,246,.25)); border-color:{ACCENT}; }}
.lr.now .ln, .lr.now .lp {{ color:#fff; }}
/* sector cards / breadth */
.secgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(172px,1fr)); gap:10px; }}
.sc {{ border-radius:14px; padding:11px 12px; border:1px solid transparent; }}
.sc .h {{ display:flex; justify-content:space-between; font-weight:700; font-size:.8rem; }} .sc .v {{ font-size:1.25rem; font-weight:800; margin-top:4px; direction:ltr; }}
.sc .f {{ display:flex; gap:8px; font-size:.7rem; font-weight:700; margin-top:4px; direction:ltr; opacity:.85; }}
.bars .b {{ margin:10px 0; }} .bars .b .t {{ display:flex; justify-content:space-between; font-size:.82rem; font-weight:650; }}
.bars .b .trk {{ height:10px; border-radius:6px; background:{BORDER}; overflow:hidden; margin-top:5px; }}
.bars .b .trk span {{ display:block; height:100%; border-radius:6px; }}
.adbar {{ display:flex; height:14px; border-radius:8px; overflow:hidden; gap:3px; direction:ltr; }}
.adbar span {{ display:block; height:100%; }}
/* options chain */
.chain {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.8rem; direction:ltr; font-variant-numeric: tabular-nums; }}
.chain th {{ position:sticky; top:0; background:{CARD2}; color:{MUTED}; font-weight:650; padding:7px 6px; text-align:right; border-bottom:1px solid {BORDER}; }}
.chain th.side {{ text-align:center; font-size:.84rem; }}
.chain td {{ padding:6px 6px; text-align:right; border-bottom:1px solid rgba(34,43,59,.6); }}
.chain td.k {{ text-align:center; font-weight:800; color:#fff; background:{CARD2}; }}
.chain tr:hover td {{ background:rgba(61,123,255,.08); }}
.chain td.itm-c {{ background:rgba(209,231,221,.10); }} .chain td.itm-p {{ background:rgba(248,215,218,.10); }}
.chain tr.atm td {{ border-top:2px solid {ACCENT}; }}
.chain .cp {{ padding:1px 6px; border-radius:6px; font-weight:700; }}
.chainwrap {{ max-height:560px; overflow:auto; border:1px solid {BORDER}; border-radius:14px; }}
/* academy */
.courses {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:14px; }}
.course {{ display:block; text-decoration:none !important; color:{TEXT} !important; background:{CARD}; border:1px solid {BORDER}; border-radius:18px; overflow:hidden;
  transition: transform .18s, border-color .18s, box-shadow .18s; border-top:4px solid var(--lv, {ACCENT}); height:100%; }}
.course:hover {{ transform: translateY(-4px); box-shadow: 0 12px 30px rgba(61,123,255,.18); }}
.course .art {{ height:150px; position:relative; overflow:hidden; }} .course .art svg {{ width:100%; height:100%; display:block; }}
.course .body {{ padding:14px 16px 16px; }}
.course .ttl {{ font-weight:800; font-size:1.05rem; line-height:1.4; }}
.course .tag {{ color:{MUTED}; font-size:.85rem; margin-top:6px; line-height:1.6; }}
.course .meta {{ display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }}
.course .play {{ position:absolute; inset-inline-end:14px; bottom:12px; width:40px; height:40px; border-radius:50%; background:rgba(255,255,255,.95);
  display:flex; align-items:center; justify-content:center; color:{BG}; }}
.course .prog {{ height:6px; background:{BORDER}; border-radius:3px; overflow:hidden; margin-top:10px; }}
.course .prog span {{ display:block; height:100%; background:var(--lv, {ACCENT}); }}
.b-beg {{ background:{POS_BG}; color:{POS_FG}; }} .b-ess {{ background:{YEL_BG}; color:{YEL_FG}; }}
.b-int {{ background:{ORG_BG}; color:{ORG_FG}; }} .b-adv {{ background:{NEG_BG}; color:{NEG_FG}; }}
[class*="st-key-crs_"], [class*="st-key-nxt_"] {{ position:relative; }}
[class*="st-key-crs_"] [data-testid="stElementContainer"], [class*="st-key-nxt_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-crs_"] .stButton, [class*="st-key-nxt_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-crs_"] .stButton button, [class*="st-key-nxt_"] .stButton button {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-crs_"]:hover .course, [class*="st-key-nxt_"]:hover .course {{ transform: translateY(-4px); box-shadow: 0 12px 30px rgba(61,123,255,.18); }}
.dash {{ display:grid; grid-template-columns: 240px 1fr 1fr; gap:14px; }}
.dcard {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:18px; padding:16px 18px; }}
.dcard .dt {{ color:{MUTED}; font-size:.78rem; font-weight:750; letter-spacing:.06em; text-transform:uppercase; margin-bottom:10px; }}
.lvl {{ margin:10px 0; }} .lvl .t {{ display:flex; justify-content:space-between; font-size:.85rem; font-weight:700; }}
.lvl .trk {{ height:10px; border-radius:6px; background:{BORDER}; overflow:hidden; margin-top:6px; }} .lvl .trk span {{ display:block; height:100%; border-radius:6px; }}
.lesson {{ background: linear-gradient(180deg, {CARD2}, {CARD}); border:1px solid {BORDER}; border-radius:18px; padding:22px 24px; }}
.lesson h3 {{ margin-top:0 !important; }} .lesson p, .lesson li {{ line-height:1.9; font-size:1rem; color:#D5DBE6; }}
.take {{ border-inline-start:3px solid {CYAN}; background:rgba(34,211,238,.07); padding:10px 14px; border-radius:10px; margin-top:12px; }}
.steps {{ display:flex; gap:6px; margin:6px 0 14px; }}
.steps span {{ flex:1; height:6px; border-radius:3px; background:{BORDER}; }} .steps span.on {{ background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.gl {{ border-bottom:1px solid {BORDER}; padding:12px 2px; }} .gl b {{ font-size:1rem; }} .gl .d {{ color:#C9D0DC; line-height:1.8; margin-top:4px; }}
.log {{ display:flex; gap:10px; align-items:center; padding:8px 0; border-bottom:1px solid {BORDER}; font-size:.86rem; }}
.foot {{ color:{MUTED}; font-size:.75rem; text-align:center; margin-top:40px; padding-top:14px; border-top:1px solid {BORDER}; }}
/* heatmap (TradingView style) */
.hmwrap {{ background:#0B0F19; border:1px solid {BORDER}; border-radius:16px; padding:8px; overflow:hidden; }}
.hm {{ width:100%; height:auto; display:block; direction:ltr; }}
.hm text {{ font-family:{FONT_LATIN}, {FONT_AR}, sans-serif; pointer-events:none; }}
.hm .tk {{ fill:#fff; font-weight:800; text-anchor:middle; }}
.hm .pc {{ fill:#fff; font-weight:600; text-anchor:middle; opacity:.93; }}
.hm .gh {{ fill:#C9CED8; font-size:12.5px; font-weight:700; }}
.hm .gc {{ font-size:12px; font-weight:800; }}
.hm a:hover .tl {{ stroke:#fff; stroke-width:2; filter:brightness(1.15); }}
.hmlegend {{ display:flex; justify-content:center; gap:3px; margin:8px 0 2px; direction:ltr; flex-wrap:wrap; }}
.hmlegend span {{ min-width:56px; padding:4px 6px; text-align:center; font-size:.74rem; font-weight:800; color:#fff; border-radius:4px; }}
/* trading dashboard (journal style) */
.tdk {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(168px,1fr)); gap:10px; margin-bottom:12px; }}
.tdc {{ background: linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; border-radius:14px; padding:12px 14px; display:flex; flex-direction:column; min-height:172px; }}
.tdc .h {{ color:{MUTED}; font-size:.66rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; }}
.tdc .big {{ font-size:1.45rem; font-weight:800; margin-top:12px; direction:ltr; }}
.tdc svg {{ display:block; margin:6px auto 0; }}
.pbox {{ display:inline-block; padding:3px 10px; border-radius:10px; font-weight:800; direction:ltr; font-variant-numeric:tabular-nums; }}
.pbox.neu {{ background:rgba(138,148,167,.16); color:#C9D0DC; }}
.chip2 {{ display:inline-block; margin-top:8px; padding:2px 9px; border-radius:12px; background:rgba(138,148,167,.16); color:#C9D0DC; font-size:.7rem; font-weight:700; }}
.tdc .foot2 {{ margin-top:auto; padding-top:10px; border-top:1px solid {BORDER}; display:flex; gap:18px; font-size:.66rem; color:{MUTED}; font-weight:800; letter-spacing:.05em; }}
.tdc .foot2 b {{ display:block; font-size:.86rem; letter-spacing:0; margin-top:2px; direction:ltr; }}
.tdc .wl2 {{ display:flex; justify-content:center; gap:8px; font-size:.8rem; font-weight:800; margin-top:2px; direction:ltr; }}
.tdc .goal {{ margin-top:auto; padding-top:8px; }}
.tdc .goal .gt {{ display:flex; justify-content:space-between; font-size:.64rem; color:{MUTED}; font-weight:700; }}
.tdc .goal .gb {{ height:4px; border-radius:3px; background:{BORDER}; margin-top:4px; overflow:hidden; }}
.tdc .goal .gb span {{ display:block; height:100%; background:{CYAN}; border-radius:3px; }}
.tdc .goal.met .gb span {{ background:{UP}; }}
.tdc .split {{ display:flex; height:8px; border-radius:5px; overflow:hidden; gap:3px; margin:12px 0 8px; direction:ltr; }}
.tdc .vals {{ display:flex; justify-content:space-between; gap:6px; font-size:.8rem; font-weight:800; direction:ltr; }}
.tdp {{ background: linear-gradient(180deg,{CARD2},{CARD}); border:1px solid {BORDER}; border-radius:16px; padding:14px 16px; margin-bottom:12px; }}
.tdp .tt {{ font-weight:800; font-size:1rem; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.tdp .tt .muted {{ font-size:.78rem; font-weight:600; }}
.rtab {{ width:100%; border-collapse:collapse; font-size:.84rem; direction:ltr; }}
.rtab th {{ color:{MUTED}; font-size:.66rem; letter-spacing:.08em; text-transform:uppercase; text-align:left; padding:6px 4px; border-bottom:1px solid {BORDER}; }}
.rtab td {{ padding:7px 4px; border-bottom:1px solid rgba(34,43,59,.6); font-weight:700; }}
.rtab td:last-child, .rtab th:last-child {{ text-align:right; }}
.rtab tr:hover td {{ background:rgba(61,123,255,.06); }}
.rtab a {{ color:#fff !important; text-decoration:none !important; }} .rtab a:hover {{ color:#7EA6FF !important; }}
.cal {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)) 124px; gap:6px; direction:ltr; }}
.cal .dh {{ text-align:center; color:{MUTED}; font-size:.72rem; font-weight:800; padding:4px 0; }}
.cal .d {{ position:relative; min-height:80px; border-radius:10px; padding:18px 6px 6px; text-align:center; background:{CARD}; border:1px solid {BORDER}; }}
.cal .d .n {{ position:absolute; top:5px; right:8px; font-size:.66rem; font-weight:700; opacity:.65; }}
.cal .d .p {{ font-weight:800; font-size:1rem; }}
.cal .d .s {{ font-size:.66rem; font-weight:650; opacity:.85; margin-top:2px; }}
.cal .d.pos {{ border-color:{POS_BD}; }} .cal .d.neg {{ border-color:{NEG_BD}; }}
.cal .d.off {{ opacity:.25; }}
.cal .wk {{ border-radius:10px; padding:8px 10px; background:{CARD2}; border:1px solid {BORDER}; min-height:80px; }}
.cal .wk .l {{ font-size:.62rem; color:{MUTED}; font-weight:800; letter-spacing:.08em; }}
.cal .wk .p {{ margin-top:6px; }} .cal .wk .s {{ margin-top:6px; font-size:.66rem; color:{MUTED}; font-weight:700; }}
.opos {{ display:flex; flex-direction:column; gap:8px; }}
.opos .o {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; align-items:center; padding:8px 10px; border-radius:12px; background:{CARD}; border:1px solid {BORDER}; direction:ltr; }}
.opos .o .m {{ color:{MUTED}; font-size:.72rem; margin-top:2px; }}
/* financial explorer / misc */
.mx {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:8px; margin:6px 0 10px; }}
.mx .m {{ background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:9px 11px; }}
.mx .m .l {{ color:{MUTED}; font-size:.72rem; font-weight:650; }} .mx .m .v {{ font-weight:800; margin-top:3px; direction:ltr; }}
.mx .m.pos .l, .mx .m.neg .l {{ opacity:.8; color:inherit; }}
.perfrow {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(96px,1fr)); gap:8px; }}
.perfrow .pc2 {{ border-radius:12px; padding:9px 10px; text-align:center; border:1px solid {BORDER}; background:{CARD}; }}
.perfrow .pc2 .l {{ font-size:.72rem; font-weight:800; opacity:.75; }} .perfrow .pc2 .v {{ font-size:1.05rem; font-weight:800; direction:ltr; margin-top:2px; }}
.perfrow .pc2.pos {{ border-color:{POS_BD}; }} .perfrow .pc2.neg {{ border-color:{NEG_BD}; }}
.sigs {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:8px; }}
.sigs .sg {{ display:flex; justify-content:space-between; align-items:center; gap:8px; padding:8px 10px; border-radius:12px; background:{CARD}; border:1px solid {BORDER}; }}
.sigs .sg .n {{ font-weight:700; font-size:.84rem; }} .sigs .sg .v {{ color:{MUTED}; font-size:.74rem; direction:ltr; }}
@media (max-width: 900px) {{ .dash {{ grid-template-columns: 1fr; }} .cal {{ grid-template-columns:repeat(5,minmax(0,1fr)); }} .cal .wk, .cal .wkh {{ display:none; }} }}
</style>
"""

RTL_CSS = f"""
<style>
.block-container, [data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"] {{ direction: rtl; }}
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], h1, h2, h3, h4, label, .stMarkdown {{ text-align: right; }}
.stPlotlyChart, .js-plotly-plot, [data-testid="stDataFrame"], .tape, .t-row, [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{ direction: ltr; }}
.stPlotlyChart *, .js-plotly-plot *, [data-testid="stPlotlyChart"] *, .hm, .hm * {{ direction: ltr !important; }}
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
    """'pos' / 'neg' / 'neu' for a signed value (the pastel rule)."""
    try:
        if v is None or pd.isna(v) or v == 0:
            return "neu"
    except (TypeError, ValueError):
        return "neu"
    good = v > 0
    if invert:
        good = not good
    return "pos" if good else "neg"


def txt(v, invert=False):
    """Text color class for signed values shown directly on dark surfaces."""
    c = cls(v, invert)
    return {"pos": "upt", "neg": "dnt"}.get(c, "muted")


def color_style(v):
    """Pandas Styler: light-green cell + dark-green text / light-red cell + dark-red text."""
    try:
        if v > 0:
            return f"background-color: {POS_BG}; color: {POS_FG}; font-weight: 700"
        if v < 0:
            return f"background-color: {NEG_BG}; color: {NEG_FG}; font-weight: 700"
    except TypeError:
        pass
    return ""


def signal_style(v, buy, sell):
    if v == buy:
        return f"background-color: {POS_BG}; color: {POS_FG}; font-weight: 700"
    if v == sell:
        return f"background-color: {NEG_BG}; color: {NEG_FG}; font-weight: 700"
    return ""


def esc(s):
    return html.escape(str(s))


def icon(name, color=None):
    style = f' style="color:{color}"' if color else ""
    return f'<span class="ms"{style}>{name}</span>'


def ico(name, kind="pos"):
    """Icon inside a pastel circle (readable on dark cards)."""
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG), "acc": (ACC_BG, ACC_FG), "gold": (YEL_BG, YEL_FG),
              "neu": ("rgba(138,148,167,.2)", "#B8C0CE")}[kind]
    return f'<span class="ico" style="background:{bg};color:{fg}">{icon(name)}</span>'


# ---------------------------------------------------------------- building blocks
def page_title(ic, title, sub=""):
    return f'<div class="page-title">{icon(ic)}<h1>{esc(title)}</h1></div>' + (f'<div class="page-sub">{sub}</div>' if sub else "")


def sec(ic, text):
    return f'<div class="sec">{icon(ic)}<span>{esc(text)}</span></div>'


def stock_href(sym, lang="en"):
    return f"stock?symbol={sym}&lang={lang}"


def logo_circle(sym, uri=None, size=32):
    s = f"width:{size}px;height:{size}px;font-size:{max(9, int(size * 0.36))}px"
    if uri:
        return f'<span class="lg" style="{s}"><img src="{uri}" alt=""/></span>'
    h = int(hashlib.md5(str(sym).encode()).hexdigest()[:6], 16)
    hue = h % 360
    return (f'<span class="lg" style="{s};background:linear-gradient(135deg,hsl({hue},62%,46%),hsl({(hue + 40) % 360},62%,34%))">'
            f'{esc(str(sym).replace("^", "")[:2])}</span>')


def company(sym, name="", uri=None, size=32, sub=None, href=None):
    sub_html = f'<div class="sub">{esc(sub if sub is not None else name)}</div>' if (sub or name) else ""
    inner = f'<div class="co">{logo_circle(sym, uri, size)}<div class="nm"><div class="tk">{esc(sym)}</div>{sub_html}</div></div>'
    return f'<a class="lnk" href="{href}" target="_self">{inner}</a>' if href else inner


def pill(pct, invert=False, suffix="%"):
    if pct is None or pd.isna(pct):
        return '<span class="pill neu">—</span>'
    return f'<span class="pill {cls(pct, invert)}">{pct:+.2f}{suffix}</span>'


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
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polygon fill="{color}" opacity=".14" points="{area}"/>'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.8" points="{pts}"/></svg>')


def tile(name, value, chg=None, pct=None, spark=None, sub="", invert=False, head_html=None, kind=None):
    """Market tile. Positive -> light-green tile + dark-green text; negative -> light-red + dark-red."""
    c = kind or cls(pct if pct is not None else chg, invert)
    color = {"pos": POS_FG, "neg": NEG_FG, "acc": ACC_FG}.get(c, MUTED)
    if pct is not None and chg is not None:
        t = f"{chg:+,.2f} ({pct:+.2f}%)"
    elif pct is not None:
        t = f"{pct:+.2f}%"
    elif chg is not None:
        t = f"{chg:+,.2f}"
    else:
        t = ""
    svg = sparkline(spark, color) if spark is not None else ""
    head = head_html or f'<div class="t-name">{esc(name)}</div>'
    k = f" {c}" if c in ("pos", "neg", "acc") else ""
    return (f'<div class="tile{k}">{head}<div class="t-row"><div><div class="t-val">{value}</div><div class="t-chg">{t}</div></div>{svg}</div>'
            + (f'<div class="t-sub">{esc(sub)}</div>' if sub else "") + "</div>")


def tiles(items):
    return '<div class="tiles">' + "".join(items) + "</div>"


def badge(text, kind="neu", ic=None):
    return f'<span class="badge b-{kind}">{icon(ic) if ic else ""}{esc(text)}</span>'


def ticker_chip(sym, pct, uri=None, href=None):
    c = cls(pct) if pct is not None and not pd.isna(pct) else "neu"
    val = pill(pct) if pct is not None and not pd.isna(pct) else ""
    inner = f'{logo_circle(sym, uri, 20)}{esc(sym)} {val}'
    if href:
        return f'<a class="tkc {c}" href="{href}" target="_self">{inner}</a>'
    return f'<span class="tkc {c}">{inner}</span>'


def kpi(ic, label, value_html, sub="", kind=None):
    k = f" {kind}" if kind in ("pos", "neg") else ""
    return (f'<div class="kpi{k}"><div class="l">{icon(ic)}{esc(label)}</div><div class="v">{value_html}</div>'
            f'<div class="s">{sub}</div></div>')


def tape(items):
    inner = "".join(f'<span class="it"><b>{esc(n)}</b>{fmt_price(p)} {pill(c)}</span>' for n, p, c in items)
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
    return (f'<div class="news{rtl}">{tag_html}<a class="t" href="{esc(n["link"])}" target="_blank">{esc(title)}</a>'
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


# ---------------------------------------------------------------- modern widgets
RATING_COLORS = ["#EF4444", "#F87171", "#64748B", "#4ADE80", "#22C55E"]


def rating_meter(score, label, title, counts=None, labels=("Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy")):
    """Segmented rating bar with a pointer (score in -1..1). counts: [(text, kind), ...]."""
    pos = max(0.0, min(100.0, (score + 1) / 2 * 100))
    kind = "pos" if score > 0.1 else ("neg" if score < -0.1 else "neu")
    bg = {"pos": f"background:{POS_BG};color:{POS_FG}", "neg": f"background:{NEG_BG};color:{NEG_FG}",
          "neu": f"background:{NEU_BG};color:{NEU_FG}"}[kind]
    segs = "".join(f'<span style="background:{c}"></span>' for c in RATING_COLORS)
    cnt = "".join(f'<span class="pill {k}" style="min-width:0">{esc(t)}</span>' for t, k in (counts or []))
    return (f'<div class="rmeter"><div class="rt">{esc(title)}</div><div class="rv" style="{bg}">{esc(label)}</div>'
            f'<div class="rbar">{segs}<i style="left:calc({pos:.1f}% - 8px)"></i></div>'
            f'<div class="rlab">{"".join(f"<span>{esc(x)}</span>" for x in labels)}</div><div class="rcnt">{cnt}</div></div>')


def ladder(levels, price, now_label="Price"):
    """levels: [(name, value, 'res'|'sup'|'piv')] -> vertical price ladder with the current price highlighted."""
    rows = sorted(levels, key=lambda x: -x[1])
    out, placed = [], False
    for name, v, kind in rows:
        if not placed and v < price:
            out.append(f'<div class="lr now"><span class="ln">{esc(now_label)}</span><span class="lp">{fmt_price(price)}</span><span></span></div>')
            placed = True
        d = (v / price - 1) * 100
        out.append(f'<div class="lr {kind}"><span class="ln">{esc(name)}</span><span class="lp">{fmt_price(v)}</span>{pill(d)}</div>')
    if not placed:
        out.append(f'<div class="lr now"><span class="ln">{esc(now_label)}</span><span class="lp">{fmt_price(price)}</span><span></span></div>')
    return '<div class="ladder">' + "".join(out) + "</div>"


def ring(pct, size=150, color=ACCENT, label="", sub="", track=BORDER, stroke=14):
    r = (size - stroke) / 2
    c = 2 * np.pi * r
    off = c * (1 - max(0, min(100, pct)) / 100)
    gid = f"rg{abs(hash((pct, color, size))) % 10**6}"
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block;margin:auto">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient></defs>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" stroke="{track}" stroke-width="{stroke}" fill="none"/>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" stroke="url(#{gid})" stroke-width="{stroke}" fill="none" stroke-linecap="round" '
            f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" transform="rotate(-90 {size / 2} {size / 2})"/>'
            f'<text x="50%" y="48%" text-anchor="middle" font-size="{size * 0.2:.0f}" font-weight="800" fill="#fff" font-family="{FONT}">{esc(label)}</text>'
            f'<text x="50%" y="64%" text-anchor="middle" font-size="{size * 0.085:.0f}" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text></svg>')


def pulse_gauge(pct, title, sub=""):
    """Semicircle gauge 0-100 with gradient arc and needle (market breadth)."""
    pct = max(0.0, min(100.0, pct))
    ang = np.pi * (1 - pct / 100)
    cx, cy, r = 150, 150, 110
    nx, ny = cx + (r - 20) * np.cos(ang), cy - (r - 20) * np.sin(ang)
    kind = "pos" if pct > 55 else ("neg" if pct < 45 else "neu")
    col = {"pos": POS_FG, "neg": NEG_FG, "neu": NEU_FG}[kind]
    bgc = {"pos": POS_BG, "neg": NEG_BG, "neu": NEU_BG}[kind]
    return (f'<svg viewBox="0 0 300 236" style="width:100%;max-width:340px;display:block;margin:auto">'
            '<defs><linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="#EF4444"/><stop offset=".5" stop-color="#F5B94A"/>'
            '<stop offset="1" stop-color="#22C55E"/></linearGradient></defs>'
            f'<path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="{BORDER}" stroke-width="22" stroke-linecap="round"/>'
            '<path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="url(#pg)" stroke-width="22" stroke-linecap="round" opacity=".95"/>'
            f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="9" fill="#fff"/>'
            f'<rect x="100" y="166" width="100" height="30" rx="9" fill="{bgc}"/>'
            f'<text x="150" y="187" text-anchor="middle" font-size="18" font-weight="800" fill="{col}" font-family="{FONT}">{pct:.0f}%</text>'
            f'<text x="150" y="214" text-anchor="middle" font-size="12.5" font-weight="700" fill="#C9D0DC" font-family="{FONT}">{esc(title)}</text>'
            f'<text x="150" y="231" text-anchor="middle" font-size="11.5" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text></svg>')


def progress_bars(items):
    """items: [(label, value_text, pct 0-100, color)]"""
    return '<div class="bars">' + "".join(
        f'<div class="b"><div class="t"><span>{esc(l)}</span><span class="num">{esc(v)}</span></div>'
        f'<div class="trk"><span style="width:{max(0, min(100, p)):.1f}%;background:{c}"></span></div></div>' for l, v, p, c in items) + "</div>"


def ad_bar(adv, dec, unch=0):
    tot = max(adv + dec + unch, 1)
    return (f'<div class="adbar"><span style="width:{adv / tot * 100:.1f}%;background:{UP}"></span>'
            f'<span style="width:{unch / tot * 100:.1f}%;background:#64748B"></span>'
            f'<span style="width:{dec / tot * 100:.1f}%;background:{DOWN}"></span></div>')


def sector_card(name, etf, d1, w1, m1, spark=None, href=None):
    c = cls(d1)
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG)}.get(c, (CARD2, TEXT))
    sp = sparkline(spark, fg, 70, 24) if spark is not None else ""
    f = lambda v: f"{v:+.1f}%" if v is not None and pd.notna(v) else "—"
    return (f'<div class="sc" style="background:{bg};color:{fg}"><div class="h"><span>{esc(name)}</span><span style="opacity:.7">{esc(etf)}</span></div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-end"><div class="v">{f(d1)}</div>{sp}</div>'
            f'<div class="f"><span>1W {f(w1)}</span><span>1M {f(m1)}</span></div></div>')


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


# ---------------------------------------------------------------- trading-dashboard widgets
def money(v, dec=0, short=False):
    """$1,234 / -$1,234 / $1.2K (sign before the dollar)."""
    if v is None or pd.isna(v):
        return "—"
    sign = "-" if v < 0 else ""
    a = abs(float(v))
    if short and a >= 1000:
        for unit, div in (("M", 1e6), ("K", 1e3)):
            if a >= div:
                return f"{sign}${a / div:.1f}{unit}"
    return f"{sign}${a:,.{dec}f}"


def pbox(text, v=None, kind=None):
    """Value inside a pastel box: light green + dark green (positive) / light red + dark red (negative)."""
    k = kind or cls(v)
    return f'<span class="pbox {k}">{text}</span>'


def semi(pct, value_text=None, size=150):
    """Half-circle gauge 0-100 (green arc when >= 50, red below) with a pastel value box."""
    pct = max(0.0, min(100.0, float(pct)))
    kind = "pos" if pct >= 50 else "neg"
    col = UP if kind == "pos" else DOWN
    r, cx, cy = 52, 75, 68
    ang = np.pi * (1 - pct / 100)
    ex, ey = cx + r * np.cos(ang), cy - r * np.sin(ang)
    bg, fg = (POS_BG, POS_FG) if kind == "pos" else (NEG_BG, NEG_FG)
    txt = value_text or f"{pct:.1f}%"
    arc = (f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round"/>'
           if pct > 0.5 else "")
    return (f'<svg width="{size}" height="{size * 0.62:.0f}" viewBox="0 0 150 93">'
            f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{BORDER}" stroke-width="12" stroke-linecap="round"/>{arc}'
            f'<rect x="{cx - 36}" y="{cy - 20}" width="72" height="26" rx="8" fill="{bg}"/>'
            f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="15" font-weight="800" fill="{fg}" font-family="{FONT}">{esc(txt)}</text></svg>')


def goal(pct_of_goal, left, right, met=False):
    w = max(0.0, min(100.0, pct_of_goal))
    return (f'<div class="goal{" met" if met else ""}"><div class="gt"><span>{esc(left)}</span><span>{esc(right)}</span></div>'
            f'<div class="gb"><span style="width:{w:.0f}%"></span></div></div>')
