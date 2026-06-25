import numpy as np
import pandas as pd


def enrich_customers(customers):
    df = customers.copy()
    score = (
        np.where(df["contract_type"].eq("Month-to-month"), 18, 2)
        + np.clip(-df["usage_change_pct"], 0, 70) * 0.55
        + np.clip(df["support_tickets"], 0, 5) * 6
        + np.clip(7 - df["nps_score"], 0, 7) * 4
        + np.clip(df["payment_failures"], 0, 3) * 9
        + np.clip(df["last_login_days"] - 5, 0, 45) * 0.45
        + np.where(df["tenure_months"] < 6, 7, 0)
    )
    df["risk_score"] = np.clip(score, 4, 98).round().astype(int)
    df["risk_level"] = pd.cut(
        df["risk_score"], bins=[0, 49, 74, 100], labels=["Low", "Medium", "High"]
    ).astype(str)
    df["primary_driver"] = df.apply(primary_driver, axis=1)
    df["recommended_action"] = df["primary_driver"].map(
        {
            "Low product engagement": "Schedule success outreach",
            "Poor support experience": "Escalate support resolution",
            "Pricing sensitivity": "Offer annual plan incentive",
            "Payment friction": "Resolve billing issue",
            "Weak customer sentiment": "Book executive check-in",
            "Early-stage adoption": "Launch onboarding play",
        }
    )
    return df


def primary_driver(row):
    candidates = {
        "Low product engagement": max(-row["usage_change_pct"], 0) + row["last_login_days"],
        "Poor support experience": row["support_tickets"] * 14,
        "Pricing sensitivity": 28 if row["contract_type"] == "Month-to-month" else 4,
        "Payment friction": row["payment_failures"] * 22,
        "Weak customer sentiment": max(8 - row["nps_score"], 0) * 7,
        "Early-stage adoption": 22 if row["tenure_months"] < 6 else 0,
    }
    return max(candidates, key=candidates.get)

