import json
import pandas as pd
import balance_cashflow_analysis as analysis  

# Load Data
summary = pd.read_csv("financial_summary.csv").iloc[0]
with open("interactive_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def fmt_value(v):
    try:
        v = float(v)
    except Exception:
        return str(v)
    abs_v = abs(v)
    if abs_v >= 1_000_000_000:
        return f"{v/1_000_000_000:.2f}B"
    if abs_v >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if abs_v >= 1_000:
        return f"{v/1_000:.2f}K"
    return f"{v:.2f}"

wc_value = fmt_value(summary["Working_Capital"])
fcf_value = fmt_value(summary["Free_Cash_Flow"])
de_value = f'{float(summary["Debt_to_Equity"]):.2f}'
asset_value = f'{float(summary["Asset_Utilization_Proxy_%"]):.2f}%'
wc_growth = f'{float(summary["Working_Capital_Growth_%"]):.2f}%'
risk = str(summary["Risk_Level"])
latest_year = int(summary["Latest_Year"])
data_json = json.dumps(data)

#HTML
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Financial Intelligence Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    * {{
        box-sizing: border-box;
    }}
    body {{
        margin: 0;
        font-family: "Segoe UI", Arial, sans-serif;
        background: #f4f7fb;
        color: #1f2937;
    }}
    .topbar {{
        background: linear-gradient(135deg, #0f172a, #1e3a8a);
        color: white;
        padding: 28px 36px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }}
    .topbar h1 {{
        margin: 0;
        font-size: 30px;
        font-weight: 700;
    }}
    .topbar p {{
        margin: 6px 0 0 0;
        color: #dbeafe;
        font-size: 14px;
    }}
    .container {{
        padding: 24px;
        max-width: 1500px;
        margin: auto;
    }}
    .controls {{
        display: flex;
        gap: 16px;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 20px;
        background: white;
        padding: 16px 18px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }}
    .controls label {{
        font-weight: 600;
        font-size: 14px;
    }}
    .controls select, .controls input {{
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid #d1d5db;
        font-size: 14px;
        background: #fff;
    }}
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 18px;
        margin-bottom: 24px;
    }}
    .kpi {{
        border-radius: 18px;
        padding: 22px;
        color: white;
        min-height: 120px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.12);
        position: relative;
        overflow: hidden;
    }}
    .kpi::after {{
        content: "";
        position: absolute;
        width: 120px;
        height: 120px;
        right: -30px;
        top: -30px;
        border-radius: 50%;
        background: rgba(255,255,255,0.12);
    }}
    .kpi h2 {{
        margin: 10px 0 0 0;
        font-size: 28px;
        font-weight: 700;
    }}
    .kpi p {{
        margin: 0;
        opacity: 0.95;
        font-size: 14px;
    }}
    .k1 {{ background: linear-gradient(135deg, #2563eb, #06b6d4); }}
    .k2 {{ background: linear-gradient(135deg, #059669, #34d399); }}
    .k3 {{ background: linear-gradient(135deg, #dc2626, #f59e0b); }}
    .k4 {{ background: linear-gradient(135deg, #7c3aed, #a78bfa); }}
    .k5 {{ background: linear-gradient(135deg, #0f766e, #2dd4bf); }}
    .grid-2 {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
    }}
    .grid-3 {{
        display: grid;
        grid-template-columns: 1.2fr 1fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
    }}
    .card {{
        background: white;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }}
    .card h3 {{
        margin: 0 0 12px 0;
        font-size: 18px;
        color: #0f172a;
    }}
    .card p {{
        font-size: 14px;
        color: #475569;
        line-height: 1.6;
    }}
    .chart-box {{
        position: relative;
        height: 340px;
    }}
    .summary-box {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: 12px;
    }}
    .mini-stat {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 12px;
        border-radius: 12px;
    }}
    .mini-stat .label {{
        font-size: 12px;
        color: #64748b;
        margin-bottom: 4px;
    }}
    .mini-stat .value {{
        font-size: 18px;
        font-weight: 700;
        color: #0f172a;
    }}
    .insight-list {{
        margin: 0;
        padding-left: 18px;
        color: #475569;
        line-height: 1.8;
    }}
    .risk-badge {{
        display: inline-block;
        padding: 8px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 13px;
        margin-top: 6px;
    }}
    .risk-low {{
        background: #dcfce7;
        color: #166534;
    }}
    .risk-moderate {{
        background: #fef3c7;
        color: #92400e;
    }}
    .risk-high {{
        background: #fee2e2;
        color: #991b1b;
    }}
    .forecast-box {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 14px;
    }}
    .forecast-item {{
        background: #eff6ff;
        border: 1px solid #dbeafe;
        padding: 14px;
        border-radius: 12px;
    }}
    .forecast-item .t {{
        font-size: 12px;
        color: #475569;
    }}
    .forecast-item .v {{
        font-size: 18px;
        font-weight: 700;
        color: #1d4ed8;
        margin-top: 4px;
    }}
    .img-card img {{
        width: 100%;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
    }}
    .footer-note {{
        text-align: center;
        font-size: 12px;
        color: #64748b;
        margin-top: 20px;
        padding-bottom: 20px;
    }}
    @media (max-width: 1200px) {{
        .kpi-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .grid-2, .grid-3 {{
            grid-template-columns: 1fr;
        }}
        .forecast-box {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}
    @media (max-width: 700px) {{
        .kpi-grid {{
            grid-template-columns: 1fr;
        }}
        .forecast-box {{
            grid-template-columns: 1fr;
        }}
        .summary-box {{
            grid-template-columns: 1fr;
        }}
    }}
</style>
</head>
<body>
<div class="topbar">
    <div>
        <h1>Financial Intelligence Dashboard</h1>
        <p>Advanced financial health, cash flow, capital structure, asset efficiency, forecasting, and scenario simulation</p>
    </div>
    <div>
        <p><strong>Latest Year:</strong> {latest_year}</p>
    </div>
</div>
<div class="container">
    <div class="controls">
        <div>
            <label for="scenarioRevenue">Revenue / Operating Uplift %</label><br>
            <input type="range" id="scenarioRevenue" min="-20" max="30" value="0" step="1" oninput="updateScenario()">
            <span id="scenarioRevenueValue">0%</span>
        </div>
        <div>
            <label for="scenarioExpense">Investment Stress %</label><br>
            <input type="range" id="scenarioExpense" min="-20" max="30" value="0" step="1" oninput="updateScenario()">
            <span id="scenarioExpenseValue">0%</span>
        </div>
        <div>
            <label for="yearSelect">Focus Year</label><br>
            <select id="yearSelect" onchange="updateYearInsights()"></select>
        </div>
    </div>
    <div class="kpi-grid">
        <div class="kpi k1">
            <p>Working Capital</p>
            <h2 id="kpiWC">{wc_value}</h2>
            <p id="kpiWCGrowthText">Growth: {wc_growth}</p>
        </div>
        <div class="kpi k2">
            <p>Free Cash Flow</p>
            <h2 id="kpiFCF">{fcf_value}</h2>
            <p>Liquidity strength indicator</p>
        </div>
        <div class="kpi k3">
            <p>Risk Level</p>
            <h2 id="kpiRisk">{risk}</h2>
            <p>Based on cash flow and leverage</p>
        </div>
        <div class="kpi k4">
            <p>Debt to Equity</p>
            <h2 id="kpiDE">{de_value}</h2>
            <p>Capital structure balance</p>
        </div>
        <div class="kpi k5">
            <p>Asset Utilization</p>
            <h2 id="kpiAsset">{asset_value}</h2>
            <p>Depreciation intensity proxy</p>
        </div>
    </div>
    <div class="grid-2">
        <div class="card">
            <h3>Working Capital & Growth</h3>
            <div class="chart-box"><canvas id="wcChart"></canvas></div>
            <div class="summary-box">
                <div class="mini-stat">
                    <div class="label">Selected Year WC</div>
                    <div class="value" id="selectedWC">-</div>
                </div>
                <div class="mini-stat">
                    <div class="label">Selected Year WC Growth</div>
                    <div class="value" id="selectedWCGrowth">-</div>
                </div>
            </div>
        </div>
        <div class="card">
            <h3>Cash Flow Breakdown</h3>
            <div class="chart-box"><canvas id="cashChart"></canvas></div>
            <div class="summary-box">
                <div class="mini-stat">
                    <div class="label">Selected Year FCF</div>
                    <div class="value" id="selectedFCF">-</div>
                </div>
                <div class="mini-stat">
                    <div class="label">Selected Year Net Cash Flow</div>
                    <div class="value" id="selectedNetCF">-</div>
                </div>
            </div>
        </div>
    </div>
    <div class="grid-3">
        <div class="card">
            <h3>Scenario Simulator</h3>
            <p>
                Adjust operating uplift and investment stress to simulate how the business could behave under better or worse financial conditions.
            </p>
            <div class="summary-box">
                <div class="mini-stat">
                    <div class="label">Scenario Operating Cash</div>
                    <div class="value" id="scenarioOperating">-</div>
                </div>
                <div class="mini-stat">
                    <div class="label">Scenario Free Cash Flow</div>
                    <div class="value" id="scenarioFCF">-</div>
                </div>
                <div class="mini-stat">
                    <div class="label">Scenario Risk</div>
                    <div class="value" id="scenarioRisk">-</div>
                </div>
                <div class="mini-stat">
                    <div class="label">Scenario Change vs Base</div>
                    <div class="value" id="scenarioDelta">-</div>
                </div>
            </div>
            <div id="scenarioRiskBadge" class="risk-badge">Risk</div>
        </div>
        <div class="card">
            <h3>Capital Structure Trend</h3>
            <div class="chart-box"><canvas id="capitalChart"></canvas></div>
        </div>
        <div class="card">
            <h3>Asset Utilization Trend</h3>
            <div class="chart-box"><canvas id="assetChart"></canvas></div>
        </div>
    </div>
    <div class="grid-2">
        <div class="card">
            <h3>Static Executive Visuals</h3>
            <div class="img-card">
                <img src="cashflow_chart.png" alt="Cash flow forecast">
            </div>
            <div class="forecast-box">
                <div class="forecast-item">
                    <div class="t">Forecast Operating Y1</div>
                    <div class="v">{fmt_value(summary["Forecast_Operating_Y1"])}</div>
                </div>
                <div class="forecast-item">
                    <div class="t">Forecast Operating Y2</div>
                    <div class="v">{fmt_value(summary["Forecast_Operating_Y2"])}</div>
                </div>
                <div class="forecast-item">
                    <div class="t">Forecast FCF Y1</div>
                    <div class="v">{fmt_value(summary["Forecast_FCF_Y1"])}</div>
                </div>
                <div class="forecast-item">
                    <div class="t">Forecast FCF Y2</div>
                    <div class="v">{fmt_value(summary["Forecast_FCF_Y2"])}</div>
                </div>
            </div>
        </div>
        <div class="card">
            <h3>Insights</h3>
            <ul class="insight-list">
                <li>{summary["WC_Insight"]}</li>
                <li>{summary["CF_Insight"]}</li>
                <li>{summary["Capital_Insight"]}</li>
                <li>{summary["Asset_Insight"]}</li>
            </ul>
            <br>
            <p>
                The dashboard combines historical balance sheet and cash flow trends with forecasting and scenario simulation.  
            </p>
        </div>
    </div>
    <div class="grid-2">
        <div class="card img-card">
            <h3>Working Capital Executive Snapshot</h3>
            <img src="wc_chart.png" alt="Working capital chart">
        </div>
        <div class="card img-card">
            <h3>Capital & Asset Executive Snapshot</h3>
            <img src="capital_chart.png" alt="Capital chart">
            <br><br>
            <img src="asset_chart.png" alt="Asset chart">
        </div>
    </div>
    <div class="footer-note">
        Built with Python, pandas, matplotlib, forecasting logic, HTML, CSS, JavaScript, and Chart.js
    </div>
</div>
<script>
const dashboardData = {data_json};

function formatValue(v) {{
    const absV = Math.abs(v);
    if (absV >= 1000000000) return (v / 1000000000).toFixed(2) + "B";
    if (absV >= 1000000) return (v / 1000000).toFixed(2) + "M";
    if (absV >= 1000) return (v / 1000).toFixed(2) + "K";
    return Number(v).toFixed(2);
}}

function formatPct(v) {{
    return Number(v).toFixed(2) + "%";
}}

function getRiskClass(risk) {{
    if (risk === "Low Risk") return "risk-badge risk-low";
    if (risk === "Moderate Risk") return "risk-badge risk-moderate";
    return "risk-badge risk-high";
}}

function scenarioRisk(fcf, deRatio) {{
    if (fcf < 0 && deRatio > 1.5) return "High Risk";
    if (fcf < 0 || deRatio > 1.5) return "Moderate Risk";
    return "Low Risk";
}}

const yearSelect = document.getElementById("yearSelect");
dashboardData.years.forEach(y => {{
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    yearSelect.appendChild(opt);
}});
yearSelect.value = dashboardData.years[dashboardData.years.length - 1];

const wcChart = new Chart(document.getElementById("wcChart"), {{
    type: "bar",
    data: {{
        labels: dashboardData.years,
        datasets: [
            {{
                type: "bar",
                label: "Working Capital",
                data: dashboardData.workingCapital,
                backgroundColor: "rgba(37, 99, 235, 0.65)",
                borderRadius: 8
            }},
            {{
                type: "line",
                label: "WC Growth %",
                data: dashboardData.wcGrowth,
                borderColor: "#dc2626",
                backgroundColor: "#dc2626",
                yAxisID: "y1",
                tension: 0.4,
                borderWidth: 3,
                pointRadius: 4,
                pointBackgroundColor: "#dc2626",
                pointBorderColor: "#dc2626",
                fill: false
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{
            mode: "index",
            intersect: false
        }},
        plugins: {{
            legend: {{ position: "top" }}
        }},
        scales: {{
            y: {{
                beginAtZero: true
            }},
            y1: {{
                position: "right",
                grid: {{ drawOnChartArea: false }},
                ticks: {{
                    callback: function(value) {{
                        return value + "%";
                    }}
                }}
            }}
        }}
    }}
}});

const cashChart = new Chart(document.getElementById("cashChart"), {{
    type: "bar",
    data: {{
        labels: dashboardData.years,
        datasets: [
            {{
                label: "Operating",
                data: dashboardData.operating,
                backgroundColor: "rgba(34, 197, 94, 0.75)",
                borderRadius: 6
            }},
            {{
                label: "Investing",
                data: dashboardData.investing,
                backgroundColor: "rgba(249, 115, 22, 0.75)",
                borderRadius: 6
            }},
            {{
                label: "Financing",
                data: dashboardData.financing,
                backgroundColor: "rgba(139, 92, 246, 0.75)",
                borderRadius: 6
            }},
            {{
                type: "line",
                label: "Free Cash Flow",
                data: dashboardData.fcf,
                borderColor: "#111827",
                backgroundColor: "#111827",
                tension: 0.35
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{
            mode: "index",
            intersect: false
        }},
        plugins: {{
            legend: {{ position: "top" }}
        }},
        scales: {{
            y: {{
                beginAtZero: false
            }}
        }}
    }}
}});

const capitalChart = new Chart(document.getElementById("capitalChart"), {{
    type: "line",
    data: {{
        labels: dashboardData.years,
        datasets: [
            {{
                label: "Equity",
                data: dashboardData.equity,
                borderColor: "#2563eb",
                backgroundColor: "rgba(37, 99, 235, 0.15)",
                tension: 0.35
            }},
            {{
                label: "Debt",
                data: dashboardData.debt,
                borderColor: "#ef4444",
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                tension: 0.35
            }},
            {{
                label: "Debt to Equity",
                data: dashboardData.deRatio,
                borderColor: "#7c3aed",
                backgroundColor: "#7c3aed",
                yAxisID: "y1",
                tension: 0.35
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ position: "top" }}
        }},
        scales: {{
            y: {{ beginAtZero: true }},
            y1: {{
                position: "right",
                grid: {{ drawOnChartArea: false }}
            }}
        }}
    }}
}});

const assetChart = new Chart(document.getElementById("assetChart"), {{
    type: "bar",
    data: {{
        labels: dashboardData.years,
        datasets: [
            {{
                label: "Net Block",
                data: dashboardData.netBlock,
                backgroundColor: "rgba(14, 165, 233, 0.75)",
                borderRadius: 6
            }},
            {{
                label: "Depreciation",
                data: dashboardData.depreciation,
                backgroundColor: "rgba(244, 63, 94, 0.70)",
                borderRadius: 6
            }},
            {{
                type: "line",
                label: "Asset Utilization %",
                data: dashboardData.assetUtilization,
                borderColor: "#0f172a",
                backgroundColor: "#0f172a",
                yAxisID: "y1",
                tension: 0.35
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ position: "top" }}
        }},
        scales: {{
            y: {{ beginAtZero: true }},
            y1: {{
                position: "right",
                grid: {{ drawOnChartArea: false }}
            }}
        }}
    }}
}});

function updateYearInsights() {{
    const selectedYear = Number(document.getElementById("yearSelect").value);
    const idx = dashboardData.years.indexOf(selectedYear);

    document.getElementById("selectedWC").textContent = formatValue(dashboardData.workingCapital[idx]);
    document.getElementById("selectedWCGrowth").textContent = formatPct(dashboardData.wcGrowth[idx]);
    document.getElementById("selectedFCF").textContent = formatValue(dashboardData.fcf[idx]);
    document.getElementById("selectedNetCF").textContent = formatValue(dashboardData.netCashFlow[idx]);

    document.getElementById("kpiWC").textContent = formatValue(dashboardData.workingCapital[idx]);
    document.getElementById("kpiFCF").textContent = formatValue(dashboardData.fcf[idx]);
    document.getElementById("kpiDE").textContent = Number(dashboardData.deRatio[idx]).toFixed(2);
    document.getElementById("kpiAsset").textContent = Number(dashboardData.assetUtilization[idx]).toFixed(2) + "%";
    document.getElementById("kpiWCGrowthText").textContent = "Growth: " + formatPct(dashboardData.wcGrowth[idx]);
    document.getElementById("kpiRisk").textContent = scenarioRisk(dashboardData.fcf[idx], dashboardData.deRatio[idx]);

    updateScenario();
}}

function updateScenario() {{
    const revPct = Number(document.getElementById("scenarioRevenue").value);
    const expPct = Number(document.getElementById("scenarioExpense").value);

    document.getElementById("scenarioRevenueValue").textContent = revPct + "%";
    document.getElementById("scenarioExpenseValue").textContent = expPct + "%";

    const selectedYear = Number(document.getElementById("yearSelect").value);
    const idx = dashboardData.years.indexOf(selectedYear);

    const baseOperating = dashboardData.operating[idx];
    const baseInvesting = dashboardData.investing[idx];
    const baseFCF = dashboardData.fcf[idx];
    const deRatio = dashboardData.deRatio[idx];

    const scenarioOperating = baseOperating * (1 + revPct / 100);
    const scenarioInvesting = baseInvesting * (1 + expPct / 100);
    const scenarioFCF = scenarioOperating + scenarioInvesting;
    const delta = scenarioFCF - baseFCF;
    const risk = scenarioRisk(scenarioFCF, deRatio);

    document.getElementById("scenarioOperating").textContent = formatValue(scenarioOperating);
    document.getElementById("scenarioFCF").textContent = formatValue(scenarioFCF);
    document.getElementById("scenarioRisk").textContent = risk;
    document.getElementById("scenarioDelta").textContent = (delta >= 0 ? "+" : "") + formatValue(delta);

    const badge = document.getElementById("scenarioRiskBadge");
    badge.textContent = risk;
    badge.className = getRiskClass(risk);
}}

updateYearInsights();
updateScenario();
</script>
</body>
</html>
"""

with open("financial_report.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Financial dashboard generated successfully!")
print("Open: financial_report.html")