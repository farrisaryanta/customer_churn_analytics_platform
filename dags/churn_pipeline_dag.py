from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# ==========================================
# DAG CONFIGURATION
# ==========================================
default_args = {
    'owner': 'farris_aryanta',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG (    
    dag_id='end_to_end_churn_analytics_pipeline',
    default_args=default_args,
    description='End-to-End pipeline for Data Ingestion, dbt Transformations, and ML Training',schedule_interval='@daily', # Berjalan otomatis setiap hari
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['churn_analytics', 'machine_learning', 'dbt'],
) as dag:

    # ==========================================
    # TASK 1: Data Ingestion (Bronze Layer)
    # ==========================================
    ingest_data_task = BashOperator(
        task_id='ingest_bronze_data',
        bash_command='python /opt/airflow/scripts/ingest_data.py',
    )

    # ==========================================
    # TASK 2: dbt Silver Layer (Data Cleansing)
    # ==========================================
    dbt_silver_task = BashOperator(
        task_id='dbt_silver_transform',
        bash_command='cd /opt/airflow/dbt && dbt run --select models/silver --profiles-dir .',
    )

    # ==========================================
    # TASK 3: dbt Gold Layer (Data Marts)
    # ==========================================
    dbt_gold_task = BashOperator(
        task_id='dbt_gold_transform',
        bash_command='cd /opt/airflow/dbt && dbt run --select models/gold --profiles-dir .',
    )

    # ==========================================
    # TASK 4: dbt Data Quality Testing
    # ==========================================
    dbt_test_task = BashOperator(
        task_id='dbt_data_quality_test',
        bash_command='cd /opt/airflow/dbt && dbt test --profiles-dir .',
    )

    # ==========================================
    # TASK 5: Train Machine Learning Model
    # ==========================================
    train_ml_task = BashOperator(
        task_id='train_churn_ml_model',
        bash_command='python /opt/airflow/scripts/train_churn_model.py',
    )

    # ==========================================
    # PIPELINE DEPENDENCIES (The Logic Flow)
    # ==========================================
    # This enforces the exact order of execution
    ingest_data_task >> dbt_silver_task >> dbt_gold_task >> dbt_test_task >> train_ml_task