"""
i18n.py - Bilingual helper. Use L("English", "عربي") anywhere in the UI.
"""
import streamlit as st


def lang():
    return st.session_state.get("lang", "en")


def is_ar():
    return lang() == "ar"


def L(en, ar):
    return ar if is_ar() else en


# Common labels reused across pages
SIGNAL = {"Buy": ("Buy", "شراء"), "Sell": ("Sell", "بيع"), "Neutral": ("Neutral", "محايد"),
          "Strong Buy": ("Strong Buy", "شراء قوي"), "Strong Sell": ("Strong Sell", "بيع قوي")}


def sig(label):
    en, ar = SIGNAL.get(label, (label, label))
    return L(en, ar)


SECTOR_AR = {
    "Technology": "التقنية", "Communication Services": "الاتصالات", "Consumer Cyclical": "السلع الاستهلاكية الكمالية",
    "Consumer Defensive": "السلع الاستهلاكية الأساسية", "Financial Services": "الخدمات المالية",
    "Healthcare": "الرعاية الصحية", "Industrials": "الصناعة", "Energy": "الطاقة", "Basic Materials": "المواد الأساسية",
    "Real Estate": "العقارات", "Utilities": "المرافق العامة", "Other": "أخرى",
}


def sector_name(s):
    return L(s, SECTOR_AR.get(s, s))


def industry_name(ind):
    from taxonomy import INDUSTRY_AR
    return L(ind, INDUSTRY_AR.get(ind, ind)) if ind else "—"


def theme_name(tk, sk=None):
    from taxonomy import THEMES
    if tk not in THEMES:
        return "—"
    en, ar, _, subs = THEMES[tk]
    if sk is None:
        return L(en, ar)
    sen, sar, _ = subs[sk]
    return L(sen, sar)
