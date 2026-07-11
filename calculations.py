import math

from scipy.optimize import brentq


def xirr(cashflows: list, dates: list):
    """Money weighted annualized return (XIRR) via Brent's method."""
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


def future_value_with_contributions(present_value: float, monthly_contribution: float,
                                     annual_return: float, years: float):
    """FV of a lump sum plus ordinary annuity monthly contributions.

    FV = P(1+r)^n + C * [((1+r)^n - 1) / r], r = annual_return / 12, n = years * 12.
    """
    r = annual_return / 12.0
    n = years * 12.0
    if r == 0:
        return present_value + monthly_contribution * n
    growth = (1 + r) ** n
    return present_value * growth + monthly_contribution * (growth - 1) / r


def required_monthly_contribution(present_value: float, target_fv: float,
                                   annual_return: float, years: float):
    """Monthly contribution needed to reach target_fv in `years`. Closed form, linear in C."""
    r = annual_return / 12.0
    n = years * 12.0
    if n <= 0:
        return None
    if r == 0:
        return (target_fv - present_value) / n
    growth = (1 + r) ** n
    denom = (growth - 1) / r
    if denom == 0:
        return None
    return (target_fv - present_value * growth) / denom


def years_to_reach_goal(present_value: float, monthly_contribution: float,
                         target_fv: float, annual_return: float):
    """Years needed to reach target_fv. Closed form via logarithms, no root finder."""
    if present_value >= target_fv:
        return 0.0
    r = annual_return / 12.0
    if r == 0:
        if monthly_contribution <= 0:
            return None
        n = (target_fv - present_value) / monthly_contribution
        return n / 12.0
    denom = present_value + monthly_contribution / r
    if denom <= 0:
        return None
    x = (target_fv + monthly_contribution / r) / denom
    if x <= 0:
        return None
    n = math.log(x) / math.log(1 + r)
    return n / 12.0 if n > 0 else 0.0
