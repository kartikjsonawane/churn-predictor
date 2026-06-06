"""
Customer Churn Prediction - Model Training Pipeline
Trains Logistic Regression and XGBoost, evaluates both, saves best model.
"""

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, roc_curve
)
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "data", "telco_churn.csv")
MODEL_DIR  = os.path.join(BASE_DIR, "models")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ─── 1. Data Generation (synthetic Telco-style) ──────────────────────────────
def generate_sample_data(n: int = 3000) -> pd.DataFrame:
    """Generate a realistic synthetic Telco churn dataset."""
    np.random.seed(42)
    df = pd.DataFrame({
        "customerID":       [f"CUST-{i:05d}" for i in range(n)],
        "gender":           np.random.choice(["Male", "Female"], n),
        "SeniorCitizen":    np.random.choice([0, 1], n, p=[0.84, 0.16]),
        "Partner":          np.random.choice(["Yes", "No"], n),
        "Dependents":       np.random.choice(["Yes", "No"], n, p=[0.3, 0.7]),
        "tenure":           np.random.randint(1, 72, n),
        "PhoneService":     np.random.choice(["Yes", "No"], n, p=[0.9, 0.1]),
        "MultipleLines":    np.random.choice(["Yes", "No", "No phone service"], n),
        "InternetService":  np.random.choice(["DSL", "Fiber optic", "No"], n, p=[0.35, 0.45, 0.2]),
        "OnlineSecurity":   np.random.choice(["Yes", "No", "No internet service"], n),
        "TechSupport":      np.random.choice(["Yes", "No", "No internet service"], n),
        "StreamingTV":      np.random.choice(["Yes", "No", "No internet service"], n),
        "Contract":         np.random.choice(["Month-to-month", "One year", "Two year"], n, p=[0.55, 0.24, 0.21]),
        "PaperlessBilling": np.random.choice(["Yes", "No"], n, p=[0.6, 0.4]),
        "PaymentMethod":    np.random.choice(
                                ["Electronic check", "Mailed check",
                                 "Bank transfer (automatic)", "Credit card (automatic)"], n),
        "MonthlyCharges":   np.round(np.random.uniform(18, 120, n), 2),
    })
    # TotalCharges ≈ tenure × MonthlyCharges + noise
    df["TotalCharges"] = np.round(
        df["tenure"] * df["MonthlyCharges"] + np.random.normal(0, 50, n), 2
    ).clip(lower=0)

    # Build churn probability with realistic business logic
    churn_prob = (
        0.35
        - 0.005 * df["tenure"]
        + 0.003 * (df["MonthlyCharges"] - 60)
        + 0.15  * (df["Contract"] == "Month-to-month").astype(int)
        - 0.10  * (df["Contract"] == "Two year").astype(int)
        + 0.10  * (df["InternetService"] == "Fiber optic").astype(int)
        + 0.05  * (df["PaymentMethod"] == "Electronic check").astype(int)
        - 0.05  * (df["Partner"] == "Yes").astype(int)
        + 0.05  * df["SeniorCitizen"]
    ).clip(0.03, 0.97)

    df["Churn"] = np.where(np.random.rand(n) < churn_prob, "Yes", "No")
    return df


# ─── 2. Preprocessing ────────────────────────────────────────────────────────
CATEGORICAL_COLS = [
    "gender", "Partner", "Dependents", "PhoneService", "MultipleLines",
    "InternetService", "OnlineSecurity", "TechSupport", "StreamingTV",
    "Contract", "PaperlessBilling", "PaymentMethod"
]
NUMERICAL_COLS = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
DROP_COLS      = ["customerID"]


