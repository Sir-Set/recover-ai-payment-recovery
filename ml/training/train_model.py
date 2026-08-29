import os

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier


DATA_PATH = "ml/data/transactions.csv"
MODEL_DIR = "ml/training/models"
MODEL_PATH = os.path.join(MODEL_DIR, "recovery_model.joblib")


def main():
    print("Loading transaction data...")

    df = pd.read_csv(DATA_PATH)

    # Features available BEFORE the recovery outcome happens.
    feature_columns = [
        "amount",
        "payment_method",
        "failure_reason",
        "attempt_number",
        "previous_successes",
        "previous_failures",
        "customer_avg_amount",
        "hour",
        "day_of_week",
    ]

    target_column = "recovered"

    X = df[feature_columns]
    y = df[target_column]

    print(f"Total transactions: {len(df):,}")
    print(f"Features: {len(feature_columns)}")

    # ---------------------------------------------------------
    # Train / test split
    # ---------------------------------------------------------
    #
    # The model sees only the training data while learning.
    # The test set remains unseen until final evaluation.
    # ---------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print(f"Training samples: {len(X_train):,}")
    print(f"Test samples: {len(X_test):,}")

    # ---------------------------------------------------------
    # Feature preprocessing
    # ---------------------------------------------------------

    categorical_features = [
        "payment_method",
        "failure_reason",
    ]

    numerical_features = [
        "amount",
        "attempt_number",
        "previous_successes",
        "previous_failures",
        "customer_avg_amount",
        "hour",
        "day_of_week",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "numerical",
                "passthrough",
                numerical_features,
            ),
        ]
    )

    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    # ---------------------------------------------------------
    # XGBoost model
    # ---------------------------------------------------------

    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
    )

    print("\nTraining XGBoost model...")

    model.fit(
        X_train_processed,
        y_train,
    )

    # ---------------------------------------------------------
    # Evaluation
    # ---------------------------------------------------------

    predictions = model.predict(X_test_processed)
    probabilities = model.predict_proba(X_test_processed)[:, 1]

    accuracy = accuracy_score(y_test, predictions)
    auc = roc_auc_score(y_test, probabilities)

    print("\n" + "=" * 60)
    print("RECOVERAI XGBOOST MODEL EVALUATION")
    print("=" * 60)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC-AUC:  {auc:.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, predictions))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))

    # ---------------------------------------------------------
    # Save model + preprocessing pipeline
    # ---------------------------------------------------------

    os.makedirs(MODEL_DIR, exist_ok=True)

    artifact = {
        "model": model,
        "preprocessor": preprocessor,
        "features": feature_columns,
    }

    joblib.dump(artifact, MODEL_PATH)

    print("\nModel saved successfully:")
    print(MODEL_PATH)


if __name__ == "__main__":
    main()