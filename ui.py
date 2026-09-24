"""
ui.py - Shared page helpers: routing, headers, sections, company rows with logos, news with affected companies.
"""
import pandas as pd
import streamlit as st

import data
import theme as T
from i18n import L, is_ar

PAGES = {}   # filled by app.py: key -> st.Page


def goto(key):
    st.switch_page(PAGES[key])


def open_stock(sym):
    st.session_state.symbol = sym.upper()
    goto("stock")


def header(ic, en, ar, sub_en="", sub_ar=""):
    st.markdown(T.page_title(ic, L(en, ar), L(sub_en, sub_ar)), unsafe_allow_html=True)


def sec(ic, en, ar):
    st.markdown(T.sec(ic, L(en, ar)), unsafe_allow_html=True)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def chips(tickers, chg, lg):
    return "".join(T.ticker_chip(s, chg.get(s, (None, None))[1], lg.get(s)) for s in tickers)


def row_list(rows, lg, show_vol=False):
    """rows: DataFrame with Symbol, Name, Price, Chg % (+ optional Rel Vol). Yahoo-style list with logo circles."""
    out = []
    for _, r in rows.iterrows():
        sub = str(r.get("Name") or "")[:28]
        right = f'<div class="px">{T.fmt_price(r["Price"])}'
        if show_vol and pd.notna(r.get("Rel Vol")):
            w = min(100, float(r["Rel Vol"]) / 5 * 100)
            right += f'<div class="meter" title="{r["Rel Vol"]:.1f}×"><span style="width:{w:.0f}%"></span></div>'
        right += "</div>"
        out.append(f'<div class="rw">{T.company(r["Symbol"], sub, lg.get(r["Symbol"]))}{right}{T.pill(r["Chg %"])}</div>')
    return '<div class="rowlist">' + "".join(out) + "</div>"


def news_list(items, limit=20, translate=None, tag_key=None):
    """News cards with 'affected companies' chips (logo + today's move)."""
    items = items[:limit]
    if not items:
        st.info(L("No news available right now.", "لا توجد أخبار متاحة حالياً."))
        return
    translate = is_ar() if translate is None else translate
    titles = [n["title"] for n in items]
    sums = [(n["summary"] or "")[:320] for n in items]
    translated_ok = True
    if translate:
        with st.spinner(L("Translating...", "جاري الترجمة للعربية...")):
            tr = data.translate(titles + sums)
        translated_ok = tr[:len(items)] != titles
        titles, sums = tr[:len(items)], tr[len(items):]
    tickers = sorted({s for n in items for s in n.get("tickers", [])})
    chg = data.changes(tickers) if tickers else {}
    lg = data.logos(tickers) if tickers else {}
    out = []
    for n, t, s in zip(items, titles, sums):
        out.append(T.news_card(n, t, s, chips(n.get("tickers", []), chg, lg), L("Affected companies", "الشركات المتأثرة"),
                               ar=translate and translated_ok, tag=n.get(tag_key) if tag_key else None))
    if translate and not translated_ok:
        st.caption(L("Translation service is busy right now; showing the original English. It will retry automatically.",
                     "خدمة الترجمة مشغولة حالياً؛ نعرض النص الإنجليزي الأصلي وستتم إعادة المحاولة تلقائياً."))
    html("".join(out))


def foot():
    html(f'<div class="foot">A.Alturaifi Pro · {L("Data: Yahoo Finance, FRED & BLS, may be delayed. Educational use only, not investment advice.", "البيانات: ياهو فاينانس وFRED ومكتب إحصاءات العمل وقد تكون متأخرة. للاستخدام التعليمي فقط وليست توصية استثمارية.")}</div>')
