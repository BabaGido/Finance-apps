
import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- Configuration ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Finance Tracker"

# --- Authenticate and Connect to Google Sheets ---
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

# --- Connect to Google Sheets ---
client = gspread.authorize(creds)
sheet = client.open_by_key("17tlk2_x8sSFl60JRW8ngfDBxvdTUwmWdusXgLim6Yvw")

# --- Load Data from Each Sheet ---
def load_sheet_data(sheet, tab_name):
    worksheet = sheet.worksheet(tab_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Load all data tables
income_df = load_sheet_data(sheet, "Income_Log")
expense_df = load_sheet_data(sheet, "Expense_Log")
debts_df = load_sheet_data(sheet, "Debts_Tracker")
goals_df = load_sheet_data(sheet, "Savings_Goals")
accounts_df = load_sheet_data(sheet, "Accounts")

# --- Streamlit Layout ---
st.set_page_config(layout="wide", page_title="💰 Finance Tracker")
st.title("💰 Personal Finance Dashboard with Google Sheets")

# Income Section
st.header("📥 Income Overview")
st.dataframe(income_df)

# Expenses Section
st.header("💸 Expense Overview")
st.dataframe(expense_df)

# Spending by Category (if Date and Category exist)
if "Category" in expense_df.columns:
    fig_expense = px.pie(expense_df, names="Category", values="Amount", title="Spending by Category")
    st.plotly_chart(fig_expense)

# Debts Section
st.header("📉 Debt Tracker")
st.dataframe(debts_df)

# Goals Section
st.header("🎯 Savings Goals")
st.dataframe(goals_df)

# Accounts Section
st.header("🏦 Account Balances")
st.dataframe(accounts_df)

# Net Worth Calculation
try:
    total_assets = accounts_df["Balance"].sum()
    total_debts = debts_df["Balance"].sum()
    net_worth = total_assets - total_debts
    st.metric("📊 Net Worth", f"${net_worth:,.2f}")
except Exception as e:
    st.warning("Could not calculate net worth. Check data format.")
