import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

from theme import (
    COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_PRIMARY, COLOR_PRIMARY_FILL_LIGHT,
    COLOR_GRAY, PIE_COLOR_SEQUENCE, CORRELATION_COLOR_SCALE,
)


def render():
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

            st.session_state["holdings_df"] = h

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
                    return f"color: {COLOR_POSITIVE}; font-weight:600" if val > 0 \
                        else f"color: {COLOR_NEGATIVE}; font-weight:600" if val < 0 else ""
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
                                 color_discrete_sequence=PIE_COLOR_SEQUENCE)
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                fig_pie.update_layout(height=340, margin=dict(t=20, b=0),
                                      showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                st.markdown("#### P&L by Position")
                colors = [COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in h["PnL"]]
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
                                                    fillcolor=COLOR_PRIMARY_FILL_LIGHT,
                                                    line=dict(color=COLOR_PRIMARY, width=2),
                                                    name="Portfolio"))
                        fig_eq.add_hline(y=1.0, line_dash="dash", line_color=COLOR_GRAY)
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
                                color_continuous_scale=CORRELATION_COLOR_SCALE,
                                zmin=-1, zmax=1,
                            )
                            fig_corr.update_layout(height=420, margin=dict(t=20, b=10))
                            st.plotly_chart(fig_corr, use_container_width=True)

                    except Exception as e:
                        st.warning(f"Could not load historical data for risk metrics: {e}")

        except Exception as e:
            st.error(f"Error reading file: {e}")
