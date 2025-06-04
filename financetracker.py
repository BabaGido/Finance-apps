import streamlit as st
import pandas as pd
import json
from google.oauth2.service_account import Credentials
import gspread
import plotly.express as px

# === IMPORTANT: Page config must be the first Streamlit call ===
st.set_page_config(layout="wide", page_title="💰 Finance Tracker")

# --- Configuration ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_KEY = "17tlk2_x8sSFl60JRW8ngfDBxvdTUwmWdusXgLim6Yvw"  # exact /d/.../ portion

# --- Authenticate and Connect to Google Sheets ---
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

# Attempt to open the spreadsheet; if it fails, show an error and stop
try:
    sheet = client.open_by_key(SHEET_KEY)
except Exception as e:
    st.error(f"❌ Could not open spreadsheet with key {SHEET_KEY}: {e}")
    st.stop()

# --- Caching wrapper so we don’t re‐hit the API on every rerun ---
@st.cache_data(ttl=300)
def load_sheet_data(tab_name: str) -> pd.DataFrame:
    """
    Load a single worksheet into a DataFrame, and cache it for 5 minutes.
    """
    try:
        ws = sheet.worksheet(tab_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        # Because set_page_config is already called, this st.error is safe
        st.error(f"❌ Could not load tab '{tab_name}': {e}")
        return pd.DataFrame()

# Load each worksheet once and cache it
income_df   = load_sheet_data("Income_Log")
expense_df  = load_sheet_data("Expense_Log")
debts_df    = load_sheet_data("Debts_Tracker")
goals_df    = load_sheet_data("Savings_Goals")
accounts_df = load_sheet_data("Accounts")

# --- Page Title ---
st.title("💰 Personal Finance Dashboard with Google Sheets")

# === INCOME SECTION ===
st.header("📥 Income Overview")
income_df["Date"] = pd.to_datetime(income_df["Date"], errors="coerce")
st.dataframe(income_df)

# Manually assign categories to Income rows
if "Category" in income_df.columns:
    income_df = income_df.drop(columns=["Category"])
income_df["Category"] = ""
income_categories = ["Salary", "Refund", "Other"]

st.write("**Assign a category to each income entry:**")
for idx, row in income_df.iterrows():
    label = f"{row['Date'].date()} – {row['Description']} ($ {row['Amount']})"
    widget_key = f"income_cat_{idx}"
    choice = st.selectbox(
        label,
        options=[""] + income_categories,
        key=widget_key
    )
    if choice in income_categories:
        income_df.at[idx, "Category"] = choice

st.subheader("📊 Your Categorized Income")
st.dataframe(income_df)

if st.button("Save Income Categories to Sheet"):
    worksheet = sheet.worksheet("Income_Log")
    values = [income_df.columns.to_list()] + income_df.fillna("").astype(str).values.tolist()
    worksheet.clear()
    worksheet.update(values)
    st.success("✅ Income categories saved back to Google Sheet!")

# Monthly Income Bar Chart
income_df["Month"] = income_df["Date"].dt.to_period("M").astype(str)
monthly_income = income_df.groupby("Month")["Amount"].sum().reset_index()
st.subheader("📅 Monthly Income Summary")
st.bar_chart(monthly_income.set_index("Month"))

# === EXPENSE SECTION ===
st.header("💸 Expense Overview")
expense_df["Date"] = pd.to_datetime(expense_df["Date"], errors="coerce")
if "Category" in expense_df.columns:
    expense_df = expense_df.drop(columns=["Category"])
expense_df["Category"] = ""
expense_categories = ["Fixed", "Variable", "Other"]

st.write("**Assign a category to each expense entry:**")
for idx, row in expense_df.iterrows():
    label = f"{row['Date'].date()} – {row['Description']} ($ {row['Amount']})"
    widget_key = f"expense_cat_{idx}"
    choice = st.selectbox(
        label,
        options=[""] + expense_categories,
        key=widget_key
    )
    if choice in expense_categories:
        expense_df.at[idx, "Category"] = choice

st.subheader("📊 Your Categorized Expenses")
st.dataframe(expense_df)

if st.button("Save Expense Categories to Sheet"):
    worksheet = sheet.worksheet("Expense_Log")
    values = [expense_df.columns.to_list()] + expense_df.fillna("").astype(str).values.tolist()
    worksheet.clear()
    worksheet.update(values)
    st.success("✅ Expense categories saved back to Google Sheet!")

# Filter by chosen expense category
category_filter = st.selectbox(
    "Filter Expense by Category",
    options=["All"] + expense_categories
)
if category_filter == "All":
    to_show = expense_df
else:
    to_show = expense_df[expense_df["Category"] == category_filter]

st.subheader(f"📊 {category_filter} Expenses")
st.dataframe(to_show)

# Spending by Category Pie Chart
spend_by_cat = (
    expense_df[expense_df["Category"] != ""]
    .groupby("Category")["Amount"]
    .sum()
    .reset_index()
    .sort_values("Amount", ascending=False)
)
fig_expense = px.pie(
    spend_by_cat,
    names="Category",
    values="Amount",
    title="Spending by Category",
    hole=0.4
)
st.plotly_chart(fig_expense, use_container_width=True)

# === DEBT TRACKER SECTION ===
st.header("📉 Debt Tracker")
debts_df["Date"] = pd.to_datetime(debts_df["Date"], errors="coerce")
if "Category" in debts_df.columns:
    debts_df = debts_df.drop(columns=["Category"])
debts_df["Category"] = ""
debt_categories = ["Credit Card", "Mortgage", "Auto Loan", "Student Loan", "Personal Loan", "Other"]

st.write("**Assign a category to each debt entry:**")
for idx, row in debts_df.iterrows():
    label = f"{row['Date'].date()} – {row['Description']} ($ {row['Amount']})"
    widget_key = f"debt_cat_{idx}"
    choice = st.selectbox(
        label,
        options=[""] + debt_categories,
        key=widget_key
    )
    if choice in debt_categories:
        debts_df.at[idx, "Category"] = choice

st.subheader("📊 Your Categorized Debts")
st.dataframe(debts_df)

if st.button("Save Debt Categories to Sheet"):
    worksheet = sheet.worksheet("Debts_Tracker")
    values = [debts_df.columns.to_list()] + debts_df.fillna("").astype(str).values.tolist()
    worksheet.clear()
    worksheet.update(values)
    st.success("✅ Debt categories saved back to Google Sheet!")
    
spend_by_debt = (
    debts_df[debts_df["Category"] != ""]
    .groupby("Category")["Amount"]
    .sum()
    .reset_index()
    .sort_values("Amount", ascending=False)
)
fig_debt = px.pie(
    spend_by_debt,
    names="Category",
    values="Amount",
    title="Debt by Category",
    hole=0.4
)
st.plotly_chart(fig_debt, use_container_width=True)

# === SAVINGS GOALS SECTION ===
st.header("🎯 Savings Goals")
goals_df["Date"] = pd.to_datetime(goals_df["Date"], errors="coerce")
if "Category" in goals_df.columns:
    goals_df = goals_df.drop(columns=["Category"])
goals_df["Category"] = ""
savings_categories = ["Emergency Fund", "Down Payment", "College Tuition", "Travel", "Other"]

st.write("**Assign a category to each savings goal:**")
for idx, row in goals_df.iterrows():
    label = f"{row['Date'].date()} – {row['Description']} ($ {row['Amount']})"
    widget_key = f"goal_cat_{idx}"
    choice = st.selectbox(
        label,
        options=[""] + savings_categories,
        key=widget_key
    )
    if choice in savings_categories:
        goals_df.at[idx, "Category"] = choice

st.subheader("📊 Your Categorized Savings Goals")
st.dataframe(goals_df)

if st.button("Save Savings Categories to Sheet"):
    worksheet = sheet.worksheet("Savings_Goals")
    values = [goals_df.columns.to_list()] + goals_df.fillna("").astype(str).values.tolist()
    worksheet.clear()
    worksheet.update(values)
    st.success("✅ Savings categories saved back to Google Sheet!")

# === ACCOUNTS SECTION ===
st.header("🏦 Account Balances")
accounts_df["Date"] = pd.to_datetime(accounts_df["Date"], errors="coerce")
if "Category" in accounts_df.columns:
    accounts_df = accounts_df.drop(columns=["Category"])
accounts_df["Category"] = ""
account_categories = ["Checking", "Savings", "Investment Portfolio"]

st.write("**Assign a category to each account balance entry:**")
for idx, row in accounts_df.iterrows():
    label = f"{row['Date'].date()} – {row['Description']} ($ {row['Amount']})"
    widget_key = f"account_cat_{idx}"
    choice = st.selectbox(
        label,
        options=[""] + account_categories,
        key=widget_key
    )
    if choice in account_categories:
        accounts_df.at[idx, "Category"] = choice

st.subheader("📊 Your Categorized Account Balances")
st.dataframe(accounts_df)

if st.button("Save Account Categories to Sheet"):
    worksheet = sheet.worksheet("Accounts")
    values = [accounts_df.columns.to_list()] + accounts_df.fillna("").astype(str).values.tolist()
    worksheet.clear()
    worksheet.update(values)
    st.success("✅ Account categories saved back to Google Sheet!")
# Savings by Categgory

save_by_cat = (
    goals_df[goals_df["Category"] != ""]
    .groupby("Category")["Amount"]
    .sum()
    .reset_index()
    .sort_values("Amount", ascending=False)
)
fig_savings = px.pie(
    save_by_cat,
    names="Category",
    values="Amount",
    title="Savings Goals by Category",
    hole=0.4
)
st.plotly_chart(fig_savings, use_container_width=True)

# === NET WORTH CALCULATION ===
try:
    total_assets = accounts_df["Amount"].sum()
    total_debts = debts_df["Amount"].sum()
    net_worth = total_assets - total_debts
    st.metric("📊 Net Worth", f"${net_worth:,.2f}")
except Exception:
    st.warning("Could not calculate net worth. Check data format.")
