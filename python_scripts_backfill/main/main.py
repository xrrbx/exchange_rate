import os
from datetime import datetime, timezone
from flask import Flask, jsonify
import yfinance as yf
from google.cloud import bigquery

app = Flask(__name__)

PROJECT_ID = "src-exchange-rate"
DATASET_ID = "raw"
TABLE_ID = "historical_exchange_rates"
TABLE_FULL_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

def run_backfill():
    tickers = yf.download(["USDEUR=X", "USDPEN=X"], period="2y", interval="1d")
    df_close = tickers['Close'].reset_index()
    
    records = []
    for _, row in df_close.iterrows():
        rate_date = row['Date'].strftime('%Y-%m-%d')
        if hasattr(row, 'USDEUR=X') and hasattr(row, 'USDPEN=X'):
            records.append({
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                "base_currency": "USD",
                "rates_date": rate_date,
                "rate_eur": float(row['USDEUR=X']),
                "rate_pen": float(row['USDPEN=X'])
            })
            
    if not records:
        return "No records found"

    # Cloud Run automatically picks up identity credentials natively
    client = bigquery.Client(project=PROJECT_ID)

    schema = [
        bigquery.SchemaField("extraction_timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("base_currency", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("rates_date", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("rate_eur", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("rate_pen", "FLOAT", mode="REQUIRED"),
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = client.load_table_from_json(records, TABLE_FULL_ID, job_config=job_config)
    job.result()
    return f"Loaded {len(records)} rows successfully."

@app.route("/", methods=["GET", "POST"])
def trigger():
    try:
        msg = run_backfill()
        return jsonify({"status": "success", "detail": msg}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))