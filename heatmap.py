"""
heatmap.py - TradingView-style stock heatmap drawn as SVG.
Tiles are grouped (sector / industry / sub-theme), sized by market cap, colored by % change,
show the company logo, ticker and change, and open the stock page on click.
"""
import html

import numpy as np

W, H = 1400, 800
HEAD = 20          # group header strip height
GAP = 3            # space between groups

# diverging scale (TradingView look): red -> dark red -> grey -> dark green -> green
STOPS = [(-1.0, (242, 54, 69)), (-0.6, (178, 40, 52)), (-0.25, (118, 32, 43)), (0.0, (64, 68, 79)),
         (0.25, (24, 88, 58)), (0.6, (22, 133, 72)), (1.0, (34, 171, 94))]
RANGE = {"1D": 3, "1W": 6, "1M": 10, "3M": 18, "YTD": 25, "1Y": 40, "PRE": 3, "POST": 3}


def color(v, rng=3.0):
    if v is None or not np.isfinite(v):
        return "#40444F"
    x = max(-1.0, min(1.0, float(v) / rng))
    for (x0, c0), (x1, c1) in zip(STOPS, STOPS[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0
            r, g, b = (round(a + (b_ - a) * t) for a, b_ in zip(c0, c1))
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#22AB5E"


# ---------------------------------------------------------------- squarified treemap (Bruls et al.)
def _row(sizes, x, y, dx, dy):
    s = sum(sizes)
    if dx >= dy:                       # column on the left
        w = s / dy if dy > 0 else 0
        out, yy = [], y
        for a in sizes:
            h = a / w if w > 0 else 0
            out.append((x, yy, w, h))
            yy += h
        return out, (x + w, y, dx - w, dy)
    h = s / dx if dx > 0 else 0        # row on top
    out, xx = [], x
    for a in sizes:
        w = a / h if h > 0 else 0
        out.append((xx, y, w, h))
        xx += w
    return out, (x, y + h, dx, dy - h)


def _worst(sizes, x, y, dx, dy):
    rects, _ = _row(sizes, x, y, dx, dy)
    return max(max(w / h, h / w) if w > 0 and h > 0 else 1e9 for _, _, w, h in rects)


def squarify(values, x, y, dx, dy):
    """values sorted descending -> list of (x, y, w, h) filling the rectangle."""
    vals = [max(float(v), 0.0) for v in values]
    tot = sum(vals)
    if tot <= 0 or dx <= 0 or dy <= 0:
        return [(x, y, 0, 0) for _ in vals]
    sizes = [v * dx * dy / tot for v in vals]
    out = []
    while sizes:
        if len(sizes) == 1:
            out.append((x, y, dx, dy))
            break
        i = 1
        while i < len(sizes) and _worst(sizes[:i], x, y, dx, dy) >= _worst(sizes[:i + 1], x, y, dx, dy):
            i += 1
        rects, (x, y, dx, dy) = _row(sizes[:i], x, y, dx, dy)
        out += rects
        sizes = sizes[i:]
    return out


# ---------------------------------------------------------------- layout
def layout(df, group_col="Group", size_col="Size", width=W, height=H):
    """df: Symbol, Group, Size, Val (+ anything). Returns (tiles, groups) with pixel rectangles."""
    d = df[df[size_col] > 0].copy()
    gs = d.groupby(group_col)[size_col].sum().sort_values(ascending=False)
    groups, tiles = [], []
    for (g, _), (gx, gy, gw, gh) in zip(gs.items(), squarify(gs.values, 0, 0, width, height)):
        gx, gy, gw, gh = gx + GAP / 2, gy + GAP / 2, gw - GAP, gh - GAP
        head = HEAD if gh > HEAD * 2.4 and gw > 46 else 0
        sub = d[d[group_col] == g].sort_values(size_col, ascending=False)
        chg = np.average(sub["Val"].fillna(0), weights=sub[size_col]) if sub[size_col].sum() > 0 else 0.0
        groups.append({"name": g, "x": gx, "y": gy, "w": gw, "h": gh, "head": head, "chg": float(chg), "n": len(sub)})
        for (_, r), (x, y, w, h) in zip(sub.iterrows(), squarify(sub[size_col].values, gx, gy + head, gw, gh - head)):
            tiles.append({**r.to_dict(), "x": x, "y": y, "w": w, "h": h})
    return tiles, groups


def big_symbols(tiles, min_side=22):
    return [t["Symbol"] for t in tiles if min(t["w"], t["h"]) >= min_side]


# ---------------------------------------------------------------- render
def _e(s):
    return html.escape(str(s), quote=True)


def _fit(text, width, fs):
    max_chars = int(width / (fs * 0.58))
    return text if len(text) <= max_chars else (text[:max(1, max_chars - 1)] + "…")


def render(tiles, groups, logos=None, rng=3.0, lang="en", label=str, tip=None, rtl=False, width=W, height=H, uid="hm"):
    """logos: symbol -> image URL (verified). label: group key -> display name. tip: tile -> tooltip text."""
    logos = logos or {}
    defs, body = [], [f'<rect width="{width}" height="{height}" fill="#0B0F19"/>']
    for g in groups:
        body.append(f'<rect x="{g["x"]:.1f}" y="{g["y"]:.1f}" width="{g["w"]:.1f}" height="{g["h"]:.1f}" fill="#141A26"/>')
    for i, t in enumerate(tiles):
        x, y, w, h = t["x"] + 0.5, t["y"] + 0.5, t["w"] - 1, t["h"] - 1
        if w < 1 or h < 1:
            continue
        sym, v = t["Symbol"], t.get("Val")
        fill = color(v, rng)
        m = min(w, h)
        n = max(len(sym), 3)
        fs = min(m * 0.19, w / (0.68 * n), 34)
        fs = fs if fs >= 7.5 else 0
        pfs = fs * 0.8
        pct = f"{v:+.2f}%" if v is not None and np.isfinite(v) else "—"
        show_pct = fs > 0 and h >= fs + pfs + 9 and w >= pfs * 0.6 * len(pct)
        text_h = (fs + (pfs + 4 if show_pct else 0)) if fs else 0
        url = logos.get(sym)
        r = min(m * 0.2, 34)
        show_logo = bool(url) and r >= 6 and h >= text_h + 2 * r + 12
        if url and not fs and m >= 16:            # tiny tile: logo only
            r, show_logo, text_h = min(m * 0.3, 11), True, 0
        total = (2 * r + (6 if text_h else 0) if show_logo else 0) + text_h
        cx, top = x + w / 2, y + h / 2 - total / 2
        parts = [f'<rect class="tl" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"/>']
        if show_logo:
            cy = top + r
            defs.append(f'<clipPath id="{uid}{i}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/></clipPath>')
            s = r * 2 * 0.8
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#fff"/>'
                         f'<image href="{_e(url)}" x="{cx - s / 2:.1f}" y="{cy - s / 2:.1f}" width="{s:.1f}" height="{s:.1f}" '
                         f'clip-path="url(#{uid}{i})" preserveAspectRatio="xMidYMid meet"/>')
            top += 2 * r + 6
        if fs:
            parts.append(f'<text x="{cx:.1f}" y="{top + fs * 0.8:.1f}" font-size="{fs:.1f}" class="tk">{_e(sym)}</text>')
            if show_pct:
                parts.append(f'<text x="{cx:.1f}" y="{top + fs + 3 + pfs * 0.8:.1f}" font-size="{pfs:.1f}" class="pc">{pct}</text>')
        title = tip(t) if tip else f"{sym} {pct}"
        href = f"stock?symbol={sym}&lang={lang}"
        body.append(f'<a href="{_e(href)}" target="_self"><title>{_e(title)}</title>{"".join(parts)}</a>')
    for g in groups:                     # headers on top
        if not g["head"]:
            continue
        name = label(g["name"])
        c = g["chg"]
        cc = "#4ADE80" if c > 0.005 else ("#F87171" if c < -0.005 else "#9AA3B2")
        chg = f"{c:+.2f}%"
        room = g["w"] - 12 - len(chg) * 7.2
        name = _fit(name, max(room, 20), 12.5)
        if rtl:
            body.append(f'<text x="{g["x"] + g["w"] - 6:.1f}" y="{g["y"] + 14.5:.1f}" class="gh" text-anchor="end">‹ {_e(name)}</text>'
                        f'<text x="{g["x"] + 6:.1f}" y="{g["y"] + 14.5:.1f}" class="gc" fill="{cc}" text-anchor="start">{chg}</text>')
        else:
            body.append(f'<text x="{g["x"] + 6:.1f}" y="{g["y"] + 14.5:.1f}" class="gh" text-anchor="start">{_e(name)} ›</text>'
                        f'<text x="{g["x"] + g["w"] - 6:.1f}" y="{g["y"] + 14.5:.1f}" class="gc" fill="{cc}" text-anchor="end">{chg}</text>')
    return (f'<div class="hmwrap"><svg class="hm" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs>{"".join(defs)}</defs>{"".join(body)}</svg></div>')


def legend(rng=3.0):
    steps = [-1, -2 / 3, -1 / 3, 0, 1 / 3, 2 / 3, 1]
    cells = "".join(f'<span style="background:{color(s * rng, rng)}">{s * rng:+.0f}%</span>'.replace("+0%", "0%") for s in steps)
    return f'<div class="hmlegend">{cells}</div>'
