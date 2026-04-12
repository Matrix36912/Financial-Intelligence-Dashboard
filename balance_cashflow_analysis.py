import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from matplotlib.ticker import FuncFormatter
from pathlib import Path
import warnings
import json

warnings.filterwarnings("ignore")

INPUT_FILE = "FS.xlsx"
OUTPUT_DIR = Path(".")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

#Helpers
def money_fmt(x, pos=None):
    if pd.isna(x):
        return "0"
    abs_x = abs(float(x))
    if abs_x >= 1_000_000_000:
        return f"{x/1_000_000_000:.1f}B"
    if abs_x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if abs_x >= 1_000:
        return f"{x/1_000:.1f}K"
    return f"{x:.0f}"


def clean_numeric(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("(", "-", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("nan", "", regex=False)
        .str.strip(),
        errors="coerce"
    )


def find_section(df, name):
    matches = df[df[0].astype(str).str.strip().str.upper() == name.strip().upper()].index
    if len(matches) == 0:
        raise ValueError(f"Section '{name}' not found in Excel file.")
    return matches[0]


def extract_section(df, name):
    start = find_section(df, name)
    sec = df.iloc[start:].copy()

    sec.columns = sec.iloc[1]
    sec = sec.iloc[2:].copy()
    sec = sec.rename(columns={sec.columns[0]: "Metric"})
    sec["Metric"] = sec["Metric"].astype(str).str.strip()

    sec = sec[
        sec["Metric"].notna()
        & (sec["Metric"] != "")
        & (sec["Metric"].str.upper() != "REPORT DATE")
    ]

    valid_cols = ["Metric"]
    for c in sec.columns:
        if c == "Metric":
            continue
        try:
            pd.to_datetime(c)
            valid_cols.append(c)
        except Exception:
            pass

    sec = sec[valid_cols]

    long = sec.melt(id_vars="Metric", var_name="Year", value_name="Value")
    long["Year"] = pd.to_datetime(long["Year"], errors="coerce").dt.year
    long["Value"] = clean_numeric(long["Value"])
    long = long.dropna(subset=["Year"])
    long["Year"] = long["Year"].astype(int)

    return long


def get_metric(df, names):
    metric_values = df["Metric"].dropna().astype(str).str.strip().unique()

    for n in names:
        if n in metric_values:
            out = df[df["Metric"] == n][["Year", "Value"]].copy()
            return out.sort_values("Year")

    for n in names:
        for real_name in metric_values:
            if n.lower() in real_name.lower():
                out = df[df["Metric"] == real_name][["Year", "Value"]].copy()
                return out.sort_values("Year")

    raise ValueError(f"Could not find metric. Tried: {names}")


def safe_merge_metric(base_df, metric_df, col_name):
    return base_df.merge(
        metric_df.rename(columns={"Value": col_name}),
        on="Year",
        how="outer"
    )


def holt_forecast(values, periods=2):
    values = np.array(values, dtype=float)
    values = values[~np.isnan(values)]

    if len(values) == 0:
        return [0] * periods

    if len(values) == 1:
        return [float(values[-1])] * periods

    try:
        model = ExponentialSmoothing(
            values,
            trend="add",
            seasonal=None,
            initialization_method="estimated"
        ).fit(optimized=True)
        fc = model.forecast(periods)
        return [float(v) for v in fc]
    except Exception:
        diffs = np.diff(values)
        avg_diff = diffs.mean() if len(diffs) > 0 else 0
        last_val = values[-1]
        return [float(last_val + avg_diff * (i + 1)) for i in range(periods)]


def classify_risk(fcf, net_cf, debt_to_equity):
    if fcf < 0 and net_cf < 0:
        return "High Risk"
    if fcf < 0 or debt_to_equity > 1.5:
        return "Moderate Risk"
    return "Low Risk"


def make_insight_trend(curr, prev, label):
    if pd.isna(prev) or prev == 0:
        return f"{label} is stable based on available historical data."
    pct = ((curr - prev) / abs(prev)) * 100
    if pct > 10:
        return f"{label} increased strongly by {pct:.1f}% versus previous year."
    if pct > 0:
        return f"{label} increased slightly by {pct:.1f}% versus previous year."
    if pct < -10:
        return f"{label} declined sharply by {abs(pct):.1f}% versus previous year."
    if pct < 0:
        return f"{label} declined slightly by {abs(pct):.1f}% versus previous year."
    return f"{label} remained almost flat versus previous year."


# Load Data
df = pd.read_excel(INPUT_FILE, header=None)

bs_long = extract_section(df, "BALANCE SHEET")
cf_long = extract_section(df, "CASH FLOW:")

#Working Capital
receivables = get_metric(bs_long, ["Receivables", "Trade Receivables"])
inventory = get_metric(bs_long, ["Inventory", "Inventories"])
cash = get_metric(bs_long, ["Cash & Bank", "Cash and Bank", "Cash", "Cash & Cash Equivalents"])

wc_df = pd.DataFrame({"Year": sorted(bs_long["Year"].unique())})
wc_df = safe_merge_metric(wc_df, receivables, "Receivables")
wc_df = safe_merge_metric(wc_df, inventory, "Inventory")
wc_df = safe_merge_metric(wc_df, cash, "Cash")
wc_df = wc_df.sort_values("Year")

for c in ["Receivables", "Inventory", "Cash"]:
    wc_df[c] = wc_df[c].fillna(0)

wc_df["Working_Capital"] = wc_df["Receivables"] + wc_df["Inventory"] + wc_df["Cash"]
wc_df["WC_Growth_%"] = wc_df["Working_Capital"].pct_change() * 100
wc_df["Cash_Share_%"] = np.where(
    wc_df["Working_Capital"] != 0,
    wc_df["Cash"] / wc_df["Working_Capital"] * 100,
    0
)

fig, ax1 = plt.subplots(figsize=(12, 6))
years = wc_df["Year"].tolist()

ax1.stackplot(
    years,
    wc_df["Receivables"],
    wc_df["Inventory"],
    wc_df["Cash"],
    labels=["Receivables", "Inventory", "Cash"],
    alpha=0.75
)

ax1.plot(
    years,
    wc_df["Working_Capital"],
    color="#111111",
    marker="o",
    linewidth=2.8,
    label="Total Working Capital"
)

for x, y in zip(years, wc_df["Working_Capital"]):
    ax1.text(x, y, money_fmt(y), fontsize=8, ha="center", va="bottom")

ax1.set_title("Working Capital Composition and Trend", fontsize=14, weight="bold")
ax1.set_xlabel("Year")
ax1.set_ylabel("Value")
ax1.yaxis.set_major_formatter(FuncFormatter(money_fmt))
ax1.grid(alpha=0.25)

ax2 = ax1.twinx()
ax2.plot(
    years,
    wc_df["WC_Growth_%"],
    color="#c0392b",
    marker="s",
    linestyle="--",
    linewidth=2,
    label="WC Growth %"
)
ax2.axhline(0, color="gray", linewidth=1, alpha=0.4)
ax2.set_ylabel("Growth %")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False)

