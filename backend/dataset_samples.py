import os
import pandas as pd
from typing import Dict, Any, List

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")

SAMPLES_CATALOG = [
    {
        "id": "telecom_churn",
        "title": "Telecom Customer Churn",
        "filename": "telecom_customer_churn.csv",
        "task": "classification",
        "target": "Churned",
        "description": "Predict customer attrition from contract terms, tenure, charges, and tech support flags.",
        "icon": "📞",
        "rows": 180,
        "features": 8
    },
    {
        "id": "housing_prices",
        "title": "Real Estate Valuation",
        "filename": "housing_prices.csv",
        "task": "regression",
        "target": "PriceUSD",
        "description": "Predict home market valuation from square footage, rooms, age, and neighborhood rating.",
        "icon": "🏡",
        "rows": 150,
        "features": 8
    },
    {
        "id": "heart_disease",
        "title": "Cardiac Health Risk",
        "filename": "heart_disease_risk.csv",
        "task": "classification",
        "target": "HighRiskDiagnosis",
        "description": "Predict clinical cardiovascular risk from blood pressure, cholesterol, and stress tests.",
        "icon": "❤️",
        "rows": 160,
        "features": 8
    }
]

def get_sample_catalog() -> List[Dict[str, Any]]:
    return SAMPLES_CATALOG

def load_sample_df(sample_id: str) -> pd.DataFrame:
    for item in SAMPLES_CATALOG:
        if item["id"] == sample_id:
            filepath = os.path.join(SAMPLE_DIR, item["filename"])
            if os.path.exists(filepath):
                return pd.read_csv(filepath)
            else:
                raise FileNotFoundError(f"Sample file not found: {filepath}")
    raise ValueError(f"Unknown sample id: {sample_id}")
