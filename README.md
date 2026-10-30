# ELT 

This Streamlit app shows the trend of three specific currencies compared to each other:
* Euro (€ - EUR)
* US Dollar ($ - USD)
* Peruvian Nuevo Sol (S/. - PEN)


## Extracting - Data Source:
Yahoo Finance API

## Loading - BigQuery
Done with a python script, including GCP credentials for authentication

## Transforming - SQL in dbt
All transformation is done in dbt, with version control

## Presenting - Streamlit
Dashboard made as an app on Streamlit: https://github.com/xrrbx/streamlit_fx

