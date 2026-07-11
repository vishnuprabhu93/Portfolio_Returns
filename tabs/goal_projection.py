import streamlit as st
import numpy as np
import plotly.graph_objects as go

from calculations import future_value_with_contributions, required_monthly_contribution, years_to_reach_goal
from theme import COLOR_PRIMARY, COLOR_ACCENT, COLOR_HIGHLIGHT, COLOR_GRAY


def render():
    st.subheader("Goal / Retirement Projection")
    st.write("Project how your savings could grow with regular contributions, and see what it takes to hit a target.")

    col_in, col_out = st.columns(2, gap="large")

    with col_in:
        st.markdown("##### Your Plan")
        current_savings = st.number_input("Current Savings ($)", min_value=0.0,
                                          value=20_000.0, step=1000.0, key="goal_savings")
        monthly_contrib = st.number_input("Monthly Contribution ($)", min_value=0.0,
                                          value=500.0, step=50.0, key="goal_contrib")
        annual_return = st.number_input("Expected Annual Return (%)", min_value=-20.0, max_value=30.0,
                                        value=8.0, step=0.5, key="goal_return") / 100

        horizon_mode = st.radio("Specify time horizon by",
                                ["Number of years", "Target age"], key="goal_hmode")
        if horizon_mode == "Number of years":
            years = st.number_input("Years to Grow", min_value=1.0, value=25.0,
                                    step=1.0, key="goal_years")
        else:
            current_age = st.number_input("Current Age", min_value=1, max_value=100,
                                          value=35, step=1, key="goal_cage")
            target_age = st.number_input("Target Age", min_value=1, max_value=120,
                                         value=65, step=1, key="goal_tage")
            years = max(target_age - current_age, 0.1)

        inflation_on = st.checkbox("Adjust for inflation", value=True, key="goal_infl_on")
        inflation_rate = 0.0
        if inflation_on:
            inflation_rate = st.number_input("Assumed Inflation (%)", min_value=0.0, max_value=15.0,
                                             value=3.0, step=0.25, key="goal_infl") / 100

        st.markdown("##### Target Goal (optional)")
        goal_on = st.checkbox("Set a target goal", key="goal_target_on")
        target_fv = None
        solve_for = None
        if goal_on:
            target_fv = st.number_input("Target Amount ($)", min_value=0.0,
                                        value=1_000_000.0, step=10_000.0, key="goal_target_amt")
            solve_for = st.radio("Solve for", ["Required monthly contribution", "Years needed"],
                                 key="goal_solve_for")

    with col_out:
        st.markdown("##### Results")
        nominal_fv = future_value_with_contributions(current_savings, monthly_contrib, annual_return, years)
        real_fv = nominal_fv / (1 + inflation_rate) ** years if inflation_on else None
        total_contributed = monthly_contrib * years * 12

        m1, m2 = st.columns(2)
        m3, m4 = st.columns(2)
        m1.metric("Projected Value (Nominal)", f"${nominal_fv:,.2f}")
        m2.metric("Projected Value (Real, Today's $)",
                  f"${real_fv:,.2f}" if inflation_on else "N/A (inflation off)")
        m3.metric("Total Contributed", f"${total_contributed:,.2f}")
        m4.metric("Time Horizon", f"{years:.1f} yrs")

        if goal_on and target_fv:
            if solve_for == "Required monthly contribution":
                req_contrib = required_monthly_contribution(current_savings, target_fv, annual_return, years)
                if req_contrib is None:
                    st.warning("Can't solve for this combination of inputs.")
                elif req_contrib <= 0:
                    st.success(
                        f"**You're already on track** — your current savings alone reach "
                        f"${target_fv:,.0f} in {years:.1f} years at this return."
                    )
                else:
                    st.info(
                        f"**Contribute ${req_contrib:,.2f}/month** to reach your "
                        f"${target_fv:,.0f} goal in {years:.1f} years."
                    )
            else:
                yrs_needed = years_to_reach_goal(current_savings, monthly_contrib, target_fv, annual_return)
                if yrs_needed is None:
                    st.warning("With these inputs, this goal isn't reachable — try a higher "
                              "contribution or return.")
                else:
                    st.info(
                        f"**{yrs_needed:.1f} years** needed to reach your ${target_fv:,.0f} goal "
                        f"at ${monthly_contrib:,.0f}/month."
                    )

        # Scenario chart
        st.markdown("##### Growth Scenarios")
        sc1, sc2, sc3 = st.columns(3)
        cons_pct = sc1.number_input("Conservative (%)", min_value=-20.0, max_value=30.0,
                                    value=5.0, step=0.5, key="goal_cons")
        mod_pct = sc2.number_input("Moderate (%)", min_value=-20.0, max_value=30.0,
                                   value=8.0, step=0.5, key="goal_mod")
        aggr_pct = sc3.number_input("Aggressive (%)", min_value=-20.0, max_value=30.0,
                                    value=11.0, step=0.5, key="goal_aggr")

        t = np.linspace(0, years, 300)
        fig = go.Figure()
        scenario_specs = [
            ("Conservative", cons_pct / 100, COLOR_GRAY),
            ("Moderate", mod_pct / 100, COLOR_PRIMARY),
            ("Aggressive", aggr_pct / 100, COLOR_ACCENT),
        ]
        for label, rate, color in scenario_specs:
            vals = [future_value_with_contributions(current_savings, monthly_contrib, rate, yr) for yr in t]
            fig.add_trace(go.Scatter(x=t, y=vals, mode="lines", name=label,
                                     line=dict(color=color, width=2)))

        if goal_on and target_fv:
            fig.add_hline(y=target_fv, line_dash="dash", line_color=COLOR_HIGHLIGHT,
                          annotation_text=f"Goal: ${target_fv:,.0f}")

        fig.update_layout(xaxis_title="Years", yaxis_tickprefix="$", yaxis_tickformat=",.0f",
                          height=320, margin=dict(t=10, b=10), legend=dict(x=0, y=1))
        st.plotly_chart(fig, use_container_width=True)
