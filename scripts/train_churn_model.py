import pandas as pd
import logging
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & LOGGING
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_USER = 'airflow'
DB_PASS = 'airflow'
DB_HOST = 'postgres' 
DB_PORT = '5432'
DB_NAME = 'airflow'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# ==========================================
# 2. DATA EXTRACTION
# ==========================================
def extract_gold_data():
    """
    Extracts Customer 360 data from the Gold schema.
    We now include 'customer_id' to map predictions back to specific users in Power BI.
    """
    logging.info("Extracting data from gold.mart_customer_rfm...")
    query = """
        SELECT 
            customer_id,
            location_city, 
            total_orders, 
            total_spend, 
            favorite_category, 
            is_churned 
        FROM gold.mart_customer_rfm;
    """
    df = pd.read_sql(query, engine)
    logging.info(f"Successfully extracted {len(df)} customer records.")
    return df

# ==========================================
# 3. MODEL TRAINING & EVALUATION
# ==========================================
def train_and_evaluate_model(df):
    """Builds and trains the ML Pipeline with class balancing."""
    logging.info("Preparing data for model training (Leakage-Free)...")
    
    # Features (X) must exclude the target and the unique identifier
    X = df.drop(columns=['is_churned', 'customer_id'])
    y = df['is_churned']

    categorical_features = ['location_city', 'favorite_category']
    numerical_features = ['total_orders', 'total_spend']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Using class_weight='balanced' to handle imbalanced churn datasets
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=100, 
            max_depth=5, 
            class_weight='balanced', 
            random_state=42
        ))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    logging.info("Training Random Forest Classifier...")
    pipeline.fit(X_train, y_train)
    
    logging.info("Evaluating model performance on test set...")
    y_pred = pipeline.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)
    
    logging.info(f"Model Accuracy: {accuracy * 100:.2f}%")
    logging.info(f"\nClassification Report:\n{report}")
    
    return pipeline

# ==========================================
# 4. BATCH INFERENCE & BI INTEGRATION
# ==========================================
def generate_and_save_predictions(model, df_raw):
    """
    Predicts churn probability for currently active customers and saves 
    the result back to PostgreSQL as a new Gold Data Mart for Power BI.
    """
    logging.info("Generating predictions for currently active customers...")
    
    # Filter customers who have not churned yet
    active_customers = df_raw[df_raw['is_churned'] == 0].copy()
    
    if active_customers.empty:
        logging.warning("No active customers found to predict.")
        return

    # Prepare features for prediction
    X_active = active_customers.drop(columns=['is_churned', 'customer_id'])

    # predict_proba returns an array [probability_of_0, probability_of_1]
    # We extract index 1 (probability of churn)
    churn_probabilities = model.predict_proba(X_active)[:, 1]

    # Build the final predictions dataframe
    predictions_df = pd.DataFrame({
        'customer_id': active_customers['customer_id'],
        'churn_probability_percent': (churn_probabilities * 100).round(2)
    })

    # Business Logic: Define Risk Levels for the BI Dashboard
    def categorize_risk(prob):
        if prob >= 70: return 'High Risk'
        elif prob >= 40: return 'Medium Risk'
        else: return 'Low Risk'

    predictions_df['risk_level'] = predictions_df['churn_probability_percent'].apply(categorize_risk)
    predictions_df['prediction_date'] = datetime.now().date()

    # Save to PostgreSQL Gold Schema
    table_name = 'mart_churn_predictions'
    logging.info(f"Saving {len(predictions_df)} predictions to gold.{table_name}...")
    predictions_df.to_sql(name=table_name, con=engine, schema='gold', if_exists='replace', index=False)
    logging.info("Predictions saved successfully. Ready for Power BI ingestion.")

# ==========================================
# 5. MODEL SERIALIZATION
# ==========================================
def save_model(model, file_path='/opt/airflow/scripts/churn_model.pkl'):
    logging.info(f"Saving model to {file_path}...")
    joblib.dump(model, file_path)
    logging.info("Model saved successfully.")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    logging.info("Starting Machine Learning Pipeline...")
    df_raw = extract_gold_data()
    
    trained_model = train_and_evaluate_model(df_raw)
    generate_and_save_predictions(trained_model, df_raw)
    save_model(trained_model)
    
    logging.info("Machine Learning Pipeline finished successfully.")