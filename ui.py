"""
ui.py - Shared page helpers: page registry / routing, headers, sections, news with affected companies.
"""
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


def affected_chips(tickers, chg):
    return "".join(T.ticker_chip(s, chg.get(s, (None, None))[1]) for s in tickers)


def news_list(items, limit=20, translate=None, tag_key=None):
    """News cards with 'affected companies' chips (green/red by today's move)."""
    items = items[:limit]
    if not items:
        st.info(L("No news available right now.", "لا توجد أخبار متاحة حالياً."))
        return
    translate = is_ar() if translate is None else translate
    titles = [n["title"] for n in items]
    sums = [(n["summary"] or "")[:320] for n in items]
    if translate:
        with st.spinner(L("Translating...", "جاري الترجمة للعربية...")):
            tr = data.translate(titles + sums)
        titles, sums = tr[:len(items)], tr[len(items):]
    tickers = sorted({s for n in items for s in n.get("tickers", [])})
    chg = data.changes(tickers) if tickers else {}
    out = []
    for n, t, s in zip(items, titles, sums):
        chips = affected_chips(n.get("tickers", []), chg)
        out.append(T.news_card(n, t, s, chips, L("Affected companies", "الشركات المتأثرة"), ar=translate,
                               tag=n.get(tag_key) if tag_key else None))
    html('<div class="rtl">' + "".join(out) + "</div>" if translate else "".join(out))


def foot():
    html(f'<div class="foot">A.Alturaifi Pro · {L("Data: Yahoo Finance & FRED, may be delayed. Educational use only, not investment advice.", "البيانات: ياهو فاينانس وFRED وقد تكون متأخرة. للاستخدام التعليمي فقط وليست توصية استثمارية.")}</div>')
