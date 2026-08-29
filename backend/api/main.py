import os

import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.database.audit import (
    get_events,
    initialize_database,
    record_event,
)

from backend.services.recovery_service import RecoveryService


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="RecoverAI API",
    description="AI-powered payment recovery decision engine",
    version="0.1.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE + SERVICE INITIALIZATION
# =========================================================

initialize_database()

recovery_service = RecoveryService()


# =========================================================
# REQUEST MODEL
# =========================================================

class RecoveryRequest(BaseModel):
    payment_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    payment_method: str = Field(min_length=1)
    failure_reason: str = Field(min_length=1)
    attempt_number: int = Field(ge=1)
    previous_successes: int = Field(ge=0)
    previous_failures: int = Field(ge=0)
    customer_avg_amount: float = Field(ge=0)
    hour: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "recover-ai",
    }


# =========================================================
# PAYMENT DATASET
# =========================================================

def get_transaction_dataset_path():
    """
    Return the absolute path to the generated transaction dataset.

    Project structure:

        recover-ai/
        ├── backend/
        │   └── api/
        │       └── main.py
        │
        └── ml/
            └── data/
                └── transactions.csv
    """

    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

    return os.path.join(
        project_root,
        "ml",
        "data",
        "transactions.csv",
    )


# =========================================================
# PAYMENTS ENDPOINT
# =========================================================

@app.get("/api/v1/payments")
def get_payments():
    """
    Return payment transactions from the generated dataset.
    """

    dataset_path = get_transaction_dataset_path()

    if not os.path.exists(dataset_path):
        return {
            "total": 0,
            "payments": [],
            "error": "Transaction dataset not found.",
        }

    try:
        df = pd.read_csv(dataset_path)

        # Convert NaN values to None so the response
        # can be safely serialized as JSON.
        df = df.where(pd.notnull(df), None)

        payments = df.to_dict(orient="records")

        return {
            "total": len(payments),
            "payments": payments,
        }

    except Exception as exc:
        return {
            "total": 0,
            "payments": [],
            "error": f"Unable to load transaction dataset: {str(exc)}",
        }


# =========================================================
# SINGLE PAYMENT LOOKUP
# =========================================================

@app.get("/api/v1/payments/{payment_id}")
def get_payment(payment_id: str):
    """
    Return one payment by payment_id.
    """

    dataset_path = get_transaction_dataset_path()

    if not os.path.exists(dataset_path):
        return {
            "error": "Transaction dataset not found.",
        }

    try:
        df = pd.read_csv(dataset_path)

        matches = df[
            df["payment_id"].astype(str) == str(payment_id)
        ]

        if matches.empty:
            return {
                "error": "Payment not found.",
                "payment_id": payment_id,
            }

        payment = matches.iloc[0].where(
            pd.notnull(matches.iloc[0]),
            None,
        ).to_dict()

        return payment

    except Exception as exc:
        return {
            "error": f"Unable to load payment: {str(exc)}",
        }


# =========================================================
# RECOVERY DECISION
# =========================================================

@app.post("/api/v1/recover")
def recover_payment(request: RecoveryRequest):
    """
    Run a payment through the complete RecoverAI
    decision pipeline.

    Flow:

        Request
          ↓
        RecoveryService
          ↓
        XGBoost
          ↓
        Intervention optimization
          ↓
        Deterministic policy
          ↓
        Audit database
          ↓
        Response
    """

    transaction = request.model_dump()

    result = recovery_service.recommend_action(
        transaction
    )

    record_event(
        payment_id=result["payment_id"],
        event_type="RECOVERY_DECISION",
        action=result["approved_action"],
        decision=result["policy_decision"],
        recovery_probability=result["recovery_probability"],
        expected_recovery=result["expected_recovery"],
        reason=result["policy_reason"],
    )

    return result


# =========================================================
# AUDIT TRAIL
# =========================================================

@app.get("/api/v1/audit")
def get_audit_events(
    payment_id: str | None = None,
):
    """
    Return recorded recovery decisions.

    Optional query parameter:

        /api/v1/audit?payment_id=pay_demo_001
    """

    return {
        "events": get_events(payment_id),
    }