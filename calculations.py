from scipy.optimize import brentq


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