plt.tight_layout()
plt.savefig("wc_chart.png", dpi=220, bbox_inches="tight")
plt.close()

#Cash Flow
op = get_metric(cf_long, ["Cash from Operating Activity", "Cash Flow from Operating Activities"])
inv = get_metric(cf_long, ["Cash from Investing Activity", "Cash Flow from Investing Activities"])
fin = get_metric(cf_long, ["Cash from Financing Activity", "Cash Flow from Financing Activities"])

cf_df = pd.DataFrame({"Year": sorted(cf_long["Year"].unique())})
cf_df = safe_merge_metric(cf_df, op, "Operating")
cf_df = safe_merge_metric(cf_df, inv, "Investing")
cf_df = safe_merge_metric(cf_df, fin, "Financing")
cf_df = cf_df.sort_values("Year")

for c in ["Operating", "Investing", "Financing"]:
    cf_df[c] = cf_df[c].fillna(0)

cf_df["Free_Cash_Flow"] = cf_df["Operating"] + cf_df["Investing"]
cf_df["Net_Cash_Flow"] = cf_df["Operating"] + cf_df["Investing"] + cf_df["Financing"]
cf_df["Operating_Cash_Quality_%"] = np.where(
    cf_df["Operating"] != 0,
    cf_df["Free_Cash_Flow"] / cf_df["Operating"] * 100,
    0
)

cf_last5 = cf_df.tail(5).copy()
years_cf = cf_last5["Year"].tolist()
x = np.arange(len(years_cf))
bar_width = 0.24

op_forecast = holt_forecast(cf_last5["Operating"].tolist(), periods=2)
inv_forecast = holt_forecast(cf_last5["Investing"].tolist(), periods=2)
fin_forecast = holt_forecast(cf_last5["Financing"].tolist(), periods=2)


