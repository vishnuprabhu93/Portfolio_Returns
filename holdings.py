import pandas as pd
import yfinance as yf


def parse_holdings_upload(uploaded_file) -> pd.DataFrame:
    """Read + normalize an uploaded Ticker/Quantity/Avg_Cost file."""
    if uploaded_file.name.endswith(".csv"):
        h = pd.read_csv(uploaded_file)
    else:
        h = pd.read_excel(uploaded_file)

    h.columns = [c.strip().replace(" ", "_").title() for c in h.columns]
    required = {"Ticker", "Quantity", "Avg_Cost"}
    if not required.issubset(h.columns):
        raise ValueError(f"Missing columns. Need: {required}. Found: {list(h.columns)}")

    h["Ticker"] = h["Ticker"].str.upper().str.strip()
    return h


def fetch_live_prices(tickers: list) -> dict:
    """Batch fetch latest close price per ticker via yfinance."""
    try:
        dl = yf.download(tickers, period="2d", progress=False, auto_adjust=True)
        if isinstance(dl.columns, pd.MultiIndex):
            close = dl["Close"]
        else:
            close = dl[["Close"]]
            close.columns = tickers
        last_row = close.dropna(how="all").iloc[-1]
        return last_row.to_dict()
    except Exception:
        return {tk: None for tk in tickers}


def with_holdings_metrics(h: pd.DataFrame) -> pd.DataFrame:
    """Add Live_Price, Cost_Basis, Current_Value, PnL, Return_% columns (fetches live prices)."""
    tickers = h["Ticker"].tolist()
    live = fetch_live_prices(tickers)
    h = h.copy()
    h["Live_Price"] = h["Ticker"].map(live)
    h["Cost_Basis"] = h["Quantity"] * h["Avg_Cost"]
    h["Current_Value"] = h["Quantity"] * h["Live_Price"]
    h["PnL"] = h["Current_Value"] - h["Cost_Basis"]
    h["Return_%"] = (h["PnL"] / h["Cost_Basis"]) * 100
    return h
