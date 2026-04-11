import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# ================= LOAD DATA =================
df = pd.read_excel("FS.xlsx", header=None)

# ================= BALANCE SHEET =================
bs_start = df[df[0] == "BALANCE SHEET"].index[0]
bs_df = df.iloc[bs_start:]

bs_df.columns = bs_df.iloc[1]
bs_df = bs_df.iloc[2:]
bs_df = bs_df.rename(columns={bs_df.columns[0]: "Metric"})
bs_df = bs_df[bs_df["Metric"] != "Report Date"]

bs_long = bs_df.melt(id_vars="Metric", var_name="Year", value_name="Value")
bs_long["Year"] = pd.to_datetime(bs_long["Year"]).dt.year

# ================= WORKING CAPITAL =================
receivables = bs_long[bs_long["Metric"] == "Receivables"]
inventory = bs_long[bs_long["Metric"] == "Inventory"]
cash = bs_long[bs_long["Metric"] == "Cash & Bank"]

wc_df = receivables.merge(inventory, on="Year", suffixes=("_Receivables", "_Inventory"))
wc_df = wc_df.merge(cash[["Year", "Value"]], on="Year")
wc_df = wc_df.rename(columns={"Value": "Cash"})

wc_df["Working_Capital"] = (
    wc_df["Value_Receivables"] +
    wc_df["Value_Inventory"] +
    wc_df["Cash"]
)

wc_df = wc_df.sort_values("Year")

for col in ["Value_Receivables", "Value_Inventory", "Cash", "Working_Capital"]:
    wc_df[col] = pd.to_numeric(wc_df[col], errors="coerce")

# ================= WORKING CAPITAL VISUAL =================
fig, ax = plt.subplots(figsize=(10, 5))

ax.stackplot(
    wc_df["Year"],
    wc_df["Value_Receivables"],
    wc_df["Value_Inventory"],
    wc_df["Cash"],
    labels=["Receivables", "Inventory", "Cash"],
    alpha=0.6
)

ax.plot(
    wc_df["Year"],
    wc_df["Working_Capital"],
    marker='o',
    linewidth=2,
    label="Total Working Capital"
)

ax.set_title("Working Capital Composition and Trend")
ax.set_xlabel("Year")
ax.set_ylabel("Value")
ax.legend()
ax.grid(alpha=0.3)

plt.savefig("wc_chart.png")
plt.close()

# ================= CASH FLOW =================
cf_start = df[df[0] == "CASH FLOW:"].index[0]
cf_df = df.iloc[cf_start:]

cf_df.columns = cf_df.iloc[1]
cf_df = cf_df.iloc[2:]
cf_df = cf_df.rename(columns={cf_df.columns[0]: "Metric"})
cf_df = cf_df[cf_df["Metric"] != "Report Date"]

cf_long = cf_df.melt(id_vars="Metric", var_name="Year", value_name="Value")
cf_long["Year"] = pd.to_datetime(cf_long["Year"]).dt.year

op_cf = cf_long[cf_long["Metric"] == "Cash from Operating Activity"]
inv_cf = cf_long[cf_long["Metric"] == "Cash from Investing Activity"]
fin_cf = cf_long[cf_long["Metric"] == "Cash from Financing Activity"]

cf_merged = op_cf.merge(inv_cf, on="Year", suffixes=("_Operating", "_Investing"))
cf_merged = cf_merged.merge(fin_cf[["Year", "Value"]], on="Year")
cf_merged = cf_merged.rename(columns={"Value": "Financing"})

for col in ["Value_Operating", "Value_Investing", "Financing"]:
    cf_merged[col] = pd.to_numeric(cf_merged[col], errors="coerce")

cf_last5 = cf_merged.sort_values("Year").tail(5)
years = cf_last5["Year"].tolist()

fig, ax = plt.subplots(figsize=(10, 5))

bar_width = 0.25
x = list(range(len(years)))

op_vals = cf_last5["Value_Operating"].tolist()
inv_vals = cf_last5["Value_Investing"].tolist()
fin_vals = cf_last5["Financing"].tolist()

