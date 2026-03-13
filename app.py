import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.optimize import brentq
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import warnings

warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Investment Returns Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="metric-container"] { background: #f7f9fc; border-radius: 8px; padding: 12px; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Helper functions ──────────────────────────────────────────────────────────

def xirr(cashflows: list, dates: list):
    """Money-weighted annualized return (XIRR) via Brent's method."""
    if len(cashflows) != len(dates) or len(cashflows) < 2:
        return None
    origin = dates[0]
    days = [(d - origin).days for d in dates]

    def npv(rate):
        return sum(cf / (1 + rate) ** (d / 365.0) for cf, d in zip(cashflows, days))

    try:
        return brentq(npv, -0.9999, 100.0, maxiter=1000)
    except Exception:
        return None


def cagr(start_val: float, end_val: float, years: float):
    if start_val <= 0 or years <= 0:
        return None
    return (end_val / start_val) ** (1.0 / years) - 1


def color_val(v, fmt=".2f"):
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    color = "#2ca02c" if v >= 0 else "#d62728"
    return f'<span style="color:{color};font-weight:600">{sign}{v:{fmt}}</span>'


# ── Header ────────────────────────────────────────────────────────────────────
st.title("📈 Investment Returns Calculator")
st.caption("Three tools in one: lump-sum return · DCA / XIRR · portfolio P&L and risk")

tab1, tab2, tab3 = st.tabs([
    "💰  Lump Sum Return",
    "📅  DCA / Periodic Investment",
    "📊  Portfolio Analyzer",
])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — LUMP SUM
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Lump Sum Return Calculator")
    st.write("You invested a single amount at one point in time. What are your returns?")

    col_in, col_out = st.columns(2, gap="large")

    with col_in:
        st.markdown("##### Your Investment")
        initial = st.number_input("Initial Investment ($)", min_value=0.01,
                                  value=10_000.0, step=500.0, key="ls_init")
        current = st.number_input("Current Value ($)", min_value=0.01,
                                  value=25_000.0, step=500.0, key="ls_cur")

        period_mode = st.radio("Specify holding period by",
                               ["Number of years", "Start date"], key="ls_pmode")
        if period_mode == "Number of years":
            years_held = st.number_input("Years Held", min_value=0.1, value=10.0,
                                         step=0.5, key="ls_yrs")
            inv_start = date.today() - timedelta(days=int(years_held * 365.25))
        else:
            inv_start = st.date_input("Investment Date", value=date(2015, 1, 1), key="ls_sd")
            years_held = (date.today() - inv_start).days / 365.25

    with col_out:
        st.markdown("##### Results")
        abs_return = current - initial
        abs_pct = (current / initial) - 1
        cagr_val = cagr(initial, current, years_held)

        m1, m2 = st.columns(2)
        m3, m4 = st.columns(2)
        m1.metric("Absolute Return", f"${abs_return:+,.2f}")
        m2.metric("Total Return %", f"{abs_pct * 100:+.2f}%")
        m3.metric("CAGR (annualized)", f"{cagr_val * 100:.2f}%" if cagr_val else "N/A")
        m4.metric("Holding Period", f"{years_held:.1f} yrs")

        if cagr_val and cagr_val > 0:
            doubling = 72 / (cagr_val * 100)
            st.info(f"**Rule of 72:** At this CAGR your money doubles every **{doubling:.1f} years**.")

        # Growth curve
        if cagr_val:
            t = np.linspace(0, years_held, 300)
            vals = initial * (1 + cagr_val) ** t
            chart_dates = [inv_start + timedelta(days=int(x * 365.25)) for x in t]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_dates, y=vals, fill="tozeroy",
                                     fillcolor="rgba(31,119,180,0.1)",
                                     line=dict(color="#1f77b4", width=2),
                                     name="Portfolio Value"))
            fig.add_hline(y=initial, line_dash="dash", line_color="gray",
                          annotation_text=f"Initial: ${initial:,.0f}")
            fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f",
                               height=260, margin=dict(t=10, b=10),
                               showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — DCA / PERIODIC
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("DCA / Periodic Investment Calculator")
    st.write("Regular contributions over time — calculates XIRR (money-weighted annualized return).")

    input_mode = st.radio("How would you like to enter your contributions?",
                          ["Simple (regular fixed contributions)",
                           "Advanced (manual cash flow table)"],
                          key="dca_imode")

    if input_mode.startswith("Simple"):
        col_in2, col_out2 = st.columns(2, gap="large")

        with col_in2:
            st.markdown("##### Contribution Details")
            contrib = st.number_input("Contribution Amount ($)", min_value=1.0,
                                      value=500.0, step=50.0, key="dca_amt")
            freq = st.selectbox("Frequency", ["Monthly", "Quarterly", "Annually"], key="dca_freq")
            n_periods = st.number_input("Number of Contributions", min_value=1,
                                        max_value=600, value=60, step=1, key="dca_n")
            first_date = st.date_input("Date of First Contribution",
                                       value=date(2020, 1, 1), key="dca_fd")
            port_val = st.number_input("Current Portfolio Value ($)", min_value=0.01,
                                       value=42_000.0, step=500.0, key="dca_pv")

        with col_out2:
            st.markdown("##### Results")
            freq_map = {"Monthly": 1, "Quarterly": 3, "Annually": 12}
            months_step = freq_map[freq]

            cf_dates, cf_vals = [], []
            for i in range(int(n_periods)):
                d = first_date + relativedelta(months=i * months_step)
                cf_dates.append(d)
                cf_vals.append(-contrib)

            # Terminal cash flow
            cf_dates.append(date.today())
            cf_vals.append(port_val)

            total_invested = contrib * int(n_periods)
            total_return = port_val - total_invested
            total_return_pct = total_return / total_invested
            xirr_val = xirr(cf_vals, cf_dates)
            years_total = (date.today() - first_date).days / 365.25

            m1, m2 = st.columns(2)
            m3, m4 = st.columns(2)
            m1.metric("Total Invested", f"${total_invested:,.2f}")
            m2.metric("Current Value", f"${port_val:,.2f}")
            m3.metric("Total Return", f"${total_return:+,.2f}",
                      delta=f"{total_return_pct * 100:+.2f}%")
            m4.metric("XIRR", f"{xirr_val * 100:.2f}%" if xirr_val else "N/A")

            if xirr_val:
                beat = xirr_val - 0.10
                sign = "above" if beat >= 0 else "below"
                st.info(
                    f"**XIRR of {xirr_val * 100:.2f}%** — your money-weighted annualized return "
                    f"over {years_total:.1f} years, accounting for contribution timing. "
                    f"That's **{abs(beat) * 100:.1f}% {sign}** the historical S&P 500 average (~10%)."
                )

            # Build chart: contributions stop at last period, but holding extends to today
            cum_inv = [contrib * (i + 1) for i in range(int(n_periods))]
            chart_d = [first_date + relativedelta(months=i * months_step)
                       for i in range(int(n_periods))]

            # Extend the invested line flat from last contribution → today
            last_contrib_date = chart_d[-1]
            today = date.today()
            if today > last_contrib_date:
                chart_d_ext  = chart_d  + [today]
                cum_inv_ext  = cum_inv  + [total_invested]   # flat — no new money added
            else:
                chart_d_ext  = chart_d
                cum_inv_ext  = cum_inv

            fig2 = go.Figure()

            # Shaded area: total amount invested over time
            fig2.add_trace(go.Scatter(
                x=chart_d_ext, y=cum_inv_ext, mode="lines",
                fill="tozeroy", fillcolor="rgba(150,150,150,0.15)",
                line=dict(color="gray", dash="dash", width=2),
                name="Total Invested"
            ))

            # Single marker: current portfolio value at today
            fig2.add_trace(go.Scatter(
                x=[today], y=[port_val],
                mode="markers+text",
                marker=dict(color="#2ca02c", size=12, symbol="diamond"),
                text=[f"  Current Value: ${port_val:,.0f}"],
                textposition="middle right",
                name="Current Value"
            ))

            # Vertical dashed line marking end of contributions
            # (add_shape + add_annotation is more compatible across Plotly versions)
            fig2.add_shape(
                type="line",
                x0=last_contrib_date, x1=last_contrib_date,
                y0=0, y1=1, yref="paper",
                line=dict(color="orange", dash="dot", width=1.5)
            )
            fig2.add_annotation(
                x=last_contrib_date, y=0.97, yref="paper",
                text="Last contribution",
                showarrow=False,
                font=dict(color="orange", size=11),
                xanchor="left", yanchor="top"
            )

            fig2.update_layout(
                yaxis_tickprefix="$", yaxis_tickformat=",.0f",
                height=300, margin=dict(t=20, b=10),
                legend=dict(x=0, y=1)
            )
            st.plotly_chart(fig2, use_container_width=True)

    else:  # Advanced cash flow table
        st.markdown("##### Enter Cash Flows")
        st.caption("Contributions = **negative** (money out of your pocket). "
                   "Last row = today's portfolio value (**positive**).")

        # Template download for advanced mode
        adv_tmpl = pd.DataFrame({
            "Date":   ["2019-01-01", "2020-01-01", "2021-01-01",
                       "2022-01-01", "2023-01-01", "2024-01-01", "2025-03-13"],
            "Amount": [-5000, -5000, -5000, -5000, -5000, -5000, 42000],
        })
        adv_buf = BytesIO()
        with pd.ExcelWriter(adv_buf, engine="openpyxl") as w:
            adv_tmpl.to_excel(w, index=False, sheet_name="CashFlows")
        st.download_button("📥 Download Cash Flow Template",
                           data=adv_buf.getvalue(),
                           file_name="cashflow_template.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="adv_tmpl_dl")

        # File uploader
        adv_upload = st.file_uploader("Upload your cash flow file (Excel or CSV) — or edit the table below",
                                      type=["xlsx", "csv"], key="adv_upload")

        # Populate table from upload if provided, otherwise use defaults
        if adv_upload:
            try:
                if adv_upload.name.endswith(".csv"):
                    uploaded_cf = pd.read_csv(adv_upload)
                else:
                    uploaded_cf = pd.read_excel(adv_upload)
                uploaded_cf.columns = [c.strip().title() for c in uploaded_cf.columns]
                # Normalise: accept "Date"/"date", "Amount"/"amount"/"Cash Flow" etc.
                col_map = {}
                for c in uploaded_cf.columns:
                    if "date" in c.lower():
                        col_map[c] = "Date"
                    elif any(k in c.lower() for k in ["amount", "cash", "flow", "value"]):
                        col_map[c] = "Amount"
                uploaded_cf = uploaded_cf.rename(columns=col_map)[["Date", "Amount"]]
                uploaded_cf["Date"] = pd.to_datetime(uploaded_cf["Date"]).dt.strftime("%Y-%m-%d")
                default_cf = uploaded_cf
                st.success(f"Loaded {len(default_cf)} rows from file.")
            except Exception as e:
                st.warning(f"Could not parse uploaded file: {e}. Using default table.")
                default_cf = adv_tmpl.copy()
                default_cf["Date"] = default_cf["Date"].astype(str)
        else:
            default_cf = adv_tmpl.copy()
            default_cf["Date"] = default_cf["Date"].astype(str)

        edited = st.data_editor(default_cf, num_rows="dynamic", use_container_width=True)

        if st.button("Calculate XIRR", type="primary", key="adv_btn"):
            try:
                edited["Date"] = pd.to_datetime(edited["Date"]).dt.date
                edited = edited.dropna()
                cf_list = edited["Amount"].tolist()
                dt_list = edited["Date"].tolist()

                res = xirr(cf_list, dt_list)
                total_in = abs(sum(x for x in cf_list if x < 0))
                final_v = sum(x for x in cf_list if x > 0)
                total_ret_pct = (final_v - total_in) / total_in if total_in > 0 else 0
                years_adv = (dt_list[-1] - dt_list[0]).days / 365.25

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Invested", f"${total_in:,.2f}")
                c2.metric("Final Value", f"${final_v:,.2f}")
                c3.metric("Total Return", f"${final_v - total_in:+,.2f}",
                          delta=f"{total_ret_pct * 100:+.2f}%")
                c4.metric("XIRR", f"{res * 100:.2f}%" if res else "N/A")

                if res:
                    beat = res - 0.10
                    sign = "above" if beat >= 0 else "below"
                    st.info(
                        f"**XIRR of {res * 100:.2f}%** over {years_adv:.1f} years. "
                        f"That's **{abs(beat) * 100:.1f}% {sign}** the historical S&P 500 average (~10%)."
                    )
            except Exception as e:
                st.error(f"Could not calculate: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — PORTFOLIO ANALYZER
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Portfolio Analyzer")
    st.write("Upload your holdings — live prices are fetched automatically, "
             "and you get full P&L and risk metrics.")

    # Template download
    tmpl = pd.DataFrame({
        "Ticker":   ["AAPL", "MSFT", "GOOGL", "SPY", "NVDA"],
        "Quantity": [10, 15, 5, 20, 8],
        "Avg_Cost": [150.00, 280.00, 2500.00, 400.00, 500.00],
    })
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        tmpl.to_excel(w, index=False, sheet_name="Holdings")
    st.download_button("📥 Download Template (.xlsx)", data=buf.getvalue(),
                       file_name="portfolio_template.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    uploaded = st.file_uploader("Upload your holdings (Excel or CSV)",
                                type=["xlsx", "csv"], key="port_file")

    if uploaded is None:
        st.info("Upload a file to get started. Columns needed: **Ticker · Quantity · Avg_Cost**")
    else:
        try:
            if uploaded.name.endswith(".csv"):
                h = pd.read_csv(uploaded)
            else:
                h = pd.read_excel(uploaded)

            # Normalise column names
            h.columns = [c.strip().replace(" ", "_").title() for c in h.columns]
            required = {"Ticker", "Quantity", "Avg_Cost"}
            if not required.issubset(h.columns):
                st.error(f"Missing columns. Need: {required}. Found: {list(h.columns)}")
                st.stop()

            h["Ticker"] = h["Ticker"].str.upper().str.strip()
            tickers = h["Ticker"].tolist()

            # Fetch live prices — batch download is more reliable than
            # calling fast_info individually (first call often returns None)
            with st.spinner("Fetching live prices…"):
                try:
                    dl = yf.download(tickers, period="2d", progress=False, auto_adjust=True)
                    if isinstance(dl.columns, pd.MultiIndex):
                        close = dl["Close"]
                    else:
                        close = dl[["Close"]]
                        close.columns = tickers
                    last_row = close.dropna(how="all").iloc[-1]
                    live = last_row.to_dict()
                except Exception:
                    live = {tk: None for tk in tickers}

            h["Live_Price"] = h["Ticker"].map(live)
            h["Cost_Basis"]    = h["Quantity"] * h["Avg_Cost"]
            h["Current_Value"] = h["Quantity"] * h["Live_Price"]
            h["PnL"]           = h["Current_Value"] - h["Cost_Basis"]
            h["Return_%"]      = (h["PnL"] / h["Cost_Basis"]) * 100

            total_cost  = h["Cost_Basis"].sum()
            total_val   = h["Current_Value"].sum()
            total_pnl   = total_val - total_cost
            total_ret   = total_pnl / total_cost * 100

            # ── Summary metrics ──
            st.markdown("#### Portfolio Summary")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Cost Basis",  f"${total_cost:,.2f}")
            m2.metric("Current Value",     f"${total_val:,.2f}")
            m3.metric("Total P&L",         f"${total_pnl:+,.2f}",
                      delta=f"{total_ret:+.2f}%")
            m4.metric("Holdings",          str(len(h)))

            # ── Holdings table ──
            st.markdown("#### Holdings Detail")

            def highlight_pnl(val):
                if isinstance(val, (int, float)):
                    return "color: #2ca02c; font-weight:600" if val > 0 \
                        else "color: #d62728; font-weight:600" if val < 0 else ""
                return ""

            disp = h[["Ticker", "Quantity", "Avg_Cost", "Live_Price",
                       "Cost_Basis", "Current_Value", "PnL", "Return_%"]].copy()
            styled = disp.style.format({
                "Avg_Cost":      "${:,.2f}",
                "Live_Price":    "${:,.2f}",
                "Cost_Basis":    "${:,.2f}",
                "Current_Value": "${:,.2f}",
                "PnL":           "${:+,.2f}",
                "Return_%":      "{:+.2f}%",
            }).map(highlight_pnl, subset=["PnL", "Return_%"])
            st.dataframe(styled, use_container_width=True)

            # ── Charts row ──
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Allocation by Current Value")
                fig_pie = px.pie(h, values="Current_Value", names="Ticker",
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                fig_pie.update_layout(height=340, margin=dict(t=20, b=0),
                                      showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                st.markdown("#### P&L by Position")
                colors = ["#2ca02c" if v >= 0 else "#d62728" for v in h["PnL"]]
                fig_bar = go.Figure(go.Bar(x=h["Ticker"], y=h["PnL"],
                                           marker_color=colors,
                                           text=[f"${v:+,.0f}" for v in h["PnL"]],
                                           textposition="outside"))
                fig_bar.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f",
                                      height=340, margin=dict(t=20, b=10),
                                      showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            # ── Risk metrics ──
            st.markdown("---")
            st.markdown("#### Risk Metrics (Based on 1-Year Historical Returns)")

            valid = h[h["Live_Price"].notna()]["Ticker"].tolist()
            if len(valid) == 0:
                st.warning("No valid tickers found for risk analysis.")
            else:
                with st.spinner("Downloading 1-year historical data…"):
                    try:
                        raw = yf.download(valid, period="1y", progress=False, auto_adjust=True)
                        if isinstance(raw.columns, pd.MultiIndex):
                            hist_prices = raw["Close"]
                        else:
                            hist_prices = raw[["Close"]]
                            hist_prices.columns = valid

                        daily_ret = hist_prices.pct_change().dropna()

                        # Portfolio weights by current value
                        wdf = h[h["Ticker"].isin(valid)].set_index("Ticker")["Current_Value"]
                        weights = (wdf / wdf.sum()).reindex(daily_ret.columns).fillna(0)
                        port_ret = daily_ret.dot(weights)

                        ann_vol   = port_ret.std() * np.sqrt(252)
                        ann_ret   = port_ret.mean() * 252
                        sharpe    = ann_ret / ann_vol if ann_vol > 0 else 0
                        cum       = (1 + port_ret).cumprod()
                        max_dd    = ((cum - cum.expanding().max()) / cum.expanding().max()).min()

                        r1, r2, r3, r4 = st.columns(4)
                        r1.metric("1Y Ann. Return",    f"{ann_ret * 100:.2f}%")
                        r2.metric("1Y Ann. Volatility", f"{ann_vol * 100:.2f}%")
                        r3.metric("Sharpe Ratio",      f"{sharpe:.2f}")
                        r4.metric("Max Drawdown (1Y)", f"{max_dd * 100:.2f}%")

                        # Portfolio equity curve
                        st.markdown("#### Portfolio Equity Curve (1 Year, Normalized to $1)")
                        fig_eq = go.Figure()
                        fig_eq.add_trace(go.Scatter(x=cum.index, y=cum.values, mode="lines",
                                                    fill="tozeroy",
                                                    fillcolor="rgba(31,119,180,0.08)",
                                                    line=dict(color="#1f77b4", width=2),
                                                    name="Portfolio"))
                        fig_eq.add_hline(y=1.0, line_dash="dash", line_color="gray")
                        fig_eq.update_layout(yaxis_title="Growth of $1",
                                             height=280, margin=dict(t=10, b=10),
                                             showlegend=False)
                        st.plotly_chart(fig_eq, use_container_width=True)

                        # Correlation matrix
                        if len(valid) > 1:
                            st.markdown("#### Return Correlation Matrix (1 Year)")
                            corr = daily_ret.corr()
                            fig_corr = px.imshow(
                                corr, text_auto=".2f",
                                color_continuous_scale="RdYlGn",
                                zmin=-1, zmax=1,
                            )
                            fig_corr.update_layout(height=420, margin=dict(t=20, b=10))
                            st.plotly_chart(fig_corr, use_container_width=True)

                    except Exception as e:
                        st.warning(f"Could not load historical data for risk metrics: {e}")

        except Exception as e:
            st.error(f"Error reading file: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Data via Yahoo Finance (yfinance). For informational purposes only — not financial advice.")
