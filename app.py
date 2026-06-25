import os
import site
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
site.addsitedir(str(ROOT / ".python_packages"))

import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.offline import get_plotlyjs
from flask import Flask, Response, jsonify, make_response, render_template, request

from analytics import enrich_customers
from database import cleaning_report, load_customers

COLORS = {
    "navy": "#10253f", "ink": "#172235", "muted": "#6d7888", "teal": "#21a69a",
    "red": "#db5b5b", "orange": "#f29b4b", "line": "#e7ebf0",
}

app = Flask(__name__, static_folder="assets")


def load_data():
    raw, source = load_customers()
    return enrich_customers(raw), source


def filter_data(df, view, segment):
    if view == "high":
        df = df[df["risk_level"] == "High"]
    elif view == "active":
        df = df[df["churned"] == 0]
    if segment != "all":
        df = df[df["segment"] == segment]
    return df


def chart_layout(height=250):
    return {
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 20, "r": 10, "t": 10, "b": 25}, "height": height,
        "font": {"family": "DM Sans", "color": COLORS["muted"], "size": 11},
        "xaxis": {"gridcolor": COLORS["line"], "linecolor": COLORS["line"]},
        "yaxis": {"gridcolor": COLORS["line"], "linecolor": COLORS["line"]},
        "hoverlabel": {"bgcolor": COLORS["navy"], "font_color": "white"},
    }


def build_payload(view="all", segment="all"):
    customers, source = load_data()
    df = filter_data(customers, view, segment)
    at_risk = df[df["risk_score"] >= 50]
    high_risk = df[df["risk_score"] >= 75]

    risk_order = ["Low", "Medium", "High"]
    risk_counts = df["risk_level"].value_counts().reindex(risk_order, fill_value=0)
    risk_fig = px.bar(
        x=risk_order, y=risk_counts.values, color=risk_order,
        color_discrete_map={"Low": COLORS["teal"], "Medium": COLORS["orange"], "High": COLORS["red"]},
    )
    risk_fig.update_layout(**chart_layout(), showlegend=False, xaxis_title="", yaxis_title="")
    risk_fig.update_traces(marker_cornerradius=6, hovertemplate="%{x} risk: %{y} customers<extra></extra>")

    drivers = at_risk.groupby("primary_driver", as_index=False)["monthly_revenue"].sum().sort_values("monthly_revenue")
    driver_fig = px.bar(drivers, x="monthly_revenue", y="primary_driver", orientation="h", color_discrete_sequence=[COLORS["teal"]])
    driver_fig.update_layout(**chart_layout(), xaxis_title="", yaxis_title="")
    driver_fig.update_traces(marker_cornerradius=5, hovertemplate="Rs. %{x:,.0f} MRR<extra></extra>")

    groups = df.groupby(["operator", "plan_type"], as_index=False)["risk_score"].mean()
    segment_fig = px.scatter(
        groups, x="operator", y="risk_score", size="risk_score", color="plan_type", size_max=34,
    )
    segment_fig.update_layout(**chart_layout(), xaxis_title="", yaxis_title="Average risk", legend_title="")

    city_risk = (
        df.groupby(["city", "state"], as_index=False)
        .agg(risk_score=("risk_score", "mean"), customers=("customer_id", "count"))
        .sort_values("risk_score", ascending=False)
        .head(10)
    )
    city_fig = px.bar(
        city_risk.sort_values("risk_score"),
        x="risk_score",
        y="city",
        orientation="h",
        color="risk_score",
        color_continuous_scale=["#16a34a", "#f59e0b", "#dc2626"],
    )
    city_fig.update_layout(**chart_layout(), xaxis_title="Average risk", yaxis_title="", coloraxis_showscale=False)

    recommendations = []
    for action, group in at_risk.groupby("recommended_action"):
        recommendations.append({
            "action": action,
            "customers": len(group),
            "revenue": f"Rs. {group['monthly_revenue'].sum():,.0f}",
        })

    table = df.sort_values("risk_score", ascending=False).head(30)
    customers_json = [{
        "customer_id": row.customer_id, "name": row.customer_name, "email": row.email, "segment": row.segment,
        "risk": int(row.risk_score), "level": row.risk_level, "driver": row.primary_driver,
        "mrr": f"Rs. {row.monthly_revenue:,.0f}", "action": row.recommended_action,
        "city": row.city, "state": row.state, "operator": row.operator, "plan_type": row.plan_type,
    } for row in table.itertuples()]

    return {
        "source": source,
        "cleaning": cleaning_report(),
        "metrics": {
            "risk_count": f"{len(at_risk):,}",
            "churn_rate": f"{df['risk_score'].mean() * 0.105:.1f}%" if len(df) else "0.0%",
            "revenue_risk": f"Rs. {high_risk['monthly_revenue'].sum():,.0f}",
            "retention_value": f"Rs. {high_risk['monthly_revenue'].sum() * 0.42:,.0f}",
        },
        "charts": {
            "risk": pio.to_json(risk_fig),
            "drivers": pio.to_json(driver_fig),
            "segments": pio.to_json(segment_fig),
            "cities": pio.to_json(city_fig),
        },
        "recommendations": recommendations,
        "customers": customers_json,
        "segments": sorted(customers["segment"].unique().tolist()),
    }


@app.get("/")
def dashboard():
    return render_template("index.html", payload=build_payload())


@app.get("/plotly.min.js")
def plotly_js():
    return Response(get_plotlyjs(), mimetype="application/javascript")


@app.get("/api/dashboard")
def dashboard_api():
    return jsonify(build_payload(request.args.get("view", "all"), request.args.get("segment", "all")))


@app.get("/api/customer/<customer_id>")
def customer_detail(customer_id):
    customers, source = load_data()
    row = customers[customers["customer_id"].eq(customer_id)]
    if row.empty:
        return jsonify({"error": "Customer not found"}), 404
    record = row.iloc[0]
    return jsonify({
        "source": source,
        "customer_id": record.customer_id,
        "name": record.customer_name,
        "email": record.email,
        "segment": record.segment,
        "contract_type": record.contract_type,
        "tenure_months": int(record.tenure_months),
        "monthly_revenue": f"Rs. {record.monthly_revenue:,.0f}",
        "city": record.city,
        "state": record.state,
        "operator": record.operator,
        "plan_type": record.plan_type,
        "usage_change_pct": f"{record.usage_change_pct:.0f}%",
        "support_tickets": int(record.support_tickets),
        "nps_score": int(record.nps_score),
        "payment_failures": int(record.payment_failures),
        "last_login_days": int(record.last_login_days),
        "risk_score": int(record.risk_score),
        "risk_level": record.risk_level,
        "primary_driver": record.primary_driver,
        "recommended_action": record.recommended_action,
    })


@app.get("/api/export")
def export_customers():
    customers, _ = load_data()
    df = filter_data(enrich_customers(customers), request.args.get("view", "all"), request.args.get("segment", "all"))
    export = df[[
        "customer_id", "customer_name", "email", "segment", "contract_type",
        "city", "state", "operator", "plan_type", "monthly_revenue",
        "risk_score", "risk_level", "primary_driver", "recommended_action",
    ]]
    response = make_response(export.to_csv(index=False))
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=customer_churn_watchlist.csv"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("APP_PORT", "8050")), debug=os.getenv("APP_DEBUG", "false").lower() == "true")
