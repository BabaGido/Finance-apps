import streamlit as st
import pandas as pd
import json
from google.oauth2.service_account import Credentials
import gspread
import plotly.express as px

# --- Configuration ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_KEY = "17tlk2_x8sSFl60JRW8ngfDBxvdTUwmWdusXgLim6Yvw"  # your sheet ID

# --- Authenticate and Connect to Google Sheets ---
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_KEY)

# --- Helper to load each tab into a DataFrame ---
def load_sheet_data(sheet_obj, tab_name):
    worksheet = sheet_obj.worksheet(tab_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Load data from Google Sheets
income_df = load_sheet_data(sheet, "Income_Log")
expense_df = load_sheet_data(sheet, "Expense_Log")
debts_df = load_sheet_data(sheet, "Debts_Tracker")
goals_df = load_sheet_data(sheet, "Savings_Goals")
accounts_df = load_sheet_data(sheet, "Accounts")

# --- Page Layout ---
st.set_page_config(layout="wide", page_title="💰 Finance Tracker")

st.title("💰 Personal Finance Dashboard with Google Sheets")

# --- Income Section ---
st.header("📥 Income Overview")
income_df["Date"] = pd.to_datetime(income_df["Date"])
st.dataframe(income_df)

# --- Monthly Income Bar Chart ---
income_df["Month"] = income_df["Date"].dt.to_period("M").astype(str)
monthly_income = income_df.groupby("Month")["Amount"].sum().reset_index()

st.subheader("📅 Monthly Income Summary")
st.bar_chart(monthly_income.set_index("Month"))

# --- Expense Section ---
st.header("💸 Expense Overview")
expense_df["Date"] = pd.to_datetime(expense_df["Date"])
st.dataframe(expense_df)

# --- Categorize Expenses as Fixed/Variable/Other based on Description ---
def categorize_expense(desc):
    desc = str(desc).lower()
    if any(keyword in desc for keyword in ["rent", "insurance", "car"]):
        return "Fixed"
    elif any(keyword in desc for keyword in ["gas", "grocery", "utilities", "internet"]):
        return "Variable"
    else:
        return "Other"

expense_df["Category"] = expense_df["Description"].apply(categorize_expense)

# --- Interactive Dropdown Filter for Expenses ---
category_filter = st.selectbox(
    "Filter Expense by Category",
    options=["All"] + expense_df["Category"].unique().tolist()
)
if category_filter == "All":
    filtered_expenses = expense_df
else:
    filtered_expenses = expense_df[expense_df["Category"] == category_filter]

st.subheader(f"📊 {category_filter} Expenses")
st.dataframe(filtered_expenses)

# --- Spending by Category Pie Chart ---
spend_by_cat = expense_df.groupby("Category")["Amount"].sum().reset_index()
fig_expense = px.pie(
    spend_by_cat,
    names="Category",
    values="Amount",
    title="Spending by Category",
    hole=0.4
)
st.plotly_chart(fig_expense, use_container_width=True)

# --- Debt Tracker Section ---
st.header("📉 Debt Tracker")
debts_df["Date"] = pd.to_datetime(debts_df["Date"])
st.dataframe(debts_df)

# --- Savings Goals Section ---
st.header("🎯 Savings Goals")
goals_df["Date"] = pd.to_datetime(goals_df["Date"])
st.dataframe(goals_df)

# --- Accounts Section ---
st.header("🏦 Account Balances")
accounts_df["Date"] = pd.to_datetime(accounts_df["Date"])
st.dataframe(accounts_df)

# --- Net Worth Calculation ---
try:
    total_assets = accounts_df["Amount"].sum()
    total_debts = debts_df["Amount"].sum()
    net_worth = total_assets - total_debts
    st.metric("📊 Net Worth", f"${net_worth:,.2f}")
except Exception:
    st.warning("Could not calculate net worth. Check data format.")
