"""
p_academy.py - Academy (interactive 3-minute courses with quizzes) · Glossary
Course cards are links (?course=<id>) so clicking the image or title opens the course.
"""
import pandas as pd
import streamlit as st

import academy as A
import charts
import data
import ta
import theme as T
import ui
from i18n import L, is_ar

ss = st.session_state
LEVELS = {"all": ("All", "الكل"), "Beginner": ("Beginner", "مبتدئ"), "Essential": ("Essential", "أساسي"),
          "Intermediate": ("Intermediate", "متوسط"), "Advanced": ("Advanced", "متقدم")}
LEVEL_KIND = {"Beginner": "up", "Essential": "gold", "Intermediate": "acc", "Advanced": "vio"}


def _course(cid):
    return next((c for c in A.COURSES if c["id"] == cid), None)


def _card(c, done):
    lvl = c["level"]
    lang = "ar" if is_ar() else "en"
    status = T.badge(L("Completed", "مكتمل"), "up", "check_circle") if done else T.badge(L("Start", "ابدأ"), "neu", "play_circle")
    mins = T.badge(L(str(c["mins"]) + " min", str(c["mins"]) + " دقائق"), "neu", "schedule")
    return (f'<a class="course" href="?course={c["id"]}&lang={lang}" target="_self"><div class="art">{A.course_art(c["art"], c["id"])}'
            f'<div class="play">{T.icon("play_arrow")}</div></div><div class="body"><div class="ttl">{T.esc(L(*c["title"]))}</div>'
            f'<div class="tag">{T.esc(L(*c["tagline"]))}</div><div class="meta">{T.badge(L(*lvl), LEVEL_KIND.get(lvl[0], "neu"), "signal_cellular_alt")}'
            f'{mins}{status}</div></div></a>')