inv_forecast = [min(inv_forecast[i], op_forecast[i] * 0.75) for i in range(2)]
fin_floor = -0.8 * max([abs(v) for v in cf_last5["Operating"].tolist()] + [1])
fin_forecast = [max(v, fin_floor) for v in fin_forecast]
fcf_forecast = [op_forecast[i] + inv_forecast[i] for i in range(2)]

forecast_years = [years_cf[-1] + 1, years_cf[-1] + 2]
x_forecast = np.arange(len(years_cf), len(years_cf) + 2)

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(x - bar_width, cf_last5["Operating"], width=bar_width, label="Operating", alpha=0.9)
ax.bar(x, cf_last5["Investing"], width=bar_width, label="Investing", alpha=0.9)
ax.bar(x + bar_width, cf_last5["Financing"], width=bar_width, label="Financing", alpha=0.9)

ax.plot(x, cf_last5["Free_Cash_Flow"], color="#111111", marker="o", linewidth=2.6, label="Free Cash Flow")

ax.plot([x[-1]] + x_forecast.tolist(), [cf_last5["Operating"].iloc[-1]] + op_forecast, "--o", linewidth=2, label="Operating Forecast")
ax.plot([x[-1]] + x_forecast.tolist(), [cf_last5["Investing"].iloc[-1]] + inv_forecast, "--o", linewidth=2, label="Investing Forecast")
ax.plot([x[-1]] + x_forecast.tolist(), [cf_last5["Financing"].iloc[-1]] + fin_forecast, "--o", linewidth=2, label="Financing Forecast")
ax.plot([x[-1]] + x_forecast.tolist(), [cf_last5["Free_Cash_Flow"].iloc[-1]] + fcf_forecast, "--o", linewidth=2.5, color="#c0392b", label="FCF Forecast")

op_upper = [v * 1.10 for v in op_forecast]
op_lower = [v * 0.90 for v in op_forecast]
ax.fill_between(x_forecast, op_lower, op_upper, alpha=0.12, label="Operating Forecast Band")

all_years_cf = years_cf + forecast_years
ax.set_xticks(np.arange(len(all_years_cf)))
ax.set_xticklabels(all_years_cf)
ax.axvspan(len(years_cf) - 0.5, len(all_years_cf) - 0.5, alpha=0.08)

ax.axhline(0, color="gray", linewidth=1)
ax.set_title("Cash Flow Breakdown with Forecast", fontsize=14, weight="bold")
ax.set_ylabel("Cash Flow Value")
ax.yaxis.set_major_formatter(FuncFormatter(money_fmt))
ax.grid(axis="y", alpha=0.25)
ax.legend(loc="best", frameon=False, ncol=2)

plt.tight_layout()
plt.savefig("cashflow_chart.png", dpi=220, bbox_inches="tight")
plt.close()

#Capital Structure
equity_share = get_metric(bs_long, ["Equity Share Capital", "Share Capital"])
reserves = get_metric(bs_long, ["Reserves", "Other Equity", "Reserves and Surplus"])
borrowings = get_metric(bs_long, ["Borrowings", "Total Borrowings", "Debt"])

cap_df = pd.DataFrame({"Year": sorted(bs_long["Year"].unique())})
cap_df = safe_merge_metric(cap_df, equity_share, "Share_Capital")
cap_df = safe_merge_metric(cap_df, reserves, "Reserves")
cap_df = safe_merge_metric(cap_df, borrowings, "Borrowings")
cap_df = cap_df.sort_values("Year")

for c in ["Share_Capital", "Reserves", "Borrowings"]:
    cap_df[c] = cap_df[c].fillna(0)

cap_df["Equity"] = cap_df["Share_Capital"] + cap_df["Reserves"]
cap_df["Debt_to_Equity"] = np.where(cap_df["Equity"] != 0, cap_df["Borrowings"] / cap_df["Equity"], 0)

latest_cap = cap_df.iloc[-1]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1, 1.25]})

sizes = [latest_cap["Equity"], latest_cap["Borrowings"]]
labels = ["Equity", "Debt"]

