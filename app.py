import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Expectations Investing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Color Scheme: Navy Blue & Gold ────────────────────────────────────────────
NAVY = "#0A1F3F"
NAVY_LIGHT = "#142D54"
NAVY_MID = "#1B3A6B"
GOLD = "#D4A843"
GOLD_LIGHT = "#E8C975"
GOLD_DIM = "#B08930"
WHITE = "#F5F5F5"
GRAY = "#8A95A5"
BG_DARK = "#060E1A"
CARD_BG = "#0D1B2E"
HIGHLIGHT_BG = "#1A3055"

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Hide default header and top padding */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    .block-container {{
        padding-top: 1rem !important;
    }}
    #MainMenu {{
        visibility: hidden;
    }}
    footer {{
        visibility: hidden;
    }}

    /* Main background */
    .stApp {{
        background: linear-gradient(135deg, {BG_DARK} 0%, {NAVY} 50%, {NAVY_LIGHT} 100%);
        color: {WHITE};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {NAVY} 0%, {BG_DARK} 100%);
        border-right: 2px solid {GOLD_DIM};
    }}
    section[data-testid="stSidebar"] .stMarkdown {{
        color: {WHITE};
    }}

    /* Headers */
    h1, h2, h3, h4 {{
        color: {GOLD} !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {NAVY};
        border-radius: 10px;
        padding: 5px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {NAVY_LIGHT};
        color: {WHITE};
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {GOLD} !important;
        color: {NAVY} !important;
    }}

    /* Metric cards */
    [data-testid="stMetric"] {{
        background: linear-gradient(135deg, {CARD_BG}, {NAVY_LIGHT});
        border: 1px solid {GOLD_DIM};
        border-radius: 12px;
        padding: 15px;
    }}
    [data-testid="stMetricValue"] {{
        color: {GOLD_LIGHT} !important;
        font-size: 1.8rem !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {GRAY} !important;
    }}

    /* Slider */
    .stSlider > div > div > div > div {{
        background-color: {GOLD} !important;
    }}
    .stSlider [data-baseweb="slider"] [role="slider"] {{
        background-color: {GOLD} !important;
        border-color: {GOLD_LIGHT} !important;
    }}

    /* Number input */
    .stNumberInput input {{
        background-color: {NAVY_LIGHT} !important;
        color: {WHITE} !important;
        border-color: {GOLD_DIM} !important;
    }}

    /* Text input */
    .stTextInput input {{
        background-color: {NAVY_LIGHT} !important;
        color: {WHITE} !important;
        border-color: {GOLD_DIM} !important;
        font-size: 1.1rem !important;
    }}

    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {GOLD_DIM}, {GOLD});
        color: {NAVY} !important;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, {GOLD}, {GOLD_LIGHT});
        color: {NAVY} !important;
    }}

    /* Dataframe */
    .stDataFrame {{
        border: 1px solid {GOLD_DIM};
        border-radius: 8px;
    }}

    /* Divider */
    hr {{
        border-color: {GOLD_DIM};
    }}

    /* Info box */
    .highlight-box {{
        background: linear-gradient(135deg, {HIGHLIGHT_BG}, {NAVY_MID});
        border: 2px solid {GOLD};
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }}

    .result-box {{
        background: linear-gradient(135deg, {GOLD_DIM}33, {GOLD}22);
        border: 3px solid {GOLD};
        border-radius: 16px;
        padding: 25px;
        margin: 15px 0;
        text-align: center;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {NAVY_LIGHT} !important;
        color: {GOLD} !important;
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ──────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Fetching market data...")
def fetch_company_data(ticker: str):
    """Fetch company financial data from yfinance."""
    stock = yf.Ticker(ticker)
    info = stock.info

    # Financial statements
    income_stmt = stock.income_stmt
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow

    # Get key data points
    data = {}
    data["name"] = info.get("longName", info.get("shortName", ticker))
    data["price"] = info.get("currentPrice", info.get("previousClose", 0))
    data["shares_outstanding"] = info.get("sharesOutstanding", 0)
    data["market_cap"] = data["price"] * data["shares_outstanding"] if data["shares_outstanding"] else 0
    data["currency"] = info.get("currency", "USD")
    data["sector"] = info.get("sector", "N/A")
    data["industry"] = info.get("industry", "N/A")
    data["beta"] = info.get("beta", 1.0)

    # Historical financials
    hist_data = {}

    if income_stmt is not None and not income_stmt.empty:
        years = sorted(income_stmt.columns, reverse=False)
        for yr in years:
            yr_label = str(yr.year) if hasattr(yr, 'year') else str(yr)
            hist_data.setdefault(yr_label, {})

            revenue = income_stmt.loc["Total Revenue", yr] if "Total Revenue" in income_stmt.index else 0
            op_income = income_stmt.loc["Operating Income", yr] if "Operating Income" in income_stmt.index else 0
            tax = income_stmt.loc["Tax Provision", yr] if "Tax Provision" in income_stmt.index else 0
            pretax_income = income_stmt.loc["Pretax Income", yr] if "Pretax Income" in income_stmt.index else 0
            ebit = income_stmt.loc["EBIT", yr] if "EBIT" in income_stmt.index else op_income

            hist_data[yr_label]["revenue"] = revenue
            hist_data[yr_label]["operating_income"] = op_income
            hist_data[yr_label]["ebit"] = ebit
            hist_data[yr_label]["tax_provision"] = tax
            hist_data[yr_label]["pretax_income"] = pretax_income

    if balance_sheet is not None and not balance_sheet.empty:
        years = sorted(balance_sheet.columns, reverse=False)
        for yr in years:
            yr_label = str(yr.year) if hasattr(yr, 'year') else str(yr)
            hist_data.setdefault(yr_label, {})

            total_debt = balance_sheet.loc["Total Debt", yr] if "Total Debt" in balance_sheet.index else 0
            cash = balance_sheet.loc["Cash And Cash Equivalents", yr] if "Cash And Cash Equivalents" in balance_sheet.index else 0
            short_investments = balance_sheet.loc["Other Short Term Investments", yr] if "Other Short Term Investments" in balance_sheet.index else 0

            # Working capital components
            current_assets = balance_sheet.loc["Current Assets", yr] if "Current Assets" in balance_sheet.index else 0
            current_liabilities = balance_sheet.loc["Current Liabilities", yr] if "Current Liabilities" in balance_sheet.index else 0

            # Net PP&E
            ppe = balance_sheet.loc["Net PPE", yr] if "Net PPE" in balance_sheet.index else 0
            total_assets = balance_sheet.loc["Total Assets", yr] if "Total Assets" in balance_sheet.index else 0

            hist_data[yr_label]["total_debt"] = total_debt if pd.notna(total_debt) else 0
            hist_data[yr_label]["cash"] = cash if pd.notna(cash) else 0
            hist_data[yr_label]["short_investments"] = short_investments if pd.notna(short_investments) else 0
            hist_data[yr_label]["current_assets"] = current_assets if pd.notna(current_assets) else 0
            hist_data[yr_label]["current_liabilities"] = current_liabilities if pd.notna(current_liabilities) else 0
            hist_data[yr_label]["ppe"] = ppe if pd.notna(ppe) else 0
            hist_data[yr_label]["total_assets"] = total_assets if pd.notna(total_assets) else 0

    if cash_flow is not None and not cash_flow.empty:
        years = sorted(cash_flow.columns, reverse=False)
        for yr in years:
            yr_label = str(yr.year) if hasattr(yr, 'year') else str(yr)
            hist_data.setdefault(yr_label, {})

            capex = cash_flow.loc["Capital Expenditure", yr] if "Capital Expenditure" in cash_flow.index else 0
            depreciation = cash_flow.loc["Depreciation And Amortization", yr] if "Depreciation And Amortization" in cash_flow.index else 0

            hist_data[yr_label]["capex"] = abs(capex) if pd.notna(capex) else 0
            hist_data[yr_label]["depreciation"] = depreciation if pd.notna(depreciation) else 0

    data["historical"] = hist_data

    # Compute derived metrics from most recent year
    sorted_years = sorted(hist_data.keys())
    if len(sorted_years) >= 2:
        latest = sorted_years[-1]
        prev = sorted_years[-2]

        rev_latest = hist_data[latest].get("revenue", 0)
        rev_prev = hist_data[prev].get("revenue", 0)

        data["latest_revenue"] = rev_latest
        data["sales_growth"] = ((rev_latest / rev_prev) - 1) * 100 if rev_prev else 5.0

        op_inc = hist_data[latest].get("operating_income", 0)
        data["op_margin"] = (op_inc / rev_latest) * 100 if rev_latest else 10.0

        # Cash tax rate
        tax = hist_data[latest].get("tax_provision", 0)
        pretax = hist_data[latest].get("pretax_income", 0)
        data["cash_tax_rate"] = (tax / pretax) * 100 if pretax and pretax > 0 else 21.0

        # Incremental fixed capital rate
        capex_latest = hist_data[latest].get("capex", 0)
        dep_latest = hist_data[latest].get("depreciation", 0)
        delta_sales = rev_latest - rev_prev

        if delta_sales and delta_sales > 0:
            data["incr_fixed_cap"] = ((capex_latest - dep_latest) / delta_sales) * 100
        else:
            data["incr_fixed_cap"] = 10.0

        # Incremental working capital rate
        ca_latest = hist_data[latest].get("current_assets", 0) - hist_data[latest].get("cash", 0)
        cl_latest = hist_data[latest].get("current_liabilities", 0)
        owc_latest = ca_latest - cl_latest

        ca_prev = hist_data[prev].get("current_assets", 0) - hist_data[prev].get("cash", 0)
        cl_prev = hist_data[prev].get("current_liabilities", 0)
        owc_prev = ca_prev - cl_prev

        delta_owc = owc_latest - owc_prev

        if delta_sales and delta_sales > 0:
            data["incr_wc"] = (delta_owc / delta_sales) * 100
        else:
            data["incr_wc"] = 5.0

        # Non-operating assets (excess cash + short-term investments)
        data["non_operating_assets"] = (
            hist_data[latest].get("cash", 0) +
            hist_data[latest].get("short_investments", 0)
        )

        # Total debt
        data["total_debt"] = hist_data[latest].get("total_debt", 0)

    elif len(sorted_years) == 1:
        latest = sorted_years[0]
        data["latest_revenue"] = hist_data[latest].get("revenue", 0)
        data["sales_growth"] = 5.0
        data["op_margin"] = 10.0
        data["cash_tax_rate"] = 21.0
        data["incr_fixed_cap"] = 10.0
        data["incr_wc"] = 5.0
        data["non_operating_assets"] = hist_data[latest].get("cash", 0)
        data["total_debt"] = hist_data[latest].get("total_debt", 0)
    else:
        data["latest_revenue"] = 0
        data["sales_growth"] = 5.0
        data["op_margin"] = 10.0
        data["cash_tax_rate"] = 21.0
        data["incr_fixed_cap"] = 10.0
        data["incr_wc"] = 5.0
        data["non_operating_assets"] = 0
        data["total_debt"] = 0

    # WACC estimation
    risk_free = 0.043  # ~10yr treasury
    equity_risk_premium = 0.055
    beta = data.get("beta", 1.0) or 1.0
    cost_of_equity = risk_free + beta * equity_risk_premium
    cost_of_debt = 0.05  # approximate
    tax_rate_for_wacc = data.get("cash_tax_rate", 21) / 100

    equity_val = data["market_cap"]
    debt_val = data.get("total_debt", 0) or 0
    total_val = equity_val + debt_val if (equity_val + debt_val) > 0 else 1

    wacc = (equity_val / total_val) * cost_of_equity + (debt_val / total_val) * cost_of_debt * (1 - tax_rate_for_wacc)
    data["wacc"] = round(wacc * 100, 2)

    return data


def run_pie_model(base_revenue, sales_growth, op_margin, cash_tax_rate,
                  incr_fixed_cap, incr_wc, wacc, continuing_value_growth,
                  non_operating_assets, total_debt, shares_outstanding,
                  current_price, max_years=50):
    """
    Run the Price-Implied Expectations (PIE) model.
    Returns: forecast table DataFrame, market-implied forecast period (years), valuation breakdown.
    """
    wacc_dec = wacc / 100
    sg_dec = sales_growth / 100
    opm_dec = op_margin / 100
    ctr_dec = cash_tax_rate / 100
    ifc_dec = incr_fixed_cap / 100
    iwc_dec = incr_wc / 100
    cv_growth_dec = continuing_value_growth / 100

    rows = []
    prev_sales = base_revenue
    cumulative_pv_fcf = 0
    matched_year = None

    for year in range(1, max_years + 1):
        # Step A: Sales
        sales = prev_sales * (1 + sg_dec)
        sales_increase = sales - prev_sales

        # Step B: Operating Profit
        operating_profit = sales * opm_dec

        # Step C: Cash Taxes & NOPAT
        cash_taxes = operating_profit * ctr_dec
        nopat = operating_profit - cash_taxes

        # Step D: Incremental Investment
        fixed_capital_inv = sales_increase * ifc_dec
        working_capital_inv = sales_increase * iwc_dec
        total_investment = fixed_capital_inv + working_capital_inv

        # Step E: Free Cash Flow
        fcf = nopat - total_investment

        # Discount factor
        discount_factor = 1 / ((1 + wacc_dec) ** year)
        pv_fcf = fcf * discount_factor
        cumulative_pv_fcf += pv_fcf

        # Continuing Value at this year (perpetuity with growth)
        if wacc_dec > cv_growth_dec:
            continuing_value = fcf * (1 + cv_growth_dec) / (wacc_dec - cv_growth_dec)
        else:
            continuing_value = fcf * 30  # fallback cap

        pv_continuing_value = continuing_value * discount_factor

        # Corporate Value = Cumulative PV of FCF + PV of Continuing Value
        corporate_value = cumulative_pv_fcf + pv_continuing_value

        # Shareholder Value
        shareholder_value = corporate_value + non_operating_assets - total_debt

        # Value per share
        value_per_share = shareholder_value / shares_outstanding if shares_outstanding > 0 else 0

        row = {
            "Year": year,
            "Sales": sales,
            "Sales Growth": sales_growth,
            "Operating Profit": operating_profit,
            "Op. Margin": op_margin,
            "Cash Taxes": cash_taxes,
            "NOPAT": nopat,
            "Fixed Capital Inv.": fixed_capital_inv,
            "Working Capital Inv.": working_capital_inv,
            "Total Investment": total_investment,
            "Free Cash Flow": fcf,
            "Discount Factor": discount_factor,
            "PV of FCF": pv_fcf,
            "Cumulative PV FCF": cumulative_pv_fcf,
            "Continuing Value": continuing_value,
            "PV Continuing Value": pv_continuing_value,
            "Corporate Value": corporate_value,
            "Non-Op Assets": non_operating_assets,
            "Debt": total_debt,
            "Shareholder Value": shareholder_value,
            "Value Per Share": value_per_share,
        }
        rows.append(row)

        # Check if we've matched the current price
        if matched_year is None and value_per_share >= current_price:
            matched_year = year

        prev_sales = sales

    df = pd.DataFrame(rows)

    # If we never matched, the market-implied period exceeds max_years
    if matched_year is None:
        matched_year = max_years

    return df, matched_year


def format_number(val, prefix="$", suffix="", decimals=1, scale=1):
    """Format large numbers with B/M/K suffixes."""
    val = val / scale
    if abs(val) >= 1e9:
        return f"{prefix}{val/1e9:,.{decimals}f}B{suffix}"
    elif abs(val) >= 1e6:
        return f"{prefix}{val/1e6:,.{decimals}f}M{suffix}"
    elif abs(val) >= 1e3:
        return f"{prefix}{val/1e3:,.{decimals}f}K{suffix}"
    else:
        return f"{prefix}{val:,.{decimals}f}{suffix}"


# ─── Sidebar: Company Input ───────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 10px 0 20px 0;">
    <h1 style="color: {GOLD}; margin: 0; font-size: 1.5rem;">📊 Expectations</h1>
    <h1 style="color: {GOLD}; margin: 0; font-size: 1.5rem;">Investing</h1>
    <p style="color: {GRAY}; font-size: 0.85rem; margin-top: 5px;">
        Based on Mauboussin's PIE Framework
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

ticker_input = st.sidebar.text_input(
    "🔍 Company Ticker",
    value="AAPL",
    help="Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
)

load_button = st.sidebar.button("Load Company Data", use_container_width=True)

# Initialize session state
if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"
    st.session_state.data_loaded = False

if load_button or not st.session_state.data_loaded:
    st.session_state.ticker = ticker_input.upper().strip()
    try:
        st.session_state.company_data = fetch_company_data(st.session_state.ticker)
        st.session_state.data_loaded = True
    except Exception as e:
        st.error(f"Error loading data for {st.session_state.ticker}: {str(e)}")
        st.stop()

if not st.session_state.data_loaded:
    st.stop()

cd = st.session_state.company_data

# ─── Sidebar: Company Info ─────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="background: linear-gradient(135deg, {CARD_BG}, {NAVY_LIGHT});
            border: 1px solid {GOLD_DIM}; border-radius: 10px; padding: 15px; margin: 10px 0;">
    <h3 style="color: {GOLD}; margin: 0 0 8px 0; font-size: 1.1rem;">{cd['name']}</h3>
    <p style="color: {WHITE}; margin: 2px 0; font-size: 0.9rem;">
        <strong>Price:</strong> ${cd['price']:,.2f}
    </p>
    <p style="color: {WHITE}; margin: 2px 0; font-size: 0.9rem;">
        <strong>Market Cap:</strong> {format_number(cd['market_cap'])}
    </p>
    <p style="color: {GRAY}; margin: 2px 0; font-size: 0.85rem;">
        {cd['sector']} · {cd['industry']}
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# ─── Sidebar: Model Inputs (Sliders) ──────────────────────────────────────────
st.sidebar.markdown(f"### ⚙️ Operating Value Drivers")

sales_growth = st.sidebar.slider(
    "Sales Growth Rate (%)",
    min_value=-20.0, max_value=50.0,
    value=round(float(cd.get("sales_growth", 5.0)), 1),
    step=0.5,
    help="Expected annual sales growth rate"
)

op_margin = st.sidebar.slider(
    "Operating Profit Margin (%)",
    min_value=-20.0, max_value=60.0,
    value=round(float(cd.get("op_margin", 10.0)), 1),
    step=0.5,
    help="Pre-tax operating profit as % of sales"
)

cash_tax_rate = st.sidebar.slider(
    "Cash Tax Rate (%)",
    min_value=0.0, max_value=50.0,
    value=min(round(float(cd.get("cash_tax_rate", 21.0)), 1), 50.0),
    step=0.5,
    help="Effective cash tax rate on operating profit"
)

st.sidebar.markdown(f"### 📈 Capital Investment Rates")

incr_fixed_cap = st.sidebar.slider(
    "Incremental Fixed Capital Rate (%)",
    min_value=-50.0, max_value=100.0,
    value=round(float(np.clip(cd.get("incr_fixed_cap", 10.0), -50, 100)), 1),
    step=0.5,
    help="(Capex − Depreciation) / Change in Sales"
)

incr_wc = st.sidebar.slider(
    "Incremental Working Capital Rate (%)",
    min_value=-50.0, max_value=100.0,
    value=round(float(np.clip(cd.get("incr_wc", 5.0), -50, 100)), 1),
    step=0.5,
    help="Change in Operating Working Capital / Change in Sales"
)

st.sidebar.markdown(f"### 💰 Valuation Parameters")

wacc = st.sidebar.slider(
    "WACC (%)",
    min_value=1.0, max_value=20.0,
    value=round(float(np.clip(cd.get("wacc", 8.0), 1, 20)), 2),
    step=0.25,
    help="Weighted Average Cost of Capital"
)

cv_growth = st.sidebar.slider(
    "Continuing Value Growth (%)",
    min_value=0.0, max_value=5.0,
    value=1.5,
    step=0.1,
    help="Long-term growth rate for continuing (terminal) value"
)

st.sidebar.markdown(f"### 🏦 Balance Sheet Items")

non_op_assets = st.sidebar.number_input(
    "Non-Operating Assets ($)",
    value=int(cd.get("non_operating_assets", 0)),
    step=1000000,
    help="Excess cash and marketable securities"
)

total_debt = st.sidebar.number_input(
    "Total Debt ($)",
    value=int(cd.get("total_debt", 0)),
    step=1000000,
    help="Total economic liabilities"
)

# ─── Run the Model ─────────────────────────────────────────────────────────────
base_revenue = cd.get("latest_revenue", 0)
shares = cd.get("shares_outstanding", 1)
current_price = cd.get("price", 0)

if base_revenue <= 0:
    st.error("Could not retrieve valid revenue data for this company. Please try another ticker.")
    st.stop()

forecast_df, implied_period = run_pie_model(
    base_revenue=base_revenue,
    sales_growth=sales_growth,
    op_margin=op_margin,
    cash_tax_rate=cash_tax_rate,
    incr_fixed_cap=incr_fixed_cap,
    incr_wc=incr_wc,
    wacc=wacc,
    continuing_value_growth=cv_growth,
    non_operating_assets=non_op_assets,
    total_debt=total_debt,
    shares_outstanding=shares,
    current_price=current_price
)

# ─── Main Content ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align: center; padding: 10px 0;">
    <h1 style="color: {GOLD}; margin-bottom: 0;">Expectations Investing Dashboard</h1>
    <p style="color: {GRAY}; font-size: 1rem;">
        Price-Implied Expectations Analysis for <strong style="color: {WHITE};">{cd['name']} ({st.session_state.ticker})</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 PIE Analysis", "📋 Historical & Forecast Financials", "📊 Sensitivity Analysis"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: PIE Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    # Key Result: Market-Implied Forecast Period
    implied_value = forecast_df.loc[forecast_df["Year"] == implied_period, "Value Per Share"].values[0]

    st.markdown(f"""
    <div class="result-box">
        <p style="color: {GRAY}; font-size: 1rem; margin: 0;">MARKET-IMPLIED FORECAST PERIOD</p>
        <h1 style="color: {GOLD}; font-size: 4rem; margin: 5px 0;">{implied_period} Years</h1>
        <p style="color: {WHITE}; font-size: 1.1rem; margin: 0;">
            The market is pricing in <strong style="color: {GOLD_LIGHT};">{implied_period} years</strong> of value-creating growth
            at {sales_growth}% sales growth and {op_margin}% operating margin
        </p>
        <p style="color: {GRAY}; font-size: 0.9rem; margin-top: 8px;">
            Implied Value: ${implied_value:,.2f} vs Current Price: ${current_price:,.2f}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)

    yr1_fcf = forecast_df.loc[0, "Free Cash Flow"]
    yr1_nopat = forecast_df.loc[0, "NOPAT"]
    corporate_val = forecast_df.loc[forecast_df["Year"] == implied_period, "Corporate Value"].values[0]
    shareholder_val = forecast_df.loc[forecast_df["Year"] == implied_period, "Shareholder Value"].values[0]

    with col1:
        st.metric("Year 1 FCF", format_number(yr1_fcf))
    with col2:
        st.metric("Year 1 NOPAT", format_number(yr1_nopat))
    with col3:
        st.metric("Corporate Value", format_number(corporate_val))
    with col4:
        st.metric("Shareholder Value", format_number(shareholder_val))
    with col5:
        st.metric("Non-Op Assets - Debt", format_number(non_op_assets - total_debt))

    st.markdown("---")

    # ─── Value Build-Up Chart ──────────────────────────────────────────────────
    st.markdown(f"### 📈 Value Per Share Build-Up Over Forecast Period")

    chart_df = forecast_df[forecast_df["Year"] <= min(implied_period + 5, 30)].copy()

    fig_value = go.Figure()

    # Value per share line
    fig_value.add_trace(go.Scatter(
        x=chart_df["Year"],
        y=chart_df["Value Per Share"],
        mode="lines+markers",
        name="Implied Value/Share",
        line=dict(color=GOLD, width=3),
        marker=dict(size=8, color=GOLD, line=dict(width=2, color=GOLD_LIGHT)),
        hovertemplate="Year %{x}<br>Value: $%{y:,.2f}<extra></extra>"
    ))

    # Current price line
    fig_value.add_hline(
        y=current_price,
        line=dict(color="#FF6B6B", width=2, dash="dash"),
        annotation_text=f"Current Price: ${current_price:,.2f}",
        annotation_position="top right",
        annotation_font_color="#FF6B6B"
    )

    # Highlight the implied period
    fig_value.add_vline(
        x=implied_period,
        line=dict(color=GOLD_LIGHT, width=2, dash="dot"),
        annotation_text=f"Implied Period: {implied_period} yrs",
        annotation_position="top left",
        annotation_font_color=GOLD_LIGHT
    )

    # Shade the forecast period
    fig_value.add_vrect(
        x0=0.5, x1=implied_period + 0.5,
        fillcolor=GOLD, opacity=0.08,
        layer="below", line_width=0,
    )

    fig_value.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE),
        xaxis=dict(
            title="Forecast Year",
            gridcolor=f"{NAVY_MID}",
            dtick=1,
        ),
        yaxis=dict(
            title="Value Per Share ($)",
            gridcolor=f"{NAVY_MID}",
            tickprefix="$",
        ),
        height=450,
        margin=dict(l=60, r=30, t=30, b=50),
        legend=dict(
            bgcolor=NAVY_LIGHT,
            bordercolor=GOLD_DIM,
            borderwidth=1,
            font=dict(color=WHITE),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig_value, use_container_width=True)

    # ─── FCF Projection Table ─────────────────────────────────────────────────
    st.markdown(f"### 💵 Free Cash Flow Projection")

    display_years = min(implied_period + 3, 30)
    display_df = forecast_df[forecast_df["Year"] <= display_years].copy()

    # Format the table
    table_df = pd.DataFrame({
        "Year": display_df["Year"].astype(int),
        "Sales": display_df["Sales"].apply(lambda x: format_number(x)),
        "Operating Profit": display_df["Operating Profit"].apply(lambda x: format_number(x)),
        "NOPAT": display_df["NOPAT"].apply(lambda x: format_number(x)),
        "Total Investment": display_df["Total Investment"].apply(lambda x: format_number(x)),
        "Free Cash Flow": display_df["Free Cash Flow"].apply(lambda x: format_number(x)),
        "PV of FCF": display_df["PV of FCF"].apply(lambda x: format_number(x)),
        "Value/Share": display_df["Value Per Share"].apply(lambda x: f"${x:,.2f}"),
    })

    # Highlight the market-implied period column
    def highlight_implied_year(row):
        if row["Year"] == implied_period:
            return [f"background-color: {GOLD}; color: {NAVY}; font-weight: bold;"] * len(row)
        return [""] * len(row)

    styled_df = table_df.style.apply(highlight_implied_year, axis=1)
    styled_df = styled_df.set_properties(**{
        "text-align": "right",
        "font-size": "0.85rem",
    })

    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=400)

    st.markdown(f"""
    <p style="color: {GRAY}; font-size: 0.85rem; text-align: center;">
        ⭐ <strong style="color: {GOLD};">Highlighted row</strong> = Market-Implied Forecast Period
        (year where implied value ≥ current stock price)
    </p>
    """, unsafe_allow_html=True)

    # ─── Valuation Waterfall ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### 🏗️ Valuation Waterfall (at Implied Period)")

    cum_pv = forecast_df.loc[forecast_df["Year"] == implied_period, "Cumulative PV FCF"].values[0]
    pv_cv = forecast_df.loc[forecast_df["Year"] == implied_period, "PV Continuing Value"].values[0]

    waterfall_labels = [
        "PV of FCFs",
        "PV of Continuing Value",
        "Corporate Value",
        "Non-Operating Assets",
        "Less: Debt",
        "Shareholder Value"
    ]
    waterfall_values = [
        cum_pv,
        pv_cv,
        0,  # total
        non_op_assets,
        -total_debt,
        0,  # total
    ]
    waterfall_measures = ["relative", "relative", "total", "relative", "relative", "total"]

    fig_waterfall = go.Figure(go.Waterfall(
        orientation="v",
        measure=waterfall_measures,
        x=waterfall_labels,
        y=waterfall_values,
        connector=dict(line=dict(color=GOLD_DIM, width=1)),
        increasing=dict(marker=dict(color=GOLD)),
        decreasing=dict(marker=dict(color="#FF6B6B")),
        totals=dict(marker=dict(color=GOLD_LIGHT)),
        textposition="outside",
        text=[format_number(abs(v)) if v != 0 else "" for v in waterfall_values],
        textfont=dict(color=WHITE, size=11),
    ))

    fig_waterfall.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE),
        yaxis=dict(
            gridcolor=f"{NAVY_MID}",
            tickprefix="$",
            title="Value ($)",
        ),
        xaxis=dict(tickfont=dict(size=11)),
        height=400,
        margin=dict(l=60, r=30, t=30, b=50),
        showlegend=False,
    )

    st.plotly_chart(fig_waterfall, use_container_width=True)

    # Per-share breakdown
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(
            "PV of FCFs / Share",
            f"${cum_pv / shares:,.2f}" if shares > 0 else "N/A"
        )
    with col_b:
        st.metric(
            "PV of Continuing Value / Share",
            f"${pv_cv / shares:,.2f}" if shares > 0 else "N/A"
        )
    with col_c:
        st.metric(
            "Net Non-Op / Share",
            f"${(non_op_assets - total_debt) / shares:,.2f}" if shares > 0 else "N/A"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Historical & Forecast Financials
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f"""
    <div style="text-align: center; padding: 5px 0 15px 0;">
        <h2 style="color: {GOLD};">Historical & Forecasted Financials</h2>
        <p style="color: {GRAY};">See how historical data transitions into the forecast used to derive the market-implied forecast period</p>
    </div>
    """, unsafe_allow_html=True)

    # Build combined historical + forecast table
    hist = cd.get("historical", {})
    sorted_hist_years = sorted(hist.keys())

    combined_rows = []

    # Historical years
    for yr_label in sorted_hist_years:
        h = hist[yr_label]
        rev = h.get("revenue", 0)
        op_inc = h.get("operating_income", 0)
        tax = h.get("tax_provision", 0)
        capex = h.get("capex", 0)
        dep = h.get("depreciation", 0)

        nopat_h = op_inc - tax if op_inc and tax else 0

        combined_rows.append({
            "Period": yr_label,
            "Type": "Historical",
            "Sales": rev,
            "Operating Profit": op_inc,
            "Op. Margin (%)": round((op_inc / rev) * 100, 1) if rev else 0,
            "NOPAT": nopat_h,
            "Capex": capex,
            "Depreciation": dep,
            "Net Fixed Capital": capex - dep if capex and dep else 0,
            "FCF (est.)": nopat_h - (capex - dep) if nopat_h else 0,
        })

    # Forecast years (up to implied period + a few)
    for _, row in forecast_df[forecast_df["Year"] <= min(implied_period + 3, 25)].iterrows():
        yr_num = int(row["Year"])
        base_year = int(sorted_hist_years[-1]) if sorted_hist_years else 2024

        combined_rows.append({
            "Period": str(base_year + yr_num),
            "Type": "Forecast" if yr_num <= implied_period else "Beyond Implied",
            "Sales": row["Sales"],
            "Operating Profit": row["Operating Profit"],
            "Op. Margin (%)": op_margin,
            "NOPAT": row["NOPAT"],
            "Capex": row["Fixed Capital Inv."] + row.get("Working Capital Inv.", 0),
            "Depreciation": 0,
            "Net Fixed Capital": row["Fixed Capital Inv."],
            "FCF (est.)": row["Free Cash Flow"],
        })

    combined_df = pd.DataFrame(combined_rows)

    # ─── Revenue & FCF Chart ──────────────────────────────────────────────────
    fig_hist = make_subplots(specs=[[{"secondary_y": True}]])

    # Separate historical and forecast
    hist_mask = combined_df["Type"] == "Historical"
    forecast_mask = combined_df["Type"] == "Forecast"
    beyond_mask = combined_df["Type"] == "Beyond Implied"

    # Revenue bars - Historical
    fig_hist.add_trace(go.Bar(
        x=combined_df.loc[hist_mask, "Period"],
        y=combined_df.loc[hist_mask, "Sales"],
        name="Revenue (Historical)",
        marker_color=NAVY_MID,
        opacity=0.8,
        hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))

    # Revenue bars - Forecast
    fig_hist.add_trace(go.Bar(
        x=combined_df.loc[forecast_mask, "Period"],
        y=combined_df.loc[forecast_mask, "Sales"],
        name="Revenue (Forecast)",
        marker_color=GOLD_DIM,
        opacity=0.8,
        hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))

    # Revenue bars - Beyond implied
    if beyond_mask.any():
        fig_hist.add_trace(go.Bar(
            x=combined_df.loc[beyond_mask, "Period"],
            y=combined_df.loc[beyond_mask, "Sales"],
            name="Revenue (Beyond Implied)",
            marker_color="rgba(26,54,93,0.53)",
            opacity=0.5,
            hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
        ))

    # FCF line
    fig_hist.add_trace(go.Scatter(
        x=combined_df["Period"],
        y=combined_df["FCF (est.)"],
        name="Free Cash Flow",
        mode="lines+markers",
        line=dict(color=GOLD_LIGHT, width=3),
        marker=dict(size=7),
        hovertemplate="%{x}<br>FCF: $%{y:,.0f}<extra></extra>",
    ), secondary_y=True)

    # Add vertical line at transition using shape (works with categorical x-axis)
    if sorted_hist_years:
        transition_label = sorted_hist_years[-1]
        fig_hist.add_shape(
            type="line",
            x0=transition_label, x1=transition_label,
            y0=0, y1=1, yref="paper",
            line=dict(color=GOLD, width=2, dash="dash"),
        )
        fig_hist.add_annotation(
            x=transition_label, y=1.05, yref="paper",
            text="← Historical | Forecast →",
            showarrow=False,
            font=dict(color=GOLD, size=12),
        )

    fig_hist.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE),
        barmode="group",
        height=500,
        margin=dict(l=60, r=60, t=30, b=50),
        legend=dict(
            bgcolor=NAVY_LIGHT,
            bordercolor=GOLD_DIM,
            borderwidth=1,
            font=dict(color=WHITE),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        hovermode="x unified",
    )
    fig_hist.update_yaxes(
        title_text="Revenue ($)", gridcolor=NAVY_MID,
        secondary_y=False, tickprefix="$",
    )
    fig_hist.update_yaxes(
        title_text="Free Cash Flow ($)", gridcolor=NAVY_MID,
        secondary_y=True, tickprefix="$",
    )

    st.plotly_chart(fig_hist, use_container_width=True)

    # ─── Cumulative PV Build-Up Chart ─────────────────────────────────────────
    st.markdown(f"### 📊 Cumulative Present Value Build-Up to Match Stock Price")
    st.markdown(f"""
    <p style="color: {GRAY};">
        This chart shows how the present value of the company's cash flows extends year by year.
        The forecast period is extended until the cumulative value per share matches the current stock price of
        <strong style="color: {GOLD};">${current_price:,.2f}</strong>.
    </p>
    """, unsafe_allow_html=True)

    pv_chart_df = forecast_df[forecast_df["Year"] <= min(implied_period + 5, 30)].copy()

    fig_pv = go.Figure()

    # Stacked area: PV of FCFs + PV of Continuing Value (per share)
    fig_pv.add_trace(go.Bar(
        x=pv_chart_df["Year"],
        y=pv_chart_df["Cumulative PV FCF"] / shares,
        name="Cumulative PV of FCFs / Share",
        marker_color=NAVY_MID,
        hovertemplate="Year %{x}<br>Cum PV FCFs: $%{y:,.2f}/share<extra></extra>",
    ))

    fig_pv.add_trace(go.Bar(
        x=pv_chart_df["Year"],
        y=pv_chart_df["PV Continuing Value"] / shares,
        name="PV of Continuing Value / Share",
        marker_color=GOLD_DIM,
        hovertemplate="Year %{x}<br>PV CV: $%{y:,.2f}/share<extra></extra>",
    ))

    # Net non-operating value per share (constant)
    net_non_op_per_share = (non_op_assets - total_debt) / shares if shares else 0
    if net_non_op_per_share != 0:
        fig_pv.add_trace(go.Bar(
            x=pv_chart_df["Year"],
            y=[net_non_op_per_share] * len(pv_chart_df),
            name="Net Non-Op Assets / Share",
            marker_color="rgba(232,201,117,0.53)",
            hovertemplate="Year %{x}<br>Net Non-Op: $%{y:,.2f}/share<extra></extra>",
        ))

    # Total value line
    fig_pv.add_trace(go.Scatter(
        x=pv_chart_df["Year"],
        y=pv_chart_df["Value Per Share"],
        name="Total Value / Share",
        mode="lines+markers",
        line=dict(color=GOLD_LIGHT, width=3),
        marker=dict(size=8, color=GOLD_LIGHT),
        hovertemplate="Year %{x}<br>Value: $%{y:,.2f}/share<extra></extra>",
    ))

    # Current price line
    fig_pv.add_hline(
        y=current_price,
        line=dict(color="#FF6B6B", width=2, dash="dash"),
        annotation_text=f"Current Price: ${current_price:,.2f}",
        annotation_position="top right",
        annotation_font_color="#FF6B6B",
    )

    fig_pv.add_vline(
        x=implied_period,
        line=dict(color=GOLD_LIGHT, width=2, dash="dot"),
        annotation_text=f"Implied: {implied_period} yrs",
        annotation_font_color=GOLD_LIGHT,
    )

    fig_pv.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE),
        barmode="stack",
        height=500,
        margin=dict(l=60, r=30, t=30, b=50),
        legend=dict(
            bgcolor=NAVY_LIGHT,
            bordercolor=GOLD_DIM,
            borderwidth=1,
            font=dict(color=WHITE),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        xaxis=dict(title="Forecast Year", gridcolor=NAVY_MID, dtick=1),
        yaxis=dict(title="Value Per Share ($)", gridcolor=NAVY_MID, tickprefix="$"),
        hovermode="x unified",
    )

    st.plotly_chart(fig_pv, use_container_width=True)

    # ─── Detailed Financials Table ─────────────────────────────────────────────
    st.markdown(f"### 📋 Detailed Financial Projections")

    detailed_table = combined_df.copy()

    # Format numbers
    for col in ["Sales", "Operating Profit", "NOPAT", "Capex", "Depreciation", "Net Fixed Capital", "FCF (est.)"]:
        detailed_table[col] = detailed_table[col].apply(lambda x: format_number(x) if pd.notna(x) and x != 0 else "-")
    detailed_table["Op. Margin (%)"] = detailed_table["Op. Margin (%)"].apply(lambda x: f"{x:.1f}%")

    def color_type(row):
        if row["Type"] == "Historical":
            return [f"background-color: {NAVY_MID}40; color: {WHITE};"] * len(row)
        elif row["Type"] == "Forecast":
            return [f"background-color: {GOLD}25; color: {WHITE};"] * len(row)
        else:
            return [f"background-color: {NAVY}40; color: {GRAY};"] * len(row)

    styled_detail = detailed_table.style.apply(color_type, axis=1)
    styled_detail = styled_detail.set_properties(**{"text-align": "right", "font-size": "0.85rem"})

    st.dataframe(styled_detail, use_container_width=True, hide_index=True, height=500)

    st.markdown(f"""
    <div style="display: flex; gap: 20px; justify-content: center; margin-top: 10px;">
        <span style="color: {NAVY_MID};">■</span> <span style="color: {GRAY};">Historical</span>
        <span style="color: {GOLD};">■</span> <span style="color: {GRAY};">Forecast (within implied period)</span>
        <span style="color: {NAVY};">■</span> <span style="color: {GRAY};">Beyond implied period</span>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: Sensitivity Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(f"""
    <div style="text-align: center; padding: 5px 0 15px 0;">
        <h2 style="color: {GOLD};">Sensitivity Analysis</h2>
        <p style="color: {GRAY};">Explore how changes in key inputs affect the market-implied forecast period and valuation</p>
    </div>
    """, unsafe_allow_html=True)

    col_x, col_y = st.columns(2)

    with col_x:
        x_axis_var = st.selectbox(
            "X-Axis Variable",
            ["Sales Growth Rate", "Operating Profit Margin"],
            index=0
        )
    with col_y:
        y_axis_var = st.selectbox(
            "Y-Axis Variable",
            ["Operating Profit Margin", "Sales Growth Rate", "WACC"],
            index=0
        )

    # Generate sensitivity grid
    def get_range(var_name, current_val):
        if var_name == "Sales Growth Rate":
            return np.arange(max(current_val - 5, 0), current_val + 6, 1.0)
        elif var_name == "Operating Profit Margin":
            return np.arange(max(current_val - 5, 1), current_val + 6, 1.0)
        elif var_name == "WACC":
            return np.arange(max(current_val - 3, 2), current_val + 4, 1.0)
        return np.arange(0, 20, 2)

    def get_current(var_name):
        if var_name == "Sales Growth Rate":
            return sales_growth
        elif var_name == "Operating Profit Margin":
            return op_margin
        elif var_name == "WACC":
            return wacc
        return 5

    x_vals = get_range(x_axis_var, get_current(x_axis_var))
    y_vals = get_range(y_axis_var, get_current(y_axis_var))

    # Build heatmap data
    z_implied = np.zeros((len(y_vals), len(x_vals)))
    z_value = np.zeros((len(y_vals), len(x_vals)))

    for i, yv in enumerate(y_vals):
        for j, xv in enumerate(x_vals):
            sg = xv if x_axis_var == "Sales Growth Rate" else (yv if y_axis_var == "Sales Growth Rate" else sales_growth)
            om = xv if x_axis_var == "Operating Profit Margin" else (yv if y_axis_var == "Operating Profit Margin" else op_margin)
            w = xv if x_axis_var == "WACC" else (yv if y_axis_var == "WACC" else wacc)

            _, ip = run_pie_model(
                base_revenue, sg, om, cash_tax_rate,
                incr_fixed_cap, incr_wc, w, cv_growth,
                non_op_assets, total_debt, shares, current_price
            )
            z_implied[i, j] = ip

    # Heatmap: Implied Forecast Period
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_implied,
        x=[f"{v:.1f}%" for v in x_vals],
        y=[f"{v:.1f}%" for v in y_vals],
        colorscale=[
            [0, NAVY],
            [0.3, NAVY_MID],
            [0.5, GOLD_DIM],
            [0.7, GOLD],
            [1, GOLD_LIGHT],
        ],
        colorbar=dict(
            title=dict(text="Years", font=dict(color=WHITE)),
            tickfont=dict(color=WHITE),
        ),
        text=z_implied.astype(int),
        texttemplate="%{text}",
        textfont=dict(color=WHITE, size=12),
        hovertemplate=f"{x_axis_var}: %{{x}}<br>{y_axis_var}: %{{y}}<br>Implied Period: %{{z:.0f}} years<extra></extra>",
    ))

    fig_heat.update_layout(
        title=dict(
            text="Market-Implied Forecast Period (Years)",
            font=dict(color=GOLD, size=16),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE),
        xaxis=dict(title=x_axis_var, gridcolor=NAVY_MID),
        yaxis=dict(title=y_axis_var, gridcolor=NAVY_MID),
        height=500,
        margin=dict(l=80, r=30, t=60, b=60),
    )

    st.plotly_chart(fig_heat, use_container_width=True)

    # ─── Single variable sensitivity ──────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### 📉 Single Variable Sensitivity")

    sens_var = st.selectbox(
        "Variable to Analyze",
        ["Sales Growth Rate", "Operating Profit Margin", "WACC", "Incr. Fixed Capital Rate", "Incr. Working Capital Rate"],
        key="sens_single"
    )

    def single_sensitivity(var_name):
        if var_name == "Sales Growth Rate":
            vals = np.arange(0, 25.5, 0.5)
            results = []
            for v in vals:
                _, ip = run_pie_model(base_revenue, v, op_margin, cash_tax_rate, incr_fixed_cap, incr_wc, wacc, cv_growth, non_op_assets, total_debt, shares, current_price)
                results.append(ip)
            return vals, results, sales_growth
        elif var_name == "Operating Profit Margin":
            vals = np.arange(1, 50.5, 0.5)
            results = []
            for v in vals:
                _, ip = run_pie_model(base_revenue, sales_growth, v, cash_tax_rate, incr_fixed_cap, incr_wc, wacc, cv_growth, non_op_assets, total_debt, shares, current_price)
                results.append(ip)
            return vals, results, op_margin
        elif var_name == "WACC":
            vals = np.arange(2, 15.25, 0.25)
            results = []
            for v in vals:
                _, ip = run_pie_model(base_revenue, sales_growth, op_margin, cash_tax_rate, incr_fixed_cap, incr_wc, v, cv_growth, non_op_assets, total_debt, shares, current_price)
                results.append(ip)
            return vals, results, wacc
        elif var_name == "Incr. Fixed Capital Rate":
            vals = np.arange(-20, 51, 1)
            results = []
            for v in vals:
                _, ip = run_pie_model(base_revenue, sales_growth, op_margin, cash_tax_rate, v, incr_wc, wacc, cv_growth, non_op_assets, total_debt, shares, current_price)
                results.append(ip)
            return vals, results, incr_fixed_cap
        else:  # Working Capital
            vals = np.arange(-20, 51, 1)
            results = []
            for v in vals:
                _, ip = run_pie_model(base_revenue, sales_growth, op_margin, cash_tax_rate, incr_fixed_cap, v, wacc, cv_growth, non_op_assets, total_debt, shares, current_price)
                results.append(ip)
            return vals, results, incr_wc

    s_vals, s_results, s_current = single_sensitivity(sens_var)

    fig_sens = go.Figure()

    fig_sens.add_trace(go.Scatter(
        x=s_vals,
        y=s_results,
        mode="lines",
        name="Implied Forecast Period",
        line=dict(color=GOLD, width=3),
        fill="tozeroy",
        fillcolor="rgba(212,175,55,0.13)",
        hovertemplate=f"{sens_var}: %{{x:.1f}}%<br>Implied Period: %{{y:.0f}} years<extra></extra>",
    ))

    # Current value marker
    idx = np.argmin(np.abs(s_vals - s_current))
    fig_sens.add_trace(go.Scatter(
        x=[s_current],
        y=[s_results[idx]],
        mode="markers",
        name="Current Value",
        marker=dict(size=14, color="#FF6B6B", symbol="diamond", line=dict(width=2, color=WHITE)),
        hovertemplate=f"Current: {s_current:.1f}%<br>Period: {s_results[idx]:.0f} years<extra></extra>",
    ))

    fig_sens.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE),
        xaxis=dict(title=f"{sens_var} (%)", gridcolor=NAVY_MID),
        yaxis=dict(title="Market-Implied Forecast Period (Years)", gridcolor=NAVY_MID),
        height=400,
        margin=dict(l=60, r=30, t=30, b=50),
        legend=dict(
            bgcolor=NAVY_LIGHT,
            bordercolor=GOLD_DIM,
            borderwidth=1,
            font=dict(color=WHITE),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig_sens, use_container_width=True)


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 10px 0;">
    <p style="color: {GRAY}; font-size: 0.8rem;">
        Based on <strong style="color: {GOLD};">Expectations Investing</strong> by Michael J. Mauboussin & Alfred Rappaport
        · <a href="https://www.expectationsinvesting.com/online-tutorial-8" style="color: {GOLD_DIM};">Tutorial Reference</a>
    </p>
    <p style="color: {GRAY}; font-size: 0.75rem;">
        Market data via Yahoo Finance · For educational purposes only · Not financial advice
    </p>
</div>
""", unsafe_allow_html=True)
