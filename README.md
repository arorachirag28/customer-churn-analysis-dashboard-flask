# Indian Customer Churn Dashboard

A simple fresher-style dashboard built with **Python, Flask, MySQL, Pandas, and Plotly**.

## What It Shows

- Customers likely to churn
- Reasons for churn
- High-risk Indian cities
- Operator and plan risk
- Retention suggestions
- Customer watchlist with drill-down
- CSV export
- Data cleaning report with duplicate, missing value, and range checks

## Data Priority

The app loads data in this order:

1. `data/kaggle_churn.csv`
2. MySQL table `churn_analytics.customers`
3. Built-in Indian sample file `data/indian_customer_churn_sample.csv`

So the dashboard works even if Kaggle credentials are not available.

## Kaggle Dataset

Kaggle downloads usually need an API token.

1. Create/download your Kaggle API token from Kaggle account settings.
2. Save it at:

   ```text
   C:\Users\<your-user>\.kaggle\kaggle.json
   ```

3. Run:

   ```powershell
   .\download_kaggle_data.ps1
   ```

By default, the script downloads `blastchar/telco-customer-churn` and saves the CSV as:

```text
data\kaggle_churn.csv
```

You can use another Kaggle dataset by setting:

```powershell
$env:KAGGLE_DATASET="dataset-owner/dataset-name"
.\download_kaggle_data.ps1
```

The app maps common Kaggle churn columns and enriches the rows with Indian city, state, operator, and plan details.

## Data Cleaning

Before charts are created, all rows pass through `cleaning.py`.

It performs:

- Duplicate removal by `customer_id`
- Missing value handling
- Category standardization
- Churn label normalization
- Numeric range checks
- Revenue and usage clipping for invalid values
- Cleaning report shown inside the dashboard

## Run

```powershell
.\run.ps1
```

Open:

```text
http://127.0.0.1:8050
```

## MySQL Setup

```powershell
.\setup_mysql.ps1
```

Then copy `.env.example` to `.env` and enter your MySQL credentials.