# ---------------------------------------------------------------- interactive blocks
def interactive(key):
    if key == "candle_anatomy":
        ui.html('<div class="card" style="text-align:center">' + A.CANDLE_ANATOMY.format(
            high=L("High", "الأعلى"), low=L("Low", "الأدنى"), open=L("Open", "الافتتاح"), close=L("Close", "الإغلاق"),
            body=L("Body", "الجسم"), wick=L("Wick", "الذيل")) + "</div>")
        return
    if key in ("live_spy", "sr_live", "ma_live", "rsi_live"):
        sym = st.selectbox(L("Try it on a live chart", "جرّبها على رسم مباشر"), ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA"], key=f"ia_{key}")
        df = data.history(sym, "2y")
        if df.empty:
            st.caption(L("Live data unavailable right now.", "البيانات المباشرة غير متاحة حالياً."))
            return
        d = ta.add_all(df)
        cfg = {"live_spy": (d.tail(126), [], []), "sr_live": (d.tail(252), ["Support / Resistance"], []),
               "ma_live": (d, ["SMA 50", "SMA 200"], []), "rsi_live": (d.tail(180), ["SMA 20"], ["RSI", "MACD"])}[key]
        st.plotly_chart(charts.price_chart(cfg[0], "Candles", cfg[1], cfg[2], False, height=460 + 120 * len(cfg[2])), key=f"iac_{key}")
        return
    if key == "position_calc":
        c = st.columns(4)
        acct = c[0].number_input(L("Account ($)", "المحفظة ($)"), 100, 10_000_000, 10000, step=500, key="pc_a")
        risk = c[1].number_input(L("Risk %", "المخاطرة %"), 0.1, 10.0, 1.0, step=0.1, key="pc_r")
        entry = c[2].number_input(L("Entry $", "الدخول $"), 0.5, 100000.0, 50.0, step=0.5, key="pc_e")
        stop = c[3].number_input(L("Stop $", "الوقف $"), 0.1, 100000.0, 48.0, step=0.5, key="pc_s")
        if stop >= entry:
            st.warning(L("Stop must be below entry for a long trade.", "الوقف لازم يكون تحت سعر الدخول في صفقة الشراء."))
            return
        rps = entry - stop
        shares = int(acct * risk / 100 / rps)
        m = st.columns(4)
        m[0].metric(L("Shares to buy", "عدد الأسهم"), f"{shares:,}")
        m[1].metric(L("Position value", "قيمة الصفقة"), f"${shares * entry:,.0f}")
        m[2].metric(L("Max loss", "أقصى خسارة"), f"${shares * rps:,.0f}")
        m[3].metric(L("Target at 2R", "الهدف عند 2R"), f"${entry + 2 * rps:,.2f}")
        return
    if key == "pe_calc":
        c = st.columns(3)
        price = c[0].number_input(L("Share price $", "سعر السهم $"), 1.0, 100000.0, 150.0, step=1.0, key="pe_p")
        eps = c[1].number_input(L("EPS (annual) $", "ربحية السهم السنوية $"), 0.01, 10000.0, 6.0, step=0.1, key="pe_e")
        growth = c[2].number_input(L("Expected growth %", "النمو المتوقع %"), 0.1, 200.0, 15.0, step=1.0, key="pe_g")
        pe = price / eps
        m = st.columns(3)
        m[0].metric("P/E", f"{pe:.1f}")
        m[1].metric("PEG", f"{pe / growth:.2f}")
        m[2].metric(L("Earnings yield", "عائد الأرباح"), f"{eps / price * 100:.2f}%")
        verdict = (L("Looks reasonable relative to growth.", "يبدو معقولاً مقارنة بالنمو.") if pe / growth < 1.5
                   else L("Priced for high expectations.", "مسعّر على توقعات مرتفعة."))
        st.info(verdict, icon=":material/lightbulb:")
        return
    if key == "payoff":
        c = st.columns(4)
        kind = c[0].segmented_control(L("Type", "النوع"), ["call", "put"], default="call", key="po_k",
                                      format_func=lambda k: "Call" if k == "call" else "Put") or "call"
        strike = c[1].slider(L("Strike $", "سعر التنفيذ $"), 50, 150, 100, key="po_s")
        prem = c[2].slider(L("Premium $", "البريميوم $"), 0.5, 15.0, 3.0, step=0.5, key="po_p")
        now = c[3].slider(L("Stock now $", "سعر السهم الآن $"), 50, 150, 100, key="po_n")
        be = strike + prem if kind == "call" else strike - prem
        st.plotly_chart(charts.payoff(kind, float(strike), float(prem), float(now), L("Profit / loss at expiration (1 contract)", "الربح والخسارة عند الانتهاء (عقد واحد)"),
                                      (L("Stock price at expiration", "سعر السهم عند الانتهاء"), L("Profit / loss ($)", "الربح / الخسارة ($)"))), key="po_chart")
        m = st.columns(3)
        m[0].metric(L("Cost (max loss)", "التكلفة (أقصى خسارة)"), f"${prem * 100:,.0f}")
        m[1].metric(L("Breakeven", "نقطة التعادل"), f"${be:,.2f}")
        m[2].metric(L("Max profit", "أقصى ربح"), L("Unlimited", "غير محدود") if kind == "call" else f"${(strike - prem) * 100:,.0f}")
        return
    if key == "macro_table":
        rows = [(("CPI inflation above expected", "التضخم أعلى من المتوقع"), ("Yields up, stocks down (growth hit most)", "العوائد ترتفع والأسهم تنخفض (أسهم النمو الأكثر تضرراً)")),
                (("Jobs much stronger than expected", "وظائف أقوى بكثير من المتوقع"), ("Mixed: strong economy, but fewer rate cuts", "مختلط: اقتصاد قوي لكن خفض فائدة أقل")),
                (("Unemployment jumps", "قفزة في البطالة"), ("Recession fears, defensives outperform", "مخاوف ركود وتفوق القطاعات الدفاعية")),
                (("Fed cuts rates", "الفيدرالي يخفض الفائدة"), ("Usually positive for stocks, weaker dollar", "إيجابي عادة للأسهم وضعف الدولار")),
                (("GDP beats", "الناتج المحلي أفضل من المتوقع"), ("Cyclicals and small caps benefit", "استفادة القطاعات الدورية والشركات الصغيرة"))]
        df = pd.DataFrame([{L("Data surprise", "المفاجأة"): L(*a), L("Typical reaction", "رد الفعل المعتاد"): L(*b)} for a, b in rows])
        st.dataframe(df, hide_index=True)
        return


# ---------------------------------------------------------------- course view
def _course_view(c):
    cid = c["id"]
    n = len(c["sections"])
    step = ss.setdefault(f"step_{cid}", 0)
    if st.button(L("All courses", "كل الدورات"), icon=":material/arrow_back:"):
        st.query_params.clear()
        st.rerun()
    lvl = c["level"]
    mins = T.badge(L(str(c["mins"]) + " min", str(c["mins"]) + " دقائق"), "neu", "schedule")
    lessons = T.badge(L(f"{n} lessons + quiz", f"{n} دروس + اختبار"), "acc", "menu_book")
    ui.html(f'<div class="course" style="pointer-events:none;margin-bottom:12px"><div class="art" style="height:170px">{A.course_art(c["art"], cid + "h")}</div>'
            f'<div class="body"><div class="ttl" style="font-size:1.5rem">{T.esc(L(*c["title"]))}</div><div class="tag">{T.esc(L(*c["tagline"]))}</div>'
            f'<div class="meta">{T.badge(L(*lvl), LEVEL_KIND.get(lvl[0], "neu"), "signal_cellular_alt")}{mins}'
            f'{lessons}</div></div></div>')
    ui.html('<div class="steps">' + "".join(f'<span class="{"on" if i <= step else ""}"></span>' for i in range(n + 1)) + "</div>")
    rtl = " rtl" if is_ar() else ""
    if step < n:
        h_en, h_ar, b_en, b_ar, t_en, t_ar, viz = c["sections"][step]
        ui.html(f'<div class="lesson{rtl}"><div class="muted" style="font-size:.8rem">{L(f"Lesson {step + 1} of {n}", f"الدرس {step + 1} من {n}")}</div>'
                f'<h3>{T.esc(L(h_en, h_ar))}</h3><p>{T.esc(L(b_en, b_ar))}</p>'
                f'<div class="take">{T.icon("lightbulb", T.CYAN)} <b>{L("Key takeaway", "الخلاصة")}:</b> {T.esc(L(t_en, t_ar))}</div></div>')
        if viz:
            ui.sec("touch_app", "Interactive", "تفاعلي")
            interactive(viz)
        a, _, b = st.columns([1, 2, 1])
        if step > 0 and a.button(L("Back", "السابق"), icon=":material/chevron_left:", width="stretch"):
            ss[f"step_{cid}"] = step - 1
            st.rerun()
        if b.button(L("Next", "التالي") if step < n - 1 else L("Take the quiz", "ابدأ الاختبار"), icon=":material/chevron_right:",
                    type="primary", width="stretch"):
            ss[f"step_{cid}"] = step + 1
            st.rerun()
        return
    # ---- quiz
    ui.sec("quiz", "Quick quiz", "اختبار سريع")
    answers = []
    for i, (q_en, q_ar, opts, ans, _, _) in enumerate(c["quiz"]):
        answers.append(st.radio(f"{i + 1}. {L(q_en, q_ar)}", list(range(len(opts))), index=None, key=f"q_{cid}_{i}",
                                format_func=lambda k, o=opts: L(*o[k])))
    a, b = st.columns([1, 1])
    if a.button(L("Back to lessons", "رجوع للدروس"), icon=":material/chevron_left:", width="stretch"):
        ss[f"step_{cid}"] = n - 1
        st.rerun()
    if b.button(L("Check answers", "تحقق من الإجابات"), type="primary", icon=":material/fact_check:", width="stretch"):
        ss[f"checked_{cid}"] = True
    if ss.get(f"checked_{cid}"):
        score = 0
        for i, ((q_en, q_ar, opts, ans, w_en, w_ar), got) in enumerate(zip(c["quiz"], answers)):
            ok = got == ans
            score += ok
            ic, col = ("check_circle", T.UP) if ok else ("cancel", T.DOWN)
            ui.html(f'<div class="check{rtl}">{T.icon(ic, col)}<div><b>{i + 1}. {T.esc(L(*opts[ans]))}</b> '
                    f'<span class="muted">· {T.esc(L(w_en, w_ar))}</span></div></div>')
        total = len(c["quiz"])
        if score >= total - 1:
            ss.setdefault("completed", set()).add(cid)
            st.success(L(f"Great job: {score}/{total}. Course completed!", f"أحسنت: {score}/{total}. أكملت الدورة!"), icon=":material/workspace_premium:")
        else:
            st.warning(L(f"{score}/{total}. Review the lessons and try again.", f"{score}/{total}. راجع الدروس وحاول مرة أخرى."), icon=":material/replay:")
        idx = [x["id"] for x in A.COURSES].index(cid)
        if idx + 1 < len(A.COURSES):
            nxt = A.COURSES[idx + 1]
            ui.html(f'<div style="margin-top:12px">{L("Next course", "الدورة التالية")}:</div>' + '<div class="courses" style="max-width:360px">'
                    + _card(nxt, nxt["id"] in ss.get("completed", set())) + "</div>")


def page_academy():
    cid = st.query_params.get("course")
    c = _course(cid) if cid else None
    if c:
        _course_view(c)
        ui.foot()
        return
    ui.header("school", "Academy", "الأكاديمية",
              "Short interactive courses: about 3 minutes each, with live charts and a quiz. Click any card to start.",
              "دورات قصيرة وتفاعلية: حوالي 3 دقائق لكل دورة، مع رسوم مباشرة واختبار. اضغط على أي بطاقة للبدء.")
    done = ss.get("completed", set())
    a, b = st.columns([2, 1])
    lvl = a.segmented_control(L("Level", "المستوى"), list(LEVELS), default="all", key="ac_lvl",
                              format_func=lambda k: L(*LEVELS[k])) or "all"
    b.metric(L("Completed", "المكتملة"), f"{len(done)}/{len(A.COURSES)}")
    courses = [c for c in A.COURSES if lvl == "all" or c["level"][0] == lvl]
    ui.html('<div class="courses">' + "".join(_card(c, c["id"] in done) for c in courses) + "</div>")
    ui.foot()


def page_glossary():
    ui.header("menu_book", "Glossary", "قاموس المصطلحات",
              "Key investing and trading terms explained simply.", "أهم مصطلحات الاستثمار والتداول بشرح مبسط.")
    q = st.text_input(L("Search a term", "ابحث عن مصطلح"), "", placeholder=L("e.g. RSI, spread, option", "مثال: RSI، السبريد، الخيارات")).strip().lower()
    items = [g for g in A.GLOSSARY if not q or q in " ".join(g).lower()]
    rtl = " rtl" if is_ar() else ""
    ui.html(f'<div class="card{rtl}">' + "".join(
        f'<div class="gl"><b>{T.esc(L(en, ar))}</b> <span class="muted">· {T.esc(ar if not is_ar() else en)}</span>'
        f'<div class="d">{T.esc(L(den, dar))}</div></div>' for en, ar, den, dar in items) + "</div>"
        if items else f'<div class="muted">{L("No matching terms.", "لا توجد مصطلحات مطابقة.")}</div>')
    ui.foot()
