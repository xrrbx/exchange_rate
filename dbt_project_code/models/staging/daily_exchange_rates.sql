SELECT  
    extraction_timestamp,
    rates_date,
    rate_eur,
    rate_pen,
FROM {{ source('raw_api_data', 'daily_exchange_rates') }}
    WHERE SAFE_CAST(rates_date AS DATE) is not null