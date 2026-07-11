import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from io import BytesIO

from calculations import xirr
from theme import COLOR_POSITIVE, COLOR_NEUTRAL_FILL, COLOR_GRAY, COLOR_HIGHLIGHT


def render():
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
                fill="tozeroy", fillcolor=COLOR_NEUTRAL_FILL,
                line=dict(color=COLOR_GRAY, dash="dash", width=2),
                name="Total Invested"
            ))

            # Single marker: current portfolio value at today
            fig2.add_trace(go.Scatter(
                x=[today], y=[port_val],
                mode="markers+text",
                marker=dict(color=COLOR_POSITIVE, size=12, symbol="diamond"),
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
                line=dict(color=COLOR_HIGHLIGHT, dash="dot", width=1.5)
            )
            fig2.add_annotation(
                x=last_contrib_date, y=0.97, yref="paper",
                text="Last contribution",
                showarrow=False,
                font=dict(color=COLOR_HIGHLIGHT, size=11),
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
