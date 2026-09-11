WITH historical_and_daily AS (
  SELECT  
    extraction_timestamp,
    rates_date,
    rate_eur,
    rate_pen
  FROM {{ ref('historical_exchange_rates')}}

  UNION ALL

  SELECT  
    extraction_timestamp,
    rates_date,
    rate_eur,
    rate_pen
  FROM {{ ref('daily_exchange_rates') }}
),

ranked_rates AS (
  SELECT  
    rates_date,
    rate_eur,
    rate_pen,
    ROW_NUMBER() OVER (
      PARTITION BY rates_date 
      ORDER BY extraction_timestamp DESC
    ) AS row_num
  FROM historical_and_daily
)

SELECT *
FROM ranked_rates