# 📈 Investment Returns Calculator

A free, open source Streamlit web app for calculating investment returns and planning ahead. Five tools in one: lump sum return, DCA / periodic contributions, full portfolio analysis with live prices and risk metrics, a goal and retirement projection planner, and a portfolio rebalancing helper.

**[Live App →](https://share.streamlit.io)** *(https://portfolioreturns.streamlit.app/)*

***

## Features

### 💰 Lump Sum Return
Calculate returns for a single investment made at one point in time.
* Absolute return ($) and total return (%)
* CAGR (Compound Annual Growth Rate)
* Rule of 72: how long until your money doubles
* Growth curve chart

### 📅 DCA / Periodic Investment
Calculate returns for regular contributions over time (Dollar Cost Averaging).

**Simple mode**: enter contribution amount, frequency (monthly, quarterly, or annually), number of periods, and current portfolio value.

**Advanced mode**: upload an Excel/CSV file with custom cash flow dates and amounts, or edit the table manually.

* XIRR (money weighted annualized return), accounting for contribution timing
* Benchmark comparison vs. S&P 500 historical average (~10%)
* Cumulative invested vs. current value chart

### 📊 Portfolio Analyzer
Upload your holdings and get live prices, P&L, and risk metrics automatically.

* **Live prices** fetched via Yahoo Finance (yfinance)
* **Per position P&L**: cost basis, current value, gain/loss, return %
* **Portfolio summary**: total invested, current value, total P&L
* **Allocation pie chart** and **P&L bar chart**
* **Risk metrics** (based on 1 year of historical daily returns):
  * Annualized return and volatility
  * Sharpe ratio (assumes 0% risk free rate)
  * Maximum drawdown
  * Portfolio equity curve (normalized to $1)
  * Return correlation matrix across holdings

### 🎯 Goal / Retirement Projection
Project how your savings could grow with regular contributions, and see what it takes to hit a target.

* Future value of a lump sum plus monthly contributions, compounded monthly
* Time horizon by number of years or by a target age
* Inflation adjusted toggle showing real value alongside nominal value (default 3% inflation)
* Optional target goal, solvable either for the required monthly contribution or for the years needed
* Three scenario growth chart (conservative, moderate, aggressive), all editable

### ⚖️ Rebalancing Helper
See how far your portfolio has drifted from target weights, and what it would take to rebalance.

* Automatically reuses the holdings you already uploaded in the Portfolio Analyzer tab, no need to upload twice
* Editable target weight table, defaulting to your current weights
* Warns if target percentages do not sum to 100%
* Full rebalancing plan showing target value, dollar difference, and a buy or sell action per position
* Optional buy only mode: allocate new cash across underweight positions instead of selling anything, which avoids triggering capital gains
* Current vs. target allocation bar chart

***

## How to Use the Portfolio Analyzer

Download the template, fill in your holdings, and upload:

| Ticker | Quantity | Avg_Cost |
|--------|----------|----------|
| AAPL   | 10       | 150.00   |
| MSFT   | 15       | 280.00   |
| SPY    | 20       | 400.00   |

* **Ticker**: stock symbol (e.g. AAPL, MSFT, SPY, BTC-USD)
* **Quantity**: number of shares held
* **Avg_Cost**: your average purchase price per share

***

## How to Use the DCA Cash Flow Template

For the Advanced DCA mode, upload a two column file:

| Date       | Amount  |
|------------|---------|
| 2020-01-01 | -5000   |
| 2021-01-01 | -5000   |
| 2025-03-13 | 42000   |

* **Negative amounts**: money you put in (outflows)
* **Positive amount**: current portfolio value (final row)

***

## How to Use the Rebalancing Helper

If you have already uploaded holdings in the Portfolio Analyzer tab during this session, the Rebalancing Helper picks them up automatically. Otherwise it shows its own uploader using the same template as the Portfolio Analyzer:

| Ticker | Quantity | Avg_Cost |
|--------|----------|----------|
| AAPL   | 10       | 150.00   |
| MSFT   | 15       | 280.00   |
| SPY    | 20       | 400.00   |

Once your holdings are loaded, set a Target % for each position (it defaults to your current weight) and the tab computes a full buy or sell plan. If you would rather add new money than sell anything, enter an amount under "Additional Cash to Invest" and the tool will spread it across your underweight positions only.

***

## Run Locally

```bash
git clone https://github.com/vishnuprabhu93/Portfolio_Returns.git
cd Portfolio_Returns
pip install -r requirements.txt
streamlit run app.py
```

***

## Deploy on Streamlit Community Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo, set **Main file path** to `app.py`
5. Click **Deploy**, you get a public URL in about 2 minutes

***

## Tech Stack

* [Streamlit](https://streamlit.io): UI framework and theming
* [yfinance](https://github.com/ranaroussi/yfinance): Yahoo Finance data
* [pandas](https://pandas.pydata.org) / [numpy](https://numpy.org): data processing
* [scipy](https://scipy.org): XIRR calculation (Brent's method)
* [plotly](https://plotly.com/python/): interactive charts

***

## Disclaimer

Data is sourced from Yahoo Finance via yfinance. This tool is for **informational purposes only** and does not constitute financial or tax advice.
