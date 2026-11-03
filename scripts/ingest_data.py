import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging
from datetime import datetime, timedelta
import random

# ==========================================
# CONFIGURATION & LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Dataabase connection mapping (Internal Ocker Network)
DB_USER = 'airflow'
DB_PASS = 'airflow'
DB_HOST = 'postgres'
DB_PORT = '5432'
DB_NAME = 'airflow'

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# ==========================================
# DATA GENERATION LOGIC
# ==========================================
def generate_relational_data(num_customers=1000, num_orders=5000):
    """Generates interconnected tables for retail churn analysis."""
    logging.info("Generating Products...")
    categories = ['Electronics', 'Clothing', 'Home', 'Beauty', 'Sports']
    products_data = []
    for i in range(1, 51):
        cat = random.choice(categories)
        products_data.append({
            'product_id': f"PRD-{i:03d}",
            'category': cat,
            'product_name': f"{cat} Item {i}",
            'base_price': round(random.uniform(10.0, 500), 2) # Helper for order items
        })
    df_product = pd.DataFrame(products_data)

    logging.info(f"Generating {num_customers} Customers...")
    locations = ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Makassar', 'Bali']
    end_date = datetime(2026, 9, 1)
    start_date = datetime(2024, 1, 1)

    customers_data = []
    for i in range(1, num_customers + 1):
        signup = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        customers_data.append({
            'customer_id': f"CUST-{i:05d}",
            'signup_date': signup,
            'location': random.choice(locations)
        })
    df_customer = pd.DataFrame(customers_data)

    logging.info(f"Generating {num_orders} Orders...")
    orders_data = []
    statuses = ['Completed', 'Completed', 'Completed', 'Pending', 'Cancelled']

    for i in range(1, num_orders + 1):
        cust = df_customer.sample(1).iloc[0]
        # Order date must be logical (after signup date)
        order_start = cust['signup_date']
        order_date = order_start + timedelta(days=random.randint(0, (end_date - order_start).days))

        orders_data.append({
            'order_id': f"ORD-{i:06d}",
            'customer_id': cust['customer_id'],
            'order_date': order_date,
            'order_status': random.choice(statuses)
        })
    df_order = pd.DataFrame(orders_data)

    logging.info("Generating Order Items...")
    order_items_data = []
    for order_id in df_order['order_id']:
        num_items = random.randint(1, 4)
        selected_products = df_product.sample(num_items)

        for _, prod in selected_products.iterrows():
            order_items_data.append({
                'order_id': order_id,
                'product_id': prod['product_id'],
                'quantity': random.randint(1, 3),
                'price': prod['base_price']
            })
    df_order_item = pd.DataFrame(order_items_data)

    # Drop the helper column to match the exact requested schema
    df_product = df_product[['product_id', 'category', 'product_name']]

    return df_customer, df_order, df_order_item, df_product

def load_data_to_postgres(df, table_name):
    """Loads DataFrame to PostgreSQL Bronze Schema."""
    logging.info(f"Loading data to bronze.{table_name}...")
    try:
        df.to_sql(
            name=table_name, 
            con=engine, 
            schema='bronze',
            if_exists='replace', 
            index=False
        )
        logging.info(f"Success: {len(df)} rows loaded into bronze.{table_name}.")
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        raise e

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    logging.info("Starting Relational Data Ingestion Job...")

    # 1. Generate all tables
    df_cust, df_ord, df_item, df_prod = generate_relational_data()

    # 2. Load to PostgreSQL (Bronze Layer)
    load_data_to_postgres(df_cust, 'raw_customers')
    load_data_to_postgres(df_prod, 'raw_products')
    load_data_to_postgres(df_ord, 'raw_orders')
    load_data_to_postgres(df_item, 'raw_order_items')

    logging.info("Data Ingestion Job finished successfully.")