def preprocess(df: pd.DataFrame, scaler=None, encoders=None, fit: bool = True):
    """
    Encode categoricals, scale numericals.
    If fit=True, create new scaler/encoders and return them.
    If fit=False, reuse provided scaler/encoders (for inference).
    """
    df = df.copy()

    # Handle missing / blank TotalCharges
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"].fillna(df["TotalCharges"].median(), inplace=True)

    # Drop non-feature columns
    df.drop(columns=[c for c in DROP_COLS if c in df.columns], inplace=True)

    # Encode target
    if "Churn" in df.columns:
        df["Churn"] = (df["Churn"] == "Yes").astype(int)

    # Label-encode categoricals
    if fit:
        encoders = {}
    for col in CATEGORICAL_COLS:
        if col not in df.columns:
            continue
        if fit:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
        else:
            le = encoders[col]
            # Handle unseen labels gracefully
            known = set(le.classes_)
            df[col] = df[col].astype(str).apply(
                lambda x: x if x in known else le.classes_[0]
            )
            df[col] = le.transform(df[col])

    # Scale numericals
    num_present = [c for c in NUMERICAL_COLS if c in df.columns]
    if fit:
        scaler = StandardScaler()
        df[num_present] = scaler.fit_transform(df[num_present])
    else:
        df[num_present] = scaler.transform(df[num_present])

    return df, scaler, encoders


# ─── 3. EDA Plots ────────────────────────────────────────────────────────────
def run_eda(df: pd.DataFrame):
    """Generate and save EDA visualisations to reports/."""
    palette = {"No": "#4CAF50", "Yes": "#F44336"}

    # Churn distribution
    fig, ax = plt.subplots(figsize=(6, 4))
    df["Churn"].value_counts().plot.bar(color=["#4CAF50", "#F44336"], ax=ax, edgecolor="white")
    ax.set_title("Churn Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Churn"); ax.set_ylabel("Count"); ax.tick_params(rotation=0)
    plt.tight_layout(); plt.savefig(f"{REPORT_DIR}/churn_distribution.png", dpi=150); plt.close()

    # Monthly charges by churn
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, grp in df.groupby("Churn"):
        grp["MonthlyCharges"].plot.kde(ax=ax, label=label, color=palette[label], linewidth=2)
    ax.set_title("Monthly Charges Distribution by Churn", fontsize=13, fontweight="bold")
    ax.legend(); ax.set_xlabel("Monthly Charges ($)")
    plt.tight_layout(); plt.savefig(f"{REPORT_DIR}/monthly_charges_dist.png", dpi=150); plt.close()

    # Correlation heatmap (numeric features only)
    num_df = df[["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]].copy()
    num_df["Churn"] = (df["Churn"] == "Yes").astype(int)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(num_df.corr(), annot=True, fmt=".2f", cmap="RdYlGn", center=0,
                linewidths=0.5, ax=ax)
    ax.set_title("Feature Correlation Heatmap", fontsize=13, fontweight="bold")
    plt.tight_layout(); plt.savefig(f"{REPORT_DIR}/correlation_heatmap.png", dpi=150); plt.close()

    print("✅  EDA plots saved to reports/")


# ─── 4. Model Training & Evaluation ─────────────────────────────────────────
def evaluate(model, X, y, name: str) -> dict:
    preds      = model.predict(X)
    proba      = model.predict_proba(X)[:, 1]
    return {
        "model":     name,
        "accuracy":  round(accuracy_score(y, preds), 4),
        "precision": round(precision_score(y, preds), 4),
        "recall":    round(recall_score(y, preds), 4),
        "f1":        round(f1_score(y, preds), 4),
        "roc_auc":   round(roc_auc_score(y, proba), 4),
    }


def plot_roc(models_proba: dict, y_test):
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = {"Logistic Regression": "#2196F3", "XGBoost": "#FF5722"}
    for name, proba in models_proba.items():
        fpr, tpr, _ = roc_curve(y_test, proba)
        auc = roc_auc_score(y_test, proba)
        ax.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})",
                color=colors.get(name, "grey"), linewidth=2)
    ax.plot([0, 1], [0, 1], "k--", linewidth=1)
    ax.set_title("ROC Curve Comparison", fontsize=13, fontweight="bold")
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right")
    plt.tight_layout(); plt.savefig(f"{REPORT_DIR}/roc_curve.png", dpi=150); plt.close()


def plot_confusion(model, X_test, y_test, name: str):
    preds = model.predict(X_test)
    cm    = confusion_matrix(y_test, preds)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["No Churn", "Churn"],
                yticklabels=["No Churn", "Churn"], ax=ax)
    ax.set_title(f"Confusion Matrix – {name}", fontsize=12, fontweight="bold")
    ax.set_ylabel("Actual"); ax.set_xlabel("Predicted")
    plt.tight_layout()
    fname = name.lower().replace(" ", "_")
    plt.savefig(f"{REPORT_DIR}/confusion_{fname}.png", dpi=150); plt.close()


