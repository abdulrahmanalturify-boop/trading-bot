import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ============ إعدادات الصفحة ============
st.set_page_config(page_title="بوت التداول", page_icon="📈", layout="wide")

# نخلي الكلام العربي من اليمين لليسار
st.markdown(
    """
    <style>
    .stMarkdown, .stAlert, h1, h2, h3, [data-testid="stMetricLabel"] {
        direction: rtl; text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📈 بوت تداول تجريبي")
st.markdown("**الفكرة:** إذا صار المتوسط القصير فوق الطويل نشتري، وإذا نزل تحته نبيع.")
st.caption("⚠️ للتعلّم فقط، مو نصيحة استثمارية. النتائج السابقة ما تضمن المستقبل.")


# ============ الإعدادات (القائمة الجانبية) ============
st.sidebar.header("⚙️ الإعدادات")
SYMBOL = st.sidebar.text_input("الرمز", "BTC-USD",
                               help="أمثلة: BTC-USD, ETH-USD, AAPL, 2222.SR").strip().upper()
PERIOD = st.sidebar.selectbox("المدة", ["6mo", "1y", "2y", "5y"], index=2)
SHORT_WINDOW = st.sidebar.slider("المتوسط القصير (أيام)", 5, 100, 20)
LONG_WINDOW = st.sidebar.slider("المتوسط الطويل (أيام)", 10, 250, 50)
START_CAPITAL = st.sidebar.number_input("رأس المال ($)", min_value=100, value=10000, step=1000)
FEE_PERCENT = st.sidebar.number_input("العمولة لكل صفقة (%)", min_value=0.0, value=0.1, step=0.05)
FEE = FEE_PERCENT / 100

if SHORT_WINDOW >= LONG_WINDOW:
    st.error("المتوسط القصير لازم يكون أصغر من الطويل.")
    st.stop()


# ============ تحميل الأسعار ============
@st.cache_data(ttl=3600)  # نحفظ البيانات ساعة عشان ما نحمّلها كل مرة
def load_prices(symbol, period):
    data = yf.download(symbol, period=period, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    if data.empty or "Close" not in data:
        return pd.DataFrame()
    return data[["Close"]].dropna()


# ============ الاستراتيجية والاختبار ============
def run_backtest(data, short_w, long_w, capital, fee):
    data = data.copy()
    data["SMA_short"] = data["Close"].rolling(short_w).mean()
    data["SMA_long"] = data["Close"].rolling(long_w).mean()
    data = data.dropna()

    # 1 = داخل السوق، 0 = خارج السوق
    data["Position"] = (data["SMA_short"] > data["SMA_long"]).astype(int)
    # 1 = شراء، -1 = بيع
    data["Trade"] = data["Position"].diff().fillna(0)

    data["Market_Return"] = data["Close"].pct_change().fillna(0)
    data["Strategy_Return"] = data["Position"].shift(1).fillna(0) * data["Market_Return"]
    data["Strategy_Return"] -= data["Trade"].abs().shift(1).fillna(0) * fee

    data["Bot_Equity"] = capital * (1 + data["Strategy_Return"]).cumprod()
    data["Hold_Equity"] = capital * (1 + data["Market_Return"]).cumprod()
    return data


with st.spinner("جاري تحميل الأسعار..."):
    prices = load_prices(SYMBOL, PERIOD)

if prices.empty:
    st.error(f"ما لقيت بيانات للرمز {SYMBOL}. تأكد إنه مكتوب صح.")
    st.stop()

data = run_backtest(prices, SHORT_WINDOW, LONG_WINDOW, START_CAPITAL, FEE)

if len(data) < 2:
    st.error("البيانات قليلة على هالمتوسطات. اختر مدة أطول أو متوسطات أقصر.")
    st.stop()

buys = data[data["Trade"] == 1]
sells = data[data["Trade"] == -1]


# ============ إشارة اليوم ============
last = data.iloc[-1]
date = data.index[-1].date()

st.subheader(f"🔔 إشارة اليوم ({date})")
if last["Trade"] == 1:
    st.success("🟢 إشارة شراء جديدة")
elif last["Trade"] == -1:
    st.error("🔴 إشارة بيع جديدة")
elif last["Position"] == 1:
    st.info("البوت داخل السوق (المتوسط القصير فوق الطويل)")
else:
    st.warning("البوت خارج السوق (المتوسط القصير تحت الطويل)")


# ============ النتائج ============
bot_final = data["Bot_Equity"].iloc[-1]
hold_final = data["Hold_Equity"].iloc[-1]
peak = data["Bot_Equity"].cummax()
max_drawdown = ((data["Bot_Equity"] - peak) / peak).min() * 100

st.subheader("💰 نتيجة الاختبار")
c1, c2, c3, c4 = st.columns(4)
c1.metric("نتيجة البوت", f"${bot_final:,.0f}", f"{(bot_final / START_CAPITAL - 1) * 100:+.1f}%")
c2.metric("الشراء والاحتفاظ", f"${hold_final:,.0f}", f"{(hold_final / START_CAPITAL - 1) * 100:+.1f}%")
c3.metric("أكبر هبوط للبوت", f"{max_drawdown:.1f}%")
c4.metric("عدد الصفقات", f"{len(buys)} شراء / {len(sells)} بيع")


# ============ الرسومات ============
st.subheader("📊 الرسم البياني")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

ax1.plot(data.index, data["Close"], label="Price", color="gray", alpha=0.6)
ax1.plot(data.index, data["SMA_short"], label=f"SMA {SHORT_WINDOW}")
ax1.plot(data.index, data["SMA_long"], label=f"SMA {LONG_WINDOW}")
ax1.scatter(buys.index, buys["Close"], marker="^", color="green", s=100, label="Buy", zorder=5)
ax1.scatter(sells.index, sells["Close"], marker="v", color="red", s=100, label="Sell", zorder=5)
ax1.set_title(f"{SYMBOL} - Moving Average Crossover")
ax1.legend()

ax2.plot(data.index, data["Bot_Equity"], label="Bot")
ax2.plot(data.index, data["Hold_Equity"], label="Buy & Hold")
ax2.set_title("Portfolio Value ($)")
ax2.legend()

plt.tight_layout()
st.pyplot(fig)


# ============ سجل الصفقات ============
with st.expander("📋 سجل الصفقات"):
    trades = data[data["Trade"] != 0][["Close", "Trade"]].copy()
    trades["العملية"] = trades["Trade"].map({1: "شراء", -1: "بيع"})
    trades = trades.rename(columns={"Close": "السعر"})[["العملية", "السعر"]]
    trades.index = trades.index.date
    st.dataframe(trades.iloc[::-1], use_container_width=True)
