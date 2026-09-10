import os
from datetime import datetime, timezone
from flask import Flask, jsonify
import yfinance as yf
from google.cloud import bigquery

app = Flask(__name__)

# Target production tables
PROJECT_ID = "src-exchange-rate"
DATASET_ID = "raw"
TABLE_ID = "daily_exchange_rates"
TABLE_FULL_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

def extract_daily_rate():
    print("Fetching today's market close rates...")
    # Fetching latest 1d data point
    tickers = yf.download(["USDEUR=X", "USDPEN=X"], period="1d", interval="1d")
    df_close = tickers['Close'].reset_index()
    
    if df_close.empty:
        return "No new market data available right now."

    latest_row = df_close.iloc[-1]
    rate_date = latest_row['Date'].strftime('%Y-%m-%d')

    record = {
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "base_currency": "USD",
        "rates_date": rate_date,
        "rate_eur": float(latest_row['USDEUR=X']),
        "rate_pen": float(latest_row['USDPEN=X'])
    }

    # Cloud Run automatically authenticates via its assigned Service Account
    client = bigquery.Client(project=PROJECT_ID)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    print(f"Loading row for date {rate_date} into BigQuery...")
    job = client.load_table_from_json([record], TABLE_FULL_ID, job_config=job_config)
    job.result()
    
    return f"Successfully appended row for date {rate_date} into {TABLE_FULL_ID}."

@app.route("/", methods=["GET", "POST"])
def trigger():
    try:
        msg = extract_daily_rate()
        return jsonify({"status": "success", "detail": msg}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))