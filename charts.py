"""
charts.py - All Plotly figures, one unified theme (site font, transparent cards, pastel up/down bars).
Rule used everywhere: positive = light-green fill + dark-green text, negative = light-red fill + dark-red text.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

import ta
from theme import (ACCENT, BG, BORDER, CYAN, DOWN, GOLD, MUTED, NEG_BD, NEG_BG, NEG_FG, ORANGE, POS_BD, POS_BG, POS_FG,
                   PURPLE, TEXT, UP, VIOLET)

FONT_FAMILY = "Plus Jakarta Sans, Readex Pro, system-ui, sans-serif"
GRID = "rgba(138,148,167,0.13)"
PALETTE = [ACCENT, CYAN, VIOLET, GOLD, "#F472B6", "#34D399", ORANGE, "#60A5FA", "#A3E635", "#FB7185", "#C084FC", "#2DD4BF"]


def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


pio.templates["alturaifi"] = go.layout.Template(layout=dict(
    font=dict(family=FONT_FAMILY, color=TEXT, size=12),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=PALETTE,
    hoverlabel=dict(bgcolor="#161D2B", bordercolor="#2B3548", font=dict(family=FONT_FAMILY, color=TEXT, size=12)),
    xaxis=dict(gridcolor=GRID, zeroline=False, linecolor="#222B3B", tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=GRID, zeroline=False, linecolor="#222B3B", tickfont=dict(color=MUTED)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#B8C0CE")),
    title=dict(font=dict(size=15, color="#FFFFFF", family=FONT_FAMILY), x=0.01, xanchor="left"),
))
TEMPLATE = "plotly_dark+alturaifi"
pio.templates.default = TEMPLATE

OVERLAYS = ["SMA 20", "SMA 50", "SMA 200", "EMA 9", "EMA 21", "Bollinger Bands", "VWAP",
            "Pivot Points", "Support / Resistance"]
PANELS = ["RSI", "MACD", "Stochastic", "ADX", "ATR", "OBV", "MFI", "CCI"]
CHART_TYPES = ["Candles", "Heikin Ashi", "OHLC", "Line", "Area"]


def style(fig, height=420, title=None, legend=True):
    top = (84 if legend else 48) if title else 14
    fig.update_layout(
        template=TEMPLATE, height=height, margin=dict(l=8, r=8, t=top, b=8), hovermode="x unified",
        title=dict(text=f"<b>{title}</b>", yref="container", y=0.985, yanchor="top") if title else None,
        showlegend=legend, legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom", traceorder="normal"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, rangeslider_visible=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, side="right")
    return fig


def pastel(values, neutral=False):
    """fills, outlines, inside-text colors, outside-text colors for signed values."""
    fill, line, txt, out = [], [], [], []
    for v in values:
        if v is None or (isinstance(v, float) and np.isnan(v)) or (neutral and v == 0):
            fill.append("#2A3142"); line.append("#3A4458"); txt.append(TEXT); out.append(MUTED)
        elif v >= 0:
            fill.append(POS_BG); line.append(POS_BD); txt.append(POS_FG); out.append(POS_BD)
        else:
            fill.append(NEG_BG); line.append(NEG_BD); txt.append(NEG_FG); out.append(NEG_BD)
    return fill, line, txt, out


def _bars(fig, **kw):
    try:
        fig.update_traces(marker_cornerradius=6, selector=dict(type="bar"), **kw)
    except (ValueError, TypeError):
        pass
    return fig


# =====================================================================
# Main price chart
# =====================================================================
def price_chart(d, chart_type="Candles", overlays=(), panels=(), intraday=False, levels=None,
                trades=None, height=None):
    fmt = "%m/%d %H:%M" if intraday else "%Y-%m-%d"
    x = d.index.strftime(fmt)
    has_vol = "Volume" in d and d["Volume"].fillna(0).sum() > 0
    rows = 1 + int(has_vol) + len(panels)
    main_h = 0.58 if panels else (0.8 if has_vol else 1.0)
    rest = 1 - main_h
    heights = [main_h] + ([0.12] if has_vol else [])
    if panels:
        each = (rest - (0.12 if has_vol else 0)) / len(panels)
        heights += [each] * len(panels)
    elif has_vol:
        heights = [main_h, rest]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.015, row_heights=heights)

    src = ta.heikin_ashi(d) if chart_type == "Heikin Ashi" else d
    if chart_type in ("Candles", "Heikin Ashi"):
        fig.add_trace(go.Candlestick(x=x, open=src["Open"], high=src["High"], low=src["Low"], close=src["Close"],
                                     increasing_line_color=UP, decreasing_line_color=DOWN,
                                     increasing_fillcolor=UP, decreasing_fillcolor=DOWN,
                                     name="Price", showlegend=False), row=1, col=1)
    elif chart_type == "OHLC":
        fig.add_trace(go.Ohlc(x=x, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"],
                              increasing_line_color=UP, decreasing_line_color=DOWN, name="Price",
                              showlegend=False), row=1, col=1)
    else:
        up = d["Close"].iloc[-1] >= d["Close"].iloc[0]
        col = UP if up else DOWN
        fig.add_trace(go.Scatter(x=x, y=d["Close"], name="Price", line=dict(color=col, width=2),
                                 fill="tozeroy" if chart_type == "Area" else None,
                                 fillcolor=rgba(col, 0.13) if chart_type == "Area" else None,
                                 showlegend=False), row=1, col=1)
        if chart_type == "Area":
            lo, hi = d["Close"].min(), d["Close"].max()
            fig.update_yaxes(range=[lo - (hi - lo) * 0.05, hi + (hi - lo) * 0.05], row=1, col=1)

    ma = {"SMA 20": ("SMA20", GOLD), "SMA 50": ("SMA50", ACCENT), "SMA 200": ("SMA200", PURPLE),
          "EMA 9": ("EMA9", "#4DD0E1"), "EMA 21": ("EMA21", "#FF8A65")}
    for o in overlays:
        if o in ma and ma[o][0] in d and d[ma[o][0]].notna().any():
            col_name, color = ma[o]
            fig.add_trace(go.Scatter(x=x, y=d[col_name], name=o, line=dict(color=color, width=1.4)), 1, 1)
        elif o == "Bollinger Bands" and "BB_up" in d:
            fig.add_trace(go.Scatter(x=x, y=d["BB_up"], name="BB Upper", line=dict(color=MUTED, width=1, dash="dot")), 1, 1)
            fig.add_trace(go.Scatter(x=x, y=d["BB_low"], name="BB Lower", line=dict(color=MUTED, width=1, dash="dot"),
                                     fill="tonexty", fillcolor="rgba(138,147,163,0.07)"), 1, 1)
        elif o == "VWAP" and intraday and "Volume" in d:
            fig.add_trace(go.Scatter(x=x, y=ta.vwap(d), name="VWAP", line=dict(color="#E040FB", width=1.4)), 1, 1)
        elif o == "Pivot Points" and len(d) > 2:
            for k, v in ta.pivot_points(d).items():
                c = UP if k.startswith("S") else (DOWN if k.startswith("R") else MUTED)
                fig.add_hline(y=v, line=dict(color=c, width=0.8, dash="dot"), row=1, col=1,
                              annotation_text=k, annotation_position="right", annotation_font_color=c)
        elif o == "Support / Resistance" and len(d) > 20:
            price = d["Close"].iloc[-1]
            for lv in ta.swing_levels(d):
                c = UP if lv < price else DOWN
                fig.add_hline(y=lv, line=dict(color=c, width=0.8, dash="dash"), row=1, col=1)

    for label, price, color, dash in levels or []:
        fig.add_hline(y=price, line=dict(color=color, width=1.4, dash=dash), row=1, col=1,
                      annotation_text=f"{label} {price:,.2f}", annotation_position="left",
                      annotation_font_color=color)

    # last price tag (TradingView style)
    last, first = float(d["Close"].iloc[-1]), float(d["Close"].iloc[0])
    up_ = last >= float(d["Close"].iloc[-2]) if len(d) > 1 else last >= first
    fig.add_hline(y=last, line=dict(color=UP if up_ else DOWN, width=1, dash="dot"), row=1, col=1,
                  annotation_text=f" {last:,.2f} ", annotation_position="right",
                  annotation_font=dict(color=POS_FG if up_ else NEG_FG, size=11),
                  annotation_bgcolor=POS_BG if up_ else NEG_BG)

    if trades is not None and not trades.empty:
        ent = trades[trades["Entry Date"].isin(d.index)]
        ext = trades[(trades["Exit Date"].isin(d.index)) & (trades["Exit Reason"] != "Open")]
        fig.add_trace(go.Scatter(x=pd.DatetimeIndex(ent["Entry Date"]).strftime(fmt), y=ent["Entry"],
                                 mode="markers", name="Buy",
                                 marker=dict(symbol="triangle-up", size=13, color=POS_BG, line=dict(width=1.5, color=UP))), 1, 1)
        fig.add_trace(go.Scatter(x=pd.DatetimeIndex(ext["Exit Date"]).strftime(fmt), y=ext["Exit"],
                                 mode="markers", name="Sell", text=ext["Exit Reason"],
                                 marker=dict(symbol="triangle-down", size=13, color=NEG_BG, line=dict(width=1.5, color=DOWN))), 1, 1)

    r = 2
    if has_vol:
        vcol = [rgba(UP, 0.5) if c >= o else rgba(DOWN, 0.5) for o, c in zip(d["Open"], d["Close"])]
        fig.add_trace(go.Bar(x=x, y=d["Volume"], marker_color=vcol, name="Volume", showlegend=False), row=r, col=1)
        if "VolAvg20" in d:
            fig.add_trace(go.Scatter(x=x, y=d["VolAvg20"], name="Vol MA20", showlegend=False,
                                     line=dict(color=GOLD, width=1)), row=r, col=1)
        r += 1

    for p in panels:
        if p == "RSI":
            fig.add_hrect(y0=30, y1=70, fillcolor=rgba(ACCENT, 0.06), line_width=0, row=r, col=1)
            fig.add_trace(go.Scatter(x=x, y=d["RSI"], name="RSI", line=dict(color=GOLD, width=1.4)), r, 1)
            fig.add_hline(y=70, line=dict(color=DOWN, dash="dot", width=0.8), row=r, col=1)
            fig.add_hline(y=30, line=dict(color=UP, dash="dot", width=0.8), row=r, col=1)
        elif p == "MACD":
            h = d["MACD_hist"]
            fig.add_trace(go.Bar(x=x, y=h, name="Hist", showlegend=False,
                                 marker_color=[rgba(UP, 0.6) if v >= 0 else rgba(DOWN, 0.6) for v in h.fillna(0)]), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["MACD"], name="MACD", line=dict(color=ACCENT, width=1.4)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["MACD_signal"], name="Signal", line=dict(color=GOLD, width=1.4)), r, 1)
        elif p == "Stochastic" and "STOCH_K" in d:
            fig.add_trace(go.Scatter(x=x, y=d["STOCH_K"], name="%K", line=dict(color=ACCENT, width=1.4)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["STOCH_D"], name="%D", line=dict(color=GOLD, width=1.4)), r, 1)
            fig.add_hline(y=80, line=dict(color=DOWN, dash="dot", width=0.8), row=r, col=1)
            fig.add_hline(y=20, line=dict(color=UP, dash="dot", width=0.8), row=r, col=1)
        elif p == "ADX" and "ADX" in d:
            fig.add_trace(go.Scatter(x=x, y=d["ADX"], name="ADX", line=dict(color=TEXT, width=1.4)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["DI_plus"], name="+DI", line=dict(color=UP, width=1)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["DI_minus"], name="−DI", line=dict(color=DOWN, width=1)), r, 1)
            fig.add_hline(y=25, line=dict(color=MUTED, dash="dot", width=0.8), row=r, col=1)
        elif p == "ATR" and "ATR" in d:
            fig.add_trace(go.Scatter(x=x, y=d["ATR"], name="ATR", line=dict(color=PURPLE, width=1.4)), r, 1)
        elif p == "OBV" and "OBV" in d:
            fig.add_trace(go.Scatter(x=x, y=d["OBV"], name="OBV", line=dict(color="#4DD0E1", width=1.4)), r, 1)
        elif p == "MFI" and "MFI" in d:
            fig.add_trace(go.Scatter(x=x, y=d["MFI"], name="MFI", line=dict(color="#FF8A65", width=1.4)), r, 1)
            fig.add_hline(y=80, line=dict(color=DOWN, dash="dot", width=0.8), row=r, col=1)
            fig.add_hline(y=20, line=dict(color=UP, dash="dot", width=0.8), row=r, col=1)
        elif p == "CCI" and "CCI" in d:
            fig.add_trace(go.Scatter(x=x, y=d["CCI"], name="CCI", line=dict(color="#81C784", width=1.4)), r, 1)
            fig.add_hline(y=100, line=dict(color=DOWN, dash="dot", width=0.8), row=r, col=1)
            fig.add_hline(y=-100, line=dict(color=UP, dash="dot", width=0.8), row=r, col=1)
        fig.update_yaxes(title_text=p, title_font=dict(size=10, color=MUTED), row=r, col=1)
        r += 1

    style(fig, height or (520 + 140 * len(panels)))
    fig.update_xaxes(type="category", nticks=8)
    return fig


# =====================================================================
# Visualizations
# =====================================================================
def score_gauge(total, title):
    color = UP if total >= 55 else (DOWN if total < 45 else GOLD)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=total, number=dict(suffix="/100", font=dict(size=28, color="#fff")),
        title=dict(text=title, font=dict(size=13, color=MUTED)),
        gauge=dict(axis=dict(range=[0, 100], tickcolor=MUTED), bar=dict(color=color, thickness=0.32), bgcolor="rgba(0,0,0,0)", borderwidth=0,
                   steps=[dict(range=[0, 45], color=rgba(DOWN, 0.16)), dict(range=[45, 55], color="rgba(138,148,167,0.14)"),
                          dict(range=[55, 100], color=rgba(UP, 0.16))])))
    return style(fig, 240, legend=False)


def gauge(score, title="Technical Rating", ticks=("Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy")):
    return score_gauge((score + 1) * 50, title)


def hbar(labels, values, title=None, height=None, suffix="%"):
    order = np.argsort(values)
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    fill, line, txt, out = pastel(values)
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker=dict(color=fill, line=dict(color=line, width=1)),
                           text=[f"{v:+.2f}{suffix}" for v in values], textposition="auto",
                           insidetextfont=dict(color=txt, size=12), outsidetextfont=dict(color=out, size=12),
                           hovertemplate="%{y}: %{x:+.2f}" + suffix + "<extra></extra>"))
    style(fig, height or max(260, 30 * len(values) + 70), title, legend=False)
    fig.update_yaxes(side="left", gridcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#3A4458")
    fig.update_layout(hovermode="closest", bargap=0.28)
    return _bars(fig)


def line(series, title=None, color=ACCENT, height=220, fill=True):
    fig = go.Figure(go.Scatter(x=series.index, y=series.values, line=dict(color=color, width=2.2, shape="spline", smoothing=0.5),
                               fill="tozeroy" if fill else None, fillcolor=rgba(color, 0.12)))
    style(fig, height, title, legend=False)
    if fill:
        lo, hi = series.min(), series.max()
        pad = (hi - lo) * 0.1 or 1
        fig.update_yaxes(range=[lo - pad, hi + pad])
    return fig


def area(series, title=None, color=CYAN, height=300, prefix="$"):
    """Gradient area line (cumulative P&L style)."""
    fig = go.Figure()
    tr = go.Scatter(x=series.index, y=series.values, mode="lines", line=dict(color=color, width=2.4, shape="spline", smoothing=0.6),
                    fill="tozeroy", hovertemplate=f"%{{x}}<br>{prefix}%{{y:,.0f}}<extra></extra>")
    try:
        tr.fillgradient = dict(type="vertical", colorscale=[[0, rgba(color, 0.0)], [1, rgba(color, 0.35)]])
    except (ValueError, AttributeError):
        tr.fillcolor = rgba(color, 0.15)
    fig.add_trace(tr)
    fig.add_hline(y=0, line=dict(color="#3A4458", width=1))
    style(fig, height, title, legend=False)
    fig.update_yaxes(tickprefix=prefix, side="left")
    fig.update_layout(hovermode="x")
    return fig


def signed_bars(x, y, title=None, height=300, prefix="$", fmt=",.0f"):
    """Daily / monthly P&L bars (pastel green / red)."""
    fill, line, _, _ = pastel(list(y))
    fig = go.Figure(go.Bar(x=x, y=y, marker=dict(color=fill, line=dict(color=line, width=1)),
                           hovertemplate=f"%{{x}}<br>{prefix}%{{y:{fmt}}}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="#3A4458", width=1))
    style(fig, height, title, legend=False)
    fig.update_yaxes(tickprefix=prefix, side="left")
    fig.update_layout(hovermode="x", bargap=0.25)
    return _bars(fig)


def equity_chart(eq, bench, names=("Strategy", "Buy & Hold", "Drawdown %")):
    dd = (eq / eq.cummax() - 1) * 100
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    tr = go.Scatter(x=eq.index, y=eq, name=names[0], line=dict(color=CYAN, width=2.4), fill="tozeroy")
    try:
        tr.fillgradient = dict(type="vertical", colorscale=[[0, rgba(CYAN, 0.0)], [1, rgba(CYAN, 0.28)]])
    except (ValueError, AttributeError):
        tr.fillcolor = rgba(CYAN, 0.12)
    fig.add_trace(tr, 1, 1)
    fig.add_trace(go.Scatter(x=bench.index, y=bench, name=names[1], line=dict(color=GOLD, width=1.6, dash="dot")), 1, 1)
    fig.add_trace(go.Scatter(x=dd.index, y=dd, name=names[2], fill="tozeroy", line=dict(color=DOWN, width=1),
                             fillcolor=rgba(DOWN, 0.22)), 2, 1)
    lo = min(eq.min(), bench.min())
    hi = max(eq.max(), bench.max())
    fig.update_yaxes(range=[lo * 0.97, hi * 1.02], row=1, col=1)
    fig.update_yaxes(title_text="Equity $", row=1, col=1, title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(title_text="DD %", row=2, col=1, title_font=dict(size=10, color=MUTED))
    return style(fig, 470)


def monthly_heatmap(table, title="Monthly Returns", months=None):
    months = months or ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    z = table.values.astype(float)
    text = [[("" if np.isnan(v) else f"{v:+.1f}%") for v in row] for row in z]
    m = np.nanmax(np.abs(z)) if np.isfinite(z).any() else 1
    fig = go.Figure(go.Heatmap(z=z, x=months, y=[str(y) for y in table.index], text=text, texttemplate="%{text}",
                               colorscale=[[0, "#F1AEB5"], [0.35, NEG_BG], [0.5, "#E2E8F0"], [0.65, POS_BG], [1, "#A3CFBB"]],
                               zmid=0, zmin=-m, zmax=m, xgap=3, ygap=3, textfont=dict(color="#1F2937", size=12),
                               showscale=False, hovertemplate="%{y} %{x}: %{text}<extra></extra>"))
    style(fig, 90 + 40 * len(table), title, legend=False)
    fig.update_yaxes(side="left", autorange="reversed", showgrid=False)
    return fig


def optimizer_heatmap(grid, xname, yname, metric, title=None):
    z = grid.values.astype(float)
    text = [[("" if np.isnan(v) else f"{v:.1f}") for v in row] for row in z]
    fig = go.Figure(go.Heatmap(z=z, x=[str(c) for c in grid.columns], y=[str(i) for i in grid.index], text=text,
                               texttemplate="%{text}", zmid=0 if "Drawdown" not in metric else None, xgap=2, ygap=2,
                               colorscale=[[0, "#B3262B"], [0.5, "#1A2130"], [1, "#16A34A"]],
                               colorbar=dict(title=metric, thickness=10)))
    style(fig, 420, title or f"{metric} by parameters", legend=False)
    fig.update_xaxes(title_text=xname, type="category")
    fig.update_yaxes(title_text=yname, side="left", type="category")
    return fig


def trade_bars(trades, title="P&L per trade (%)"):
    fill, line, txt, out = pastel(list(trades["P&L %"]))
    fig = go.Figure(go.Bar(x=[f"#{i + 1}" for i in range(len(trades))], y=trades["P&L %"],
                           marker=dict(color=fill, line=dict(color=line, width=1)),
                           text=[f"{v:+.1f}%" for v in trades["P&L %"]], textposition="auto",
                           insidetextfont=dict(color=txt), outsidetextfont=dict(color=out), hovertext=trades["Exit Reason"]))
    return _bars(style(fig, 320, title, legend=False))


def cumulative_pnl(trades, title="Cumulative P&L ($)", xlab="Trade #"):
    c = trades["P&L $"].cumsum()
    c.index = range(1, len(c) + 1)
    fig = area(c, title, CYAN, 300)
    fig.update_xaxes(title_text=xlab)
    return fig


def pie(labels, values, title, colors=None, center=None):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62, sort=False,
                           marker=dict(colors=colors or [UP, DOWN, ACCENT, GOLD, PURPLE, CYAN, ORANGE, MUTED], line=dict(color=BG, width=3)),
                           textinfo="percent", textfont=dict(color="#0A0E17", size=12)))
    if center:
        fig.add_annotation(text=center, showarrow=False, font=dict(size=18, color="#fff"))
    return style(fig, 300, title)


def histogram(values, title, color=ACCENT):
    fig = go.Figure(go.Histogram(x=values, marker=dict(color=rgba(color, 0.75), line=dict(color=color, width=1)), nbinsx=20))
    return _bars(style(fig, 300, title, legend=False))


def scan_scatter(res, title="Momentum map: 1-month return vs RSI (bubble = volume, color = score)"):
    d = res.dropna(subset=["RSI", "1M %"])
    size = d["Vol ×"].fillna(1).clip(0.5, 5) * 9
    fig = go.Figure(go.Scatter(
        x=d["1M %"], y=d["RSI"], mode="markers+text", text=d["Symbol"], textposition="top center",
        textfont=dict(size=9, color=MUTED),
        marker=dict(size=size, color=d["Score"], colorscale=[[0, DOWN], [0.5, GOLD], [1, UP]],
                    showscale=True, colorbar=dict(title="Score", thickness=10), line=dict(width=0)),
        hovertemplate="<b>%{text}</b><br>1M: %{x:.1f}%<br>RSI: %{y:.0f}<extra></extra>"))
    fig.add_hrect(y0=70, y1=100, fillcolor=rgba(DOWN, 0.06), line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor=rgba(UP, 0.06), line_width=0)
    fig.add_vline(x=0, line=dict(color=MUTED, dash="dot", width=0.8))
    style(fig, 460, title, legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title_text="1M return %", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title_text="RSI", side="left", range=[max(0, d["RSI"].min() - 8), min(100, d["RSI"].max() + 8)] if not d.empty else None)
    return fig


def returns_bars(d, title="Performance"):
    c = d["Close"]
    periods = {"1W": 5, "1M": 21, "3M": 63, "6M": 126, "1Y": 252}
    labels, vals = [], []
    for k, n in periods.items():
        if len(c) > n:
            labels.append(k)
            vals.append((c.iloc[-1] / c.iloc[-n - 1] - 1) * 100)
    ytd = c[c.index.year == c.index[-1].year]
    if len(ytd) > 1:
        labels.append("YTD")
        vals.append((c.iloc[-1] / ytd.iloc[0] - 1) * 100)
    fill, line, txt, out = pastel(vals)
    fig = go.Figure(go.Bar(x=labels, y=vals, marker=dict(color=fill, line=dict(color=line, width=1)),
                           text=[f"{v:+.1f}%" for v in vals], textposition="auto",
                           insidetextfont=dict(color=txt, size=13), outsidetextfont=dict(color=out, size=13)))
    return _bars(style(fig, 280, title, legend=False))


def rec_chart(rec, title="Analyst recommendations"):
    cols = [("strongBuy", "Strong Buy", "#16A34A"), ("buy", "Buy", "#86EFAC"), ("hold", "Hold", "#FDE68A"),
            ("sell", "Sell", "#FCA5A5"), ("strongSell", "Strong Sell", "#DC2626")]
    fig = go.Figure()
    periods = rec["period"] if "period" in rec else rec.index.astype(str)
    for key, name, color in cols:
        if key in rec:
            fig.add_trace(go.Bar(x=periods, y=rec[key], name=name, marker_color=color))
    fig.update_layout(barmode="stack", bargap=0.35)
    return _bars(style(fig, 300, title))


def target_chart(price, t, title="12-month price targets"):
    fig = go.Figure()
    lo, hi = t.get("low"), t.get("high")
    if lo and hi:
        fig.add_trace(go.Scatter(x=[lo, hi], y=[0, 0], mode="lines", line=dict(color=BORDER, width=12),
                                 showlegend=False, hoverinfo="skip"))
    for key, name, color in (("low", "Low", DOWN), ("mean", "Mean", ACCENT), ("median", "Median", GOLD),
                             ("high", "High", UP)):
        v = t.get(key)
        if v:
            fig.add_trace(go.Scatter(x=[v], y=[0], mode="markers+text", name=name, text=[f"{name}<br>${v:,.0f}"],
                                     textposition="top center", marker=dict(size=15, color=color, line=dict(color=BG, width=2))))
    if price:
        fig.add_trace(go.Scatter(x=[price], y=[0], mode="markers+text", name="Current", text=[f"Now<br>${price:,.0f}"],
                                 textposition="bottom center", marker=dict(size=17, color="#fff", symbol="diamond")))
    style(fig, 220, title, legend=False)
    fig.update_yaxes(visible=False, range=[-1, 1])
    fig.update_layout(hovermode="closest")
    return fig


def eps_chart(eh, title="EPS: estimate vs actual"):
    est = next((c for c in eh.columns if "Estimate" in c), None)
    rep = next((c for c in eh.columns if "Reported" in c), None)
    if not est or not rep:
        return None
    e = eh.dropna(subset=[rep]).head(8).iloc[::-1]
    x = [pd.Timestamp(i).strftime("%b %Y") for i in e.index]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=e[est], mode="markers", name="Estimate",
                             marker=dict(size=16, color="rgba(0,0,0,0)", line=dict(color=MUTED, width=2))))
    beat = [a >= b for a, b in zip(e[rep], e[est])]
    fig.add_trace(go.Scatter(x=x, y=e[rep], mode="markers", name="Actual",
                             marker=dict(size=14, color=[POS_BG if b else NEG_BG for b in beat], line=dict(color=[UP if b else DOWN for b in beat], width=2))))
    style(fig, 300, title)
    fig.update_xaxes(type="category")
    return fig


# =====================================================================
# Markets
# =====================================================================
def sector_rrg(tails, names, title="Sector rotation (vs S&P 500)", labels=("Leading", "Weakening", "Lagging", "Improving")):
    """Relative Rotation Graph. tails: {etf: DataFrame[ratio, mom]} (weekly points, last = now)."""
    fig = go.Figure()
    allx = np.concatenate([t["ratio"].values for t in tails.values()]) if tails else np.array([100])
    ally = np.concatenate([t["mom"].values for t in tails.values()]) if tails else np.array([100])
    span_x = max(2.5, np.nanmax(np.abs(allx - 100)) * 1.2)
    span_y = max(2.5, np.nanmax(np.abs(ally - 100)) * 1.2)
    x0, x1, y0, y1 = 100 - span_x, 100 + span_x, 100 - span_y, 100 + span_y
    for (a, b, c, d_, col) in ((100, x1, 100, y1, UP), (100, x1, y0, 100, GOLD), (x0, 100, y0, 100, DOWN), (x0, 100, 100, y1, ACCENT)):
        fig.add_shape(type="rect", x0=a, x1=b, y0=c, y1=d_, fillcolor=rgba(col, 0.07), line_width=0, layer="below")
    for (tx, ty, txt, col) in ((x1, y1, labels[0], UP), (x1, y0, labels[1], GOLD), (x0, y0, labels[2], DOWN), (x0, y1, labels[3], ACCENT)):
        fig.add_annotation(x=tx, y=ty, text=f"<b>{txt}</b>", showarrow=False, xanchor="right" if tx == x1 else "left",
                           yanchor="top" if ty == y1 else "bottom", font=dict(color=col, size=13), xshift=-8 if tx == x1 else 8,
                           yshift=-6 if ty == y1 else 6)
    for i, (etf, t) in enumerate(tails.items()):
        col = PALETTE[i % len(PALETTE)]
        n = len(t)
        fig.add_trace(go.Scatter(x=t["ratio"], y=t["mom"], mode="lines+markers", line=dict(color=rgba(col, 0.5), width=1.6),
                                 marker=dict(size=[3 + 4 * j / max(n - 1, 1) for j in range(n)], color=rgba(col, 0.6)),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=[t["ratio"].iloc[-1]], y=[t["mom"].iloc[-1]], mode="markers+text", text=[f"<b>{etf}</b>"],
                                 textposition="top center", textfont=dict(color=col, size=11), name=names.get(etf, etf),
                                 marker=dict(size=15, color=col, line=dict(color="#fff", width=1.5)),
                                 hovertemplate=f"<b>{names.get(etf, etf)}</b> ({etf})<br>RS-Ratio %{{x:.2f}}<br>RS-Momentum %{{y:.2f}}<extra></extra>"))
    fig.add_hline(y=100, line=dict(color="#3A4458", width=1))
    fig.add_vline(x=100, line=dict(color="#3A4458", width=1))
    style(fig, 470, title, legend=False)
    fig.update_xaxes(range=[x0, x1], showgrid=False, title_text="RS-Ratio", title_font=dict(size=11, color=MUTED))
    fig.update_yaxes(range=[y0, y1], showgrid=False, side="left", title_text="RS-Momentum", title_font=dict(size=11, color=MUTED))
    fig.update_layout(hovermode="closest")
    return fig


def change_distribution(chg, title="Distribution of today's moves", xlab="Change %", ylab="Stocks"):
    bins = np.arange(-5, 5.5, 0.5)
    v = np.clip(pd.Series(chg).dropna().values, -4.999, 4.999)
    counts, edges = np.histogram(v, bins=bins)
    mids = (edges[:-1] + edges[1:]) / 2
    fill, line, txt, out = pastel(list(mids))
    fig = go.Figure(go.Bar(x=mids, y=counts, width=0.44, marker=dict(color=fill, line=dict(color=line, width=1)),
                           text=[str(c) if c else "" for c in counts], textposition="outside", textfont=dict(color=MUTED, size=10),
                           hovertemplate="%{x:+.1f}%: %{y}<extra></extra>"))
    style(fig, 300, title, legend=False)
    fig.update_xaxes(title_text=xlab, ticksuffix="%", tickvals=[-4, -3, -2, -1, 0, 1, 2, 3, 4], showgrid=False)
    fig.update_yaxes(title_text=ylab, side="left", showgrid=True, range=[0, max(counts.max(), 1) * 1.2])
    fig.update_layout(hovermode="closest")
    return _bars(fig)


def norm_lines(series_map, title=None, height=360):
    """Relative performance (rebased to 0%)."""
    fig = go.Figure()
    for i, (name, s) in enumerate(series_map.items()):
        s = s.dropna()
        if len(s) < 2:
            continue
        r = (s / s.iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(x=r.index, y=r.values, name=name, mode="lines", line=dict(width=2, color=PALETTE[i % len(PALETTE)]),
                                 hovertemplate=f"{name}: %{{y:+.2f}}%<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="#3A4458", width=1))
    style(fig, height, title)
    fig.update_yaxes(ticksuffix="%")
    return fig


def term_structure(labels, values, title="VIX term structure"):
    contango = len(values) > 1 and values[-1] > values[0]
    col = UP if contango else DOWN
    fig = go.Figure(go.Scatter(x=labels, y=values, mode="lines+markers+text", text=[f"{v:.2f}" for v in values],
                               textposition="top center", textfont=dict(color="#fff"),
                               line=dict(color=col, width=3, shape="spline"), marker=dict(size=12, color=POS_BG if contango else NEG_BG,
                                                                                      line=dict(color=col, width=2)),
                               fill="tozeroy", fillcolor=rgba(col, 0.08)))
    style(fig, 300, title, legend=False)
    lo, hi = min(values), max(values)
    fig.update_yaxes(range=[lo * 0.85, hi * 1.12], side="left")
    fig.update_layout(hovermode="x")
    return fig


def pc_bars(symbols, ratios, title="Put/Call volume ratio"):
    fill, line, txt = [], [], []
    for r in ratios:
        if r < 0.7:
            fill.append(POS_BG); line.append(POS_BD); txt.append(POS_FG)
        elif r > 1.0:
            fill.append(NEG_BG); line.append(NEG_BD); txt.append(NEG_FG)
        else:
            fill.append("#E2E8F0"); line.append("#CBD5E1"); txt.append("#334155")
    fig = go.Figure(go.Bar(x=symbols, y=ratios, marker=dict(color=fill, line=dict(color=line, width=1)), text=[f"{r:.2f}" for r in ratios],
                           textposition="inside", insidetextfont=dict(color=txt, size=12)))
    fig.add_hline(y=1, line=dict(color=DOWN, dash="dot", width=1))
    fig.add_hline(y=0.7, line=dict(color=UP, dash="dot", width=1))
    return _bars(style(fig, 300, title, legend=False))


# =====================================================================
# Financials
# =====================================================================
def metric_bars(labels, values, title=None, kind="money", height=340):
    """Interactive financial explorer bars with period-over-period growth tags."""
    fill, line, txt, out = pastel(values)

    def f(v):
        if v is None or np.isnan(v):
            return ""
        if kind == "money":
            a = abs(v)
            s = f"{a / 1e12:.2f}T" if a >= 1e12 else (f"{a / 1e9:.2f}B" if a >= 1e9 else f"{a / 1e6:.0f}M")
            return ("-" if v < 0 else "") + "$" + s
        if kind == "pct":
            return f"{v:.1f}%"
        if kind == "eps":
            return f"${v:.2f}"
        return f"{v:.2f}"
    fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=fill, line=dict(color=line, width=1.2)),
                           text=[f(v) for v in values], textposition="auto", insidetextfont=dict(color=txt, size=12),
                           outsidetextfont=dict(color=out, size=12), hovertemplate="%{x}: %{text}<extra></extra>"))
    for i in range(1, len(values)):
        a, b = values[i - 1], values[i]
        if a and b is not None and not np.isnan(a) and not np.isnan(b) and a != 0 and kind in ("money", "eps"):
            g = (b / abs(a) - 1) * 100 if a > 0 else (b - a) / abs(a) * 100
            fig.add_annotation(x=labels[i], y=max(b, 0), text=f"{g:+.0f}%", showarrow=False, yshift=16,
                               font=dict(size=11, color=POS_BD if g >= 0 else NEG_BD))
    style(fig, height, title, legend=False)
    fig.update_yaxes(side="left", showticklabels=False, showgrid=False, zeroline=True, zerolinecolor="#3A4458")
    fig.update_xaxes(type="category")
    fig.update_layout(hovermode="closest", bargap=0.3)
    return _bars(fig)


def cash_waterfall(items, title="Where the cash went (latest year)"):
    """items: [(label, value, 'relative'|'total')]"""
    run, text, peak = 0.0, [], 0.0
    for _, v, m in items:
        if m == "total":
            v = run
        else:
            run += v
        peak = max(peak, run, v)
        text.append(("-" if v < 0 else "") + f"${abs(v) / 1e9:.1f}B")
    fig = go.Figure(go.Waterfall(
        x=[i[0] for i in items], y=[i[1] for i in items], measure=[i[2] for i in items],
        text=text, textposition="outside",
        textfont=dict(color="#E9EDF5", size=12),
        increasing=dict(marker=dict(color=POS_BG, line=dict(color=POS_BD, width=1.5))),
        decreasing=dict(marker=dict(color=NEG_BG, line=dict(color=NEG_BD, width=1.5))),
        totals=dict(marker=dict(color="#DBEAFE", line=dict(color="#93C5FD", width=1.5))),
        connector=dict(line=dict(color="#3A4458", width=1, dash="dot"))))
    style(fig, 360, title, legend=False)
    fig.update_yaxes(side="left", tickprefix="$", showgrid=True, range=[min(0, run) * 1.15, peak * 1.16 if peak > 0 else None])
    fig.update_layout(hovermode="closest")
    return fig


def cash_trend(periods, ocf, capex, fcf, margin=None, title="Cash flow trend", names=("Operating cash flow", "Capital expenditure", "Free cash flow", "FCF margin")):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    b = lambda v: [x / 1e9 if x is not None and not np.isnan(x) else None for x in v]
    fig.add_trace(go.Bar(x=periods, y=b(ocf), name=names[0], marker=dict(color="#DBEAFE", line=dict(color="#93C5FD", width=1))), secondary_y=False)
    fig.add_trace(go.Bar(x=periods, y=b(capex), name=names[1], marker=dict(color=NEG_BG, line=dict(color=NEG_BD, width=1))), secondary_y=False)
    fig.add_trace(go.Bar(x=periods, y=b(fcf), name=names[2], marker=dict(color=POS_BG, line=dict(color=POS_BD, width=1))), secondary_y=False)
    if margin is not None:
        fig.add_trace(go.Scatter(x=periods, y=margin, name=names[3], mode="lines+markers", line=dict(color=GOLD, width=2.4),
                                 marker=dict(size=8)), secondary_y=True)
    style(fig, 360, title)
    fig.update_layout(barmode="group", bargap=0.25, hovermode="x unified")
    fig.update_yaxes(tickprefix="$", ticksuffix="B", side="left", secondary_y=False)
    fig.update_yaxes(ticksuffix="%", showgrid=False, secondary_y=True)
    fig.update_xaxes(type="category")
    return _bars(fig)


# =====================================================================
# Options
# =====================================================================
def oi_by_strike(calls, puts, price, title="Open interest by strike", names=("Calls", "Puts")):
    fig = go.Figure()
    if not calls.empty:
        fig.add_trace(go.Bar(x=calls["strike"], y=calls["openInterest"].fillna(0), name=names[0],
                             marker=dict(color=POS_BG, line=dict(color=POS_BD, width=1))))
    if not puts.empty:
        fig.add_trace(go.Bar(x=puts["strike"], y=-puts["openInterest"].fillna(0), name=names[1],
                             marker=dict(color=NEG_BG, line=dict(color=NEG_BD, width=1))))
    fig.add_vline(x=price, line=dict(color=CYAN, width=1.5, dash="dash"), annotation_text=f"{price:,.2f}", annotation_font_color=CYAN)
    fig.update_layout(barmode="relative", bargap=0.15)
    style(fig, 360, title)
    fig.update_layout(hovermode="x")
    return fig


def iv_smile(calls, puts, price, title="Implied volatility smile", names=("Calls IV", "Puts IV")):
    fig = go.Figure()
    for df, name, color in ((calls, names[0], UP), (puts, names[1], DOWN)):
        if not df.empty:
            d = df[df["impliedVolatility"] > 0.001]
            fig.add_trace(go.Scatter(x=d["strike"], y=d["impliedVolatility"] * 100, mode="lines+markers", name=name,
                                     line=dict(color=color, width=2, shape="spline"), marker=dict(size=5)))
    fig.add_vline(x=price, line=dict(color=CYAN, width=1.5, dash="dash"))
    style(fig, 360, title)
    fig.update_yaxes(ticksuffix="%")
    return fig


def payoff(kind, strike, premium, price_now, title="Profit / loss at expiration", labels=("Stock price at expiration", "Profit / loss ($)")):
    """Payoff of one long option contract (100 shares)."""
    xs = np.linspace(max(0.01, strike * 0.6), strike * 1.4, 160)
    if kind == "call":
        pnl = (np.maximum(xs - strike, 0) - premium) * 100
        be = strike + premium
    else:
        pnl = (np.maximum(strike - xs, 0) - premium) * 100
        be = strike - premium
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=np.where(pnl >= 0, pnl, np.nan), fill="tozeroy", line=dict(color=UP, width=2.5),
                             fillcolor=rgba(UP, 0.18), name="Profit", hovertemplate="$%{x:.2f} → %{y:+,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=np.where(pnl < 0, pnl, np.nan), fill="tozeroy", line=dict(color=DOWN, width=2.5),
                             fillcolor=rgba(DOWN, 0.18), name="Loss", hovertemplate="$%{x:.2f} → %{y:+,.0f}<extra></extra>"))
    fig.add_vline(x=strike, line=dict(color=MUTED, dash="dot"), annotation_text=f"K {strike:,.0f}")
    fig.add_vline(x=be, line=dict(color=GOLD, dash="dash"), annotation_text=f"BE {be:,.2f}", annotation_font_color=GOLD)
    fig.add_vline(x=price_now, line=dict(color=CYAN, width=1), annotation_text="Now", annotation_position="bottom right")
    fig.add_hline(y=0, line=dict(color=BORDER))
    style(fig, 360, title, legend=False)
    fig.update_xaxes(title_text=labels[0], showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title_text=labels[1])
    fig.update_layout(hovermode="closest")
    return fig


def movers_bubble(df, title="Change vs relative volume (bubble = market cap)", xlab="Relative volume (×)", ylab="Change %"):
    d = df.dropna(subset=["Chg %"]).copy()
    d["Rel Vol"] = d["Rel Vol"].fillna(1).clip(0.1, 15)
    cap = d["Mkt Cap"].fillna(d["Mkt Cap"].median() if d["Mkt Cap"].notna().any() else 1e9).clip(lower=1e8)
    size = np.sqrt(cap / cap.max()) * 46 + 8
    fill, line, txt, _ = pastel(list(d["Chg %"]))
    fig = go.Figure(go.Scatter(
        x=d["Rel Vol"], y=d["Chg %"], mode="markers+text", text=d["Symbol"], textposition="middle center",
        textfont=dict(size=9, color=txt),
        marker=dict(size=size, color=fill, line=dict(width=1.5, color=line), opacity=0.95),
        customdata=d["Name"], hovertemplate="<b>%{text}</b> %{customdata}<br>%{y:+.2f}% · %{x:.1f}×<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="#3A4458"))
    fig.add_vline(x=1, line=dict(color=MUTED, dash="dot"))
    style(fig, 440, title, legend=False)
    fig.update_xaxes(title_text=xlab, type="log", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title_text=ylab, ticksuffix="%", side="left")
    fig.update_layout(hovermode="closest")
    return fig


# =====================================================================
# Academy & bot
# =====================================================================
def level_progress(levels, completed, in_progress, total, colors, title=None, names=("Completed", "In progress", "Not started")):
    """Stacked horizontal bars per level: completed (solid) · in progress (light) · not started."""
    fig = go.Figure()
    rest = [t - c - p for t, c, p in zip(total, completed, in_progress)]
    fig.add_trace(go.Bar(y=levels, x=completed, orientation="h", name=names[0], marker=dict(color=colors),
                         text=[str(v) if v else "" for v in completed], textposition="inside", insidetextfont=dict(color="#0A0E17")))
    fig.add_trace(go.Bar(y=levels, x=in_progress, orientation="h", name=names[1], marker=dict(color=[rgba(c, 0.45) for c in colors]),
                         text=[str(v) if v else "" for v in in_progress], textposition="inside", insidetextfont=dict(color="#fff")))
    fig.add_trace(go.Bar(y=levels, x=rest, orientation="h", name=names[2], marker=dict(color="#222B3B"), hoverinfo="skip"))
    style(fig, 260, title)
    fig.update_layout(barmode="stack", bargap=0.35, hovermode="closest")
    fig.update_yaxes(side="left", autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, dtick=1)
    return _bars(fig)
