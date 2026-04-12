# Financial Intelligence Dashboard using Python

An advanced financial analytics project that transforms raw financial statements into an **interactive decision-making dashboard**.
This project goes beyond static analysis by combining **financial modeling, forecasting, and scenario simulation** to evaluate a company’s financial health.

## Overview

This solution analyzes key financial areas:

- Working Capital efficiency
- Cash Flow behavior and liquidity
- Capital structure (Debt vs Equity)
- Asset utilization trends
- Forward-looking financial forecasts

It generates a **fully interactive HTML dashboard** used for business insights and strategic decisions.

## Dashboard Preview
![Dashboard Preview](Financial%20Intelligence%20Dashboard.png)

## Key Features

### Financial Analysis
- Working Capital breakdown (Receivables, Inventory, Cash)
- Cash Flow analysis (Operating, Investing, Financing)
- Capital structure evaluation (Debt-to-Equity trends)
- Asset efficiency insights (Depreciation vs Net Block)

### Interactivity 
- Dynamic KPI cards based on selected year
- Full historical trend charts (not filtered by slicers)
- Year-based deep-dive insights

### Scenario Simulation
- Revenue / operating uplift simulation
- Investment stress testing
- Real-time impact on:
  - Free Cash Flow
  - Risk level
  - Financial stability

### Forecasting
- Time series forecasting using Holt’s Exponential Smoothing
- Predictive operating cash flow and free cash flow

### Business Insights
- Automated insight generation
- Decision-focused explanations (not just numbers)

## Tech Stack

- **Python** (Pandas, NumPy)
- **Visualization**: Matplotlib
- **Forecasting**: Exponential Smoothing
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js

## Why Exponential Smoothing (and not other models?)

For this project, I chose Exponential Smoothing mainly because it fits well with the nature of financial data I was working with.

Financial metrics like cash flow and working capital usually follow gradual trends over time, rather than very complex or random patterns. Exponential smoothing handles this really well by giving more importance to recent data while still considering past values.

I did consider other approaches:

**ARIMA** is powerful, but it requires additional steps like making the data stationary and tuning multiple parameters, which adds complexity without much practical benefit here.
**Linear regression** is simple, but it doesn’t capture time-based patterns properly.
ML models like **Random Forest or XGBoost** can handle complex relationships, but for structured financial time series, they felt unnecessary and harder to interpret.
**Deep learning (like LSTM)** is even more complex and typically useful when patterns are highly non-linear, which wasn’t the case in this dataset.
In comparison, Exponential Smoothing is:
- Simple to implement
- Reliable for short-term forecasting
Overall, it provided a good balance between accuracy and practicality

## Output

The project generates:

- Interactive financial dashboard (`financial_report.html`)
- Visual trend analysis
- Forecasted financial metrics
- Business insights for decision-making

## Live Dashboard
 [View Interactive Dashboard](https://matrix36912.github.io/Financial-Intelligence-Dashboard/index.html)

## Business Value

This solution can be used by:
- Finance teams for performance analysis
- Business analysts for decision support
- Leadership for strategic planning
  
It bridges the gap between **raw financial data into actionable insights**

- ## Installation

Clone the repository and install dependencies:
# Install dependencies
pip install -r requirements.txt

# Run the project
python run.py

# Open the dashboard
# Open this file in your browser:
index.html