ax1.pie(
    sizes,
    labels=labels,
    autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
    startangle=90,
    wedgeprops={"width": 0.45, "edgecolor": "white"},
    pctdistance=0.78,
    textprops={"fontsize": 9}
)
centre_circle = plt.Circle((0, 0), 0.45, fc="white")
ax1.add_artist(centre_circle)
ax1.text(0, 0.05, "D/E Ratio", ha="center", va="center", fontsize=10, color="gray")
ax1.text(0, -0.08, f"{latest_cap['Debt_to_Equity']:.2f}", ha="center", va="center", fontsize=14, weight="bold")
ax1.set_title(f"Capital Structure ({int(latest_cap['Year'])})", fontsize=12, weight="bold")

ax2.plot(cap_df["Year"], cap_df["Equity"], marker="o", linewidth=2.5, label="Equity")
ax2.plot(cap_df["Year"], cap_df["Borrowings"], marker="o", linewidth=2.5, label="Debt")
ax2.set_title("Capital Trend Over Time", fontsize=12, weight="bold")
ax2.set_xlabel("Year")
ax2.set_ylabel("Value")
ax2.yaxis.set_major_formatter(FuncFormatter(money_fmt))
ax2.grid(alpha=0.25)
ax2.legend(frameon=False)

plt.tight_layout()
plt.savefig("capital_chart.png", dpi=220, bbox_inches="tight")
plt.close()

#Asset Efficiency
net_block = get_metric(bs_long, [
    "Net Block",
    "Net Fixed Assets",
    "Property Plant & Equipment",
    "Property, Plant and Equipment"
])

dep_candidates = bs_long[bs_long["Metric"].str.contains("depreciation|amort", case=False, na=False)]

if not dep_candidates.empty:
    depreciation = dep_candidates.groupby("Year")["Value"].sum().reset_index()
else:
    net_block_temp = net_block.sort_values("Year").copy()
    net_block_temp["Value"] = net_block_temp["Value"].fillna(0)
    net_block_temp["Depreciation"] = net_block_temp["Value"].diff().abs()
    depreciation = net_block_temp[["Year", "Depreciation"]].copy()

asset_df = pd.DataFrame({"Year": sorted(bs_long["Year"].unique())})
asset_df = asset_df.merge(net_block.rename(columns={"Value": "Net_Block"}), on="Year", how="left")
asset_df = asset_df.merge(depreciation.rename(columns={"Value": "Depreciation"}), on="Year", how="left")
asset_df = asset_df.sort_values("Year")

asset_df["Net_Block"] = asset_df["Net_Block"].fillna(0)
asset_df["Depreciation"] = asset_df["Depreciation"].fillna(0)
asset_df["Asset_Utilization_Proxy_%"] = np.where(
    asset_df["Net_Block"] != 0,
    asset_df["Depreciation"].abs() / asset_df["Net_Block"] * 100,
    0
)

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.bar(asset_df["Year"] - 0.15, asset_df["Net_Block"], width=0.3, label="Net Block", alpha=0.85)
ax1.bar(asset_df["Year"] + 0.15, asset_df["Depreciation"], width=0.3, label="Depreciation", alpha=0.85)

ax1.set_title("Asset Efficiency and Utilization Trend", fontsize=14, weight="bold")
ax1.set_xlabel("Year")
ax1.set_ylabel("Value")
ax1.yaxis.set_major_formatter(FuncFormatter(money_fmt))
ax1.grid(axis="y", alpha=0.25)

ax2 = ax1.twinx()
ax2.plot(
    asset_df["Year"],
    asset_df["Asset_Utilization_Proxy_%"],
    marker="o",
    linestyle="--",
    linewidth=2.2,
    color="#c0392b",
    label="Depreciation / Net Block %"
)
ax2.set_ylabel("Utilization Proxy %")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=False)

plt.tight_layout()
plt.savefig("asset_chart.png", dpi=220, bbox_inches="tight")
plt.close()

#Summary
latest_wc = wc_df.iloc[-1]
prev_wc = wc_df.iloc[-2] if len(wc_df) > 1 else latest_wc

latest_cf = cf_df.iloc[-1]
prev_cf = cf_df.iloc[-2] if len(cf_df) > 1 else latest_cf

latest_asset = asset_df.iloc[-1]
latest_year = int(max(wc_df["Year"].max(), cf_df["Year"].max(), cap_df["Year"].max(), asset_df["Year"].max()))

latest_risk = classify_risk(
    latest_cf["Free_Cash_Flow"],
    latest_cf["Net_Cash_Flow"],
    latest_cap["Debt_to_Equity"]
)

wc_insight = make_insight_trend(latest_wc["Working_Capital"], prev_wc["Working_Capital"], "Working capital")
fcf_insight = make_insight_trend(latest_cf["Free_Cash_Flow"], prev_cf["Free_Cash_Flow"], "Free cash flow")

