"""
charts.py - All Plotly figures (Webull-style dark theme).
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import ta
from theme import ACCENT, BG, BORDER, DOWN, GOLD, MUTED, PURPLE, TEXT, UP


def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"

OVERLAYS = ["SMA 20", "SMA 50", "SMA 200", "EMA 9", "EMA 21", "Bollinger Bands", "VWAP",
            "Pivot Points", "Support / Resistance"]
PANELS = ["RSI", "MACD", "Stochastic", "ADX", "ATR", "OBV", "MFI", "CCI"]
CHART_TYPES = ["Candles", "Heikin Ashi", "OHLC", "Line", "Area"]


def style(fig, height=420, title=None, legend=True):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=BG, height=height,
        margin=dict(l=8, r=8, t=40 if title else 16, b=8), hovermode="x unified",
        title=dict(text=title, font=dict(size=14)) if title else None,
        showlegend=legend, legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom", bgcolor="rgba(0,0,0,0)"),
        font=dict(color=TEXT, family="Inter, sans-serif", size=12),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, rangeslider_visible=False)
    fig.update_yaxes(gridcolor=BORDER, zeroline=False, side="right")
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
        fig.add_trace(go.Scatter(x=x, y=d["Close"], name="Price", line=dict(color=col, width=1.8),
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
            fig.add_trace(go.Scatter(x=x, y=d[col_name], name=o, line=dict(color=color, width=1.3)), 1, 1)
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

    if trades is not None and not trades.empty:
        ent = trades[trades["Entry Date"].isin(d.index)]
        ext = trades[(trades["Exit Date"].isin(d.index)) & (trades["Exit Reason"] != "Open")]
        fig.add_trace(go.Scatter(x=pd.DatetimeIndex(ent["Entry Date"]).strftime(fmt), y=ent["Entry"],
                                 mode="markers", name="Buy",
                                 marker=dict(symbol="triangle-up", size=12, color=UP,
                                             line=dict(width=1, color=BG))), 1, 1)
        fig.add_trace(go.Scatter(x=pd.DatetimeIndex(ext["Exit Date"]).strftime(fmt), y=ext["Exit"],
                                 mode="markers", name="Sell", text=ext["Exit Reason"],
                                 marker=dict(symbol="triangle-down", size=12, color=DOWN,
                                             line=dict(width=1, color=BG))), 1, 1)

    r = 2
    if has_vol:
        vcol = [UP if c >= o else DOWN for o, c in zip(d["Open"], d["Close"])]
        fig.add_trace(go.Bar(x=x, y=d["Volume"], marker_color=vcol, opacity=0.6, name="Volume",
                             showlegend=False), row=r, col=1)
        if "VolAvg20" in d:
            fig.add_trace(go.Scatter(x=x, y=d["VolAvg20"], name="Vol MA20", showlegend=False,
                                     line=dict(color=GOLD, width=1)), row=r, col=1)
        r += 1

    for p in panels:
        if p == "RSI":
            fig.add_trace(go.Scatter(x=x, y=d["RSI"], name="RSI", line=dict(color=GOLD, width=1.3)), r, 1)
            fig.add_hline(y=70, line=dict(color=DOWN, dash="dot", width=0.8), row=r, col=1)
            fig.add_hline(y=30, line=dict(color=UP, dash="dot", width=0.8), row=r, col=1)
        elif p == "MACD":
            h = d["MACD_hist"]
            fig.add_trace(go.Bar(x=x, y=h, name="Hist", showlegend=False,
                                 marker_color=[UP if v >= 0 else DOWN for v in h.fillna(0)]), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["MACD"], name="MACD", line=dict(color=ACCENT, width=1.3)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["MACD_signal"], name="Signal", line=dict(color=GOLD, width=1.3)), r, 1)
        elif p == "Stochastic" and "STOCH_K" in d:
            fig.add_trace(go.Scatter(x=x, y=d["STOCH_K"], name="%K", line=dict(color=ACCENT, width=1.3)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["STOCH_D"], name="%D", line=dict(color=GOLD, width=1.3)), r, 1)
            fig.add_hline(y=80, line=dict(color=DOWN, dash="dot", width=0.8), row=r, col=1)
            fig.add_hline(y=20, line=dict(color=UP, dash="dot", width=0.8), row=r, col=1)
        elif p == "ADX" and "ADX" in d:
            fig.add_trace(go.Scatter(x=x, y=d["ADX"], name="ADX", line=dict(color=TEXT, width=1.4)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["DI_plus"], name="+DI", line=dict(color=UP, width=1)), r, 1)
            fig.add_trace(go.Scatter(x=x, y=d["DI_minus"], name="−DI", line=dict(color=DOWN, width=1)), r, 1)
            fig.add_hline(y=25, line=dict(color=MUTED, dash="dot", width=0.8), row=r, col=1)
        elif p == "ATR" and "ATR" in d:
            fig.add_trace(go.Scatter(x=x, y=d["ATR"], name="ATR", line=dict(color=PURPLE, width=1.3)), r, 1)
        elif p == "OBV" and "OBV" in d:
            fig.add_trace(go.Scatter(x=x, y=d["OBV"], name="OBV", line=dict(color="#4DD0E1", width=1.3)), r, 1)
        elif p == "MFI" and "MFI" in d:
            fig.add_trace(go.Scatter(x=x, y=d["MFI"], name="MFI", line=dict(color="#FF8A65", width=1.3)), r, 1)
            fig.add_hline(y=80, line=dict(color=DOWN, dash="dot", width=0.8), row=r, col=1)
            fig.add_hline(y=20, line=dict(color=UP, dash="dot", width=0.8), row=r, col=1)
        elif p == "CCI" and "CCI" in d:
            fig.add_trace(go.Scatter(x=x, y=d["CCI"], name="CCI", line=dict(color="#81C784", width=1.3)), r, 1)
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
def gauge(score, title="Technical Rating"):
    val = (score + 1) * 50
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=val, number=dict(suffix="", font=dict(size=28)),
        title=dict(text=title, font=dict(size=13, color=MUTED)),
        gauge=dict(axis=dict(range=[0, 100], tickvals=[10, 30, 50, 70, 90],
                             ticktext=["Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy"],
                             tickfont=dict(size=9)),
                   bar=dict(color=TEXT, thickness=0.25), bgcolor=BG, borderwidth=0,
                   steps=[dict(range=[0, 25], color="#5c1a1d"), dict(range=[25, 45], color="#3d2224"),
                          dict(range=[45, 55], color="#2a3040"), dict(range=[55, 75], color="#16392f"),
                          dict(range=[75, 100], color="#0f5140")])))
    return style(fig, 250, legend=False)


def score_gauge(total, title):
    color = UP if total >= 55 else (DOWN if total < 45 else GOLD)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=total, number=dict(suffix="/100", font=dict(size=26)),
        title=dict(text=title, font=dict(size=13, color=MUTED)),
        gauge=dict(axis=dict(range=[0, 100]), bar=dict(color=color, thickness=0.3), bgcolor=BG, borderwidth=0,
                   steps=[dict(range=[0, 45], color="#2a1a1d"), dict(range=[45, 55], color="#262b36"),
                          dict(range=[55, 100], color="#132b25")])))
    return style(fig, 240, legend=False)


def treemap(df):
    """df: Symbol, Sector, Chg %, Size."""
    labels = list(df["Sector"].unique()) + list(df["Symbol"])
    parents = [""] * df["Sector"].nunique() + list(df["Sector"])
    sec_size = df.groupby("Sector")["Size"].sum()
    w = df.assign(_w=df["Chg %"] * df["Size"]).groupby("Sector")[["_w", "Size"]].sum()
    sec_chg = w["_w"] / w["Size"]
    values = [sec_size[s] for s in df["Sector"].unique()] + list(df["Size"])
    colors = [sec_chg[s] for s in df["Sector"].unique()] + list(df["Chg %"])
    text = [f"{c:+.2f}%" for c in colors]
    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values, branchvalues="total", text=text,
        texttemplate="<b>%{label}</b><br>%{text}", hovertemplate="<b>%{label}</b><br>%{text}<extra></extra>",
        marker=dict(colors=colors, colorscale=[[0, "#B3262B"], [0.5, "#2A3040"], [1, "#00A574"]],
                    cmid=0, cmin=-3, cmax=3, line=dict(width=1, color=BG)),
        tiling=dict(pad=2)))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return style(fig, 520, legend=False)


def hbar(labels, values, title=None, height=None, suffix="%"):
    order = np.argsort(values)
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h",
                           marker_color=[UP if v >= 0 else DOWN for v in values],
                           text=[f"{v:+.2f}{suffix}" for v in values], textposition="outside"))
    style(fig, height or max(260, 28 * len(values) + 60), title, legend=False)
    fig.update_yaxes(side="left", gridcolor="rgba(0,0,0,0)")
    fig.update_layout(hovermode="closest")
    return fig


def line(series, title=None, color=ACCENT, height=220, fill=True):
    fig = go.Figure(go.Scatter(x=series.index, y=series.values, line=dict(color=color, width=1.8),
                               fill="tozeroy" if fill else None, fillcolor=rgba(color, 0.12)))
    style(fig, height, title, legend=False)
    if fill:
        lo, hi = series.min(), series.max()
        pad = (hi - lo) * 0.1 or 1
        fig.update_yaxes(range=[lo - pad, hi + pad])
    return fig


def equity_chart(eq, bench):
    dd = (eq / eq.cummax() - 1) * 100
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=eq.index, y=eq, name="Strategy", line=dict(color=UP, width=2)), 1, 1)
    fig.add_trace(go.Scatter(x=bench.index, y=bench, name="Buy & Hold", line=dict(color=MUTED, width=1.3, dash="dot")), 1, 1)
    fig.add_trace(go.Scatter(x=dd.index, y=dd, name="Drawdown %", fill="tozeroy",
                             line=dict(color=DOWN, width=1), fillcolor=rgba(DOWN, 0.2)), 2, 1)
    fig.update_yaxes(title_text="Equity $", row=1, col=1, title_font=dict(size=10, color=MUTED))
    fig.update_yaxes(title_text="DD %", row=2, col=1, title_font=dict(size=10, color=MUTED))
    return style(fig, 460)


def monthly_heatmap(table):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    z = table.values.astype(float)
    text = [[("" if np.isnan(v) else f"{v:+.1f}%") for v in row] for row in z]
    fig = go.Figure(go.Heatmap(z=z, x=months, y=[str(y) for y in table.index], text=text, texttemplate="%{text}",
                               colorscale=[[0, "#B3262B"], [0.5, "#1A2130"], [1, "#00A574"]], zmid=0,
                               showscale=False, hovertemplate="%{y} %{x}: %{text}<extra></extra>"))
    style(fig, 90 + 38 * len(table), "Monthly Returns", legend=False)
    fig.update_yaxes(side="left", autorange="reversed")
    return fig


def optimizer_heatmap(grid, xname, yname, metric):
    z = grid.values.astype(float)
    text = [[("" if np.isnan(v) else f"{v:.1f}") for v in row] for row in z]
    fig = go.Figure(go.Heatmap(z=z, x=[str(c) for c in grid.columns], y=[str(i) for i in grid.index], text=text,
                               texttemplate="%{text}", zmid=0 if "Drawdown" not in metric else None,
                               colorscale=[[0, "#B3262B"], [0.5, "#1A2130"], [1, "#00A574"]],
                               colorbar=dict(title=metric, thickness=10)))
    style(fig, 420, f"{metric} by parameters", legend=False)
    fig.update_xaxes(title_text=xname, type="category")
    fig.update_yaxes(title_text=yname, side="left", type="category")
    return fig


def trade_bars(trades):
    fig = go.Figure(go.Bar(x=[f"#{i + 1}" for i in range(len(trades))], y=trades["P&L %"],
                           marker_color=[UP if v >= 0 else DOWN for v in trades["P&L %"]],
                           text=[f"{v:+.1f}%" for v in trades["P&L %"]], textposition="outside",
                           hovertext=trades["Exit Reason"]))
    return style(fig, 320, "P&L per trade (%)", legend=False)


def cumulative_pnl(trades):
    c = trades["P&L $"].cumsum()
    fig = go.Figure(go.Scatter(x=list(range(1, len(c) + 1)), y=c, mode="lines+markers",
                               line=dict(color=ACCENT, width=2), fill="tozeroy", fillcolor=rgba(ACCENT, 0.13)))
    style(fig, 300, "Cumulative P&L ($)", legend=False)
    fig.update_xaxes(title_text="Trade #")
    return fig


def pie(labels, values, title):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55,
                           marker=dict(colors=[UP, DOWN, ACCENT, GOLD, PURPLE, MUTED])))
    return style(fig, 300, title)


def histogram(values, title, color=ACCENT):
    fig = go.Figure(go.Histogram(x=values, marker_color=color, nbinsx=20))
    return style(fig, 300, title, legend=False)


def scan_scatter(res):
    d = res.dropna(subset=["RSI", "1M %"])
    size = d["Vol ×"].fillna(1).clip(0.5, 5) * 9
    fig = go.Figure(go.Scatter(
        x=d["1M %"], y=d["RSI"], mode="markers+text", text=d["Symbol"], textposition="top center",
        textfont=dict(size=9, color=MUTED),
        marker=dict(size=size, color=d["Score"], colorscale=[[0, DOWN], [0.5, GOLD], [1, UP]],
                    showscale=True, colorbar=dict(title="Score", thickness=10), line=dict(width=0)),
        hovertemplate="<b>%{text}</b><br>1M: %{x:.1f}%<br>RSI: %{y:.0f}<extra></extra>"))
    fig.add_hline(y=70, line=dict(color=DOWN, dash="dot", width=0.8))
    fig.add_hline(y=30, line=dict(color=UP, dash="dot", width=0.8))
    fig.add_vline(x=0, line=dict(color=MUTED, dash="dot", width=0.8))
    style(fig, 460, "Momentum map: 1-month return vs RSI (bubble = volume, color = score)", legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title_text="1M return %", showgrid=True, gridcolor=BORDER)
    fig.update_yaxes(title_text="RSI", side="left")
    return fig


def returns_bars(d):
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
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=[UP if v >= 0 else DOWN for v in vals],
                           text=[f"{v:+.1f}%" for v in vals], textposition="outside"))
    return style(fig, 280, "Performance", legend=False)


def rec_chart(rec):
    cols = [("strongBuy", "Strong Buy", "#00A574"), ("buy", "Buy", "#5CD6A8"), ("hold", "Hold", GOLD),
            ("sell", "Sell", "#FF8A80"), ("strongSell", "Strong Sell", DOWN)]
    fig = go.Figure()
    periods = rec["period"] if "period" in rec else rec.index.astype(str)
    for key, name, color in cols:
        if key in rec:
            fig.add_trace(go.Bar(x=periods, y=rec[key], name=name, marker_color=color))
    fig.update_layout(barmode="stack")
    return style(fig, 300, "Analyst recommendations")


def target_chart(price, t):
    fig = go.Figure()
    lo, hi = t.get("low"), t.get("high")
    if lo and hi:
        fig.add_trace(go.Scatter(x=[lo, hi], y=[0, 0], mode="lines", line=dict(color=BORDER, width=10),
                                 showlegend=False, hoverinfo="skip"))
    for key, name, color in (("low", "Low", DOWN), ("mean", "Mean", ACCENT), ("median", "Median", GOLD),
                             ("high", "High", UP)):
        v = t.get(key)
        if v:
            fig.add_trace(go.Scatter(x=[v], y=[0], mode="markers+text", name=name, text=[f"{name}<br>${v:,.0f}"],
                                     textposition="top center", marker=dict(size=14, color=color)))
    if price:
        fig.add_trace(go.Scatter(x=[price], y=[0], mode="markers+text", name="Current", text=[f"Now<br>${price:,.0f}"],
                                 textposition="bottom center", marker=dict(size=16, color=TEXT, symbol="diamond")))
    style(fig, 220, "12-month price targets", legend=False)
    fig.update_yaxes(visible=False, range=[-1, 1])
    fig.update_layout(hovermode="closest")
    return fig


def eps_chart(eh):
    est = next((c for c in eh.columns if "Estimate" in c), None)
    rep = next((c for c in eh.columns if "Reported" in c), None)
    if not est or not rep:
        return None
    e = eh.dropna(subset=[rep]).head(8).iloc[::-1]
    x = [pd.Timestamp(i).strftime("%b %Y") for i in e.index]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=e[est], mode="markers", name="Estimate",
                             marker=dict(size=14, color="rgba(0,0,0,0)", line=dict(color=MUTED, width=2))))
    fig.add_trace(go.Scatter(x=x, y=e[rep], mode="markers", name="Actual",
                             marker=dict(size=12, color=[UP if a >= b else DOWN for a, b in zip(e[rep], e[est])])))
    style(fig, 300, "EPS: estimate vs actual")
    fig.update_xaxes(type="category")
    return fig


def income_chart(inc):
    rows = {"Total Revenue": ACCENT, "Gross Profit": GOLD, "Net Income": UP}
    fig = go.Figure()
    cols = list(inc.columns)[:6][::-1]
    x = [pd.Timestamp(c).strftime("%b %Y") for c in cols]
    for r, color in rows.items():
        if r in inc.index:
            fig.add_trace(go.Bar(x=x, y=[inc.loc[r, c] / 1e9 for c in cols], name=r, marker_color=color))
    fig.update_layout(barmode="group")
    style(fig, 320, "Quarterly results ($B)")
    fig.update_xaxes(type="category")
    return fig
