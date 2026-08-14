import json
import math
import re
import warnings
from collections import Counter
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor


warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"
TMP_DIR = OUTPUTS_DIR / "tmp"

SCHOOLS_PATH = DATA_DIR / "schools.xlsx"
TEACHERS_PATH = DATA_DIR / "teachers.xlsx"
ANALYSIS_PATH = DATA_DIR / "school_math_analysis.xlsx"
PREDICTION_PAYLOAD_PATH = TMP_DIR / "ml_predictions_payload.json"
METRICS_PATH = OUTPUTS_DIR / "ml_model_metrics.json"

AS_OF_DATE = date(2026, 8, 6)
THAI_MONTHS = {
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
}

FUTURE_FEATURES = [
    "school_code",
    "school_size",
    "total_students",
    "actual_math_teachers",
    "math_teacher_avg_age",
    "math_teacher_min_years_to_retirement",
    "math_teacher_retirements_next_5y",
]

RISK_FEATURES = [
    "school_size",
    "hired_teachers",
    "hired_teacher_ratio",
    "condition_of_tenure_mode",
    "tenure_eligible_ratio",
    "near_tenure_ratio",
    "avg_years_service",
    "new_teacher_ratio",
]

FUTURE_NUMERIC = [
    "total_students",
    "actual_math_teachers",
    "math_teacher_avg_age",
    "math_teacher_min_years_to_retirement",
    "math_teacher_retirements_next_5y",
]
FUTURE_CATEGORICAL = ["school_code", "school_size"]

RISK_NUMERIC = [
    "hired_teachers",
    "hired_teacher_ratio",
    "tenure_eligible_ratio",
    "near_tenure_ratio",
    "avg_years_service",
    "new_teacher_ratio",
]
RISK_CATEGORICAL = ["school_size", "condition_of_tenure_mode"]


def ensure_dirs():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def normalize_code(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def parse_thai_date(value):
    if pd.isna(value):
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        return value
    text = str(value).strip()
    if not text:
        return pd.NaT
    parts = text.split()
    if len(parts) < 3:
        return pd.NaT
    try:
        day = int(parts[0])
        month = THAI_MONTHS.get(parts[1])
        year = int(parts[2])
        if year > 2400:
            year -= 543
        if month is None:
            return pd.NaT
        return pd.Timestamp(date(year, month, day))
    except (TypeError, ValueError):
        return pd.NaT


def years_between(later, earlier):
    if pd.isna(later) or pd.isna(earlier):
        return np.nan
    return max(0.0, (later.date() - earlier.date()).days / 365.25)


def create_preprocessor(numeric_features, categorical_features):
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_features,
            ),
        ],
        sparse_threshold=0,
    )


