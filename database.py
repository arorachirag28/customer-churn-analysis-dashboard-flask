import os
from contextlib import closing
from pathlib import Path

import mysql.connector
import pandas as pd
from dotenv import load_dotenv
from cleaning import clean_customers

load_dotenv()

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
KAGGLE_CSV = Path(os.getenv("KAGGLE_DATA_PATH", DATA_DIR / "kaggle_churn.csv"))
INDIAN_SAMPLE_CSV = DATA_DIR / "indian_customer_churn_sample.csv"

INDIAN_CITIES = [
    ("Mumbai", "Maharashtra"), ("Delhi", "Delhi"), ("Bengaluru", "Karnataka"),
    ("Hyderabad", "Telangana"), ("Chennai", "Tamil Nadu"), ("Kolkata", "West Bengal"),
    ("Pune", "Maharashtra"), ("Ahmedabad", "Gujarat"), ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh"), ("Kochi", "Kerala"), ("Indore", "Madhya Pradesh"),
]
OPERATORS = ["Jio", "Airtel", "Vi", "BSNL"]
PLANS = ["Prepaid", "Postpaid", "Broadband", "Family Plan"]


def connection_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "churn_analytics"),
        "connection_timeout": 3,
    }


def load_mysql_customers():
    with closing(mysql.connector.connect(**connection_config())) as connection:
        return pd.read_sql(
            """
            SELECT customer_id, customer_name, email, segment, contract_type,
                   city, state, operator, plan_type,
                   tenure_months, monthly_revenue, usage_change_pct,
                   support_tickets, nps_score, payment_failures,
                   last_login_days, churned
            FROM customers
            """,
            connection,
        )


LAST_CLEANING_REPORT = {}


def load_customers():
    global LAST_CLEANING_REPORT
    if KAGGLE_CSV.exists():
        cleaned, report = clean_customers(standardize_churn_csv(KAGGLE_CSV))
        LAST_CLEANING_REPORT = report
        return cleaned, "Kaggle CSV + Indian enrichment"
    try:
        customers = load_mysql_customers()
        cleaned, report = clean_customers(add_indian_context(customers))
        LAST_CLEANING_REPORT = report
        return cleaned, "MySQL connected"
    except Exception:
        cleaned, report = clean_customers(standardize_churn_csv(INDIAN_SAMPLE_CSV))
        LAST_CLEANING_REPORT = report
        return cleaned, "Indian sample data"


def cleaning_report():
    return LAST_CLEANING_REPORT


def standardize_churn_csv(path):
    source = pd.read_csv(path)
    source.columns = [str(column).strip() for column in source.columns]
    normalized = pd.DataFrame()
    normalized["customer_id"] = pick_column(source, ["customer_id", "CustomerID", "customerID"], prefix="IND")
    normalized["customer_name"] = pick_column(source, ["customer_name", "Name", "Customer Name"], default_names=True)
    normalized["email"] = normalized["customer_id"].astype(str).str.lower().str.replace(r"[^a-z0-9]+", "", regex=True) + "@example.in"
    normalized["segment"] = pick_segment(source)
    normalized["contract_type"] = pick_contract(source)
    normalized["tenure_months"] = numeric_column(source, ["tenure_months", "tenure", "Tenure"], fallback=12).clip(1, 84)
    normalized["monthly_revenue"] = numeric_column(
        source, ["monthly_revenue", "MonthlyCharges", "Monthly Charge", "EstimatedSalary", "Balance"], fallback=899
    ).clip(199, 25000)
    normalized["usage_change_pct"] = numeric_column(source, ["usage_change_pct", "Usage Change", "usage_change"], fallback=-8).clip(-80, 40)
    normalized["support_tickets"] = numeric_column(source, ["support_tickets", "Support Tickets", "NumOfProducts"], fallback=1).clip(0, 5).astype(int)
    normalized["nps_score"] = numeric_column(source, ["nps_score", "NPS", "Satisfaction Score", "CreditScore"], fallback=6).clip(1, 10).astype(int)
    normalized["payment_failures"] = numeric_column(source, ["payment_failures", "Payment Failures"], fallback=0).clip(0, 3).astype(int)
    normalized["last_login_days"] = numeric_column(source, ["last_login_days", "Last Login Days"], fallback=9).clip(1, 60).astype(int)
    normalized["churned"] = churn_column(source)
    return add_indian_context(normalized, source)


def pick_column(df, names, prefix=None, default_names=False):
    for name in names:
        if name in df.columns:
            return df[name].astype(str)
    if default_names:
        names = [
            "Aarav Sharma", "Priya Nair", "Rohan Mehta", "Sneha Iyer", "Arjun Reddy",
            "Ananya Gupta", "Vikram Singh", "Kavya Menon", "Rahul Verma", "Neha Patil",
            "Aditya Rao", "Pooja Das", "Karan Malhotra", "Meera Joshi", "Siddharth Jain",
        ]
        return pd.Series([names[i % len(names)] for i in range(len(df))])
    return pd.Series([f"{prefix}-{1001 + i}" for i in range(len(df))])


def numeric_column(df, names, fallback):
    for name in names:
        if name in df.columns:
            values = pd.to_numeric(df[name], errors="coerce")
            if values.max(skipna=True) and name in ["CreditScore", "EstimatedSalary", "Balance"]:
                values = values.rank(pct=True) * 9 + 1 if name == "CreditScore" else values / 100
            return values.fillna(fallback)
    return pd.Series([fallback + ((i % 9) - 4) for i in range(len(df))])


def pick_segment(df):
    for name in ["segment", "Segment", "Customer Segment"]:
        if name in df.columns:
            return df[name].astype(str)
    if "InternetService" in df.columns:
        return df["InternetService"].replace({"Fiber optic": "Premium", "DSL": "Standard", "No": "Basic"})
    if "Geography" in df.columns:
        return df["Geography"].replace({"France": "Urban", "Spain": "Semi-urban", "Germany": "Metro"})
    return pd.Series([["Urban", "Semi-urban", "Rural", "Metro"][i % 4] for i in range(len(df))])


def pick_contract(df):
    for name in ["contract_type", "Contract", "Subscription Type"]:
        if name in df.columns:
            return df[name].astype(str).replace({"One year": "Annual", "Two year": "Annual"})
    return pd.Series(["Month-to-month" if i % 3 else "Annual" for i in range(len(df))])


def churn_column(df):
    for name in ["churned", "Churn", "Exited", "churn"]:
        if name in df.columns:
            return df[name].astype(str).str.lower().isin(["1", "yes", "true", "churned"]).astype(int)
    return pd.Series([(i % 5 == 0) for i in range(len(df))]).astype(int)


def add_indian_context(customers, source=None):
    df = customers.copy()
    source = source if source is not None else pd.DataFrame(index=df.index)
    for column, values in [
        ("city", [city for city, _ in INDIAN_CITIES]),
        ("state", [state for _, state in INDIAN_CITIES]),
        ("operator", OPERATORS),
        ("plan_type", PLANS),
    ]:
        if column in source.columns:
            df[column] = source[column].astype(str)
        elif column not in df.columns:
            df[column] = [values[i % len(values)] for i in range(len(df))]
    return df
