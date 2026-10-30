import os
from datetime import datetime, timezone
import yfinance as yf
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "src-exchange-rate"
DATASET_ID = "raw"
TABLE_ID = "historical_exchange_rates"
TABLE_FULL_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
KEY_FILE_PATH = "/home/renzo/Downloads/dbt-analytics-500510-3c0894f4c520.json"

def run_backfill():
    print("Downloading 2 years of daily historical forex data from Yahoo Finance...")
    tickers = yf.download(["USDEUR=X", "USDPEN=X"], period="2y", interval="1d")
    df_close = tickers['Close'].reset_index()
    
    records = []
    for _, row in df_close.iterrows():
        rate_date = row['Date'].strftime('%Y-%m-%d')
        
        # Guard against empty values on weekend market closures
        if hasattr(row, 'USDEUR=X') and hasattr(row, 'USDPEN=X'):
            records.append({
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                "base_currency": "USD",
                "rates_date": rate_date,
                "rate_eur": float(row['USDEUR=X']),
                "rate_pen": float(row['USDPEN=X'])
            })
            
    if not records:
        print("No historical data records found.")
        return

    # Stream into BigQuery
    credentials = service_account.Credentials.from_service_account_file(KEY_FILE_PATH)
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

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

    print(f"Loading {len(records)} daily historical rows into BigQuery...")
    job = client.load_table_from_json(records, TABLE_FULL_ID, job_config=job_config)
    job.result()
    print("Historical backfill completed successfully!")

if __name__ == "__main__":
    run_backfill()
