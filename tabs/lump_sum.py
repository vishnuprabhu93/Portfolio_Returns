import streamlit as st
import numpy as np
from datetime import date, timedelta
import plotly.graph_objects as go

from calculations import cagr
from theme import COLOR_PRIMARY, COLOR_PRIMARY_FILL


def render():
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
                                     fillcolor=COLOR_PRIMARY_FILL,
                                     line=dict(color=COLOR_PRIMARY, width=2),
                                     name="Portfolio Value"))
            fig.add_hline(y=initial, line_dash="dash", line_color="gray",
                          annotation_text=f"Initial: ${initial:,.0f}")
            fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f",
                               height=260, margin=dict(t=10, b=10),
                               showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