def load_dataset():
    schools = pd.read_excel(SCHOOLS_PATH, dtype={"school_code": str, "area_code": str})
    teachers = pd.read_excel(TEACHERS_PATH, dtype={"teacher_id": str, "school_code": str})
    analysis = pd.read_excel(ANALYSIS_PATH, sheet_name="school_math_analysis", dtype={"school_code": str})

    for frame in [schools, teachers, analysis]:
        if "school_code" in frame.columns:
            frame["school_code"] = frame["school_code"].map(normalize_code)

    teachers["birth_dt"] = teachers["birth_date"].map(parse_thai_date)
    teachers["retirement_dt"] = teachers["retirement_date"].map(parse_thai_date)
    teachers["start_dt"] = teachers["start_date"].map(parse_thai_date)
    as_of_ts = pd.Timestamp(AS_OF_DATE)
    teachers["age"] = teachers["birth_dt"].map(lambda x: years_between(as_of_ts, x))
    teachers["years_to_retirement"] = teachers["retirement_dt"].map(lambda x: years_between(x, as_of_ts))
    teachers["years_service"] = teachers["start_dt"].map(lambda x: years_between(as_of_ts, x))
    teachers["retire_next_5y"] = teachers["years_to_retirement"].between(0, 5, inclusive="both").astype(int)
    teachers["tenure_eligible"] = teachers["condition_of_tenure"].fillna("").str.contains("4 ปี|ครบ", regex=True).astype(int)
    teachers["near_tenure"] = teachers["years_service"].between(3, 4, inclusive="left").astype(int)
    teachers["new_teacher"] = (teachers["years_service"] < 3).fillna(False).astype(int)

    teacher_agg = teachers.groupby("school_code").agg(
        math_teacher_avg_age=("age", "mean"),
        math_teacher_min_years_to_retirement=("years_to_retirement", "min"),
        math_teacher_retirements_next_5y=("retire_next_5y", "sum"),
        tenure_eligible_ratio=("tenure_eligible", "mean"),
        near_tenure_ratio=("near_tenure", "mean"),
        avg_years_service=("years_service", "mean"),
        new_teacher_ratio=("new_teacher", "mean"),
        condition_of_tenure_mode=("condition_of_tenure", lambda s: s.mode().iloc[0] if not s.mode().empty else "ไม่พบข้อมูล"),
    ).reset_index()

    data = (
        schools.merge(analysis, on="school_code", how="left")
        .merge(teacher_agg, on="school_code", how="left")
    )

    data["actual_math_teachers"] = data["actual_math_teachers"].fillna(0).astype(int)
    data["calculated_min_math"] = data["calculated_min_math"].fillna(0).astype(int)
    data["hired_teachers"] = data["hired_teachers"].fillna(0).astype(int)
    data["actual_teachers"] = data["actual_teachers"].fillna(0).astype(int)
    data["hired_teacher_ratio"] = data["hired_teachers"] / data["actual_teachers"].replace(0, np.nan)
    data["hired_teacher_ratio"] = data["hired_teacher_ratio"].fillna(0)
    data["school_size"] = data["school_size"].fillna("ไม่ระบุ")
    data["condition_of_tenure_mode"] = data["condition_of_tenure_mode"].fillna("ไม่พบข้อมูล")
    for column in [
        "math_teacher_avg_age",
        "math_teacher_min_years_to_retirement",
        "math_teacher_retirements_next_5y",
        "tenure_eligible_ratio",
        "near_tenure_ratio",
        "avg_years_service",
        "new_teacher_ratio",
    ]:
        data[column] = data[column].fillna(0)

    remaining_math_after_5y = (data["actual_math_teachers"] - data["math_teacher_retirements_next_5y"]).clip(lower=0)
    data["future_shortage_target"] = (data["calculated_min_math"] - remaining_math_after_5y).clip(lower=0).round().astype(int)

    small_school = data["school_size"].str.contains("เล็ก", na=False)
    eligible = data["tenure_eligible_ratio"] >= 0.5
    near = data["near_tenure_ratio"] >= 0.25
    hired_high = data["hired_teacher_ratio"] >= 0.20
    hired_medium = data["hired_teacher_ratio"] >= 0.10
    new_high = data["new_teacher_ratio"] >= 0.30
    new_medium = data["new_teacher_ratio"] >= 0.15
    at_or_below_min = data["actual_math_teachers"] <= data["calculated_min_math"]

    data["risk_target"] = "ต่ำ"
    data.loc[near | hired_medium | new_medium, "risk_target"] = "ปานกลาง"
    data.loc[
        (eligible & (hired_high | new_high | small_school))
        | (small_school & at_or_below_min & (data["actual_math_teachers"] > 0)),
        "risk_target",
    ] = "สูง"

    return data


def make_future_estimators():
    return {
        "Logistic Regression": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(FUTURE_NUMERIC, FUTURE_CATEGORICAL)),
                ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
            ]
        ),
        "Decision Tree": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(FUTURE_NUMERIC, FUTURE_CATEGORICAL)),
                ("model", DecisionTreeRegressor(max_depth=5, random_state=42)),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(FUTURE_NUMERIC, FUTURE_CATEGORICAL)),
                ("model", RandomForestRegressor(n_estimators=250, max_depth=6, random_state=42, n_jobs=1)),
            ]
        ),
        "XGBoost": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(FUTURE_NUMERIC, FUTURE_CATEGORICAL)),
                (
                    "model",
                    XGBRegressor(
                        n_estimators=120,
                        max_depth=3,
                        learning_rate=0.08,
                        objective="reg:squarederror",
                        random_state=42,
                        n_jobs=1,
                    ),
                ),
            ]
        ),
        "LightGBM": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(FUTURE_NUMERIC, FUTURE_CATEGORICAL)),
                (
                    "model",
                    LGBMRegressor(
                        n_estimators=120,
                        learning_rate=0.08,
                        max_depth=3,
                        min_child_samples=3,
                        random_state=42,
                        verbose=-1,
                    ),
                ),
            ]
        ),
        "KNN": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(FUTURE_NUMERIC, FUTURE_CATEGORICAL)),
                ("model", KNeighborsRegressor(n_neighbors=3)),
            ]
        ),
    }


