import streamlit as st
import warnings

from theme import BASE_CSS
from tabs import lump_sum, dca, portfolio_analyzer

warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Investment Returns Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(BASE_CSS, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📈 Investment Returns Calculator")
st.caption("Three tools in one: lump-sum return · DCA / XIRR · portfolio P&L and risk")

tab1, tab2, tab3 = st.tabs([
    "💰  Lump Sum Return",
    "📅  DCA / Periodic Investment",
    "📊  Portfolio Analyzer",
])

with tab1:
    lump_sum.render()

with tab2:
    dca.render()

with tab3:
    portfolio_analyzer.render()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Data via Yahoo Finance (yfinance). For informational purposes only — not financial advice.")
