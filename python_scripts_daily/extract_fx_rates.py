import os
from datetime import datetime, timezone
import yfinance as yf
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "src-exchange-rate"
DATASET_ID = "raw"
TABLE_ID = "daily_exchange_rates"
TABLE_FULL_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
KEY_FILE_PATH = "/home/renzo/Downloads/dbt-analytics-500510-3c0894f4c520.json"

def extract_daily_rate():
    print("Fetching today's market close rates...")
    # Grabbing just the last day's data point
    tickers = yf.download(["USDEUR=X", "USDPEN=X"], period="1d", interval="1d")
    df_close = tickers['Close'].reset_index()
    
    if df_close.empty:
        print("No new market data available right now.")
        return

    latest_row = df_close.iloc[-1]
    rate_date = latest_row['Date'].strftime('%Y-%m-%d')

    record = {
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "base_currency": "USD",
        "rates_date": rate_date,
        "rate_eur": float(latest_row['USDEUR=X']),
        "rate_pen": float(latest_row['USDPEN=X'])
    }

    credentials = service_account.Credentials.from_service_account_file(KEY_FILE_PATH)
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = client.load_table_from_json([record], TABLE_FULL_ID, job_config=job_config)
    job.result()
    print(f"Successfully appended row for date {rate_date} into {TABLE_FULL_ID}.")

if __name__ == "__main__":
    extract_daily_rate()