def make_risk_estimators():
    return {
        "Logistic Regression": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(RISK_NUMERIC, RISK_CATEGORICAL)),
                ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
            ]
        ),
        "Decision Tree": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(RISK_NUMERIC, RISK_CATEGORICAL)),
                ("model", DecisionTreeClassifier(max_depth=5, random_state=42, class_weight="balanced")),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(RISK_NUMERIC, RISK_CATEGORICAL)),
                ("model", RandomForestClassifier(n_estimators=250, max_depth=6, random_state=42, n_jobs=1, class_weight="balanced")),
            ]
        ),
        "XGBoost": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(RISK_NUMERIC, RISK_CATEGORICAL)),
                (
                    "model",
                    XGBClassifier(
                        n_estimators=120,
                        max_depth=3,
                        learning_rate=0.08,
                        eval_metric="mlogloss",
                        random_state=42,
                        n_jobs=1,
                    ),
                ),
            ]
        ),
        "LightGBM": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(RISK_NUMERIC, RISK_CATEGORICAL)),
                (
                    "model",
                    LGBMClassifier(
                        n_estimators=120,
                        learning_rate=0.08,
                        max_depth=3,
                        min_child_samples=3,
                        random_state=42,
                        verbose=-1,
                    ),
                ),
            ]
        ),
        "KNN": Pipeline(
            steps=[
                ("preprocess", create_preprocessor(RISK_NUMERIC, RISK_CATEGORICAL)),
                ("model", KNeighborsClassifier(n_neighbors=3)),
            ]
        ),
    }


def rounded_nonnegative(values):
    arr = np.asarray(values, dtype=float)
    return np.maximum(0, np.rint(arr)).astype(int)


def evaluate_future_models(data):
    x = data[FUTURE_FEATURES]
    y = data["future_shortage_target"].astype(int).to_numpy()
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    metrics = []
    estimators = make_future_estimators()

    for name, estimator in estimators.items():
        try:
            raw_pred = cross_val_predict(estimator, x, y, cv=cv)
            pred = rounded_nonnegative(raw_pred)
            metrics.append({
                "model": name,
                "mae": float(mean_absolute_error(y, pred)),
                "rmse": float(math.sqrt(mean_squared_error(y, pred))),
                "accuracy": float(accuracy_score(y, pred)),
                "status": "trained",
            })
        except Exception as exc:
            metrics.append({
                "model": name,
                "mae": None,
                "rmse": None,
                "accuracy": None,
                "status": f"failed: {exc}",
            })

    trained = [row for row in metrics if row["mae"] is not None]
    if not trained:
        best_name = "Dummy"
        best_estimator = DummyRegressor(strategy="median")
        best_estimator.fit(x, y)
        best_metric = {"model": best_name, "mae": None, "rmse": None, "accuracy": None, "status": "fallback"}
    else:
        best_metric = sorted(trained, key=lambda row: (row["mae"], row["rmse"], -row["accuracy"]))[0]
        best_name = best_metric["model"]
        best_estimator = estimators[best_name]
        best_estimator.fit(x, y)

    predictions = rounded_nonnegative(best_estimator.predict(x))
    model_path = MODELS_DIR / "future_shortage_best_model.joblib"
    joblib.dump(
        {
            "task": "future_shortage_prediction",
            "model_name": best_name,
            "model": best_estimator,
            "features": FUTURE_FEATURES,
            "target_definition": "max(calculated_min_math - max(actual_math_teachers - math_teacher_retirements_next_5y, 0), 0)",
            "as_of_date": AS_OF_DATE.isoformat(),
            "metrics": best_metric,
        },
        model_path,
    )
    return metrics, best_metric, predictions, model_path