# Colors
color_operating = "tab:blue"
color_investing = "tab:orange"
color_financing = "tab:purple"

# ================= BARS =================
ax.bar([i - bar_width for i in x], op_vals, width=bar_width,
       color=color_operating, label="Operating")

ax.bar(x, inv_vals, width=bar_width,
       color=color_investing, label="Investing")

ax.bar([i + bar_width for i in x], fin_vals, width=bar_width,
       color=color_financing, label="Financing")

# ================= FORECAST (HOLT METHOD ONLY CHANGE) =================
def holt_forecast(values, periods=2):
    values = np.array(values, dtype=float)

    model = ExponentialSmoothing(
        values,
        trend='add',
        seasonal=None
    ).fit()

    forecast = model.forecast(periods)
    return forecast.tolist()

forecast_years = [years[-1] + 1, years[-1] + 2]

op_forecast = holt_forecast(op_vals)
inv_forecast = holt_forecast(inv_vals)
fin_forecast = holt_forecast(fin_vals)

# Business control
inv_forecast = [min(inv_forecast[i], op_forecast[i]*0.7) for i in range(2)]
fin_forecast = [max(val, -30000) for val in fin_forecast]

x_forecast = [len(x), len(x) + 1]

# ================= FORECAST LINES =================
ax.plot([x[-1]] + x_forecast, [op_vals[-1]] + op_forecast,
        '--o', color=color_operating, label="Operating Forecast")

ax.plot([x[-1]] + x_forecast, [inv_vals[-1]] + inv_forecast,
        '--o', color=color_investing, label="Investing Forecast")

ax.plot([x[-1]] + x_forecast, [fin_vals[-1]] + fin_forecast,
        '--o', color=color_financing, label="Financing Forecast")

# Axis
years_extended = years + forecast_years
ax.set_xticks(range(len(years_extended)))
ax.set_xticklabels(years_extended)

# Highlight forecast zone
ax.axvspan(len(years)-1, len(years_extended)-1, alpha=0.08)

ax.set_title("Cash Flow Breakdown with Forecast")
ax.set_ylabel("Cash Flow Value")

ax.legend()
ax.grid(alpha=0.3)

plt.savefig("cashflow_chart.png")
plt.close()

# ================= CAPITAL STRUCTURE (SMALLER PIE) =================
equity_share = bs_long[bs_long["Metric"] == "Equity Share Capital"]
reserves = bs_long[bs_long["Metric"] == "Reserves"]
borrowings = bs_long[bs_long["Metric"] == "Borrowings"]

capital_df = equity_share.merge(reserves, on="Year", suffixes=("_Share", "_Reserves"))
capital_df = capital_df.merge(borrowings[["Year", "Value"]], on="Year")
capital_df = capital_df.rename(columns={"Value": "Borrowings"})

capital_df["Value_Share"] = pd.to_numeric(capital_df["Value_Share"], errors="coerce")
capital_df["Value_Reserves"] = pd.to_numeric(capital_df["Value_Reserves"], errors="coerce")
capital_df["Borrowings"] = pd.to_numeric(capital_df["Borrowings"], errors="coerce")

capital_df["Equity"] = capital_df["Value_Share"] + capital_df["Value_Reserves"]

latest = capital_df.sort_values("Year").iloc[-1]

# 🔥 SMALLER + CLEAN PIE
fig, ax = plt.subplots(figsize=(3, 3))  # 👈 reduced size

wedges, texts, autotexts = ax.pie(
    [latest["Equity"], latest["Borrowings"]],
    labels=["Equity", "Debt"],
    autopct='%1.1f%%',
    startangle=90,
    colors=['#4C72B0', '#DD8452'],
    textprops={'fontsize': 8},   # 👈 smaller text
    pctdistance=0.7
)

# Keep circle shape
ax.set_aspect('equal')

# Smaller title
ax.set_title(f"Capital Structure ({int(latest['Year'])})", fontsize=10)

plt.savefig("capital_chart.png", bbox_inches='tight')  # 👈 remove extra white space
plt.close()
# ================= DONE =================
print("All charts generated successfully.")