"""
Customer Churn Prediction API  –  FastAPI
Endpoints:
  GET  /health       – liveness check
  POST /predict      – single customer churn prediction
  POST /predict/batch – batch predictions
  GET  /model-info   – model metadata and metrics
  POST /predict/csv  – upload CSV, get predictions back
"""

import io
import os
import csv
import json
import logging
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.ml.predictor import PredictionService

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Customer Churn Prediction API",
    description="Predict customer churn probability using ML models.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow React dev-server and production frontend
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic Schemas ────────────────────────────────────────────────────────
class CustomerInput(BaseModel):
    """Fields match the Telco-style dataset used during training."""
    gender:           str   = Field("Male",              example="Male")
    SeniorCitizen:    int   = Field(0,                   example=0, ge=0, le=1)
    Partner:          str   = Field("No",                example="Yes")
    Dependents:       str   = Field("No",                example="No")
    tenure:           int   = Field(12,                  example=12, ge=0)
    PhoneService:     str   = Field("Yes",               example="Yes")
    MultipleLines:    str   = Field("No",                example="No")
    InternetService:  str   = Field("DSL",               example="Fiber optic")
    OnlineSecurity:   str   = Field("No",                example="Yes")
    TechSupport:      str   = Field("No",                example="No")
    StreamingTV:      str   = Field("No",                example="No")
    Contract:         str   = Field("Month-to-month",    example="Two year")
    PaperlessBilling: str   = Field("Yes",               example="Yes")
    PaymentMethod:    str   = Field("Electronic check",  example="Bank transfer (automatic)")
    MonthlyCharges:   float = Field(70.0,                example=70.0, gt=0)
    TotalCharges:     Optional[float] = Field(None,      example=840.0)

    class Config:
        schema_extra = {
            "example": {
                "gender": "Female", "SeniorCitizen": 0,
                "Partner": "Yes", "Dependents": "No",
                "tenure": 12, "PhoneService": "Yes",
                "MultipleLines": "No", "InternetService": "Fiber optic",
                "OnlineSecurity": "No", "TechSupport": "No",
                "StreamingTV": "Yes", "Contract": "Month-to-month",
                "PaperlessBilling": "Yes", "PaymentMethod": "Electronic check",
                "MonthlyCharges": 79.85, "TotalCharges": 958.20
            }
        }


class PredictionResponse(BaseModel):
    churn_probability: float
    churn_label:       str
    risk_level:        str
    model_name:        str


# ─── Startup ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Loading ML model …")
    try:
        PredictionService.load()
        logger.info("Model loaded successfully.")
    except FileNotFoundError as e:
        logger.warning(str(e))


# ─── Endpoints ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    """Liveness check – returns API status and model availability."""
    model_ready = PredictionService._bundle is not None
    return {
        "status":      "ok",
        "model_ready": model_ready,
        "version":     "1.0.0",
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(customer: CustomerInput):
    """
    Predict churn probability for a single customer.

    - **churn_probability**: 0.0–1.0 probability of churn
    - **churn_label**: "Yes" if probability ≥ 0.5
    - **risk_level**: Low / Medium / High
    """
    try:
        result = PredictionService.predict(customer.dict())
        logger.info(f"Prediction: prob={result['churn_probability']}, label={result['churn_label']}")
        return result
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", tags=["Prediction"])
def predict_batch(customers: list[CustomerInput]):
    """Predict churn for a batch of customers (max 500)."""
    if len(customers) > 500:
        raise HTTPException(status_code=400, detail="Batch size exceeds limit of 500.")
    try:
        results = PredictionService.predict_batch([c.dict() for c in customers])
        return {"predictions": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/csv", tags=["Prediction"])
async def predict_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file with customer records.
    Returns predictions for each row plus a downloadable JSON.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse CSV file.")

    records = df.to_dict(orient="records")
    if len(records) > 1000:
        raise HTTPException(status_code=400, detail="CSV exceeds 1000 row limit.")

    results = PredictionService.predict_batch(records)
    for i, row in enumerate(results):
        row["row_index"] = i
        if "customerID" in records[i]:
            row["customerID"] = records[i]["customerID"]

    return {"predictions": results, "count": len(results)}


@app.get("/model-info", tags=["Model"])
def model_info():
    """Return model name, feature list, and evaluation metrics."""
    try:
        return PredictionService.model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