# ─── 5. Main ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Customer Churn Prediction – Training Pipeline")
    print("=" * 55)

    # Load or generate data
    if os.path.exists(DATA_PATH):
        print(f"\n📂  Loading data from {DATA_PATH}")
        df_raw = pd.read_csv(DATA_PATH)
    else:
        print("\n⚙️   Generating synthetic Telco dataset …")
        df_raw = generate_sample_data(3000)
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        df_raw.to_csv(DATA_PATH, index=False)
        print(f"    Saved to {DATA_PATH}")

    print(f"    Shape: {df_raw.shape}  |  Churn rate: {(df_raw['Churn']=='Yes').mean():.1%}")

    # EDA
    run_eda(df_raw)

    # Preprocessing
    df_proc, scaler, encoders = preprocess(df_raw, fit=True)
    X = df_proc.drop(columns=["Churn"])
    y = df_proc["Churn"]

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
    X_val,   X_test, y_val,   y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp)
    print(f"\n📊  Train: {len(X_train)}  |  Val: {len(X_val)}  |  Test: {len(X_test)}")

    # --- Logistic Regression ---
    print("\n🔧  Training Logistic Regression …")
    lr = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
    lr.fit(X_train, y_train)
    lr_metrics = evaluate(lr, X_test, y_test, "Logistic Regression")

    # --- XGBoost ---
    print("🔧  Training XGBoost …")
    xgb = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42, verbosity=0
    )
    xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    xgb_metrics = evaluate(xgb, X_test, y_test, "XGBoost")

    # Print comparison table
    print("\n" + "─" * 55)
    print(f"  {'Metric':<14} {'Logistic Reg':>16} {'XGBoost':>12}")
    print("─" * 55)
    for k in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
        print(f"  {k.capitalize():<14} {lr_metrics[k]:>16.4f} {xgb_metrics[k]:>12.4f}")
    print("─" * 55)

    # Save ROC & confusion matrices
    plot_roc({"Logistic Regression": lr.predict_proba(X_test)[:, 1],
              "XGBoost": xgb.predict_proba(X_test)[:, 1]}, y_test)
    plot_confusion(lr,  X_test, y_test, "Logistic Regression")
    plot_confusion(xgb, X_test, y_test, "XGBoost")

    # Choose best model by ROC-AUC
    best_name    = "XGBoost" if xgb_metrics["roc_auc"] >= lr_metrics["roc_auc"] else "Logistic Regression"
    best_model   = xgb     if best_name == "XGBoost" else lr
    best_metrics = xgb_metrics if best_name == "XGBoost" else lr_metrics
    print(f"\n🏆  Best model: {best_name} (ROC-AUC = {best_metrics['roc_auc']:.4f})")

    # Feature importance (XGBoost)
    if hasattr(best_model, "feature_importances_"):
        fi = pd.Series(best_model.feature_importances_, index=X.columns).nlargest(10)
        fig, ax = plt.subplots(figsize=(7, 4))
        fi.sort_values().plot.barh(color="#FF5722", ax=ax, edgecolor="white")
        ax.set_title("Top-10 Feature Importances (XGBoost)", fontsize=12, fontweight="bold")
        ax.set_xlabel("Importance Score")
        plt.tight_layout(); plt.savefig(f"{REPORT_DIR}/feature_importance.png", dpi=150); plt.close()
        print("✅  Feature importance plot saved.")

    # Persist artefacts
    bundle = {
        "model":    best_model,
        "scaler":   scaler,
        "encoders": encoders,
        "features": list(X.columns),
        "metrics":  best_metrics,
        "name":     best_name,
    }
    model_path = os.path.join(MODEL_DIR, "best_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"✅  Model saved → {model_path}")

    # Save metrics JSON (used by the API)
    metrics_path = os.path.join(MODEL_DIR, "metrics.json")
    all_metrics  = {"best": best_metrics, "logistic_regression": lr_metrics, "xgboost": xgb_metrics}
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"✅  Metrics saved → {metrics_path}")
    print("\n🎉  Training complete!\n")


if __name__ == "__main__":
    main()
