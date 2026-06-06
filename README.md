# 📊 ChurnGuard – Customer Churn Prediction System
> 🚀 **Live API:** https://churn-predictor-7xon.onrender.com/docs
> A production-style ML system that predicts customer churn probability using XGBoost & Logistic Regression, with a React dashboard and FastAPI backend.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)

---

## 🏗 Architecture

```
┌─────────────────┐     REST API     ┌──────────────────┐
│  React Frontend │ ───────────────► │  FastAPI Backend  │
│  (Tailwind CSS) │ ◄─────────────── │  /predict        │
└─────────────────┘     JSON         │  /predict/batch  │
                                     │  /predict/csv    │
                                     │  /model-info     │
                                     │  /health         │
                                     └────────┬─────────┘
                                              │
                                     ┌────────▼─────────┐
                                     │  ML Pipeline      │
                                     │  ─ LabelEncoder  │
                                     │  ─ StandardScaler│
                                     │  ─ XGBoost       │
                                     │  best_model.pkl  │
                                     └──────────────────┘
```

## 📁 Folder Structure

```
churn-predictor/
├── backend/
│   ├── api/
│   │   └── app.py           # FastAPI application & endpoints
│   ├── ml/
│   │   ├── train.py         # Training pipeline (EDA → models → save)
│   │   └── predictor.py     # PredictionService (load → predict)
│   └── tests/
│       └── test_api.py      # Pytest unit tests
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── PredictPage.jsx    # Customer form + result
│   │   │   ├── AnalyticsPage.jsx  # Model metrics charts
│   │   │   └── BatchPage.jsx      # CSV upload
│   │   ├── components/
│   │   │   └── RiskGauge.jsx      # SVG circular gauge
│   │   ├── utils/
│   │   │   └── api.js             # Axios API helpers
│   │   └── App.jsx                # Router + sidebar
│   ├── Dockerfile
│   └── package.json
├── data/
│   └── telco_churn.csv      # Auto-generated on first training run
├── models/
│   ├── best_model.pkl       # Saved model bundle (model + scaler + encoders)
│   └── metrics.json         # Evaluation metrics
├── reports/                 # EDA plots (PNG)
│   ├── churn_distribution.png
│   ├── monthly_charges_dist.png
│   ├── correlation_heatmap.png
│   ├── roc_curve.png
│   ├── feature_importance.png
│   └── confusion_*.png
├── main.py                  # Uvicorn entrypoint
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+ and Node.js 18+
- (Optional) Docker Desktop

### 1. Clone & Install
```bash
git clone https://github.com/YOUR_USERNAME/churn-predictor.git
cd churn-predictor

# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Train the Model
```bash
python backend/ml/train.py
```
This will:
- Generate a synthetic 3,000-row Telco-style dataset in `data/`
- Run EDA and save plots to `reports/`
- Train Logistic Regression + XGBoost
- Save the best model to `models/best_model.pkl`

### 3. Start the Backend
```bash
python main.py
# or
uvicorn main:app --reload
```
API is live at **http://localhost:8000**  
Swagger docs at **http://localhost:8000/docs**

### 4. Start the Frontend
```bash
cd frontend
npm run dev
```
Dashboard at **http://localhost:5173**

---

## 🐳 Docker (Recommended)

```bash
# Build and start both services
docker compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

---

## 🔌 API Reference

### `GET /health`
```json
{ "status": "ok", "model_ready": true, "version": "1.0.0" }
```

### `POST /predict`
**Request:**
```json
{
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
  "TotalCharges": 958.20
}
```
**Response:**
```json
{
  "churn_probability": 0.7231,
  "churn_label": "Yes",
  "risk_level": "High",
  "model_name": "XGBoost"
}
```

### `GET /model-info`
```json
{
  "model_name": "XGBoost",
  "features": ["gender", "SeniorCitizen", "tenure", "..."],
  "metrics": {
    "accuracy": 0.8120,
    "precision": 0.7834,
    "recall": 0.7612,
    "f1": 0.7721,
    "roc_auc": 0.8543
  }
}
```

### `POST /predict/csv`
Upload a CSV file as multipart form data.  
Returns JSON with predictions for each row.

---

## 🧪 Running Tests

```bash
# Make sure backend is running (or just run pytest directly)
pytest backend/tests/ -v
```

---

## ☁️ Deployment Guide

### Render (Free Tier)
1. Push to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set:
   - **Build command:** `pip install -r requirements.txt && python backend/ml/train.py`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add env variable: `ALLOWED_ORIGINS=https://your-frontend.vercel.app`

### Railway
```bash
railway login
railway init
railway up
```

### AWS EC2
```bash
# SSH into your instance then:
git clone https://github.com/YOUR_USERNAME/churn-predictor.git
cd churn-predictor
docker compose up -d
```

---

## 🎯 Model Performance

| Metric    | Logistic Regression | XGBoost  |
|-----------|---------------------|----------|
| Accuracy  | ~78%                | ~82%     |
| Precision | ~75%                | ~79%     |
| Recall    | ~72%                | ~76%     |
| F1 Score  | ~73%                | ~77%     |
| ROC-AUC   | ~84%                | ~87%     |

*Results vary slightly each run due to data generation randomness.*

---

## 🔮 Bonus Features Included

- ✅ **Batch CSV upload** – predict for up to 1,000 customers at once
- ✅ **Export predictions** – download results as CSV
- ✅ **Risk levels** – Low / Medium / High classification with colour coding
- ✅ **Visual gauge** – animated circular risk gauge in the dashboard

---

## 📝 Environment Variables

| Variable         | Default                   | Description                    |
|------------------|---------------------------|--------------------------------|
| `PORT`           | `8000`                    | API server port                |
| `ALLOWED_ORIGINS`| `http://localhost:3000,...`| CORS allowed origins           |
| `VITE_API_URL`   | `http://localhost:8000`   | Frontend → API URL             |

Create a `.env` file in the root to override.

---

## 📄 License

MIT © 2024 – Built as an internship portfolio project.
