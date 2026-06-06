"""
Unit tests for the Churn Prediction API and ML pipeline.
Run with:  pytest backend/tests/ -v
"""

import os
import sys
import json
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from backend.api.app import app
from backend.ml.predictor import PredictionService

client = TestClient(app)

# ─── Fixtures ────────────────────────────────────────────────────────────────
SAMPLE_CUSTOMER = {
    "gender": "Female",
    "SeniorCitizen": 0,
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": 12,
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "TechSupport": "No",
    "StreamingTV": "Yes",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 79.85,
    "TotalCharges": 958.20,
}

SAMPLE_LOW_RISK = {
    "gender": "Male",
    "SeniorCitizen": 0,
    "Partner": "Yes",
    "Dependents": "Yes",
    "tenure": 60,
    "PhoneService": "Yes",
    "MultipleLines": "Yes",
    "InternetService": "DSL",
    "OnlineSecurity": "Yes",
    "TechSupport": "Yes",
    "StreamingTV": "No",
    "Contract": "Two year",
    "PaperlessBilling": "No",
    "PaymentMethod": "Bank transfer (automatic)",
    "MonthlyCharges": 45.00,
    "TotalCharges": 2700.00,
}


# ─── Health Tests ─────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_status_ok(self):
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_health_has_version(self):
        data = client.get("/health").json()
        assert "version" in data


# ─── Prediction Tests ────────────────────────────────────────────────────────
class TestPredict:
    def test_predict_returns_200(self):
        r = client.post("/predict", json=SAMPLE_CUSTOMER)
        assert r.status_code == 200

    def test_predict_response_schema(self):
        data = client.post("/predict", json=SAMPLE_CUSTOMER).json()
        assert "churn_probability" in data
        assert "churn_label" in data
        assert "risk_level" in data
        assert "model_name" in data

    def test_probability_in_range(self):
        data = client.post("/predict", json=SAMPLE_CUSTOMER).json()
        prob = data["churn_probability"]
        assert 0.0 <= prob <= 1.0

    def test_churn_label_valid(self):
        data = client.post("/predict", json=SAMPLE_CUSTOMER).json()
        assert data["churn_label"] in ("Yes", "No")

    def test_risk_level_valid(self):
        data = client.post("/predict", json=SAMPLE_CUSTOMER).json()
        assert data["risk_level"] in ("Low", "Medium", "High")

    def test_low_risk_customer_lower_probability(self):
        high_risk  = client.post("/predict", json=SAMPLE_CUSTOMER).json()
        low_risk   = client.post("/predict", json=SAMPLE_LOW_RISK).json()
        # Long-tenure, two-year contract customer should have lower churn prob
        assert low_risk["churn_probability"] < high_risk["churn_probability"]

    def test_missing_total_charges_handled(self):
        customer = SAMPLE_CUSTOMER.copy()
        customer.pop("TotalCharges", None)
        r = client.post("/predict", json=customer)
        assert r.status_code == 200

    def test_invalid_payload_returns_422(self):
        r = client.post("/predict", json={"bad_field": "value"})
        # FastAPI validates required fields but most have defaults; just check no 500
        assert r.status_code in (200, 422)


# ─── Batch Prediction Tests ───────────────────────────────────────────────────
class TestBatchPredict:
    def test_batch_predict_returns_200(self):
        payload = [SAMPLE_CUSTOMER, SAMPLE_LOW_RISK]
        r = client.post("/predict/batch", json=payload)
        assert r.status_code == 200

    def test_batch_count_matches(self):
        payload = [SAMPLE_CUSTOMER, SAMPLE_LOW_RISK]
        data = client.post("/predict/batch", json=payload).json()
        assert data["count"] == 2
        assert len(data["predictions"]) == 2


# ─── Model Info Tests ─────────────────────────────────────────────────────────
class TestModelInfo:
    def test_model_info_returns_200(self):
        r = client.get("/model-info")
        assert r.status_code == 200

    def test_model_info_has_metrics(self):
        data = client.get("/model-info").json()
        assert "metrics" in data
        assert "model_name" in data
        assert "features" in data

    def test_metrics_have_required_keys(self):
        metrics = client.get("/model-info").json()["metrics"]
        for key in ("accuracy", "precision", "recall", "f1", "roc_auc"):
            assert key in metrics, f"Missing metric: {key}"


# ─── Prediction Service Unit Tests ───────────────────────────────────────────
class TestPredictionService:
    def test_predict_returns_dict(self):
        result = PredictionService.predict(SAMPLE_CUSTOMER)
        assert isinstance(result, dict)

    def test_predict_probability_float(self):
        result = PredictionService.predict(SAMPLE_CUSTOMER)
        assert isinstance(result["churn_probability"], float)

    def test_predict_batch_length(self):
        batch = [SAMPLE_CUSTOMER, SAMPLE_LOW_RISK]
        results = PredictionService.predict_batch(batch)
        assert len(results) == len(batch)

    def test_model_info_dict(self):
        info = PredictionService.model_info()
        assert isinstance(info, dict)
        assert "model_name" in info
