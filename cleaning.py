import pandas as pd

NUMERIC_RULES = {
    "tenure_months": (1, 84, 12),
    "monthly_revenue": (199, 25000, 899),
    "usage_change_pct": (-80, 40, -8),
    "support_tickets": (0, 5, 1),
    "nps_score": (1, 10, 6),
    "payment_failures": (0, 3, 0),
    "last_login_days": (1, 60, 9),
}


def clean_customers(customers):
    before_rows = len(customers)
    before_missing = int(customers.isna().sum().sum())
    df = customers.copy()

    df.columns = [str(column).strip().lower() for column in df.columns]
    ensure_required_columns(df)

    for column in ["customer_id", "customer_name", "email", "city", "state", "operator", "plan_type", "segment", "contract_type"]:
        df[column] = df[column].astype(str).str.strip()
        df[column] = df[column].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    df["customer_id"] = df["customer_id"].fillna(pd.Series([f"IND-{1001 + i}" for i in range(len(df))]))
    df["customer_name"] = df["customer_name"].fillna("Unknown Customer")
    df["email"] = df["email"].fillna(df["customer_id"].str.lower() + "@example.in")
    df["city"] = title_fill(df["city"], "Mumbai")
    df["state"] = title_fill(df["state"], "Maharashtra")
    df["operator"] = clean_operator(df["operator"])
    df["plan_type"] = clean_plan(df["plan_type"])
    df["segment"] = clean_segment(df["segment"])
    df["contract_type"] = clean_contract(df["contract_type"])

    clipped_values = 0
    for column, (lower, upper, fallback) in NUMERIC_RULES.items():
        values = pd.to_numeric(df[column], errors="coerce").fillna(fallback)
        clipped_values += int(((values < lower) | (values > upper)).sum())
        values = values.clip(lower, upper)
        if column in ["support_tickets", "nps_score", "payment_failures", "last_login_days", "tenure_months"]:
            values = values.round().astype(int)
        df[column] = values

    df["churned"] = df["churned"].astype(str).str.lower().isin(["1", "yes", "true", "churned"]).astype(int)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    df = df.reset_index(drop=True)

    after_missing = int(df.isna().sum().sum())
    report = {
        "rows_before": before_rows,
        "rows_after": len(df),
        "duplicates_removed": before_rows - len(df),
        "missing_values_before": before_missing,
        "missing_values_after": after_missing,
        "out_of_range_values_fixed": clipped_values,
        "status": "Clean" if after_missing == 0 else "Needs review",
    }
    return df, report


def ensure_required_columns(df):
    defaults = {
        "customer_id": pd.NA,
        "customer_name": pd.NA,
        "email": pd.NA,
        "city": "Mumbai",
        "state": "Maharashtra",
        "operator": "Jio",
        "plan_type": "Prepaid",
        "segment": "Urban",
        "contract_type": "Month-to-month",
        "churned": 0,
    }
    for column, (_, _, fallback) in NUMERIC_RULES.items():
        defaults[column] = fallback
    for column, default in defaults.items():
        if column not in df.columns:
            df[column] = default


def title_fill(series, fallback):
    return series.fillna(fallback).astype(str).str.strip().str.title()


def clean_operator(series):
    values = series.fillna("Jio").astype(str).str.strip().str.lower()
    mapping = {"reliance jio": "Jio", "jio": "Jio", "airtel": "Airtel", "bharti airtel": "Airtel", "vi": "Vi", "vodafone idea": "Vi", "bsnl": "BSNL"}
    return values.map(mapping).fillna(values.str.title())


def clean_plan(series):
    values = series.fillna("Prepaid").astype(str).str.strip().str.lower()
    mapping = {"prepaid": "Prepaid", "postpaid": "Postpaid", "broadband": "Broadband", "family": "Family Plan", "family plan": "Family Plan"}
    return values.map(mapping).fillna(values.str.title())


def clean_segment(series):
    values = series.fillna("Urban").astype(str).str.strip().str.lower()
    mapping = {
        "urban": "Urban", "semi-urban": "Semi-urban", "semi urban": "Semi-urban",
        "rural": "Rural", "metro": "Metro", "premium": "Premium", "standard": "Standard", "basic": "Basic",
    }
    return values.map(mapping).fillna(values.str.title())


def clean_contract(series):
    values = series.fillna("Month-to-month").astype(str).str.strip().str.lower()
    annual = values.isin(["annual", "one year", "two year", "1 year", "2 year", "yearly"])
    return pd.Series(["Annual" if is_annual else "Month-to-month" for is_annual in annual], index=series.index)