if latest_cap["Debt_to_Equity"] < 0.5:
    cap_insight = f"The company has a conservative capital structure with low leverage. Debt-to-equity is {latest_cap['Debt_to_Equity']:.2f}."
elif latest_cap["Debt_to_Equity"] < 1.5:
    cap_insight = f"The company has a balanced capital structure. Debt-to-equity is {latest_cap['Debt_to_Equity']:.2f}."
else:
    cap_insight = f"The company is relatively debt-heavy. Debt-to-equity is {latest_cap['Debt_to_Equity']:.2f}."

asset_insight = f"Asset utilization proxy is {latest_asset['Asset_Utilization_Proxy_%']:.2f}%, indicating how depreciation intensity compares against asset base."

summary_df = pd.DataFrame([{
    "Latest_Year": latest_year,
    "Working_Capital": round(float(latest_wc["Working_Capital"]), 2),
    "Working_Capital_Growth_%": round(float(latest_wc["WC_Growth_%"]) if pd.notna(latest_wc["WC_Growth_%"]) else 0, 2),
    "Free_Cash_Flow": round(float(latest_cf["Free_Cash_Flow"]), 2),
    "Net_Cash_Flow": round(float(latest_cf["Net_Cash_Flow"]), 2),
    "Risk_Level": latest_risk,
    "Debt_to_Equity": round(float(latest_cap["Debt_to_Equity"]), 2),
    "Asset_Utilization_Proxy_%": round(float(latest_asset["Asset_Utilization_Proxy_%"]), 2),
    "WC_Insight": wc_insight,
    "CF_Insight": fcf_insight,
    "Capital_Insight": cap_insight,
    "Asset_Insight": asset_insight,
    "Forecast_Operating_Y1": round(float(op_forecast[0]), 2),
    "Forecast_Operating_Y2": round(float(op_forecast[1]), 2),
    "Forecast_FCF_Y1": round(float(fcf_forecast[0]), 2),
    "Forecast_FCF_Y2": round(float(fcf_forecast[1]), 2),
}])

summary_df.to_csv("financial_summary.csv", index=False)

interactive_data = {
    "years": [int(y) for y in wc_df["Year"].tolist()],
    "workingCapital": [float(v) if pd.notna(v) else 0 for v in wc_df["Working_Capital"].tolist()],
    "wcGrowth": [float(v) if pd.notna(v) else 0 for v in wc_df["WC_Growth_%"].fillna(0).tolist()],
    "cashShare": [float(v) if pd.notna(v) else 0 for v in wc_df["Cash_Share_%"].fillna(0).tolist()],
    "operating": [float(v) if pd.notna(v) else 0 for v in cf_df["Operating"].tolist()],
    "investing": [float(v) if pd.notna(v) else 0 for v in cf_df["Investing"].tolist()],
    "financing": [float(v) if pd.notna(v) else 0 for v in cf_df["Financing"].tolist()],
    "fcf": [float(v) if pd.notna(v) else 0 for v in cf_df["Free_Cash_Flow"].tolist()],
    "netCashFlow": [float(v) if pd.notna(v) else 0 for v in cf_df["Net_Cash_Flow"].tolist()],
    "equity": [float(v) if pd.notna(v) else 0 for v in cap_df["Equity"].tolist()],
    "debt": [float(v) if pd.notna(v) else 0 for v in cap_df["Borrowings"].tolist()],
    "deRatio": [float(v) if pd.notna(v) else 0 for v in cap_df["Debt_to_Equity"].tolist()],
    "netBlock": [float(v) if pd.notna(v) else 0 for v in asset_df["Net_Block"].tolist()],
    "depreciation": [float(v) if pd.notna(v) else 0 for v in asset_df["Depreciation"].tolist()],
    "assetUtilization": [float(v) if pd.notna(v) else 0 for v in asset_df["Asset_Utilization_Proxy_%"].tolist()],
    "forecastYears": forecast_years,
    "forecastOperating": op_forecast,
    "forecastFCF": fcf_forecast
}

with open("interactive_data.json", "w", encoding="utf-8") as f:
    json.dump(interactive_data, f, indent=2)

print("Analysis complete")
print("Generated files:")
print("- wc_chart.png")
print("- cashflow_chart.png")
print("- capital_chart.png")
print("- asset_chart.png")
print("- financial_summary.csv")
print("- interactive_data.json")