def evaluate_risk_models(data):
    x = data[RISK_FEATURES]
    y_text = data["risk_target"].astype(str).to_numpy()
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_text)
    class_counts = Counter(y_text)
    min_class_count = min(class_counts.values()) if class_counts else 0
    if len(class_counts) > 1 and min_class_count >= 3:
        cv = StratifiedKFold(n_splits=min(5, min_class_count), shuffle=True, random_state=42)
    else:
        cv = KFold(n_splits=5, shuffle=True, random_state=42)

    metrics = []
    estimators = make_risk_estimators()
    for name, estimator in estimators.items():
        try:
            pred_encoded = cross_val_predict(estimator, x, y, cv=cv)
            pred_text = label_encoder.inverse_transform(pred_encoded)
            metrics.append({
                "model": name,
                "accuracy": float(accuracy_score(y_text, pred_text)),
                "macro_f1": float(f1_score(y_text, pred_text, average="macro", zero_division=0)),
                "status": "trained",
            })
        except Exception as exc:
            metrics.append({
                "model": name,
                "accuracy": None,
                "macro_f1": None,
                "status": f"failed: {exc}",
            })

    trained = [row for row in metrics if row["accuracy"] is not None]
    if not trained:
        best_name = "Dummy"
        best_estimator = DummyClassifier(strategy="most_frequent")
        best_estimator.fit(x, y)
        best_metric = {"model": best_name, "accuracy": None, "macro_f1": None, "status": "fallback"}
    else:
        best_metric = sorted(trained, key=lambda row: (-row["macro_f1"], -row["accuracy"], row["model"]))[0]
        best_name = best_metric["model"]
        best_estimator = estimators[best_name]
        best_estimator.fit(x, y)

    predictions = label_encoder.inverse_transform(best_estimator.predict(x))
    model_path = MODELS_DIR / "sudden_shortage_risk_best_model.joblib"
    joblib.dump(
        {
            "task": "sudden_shortage_risk_level",
            "model_name": best_name,
            "model": best_estimator,
            "label_encoder": label_encoder,
            "features": RISK_FEATURES,
            "label_definition": "rule-based thresholds using tenure eligibility, hired teacher ratio, new teacher ratio, and small school status",
            "as_of_date": AS_OF_DATE.isoformat(),
            "metrics": best_metric,
        },
        model_path,
    )
    return metrics, best_metric, predictions, model_path


def main():
    ensure_dirs()
    data = load_dataset()
    future_metrics, future_best, future_predictions, future_model_path = evaluate_future_models(data)
    risk_metrics, risk_best, risk_predictions, risk_model_path = evaluate_risk_models(data)

    data["future_shortage_prediction"] = future_predictions.astype(int)
    data["sudden_shortage_risk_level"] = risk_predictions

    analysis_records = data[
        [
            "school_code",
            "calculated_min_math",
            "actual_math_teachers",
            "current_math_status",
            "future_shortage_prediction",
            "sudden_shortage_risk_level",
        ]
    ].to_dict(orient="records")

    payload = {
        "analysis": analysis_records,
        "future_metrics": future_metrics,
        "future_best": future_best,
        "risk_metrics": risk_metrics,
        "risk_best": risk_best,
        "risk_target_distribution": dict(Counter(data["risk_target"])),
        "future_target_distribution": {str(k): int(v) for k, v in Counter(data["future_shortage_target"]).items()},
        "model_paths": {
            "future_shortage_prediction": str(future_model_path),
            "sudden_shortage_risk_level": str(risk_model_path),
        },
        "notes": [
            "Prototype training uses rule-derived labels because observed future shortage and sudden resignation/transfer outcomes are not available.",
            "teachers.xlsx contains individual math teacher rows for the four target areas; schools without matching rows have actual_math_teachers equal to 0.",
            "Future shortage target is a 5-year shortage count after subtracting math teachers retiring within five years, assuming no replacement hiring.",
        ],
    }
    PREDICTION_PAYLOAD_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    METRICS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "rows": len(data),
        "future_best": future_best,
        "risk_best": risk_best,
        "model_paths": payload["model_paths"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
