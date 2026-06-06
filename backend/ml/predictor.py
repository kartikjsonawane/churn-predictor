"""
Prediction Service
Loads the saved model bundle and exposes a clean predict() interface.
"""

import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "best_model.pkl")

# Categorical and numerical feature lists (must match train.py)
CATEGORICAL_COLS = [
    "gender", "Partner", "Dependents", "PhoneService", "MultipleLines",
    "InternetService", "OnlineSecurity", "TechSupport", "StreamingTV",
    "Contract", "PaperlessBilling", "PaymentMethod"
]
NUMERICAL_COLS = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]


class PredictionService:
    """Singleton-style service that loads the model once at startup."""

    _bundle = None  # Cached model bundle

    @classmethod
    def load(cls):
        """Load model bundle from disk (called once at API startup)."""
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run `python backend/ml/train.py` first."
            )
        with open(MODEL_PATH, "rb") as f:
            cls._bundle = pickle.load(f)
        print(f"✅  Loaded model: {cls._bundle['name']}")

    @classmethod
    def _ensure_loaded(cls):
        if cls._bundle is None:
            cls.load()

    @classmethod
    def predict(cls, customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict churn for a single customer dict.

        Returns:
            {
              "churn_probability": float,   # 0.0 – 1.0
              "churn_label":       str,     # "Yes" | "No"
              "risk_level":        str,     # "Low" | "Medium" | "High"
              "model_name":        str,
            }
        """
        cls._ensure_loaded()
        bundle   = cls._bundle
        model    = bundle["model"]
        scaler   = bundle["scaler"]
        encoders = bundle["encoders"]
        features = bundle["features"]

        # Build a single-row DataFrame with expected columns
        df = pd.DataFrame([customer])

        # Compute TotalCharges if missing
        if "TotalCharges" not in df.columns or pd.isna(df["TotalCharges"].iloc[0]):
            df["TotalCharges"] = df["tenure"] * df["MonthlyCharges"]

        # Encode categoricals
        for col in CATEGORICAL_COLS:
            if col not in df.columns:
                df[col] = "No"   # sensible default
            le      = encoders[col]
            known   = set(le.classes_)
            val     = str(df[col].iloc[0])
            df[col] = le.transform([val if val in known else le.classes_[0]])

        # Scale numericals
        num_present = [c for c in NUMERICAL_COLS if c in df.columns]
        df[num_present] = scaler.transform(df[num_present])

        # Align columns to training feature order
        df = df.reindex(columns=features, fill_value=0)

        # Predict
        proba = float(model.predict_proba(df)[0][1])
        label = "Yes" if proba >= 0.5 else "No"
        risk  = "High" if proba >= 0.7 else ("Medium" if proba >= 0.4 else "Low")

        return {
            "churn_probability": round(proba, 4),
            "churn_label":       label,
            "risk_level":        risk,
            "model_name":        bundle["name"],
        }

    @classmethod
    def predict_batch(cls, customers: list) -> list:
        """Predict churn for a list of customer dicts."""
        return [cls.predict(c) for c in customers]

    @classmethod
    def model_info(cls) -> Dict[str, Any]:
        """Return model metadata and evaluation metrics."""
        cls._ensure_loaded()
        b = cls._bundle
        return {
            "model_name": b["name"],
            "features":   b["features"],
            "metrics":    b["metrics"],
        }
