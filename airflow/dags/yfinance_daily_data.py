from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Constants
SYMBOLS = ["AAPL", "GOOGL", "MSFT"]
START_DATE = "2024-01-01"
END_DATE = "2024-03-01"

def get_bank_info(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    return {
        "symbol": symbol,
        "industry": info.get("industry", "N/A"),
        "sector": info.get("sector", "N/A"),
        "employee_count": info.get("fullTimeEmployees", 0),
        "city": info.get("city", "N/A"),
        "phone": info.get("phone", "N/A"),
        "state": info.get("state", "N/A"),
        "country": info.get("country", "N/A"),
        "website": info.get("website", "N/A"),
        "address": info.get("address1", "N/A")
    }

def get_stock_data(symbol, start_date, end_date):
    stock = yf.Ticker(symbol)
    data = stock.history(start=start_date, end=end_date)
    data.reset_index(inplace=True)
    data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    data.insert(0, 'symbol', symbol)
    return data

def get_fundamentals(symbol):
    stock = yf.Ticker(symbol)
    balance = stock.balance_sheet
    return {
        "symbol": symbol,
        "period": datetime.today().strftime("%Y-%m"),  # YYYY-MM format
        "assets": balance.loc["Total Assets"].values[0] if "Total Assets" in balance.index else 0,
        "debt": balance.loc["Total Debt"].values[0] if "Total Debt" in balance.index else 0,
        "invested_capital": balance.loc["Invested Capital"].values[0] if "Invested Capital" in balance.index else 0,
        "shares_issued": balance.loc["Ordinary Shares Number"].values[0] if "Ordinary Shares Number" in balance.index else 0
    }

def get_holders(symbol):
    stock = yf.Ticker(symbol)
    holders = stock.institutional_holders
    if holders is not None:
        holders.insert(0, "symbol", symbol)
        holders["date"] = pd.Timestamp.today()
        return holders[["symbol", "date", "Holder", "Shares", "Value"]]
    return pd.DataFrame()

def insert_data_into_postgres():
    pg_hook = PostgresHook(postgres_conn_id="finance_db")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    
    for symbol in SYMBOLS:
        print(f"Buscando data para {symbol}...")

        stock_data = get_stock_data(symbol, START_DATE, END_DATE)
        fundamentals = get_fundamentals(symbol)
        bank_info = get_bank_info(symbol)
        holders = get_holders(symbol)

        cursor.execute("""
            INSERT INTO finance_data.company_registry.bank_info 
            (symbol, industry, sector, employee_count, city, phone, state, country, website, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO NOTHING;
        """, (
            bank_info["symbol"], bank_info["industry"], bank_info["sector"], 
            bank_info["employee_count"], bank_info["city"], bank_info["phone"], 
            bank_info["state"], bank_info["country"], bank_info["website"], bank_info["address"]
        ))

        print("Fundamentals: " + str(fundamentals))

        cursor.execute("""
            INSERT INTO finance_data.company_registry.fundamentals 
            (symbol, period, assets, debt, invested_capital, shares_issued)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, period) DO NOTHING;
        """, (
            fundamentals["symbol"], fundamentals["period"], fundamentals["assets"], 
            fundamentals["debt"], fundamentals["invested_capital"], fundamentals["shares_issued"]
        ))

        # Insert stock price data
        for _, row in stock_data.iterrows():
            cursor.execute("""
                INSERT INTO finance_data.company_registry.stock_price 
                (symbol, date, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, tuple(row))

        # Insert holders data
        for _, row in holders.iterrows():
            cursor.execute("""
                INSERT INTO finance_data.company_registry.holders 
                (symbol, date, holder, shares, value)
                VALUES (%s, %s, %s, %s, %s)
            """, tuple(row))

    conn.commit()
    cursor.close()
    conn.close()

# Define DAG in Airflow
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "yfinance_daily_data",
    default_args=default_args,
    description="Fetch daily financial data and store it in PostgreSQL",
    schedule_interval=timedelta(days=1),
    catchup=False,
)

fetch_and_store_task = PythonOperator(
    task_id="fetch_and_store_data",
    python_callable=insert_data_into_postgres,
    dag=dag,
)

fetch_and_store_task
