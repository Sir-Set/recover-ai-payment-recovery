import joblib
import pandas as pd

from backend.policies.recovery_policy import (
    Action,
    RecoveryContext,
    evaluate_policy,
)
from backend.services.decision_engine import (
    estimate_actions,
    choose_best_action,
)


MODEL_PATH = "ml/training/models/recovery_model.joblib"


class RecoveryService:
    """Coordinates prediction, decision-making, and policy validation."""

    def __init__(self, model_path: str = MODEL_PATH):
        artifact = joblib.load(model_path)

        self.model = artifact["model"]
        self.preprocessor = artifact["preprocessor"]
        self.features = artifact["features"]

    def predict_recovery_probability(
        self,
        transaction: dict,
    ) -> float:
        """Predict the probability of recovering a failed payment."""

        transaction_df = pd.DataFrame(
            [transaction],
            columns=self.features,
        )

        processed = self.preprocessor.transform(
            transaction_df
        )

        probability = self.model.predict_proba(
            processed
        )[0][1]

        return float(probability)

    def recommend_action(
        self,
        transaction: dict,
    ) -> dict:
        """Generate a recommendation and apply policy controls."""

        recovery_probability = (
            self.predict_recovery_probability(transaction)
        )

        action_estimates = estimate_actions(
            amount=transaction["amount"],
            model_probability=recovery_probability,
            failure_reason=transaction["failure_reason"],
        )

        best_action = choose_best_action(
            action_estimates
        )

        recommended_action = Action(
            best_action.action
        )

        policy_context = RecoveryContext(
            amount=transaction["amount"],
            confidence=recovery_probability,
            attempt_number=transaction["attempt_number"],
            failure_reason=transaction["failure_reason"],
            recommended_action=recommended_action,
        )

        policy_result = evaluate_policy(
            policy_context
        )

        return {
            "payment_id": transaction["payment_id"],
            "amount": transaction["amount"],
            "recovery_probability": recovery_probability,
            "recommended_action": best_action.action,
            "expected_recovery": best_action.expected_recovery,
            "intervention_cost": best_action.cost,
            "net_expected_value": best_action.expected_net_value,
            "policy_decision": policy_result.decision.value,
            "approved_action": policy_result.action.value,
            "policy_reason": policy_result.reason,
            "action_estimates": [
                {
                    "action": estimate.action,
                    "probability": estimate.probability,
                    "expected_recovery": estimate.expected_recovery,
                    "cost": estimate.cost,
                    "expected_net_value": estimate.expected_net_value,
                }
                for estimate in action_estimates
            ],
        }


def main():
    service = RecoveryService()

    example_transaction = {
        "payment_id": "pay_demo_001",
        "amount": 8999.0,
        "payment_method": "upi",
        "failure_reason": "bank_timeout",
        "attempt_number": 1,
        "previous_successes": 7,
        "previous_failures": 1,
        "customer_avg_amount": 7200.0,
        "hour": 14,
        "day_of_week": 2,
    }

    result = service.recommend_action(
        example_transaction
    )

    print("=" * 60)
    print("RECOVERAI DECISION ENGINE")
    print("=" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("=" * 60)


if __name__ == "__main__":
    main()