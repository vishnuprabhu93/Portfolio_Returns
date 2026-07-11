import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

from theme import COLOR_PRIMARY, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_GRAY
from holdings import parse_holdings_upload, with_holdings_metrics


def render():
    st.subheader("Rebalancing Helper")
    st.write("See how far your portfolio has drifted from target weights, and what it would take to rebalance.")

    cached = st.session_state.get("holdings_df")

    if cached is not None and not cached.empty:
        st.caption("Using the holdings you uploaded in the Portfolio Analyzer tab.")
        h = cached[["Ticker", "Current_Value"]].copy()
    else:
        st.info("No holdings loaded yet from Portfolio Analyzer — upload your holdings below.")

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
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="rebal_tmpl_dl")

        uploaded = st.file_uploader("Upload your holdings (Excel or CSV)",
                                    type=["xlsx", "csv"], key="rebal_file")
        if uploaded is None:
            return

        try:
            raw = parse_holdings_upload(uploaded)
            with st.spinner("Fetching live prices…"):
                full = with_holdings_metrics(raw)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

        h = full[["Ticker", "Current_Value"]].copy()

    h = h.dropna(subset=["Current_Value"])
    if h.empty:
        st.warning("No holdings with valid current values to rebalance.")
        return

    total_value = h["Current_Value"].sum()
    h["Current_%"] = h["Current_Value"] / total_value * 100

    st.markdown("##### Set Target Weights")
    st.caption("Defaults to your current weights — edit the Target % column below.")

    edit_df = h[["Ticker", "Current_Value", "Current_%"]].copy()
    edit_df["Target_%"] = edit_df["Current_%"].round(2)

    edited = st.data_editor(
        edit_df,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
            "Current_Value": st.column_config.NumberColumn("Current Value", format="$%.2f", disabled=True),
            "Current_%": st.column_config.NumberColumn("Current %", format="%.2f%%", disabled=True),
            "Target_%": st.column_config.NumberColumn("Target %", format="%.2f%%",
                                                       min_value=0.0, max_value=100.0, step=0.5),
        },
        hide_index=True,
        use_container_width=True,
        key="rebal_editor",
    )

    target_sum = edited["Target_%"].sum()
    if abs(target_sum - 100) > 0.5:
        st.warning(f"Target percentages sum to {target_sum:.2f}%, not 100%. Adjust before relying on the plan below.")

    st.markdown("##### Rebalancing Plan")
    out = edited.copy()
    out["Target_Value"] = total_value * out["Target_%"] / 100
    out["Difference"] = out["Target_Value"] - out["Current_Value"]

    def action_label(diff):
        if diff > 0.5:
            return f"Buy ${diff:,.2f}"
        elif diff < -0.5:
            return f"Sell ${abs(diff):,.2f}"
        return "Hold"

    out["Action"] = out["Difference"].apply(action_label)

    disp = out[["Ticker", "Current_Value", "Current_%", "Target_%",
               "Target_Value", "Difference", "Action"]].copy()

    def highlight_action(val):
        if isinstance(val, str):
            if val.startswith("Buy"):
                return f"color: {COLOR_POSITIVE}; font-weight:600"
            elif val.startswith("Sell"):
                return f"color: {COLOR_NEGATIVE}; font-weight:600"
        return ""

    styled = disp.style.format({
        "Current_Value": "${:,.2f}",
        "Current_%":      "{:.2f}%",
        "Target_%":       "{:.2f}%",
        "Target_Value":   "${:,.2f}",
        "Difference":     "${:+,.2f}",
    }).map(highlight_action, subset=["Action"])
    st.dataframe(styled, use_container_width=True)

    st.caption("Selling to rebalance may trigger capital gains taxes — this isn't tax advice.")

    # ── Buy-only mode with additional cash ──
    st.markdown("##### Invest New Cash Instead of Selling")
    additional_cash = st.number_input("Additional Cash to Invest ($)", min_value=0.0,
                                      value=0.0, step=100.0, key="rebal_cash")
    if additional_cash > 0:
        buy_plan = out[["Ticker"]].copy()
        buy_plan["Underweight"] = (out["Target_Value"] - out["Current_Value"]).clip(lower=0)
        total_underweight = buy_plan["Underweight"].sum()

        if total_underweight > 0:
            buy_plan["Allocation"] = additional_cash * buy_plan["Underweight"] / total_underweight
        else:
            buy_plan["Allocation"] = additional_cash * out["Target_%"] / out["Target_%"].sum()

        st.caption(
            "New cash is allocated across underweight positions in proportion to how far each is "
            "below target — this avoids selling (and the capital gains that can trigger)."
        )
        buy_styled = buy_plan.style.format({"Underweight": "${:,.2f}", "Allocation": "${:,.2f}"})
        st.dataframe(buy_styled, use_container_width=True)

    # ── Bar chart: current % vs target % ──
    st.markdown("##### Current vs. Target Allocation")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=out["Ticker"], y=out["Current_%"], name="Current %", marker_color=COLOR_GRAY))
    fig.add_trace(go.Bar(x=out["Ticker"], y=out["Target_%"], name="Target %", marker_color=COLOR_PRIMARY))
    fig.update_layout(barmode="group", yaxis_ticksuffix="%", height=340,
                      margin=dict(t=10, b=10), legend=dict(x=0, y=1))
    st.plotly_chart(fig, use_container_width=True)
