import joblib
import numpy as np
import pandas as pd

from backend.services.recovery_service import RecoveryService
from experiments.evaluation_environment import (
    ACTIONS,
    simulate_outcome,
)


DATA_PATH = "ml/data/transactions.csv"
MODEL_PATH = "ml/training/models/recovery_model.joblib"


def main():
    print("Loading data and RecoverAI decision engine...")

    df = pd.read_csv(DATA_PATH)

    # Use the exact same service that the API uses.
    service = RecoveryService(MODEL_PATH)

    rng = np.random.default_rng(2026)

    baseline_net = 0.0
    recoverai_net = 0.0

    baseline_revenue = 0.0
    recoverai_revenue = 0.0

    baseline_cost = 0.0
    recoverai_cost = 0.0

    baseline_recoveries = 0
    recoverai_recoveries = 0

    action_counts = {
        "retry": 0,
        "reminder": 0,
        "escalate": 0,
    }

    automated_actions = 0
    human_reviews = 0

    for _, row in df.iterrows():

        transaction = {
            "payment_id": row["payment_id"],
            "amount": row["amount"],
            "payment_method": row["payment_method"],
            "failure_reason": row["failure_reason"],
            "attempt_number": row["attempt_number"],
            "previous_successes": row["previous_successes"],
            "previous_failures": row["previous_failures"],
            "customer_avg_amount": row["customer_avg_amount"],
            "hour": row["hour"],
            "day_of_week": row["day_of_week"],
        }

        # -----------------------------------------------------
        # RecoverAI production decision engine
        # -----------------------------------------------------

        decision = service.recommend_action(transaction)

        # The action that survives the policy engine is the action
        # RecoverAI is actually allowed to take.
        selected_action = decision["approved_action"]

        # -----------------------------------------------------
        # Independent evaluation environment
        # -----------------------------------------------------

        potential_outcomes = {}

        for action in ACTIONS:
            potential_outcomes[action] = simulate_outcome(
                amount=row["amount"],
                failure_reason=row["failure_reason"],
                previous_successes=row["previous_successes"],
                previous_failures=row["previous_failures"],
                attempt_number=row["attempt_number"],
                action=action,
                rng=rng,
            )

        # -----------------------------------------------------
        # Baseline
        #
        # Baseline always retries.
        # -----------------------------------------------------

        baseline = potential_outcomes["retry"]

        baseline_net += baseline["net_recovery"]
        baseline_revenue += baseline["recovery_amount"]
        baseline_cost += baseline["intervention_cost"]
        baseline_recoveries += baseline["recovered"]

        # -----------------------------------------------------
        # RecoverAI
        # -----------------------------------------------------

        recoverai = potential_outcomes[selected_action]

        recoverai_net += recoverai["net_recovery"]
        recoverai_revenue += recoverai["recovery_amount"]
        recoverai_cost += recoverai["intervention_cost"]
        recoverai_recoveries += recoverai["recovered"]

        action_counts[selected_action] += 1

        if selected_action == "escalate":
            human_reviews += 1
        else:
            automated_actions += 1

    # ---------------------------------------------------------
    # Business metrics
    # ---------------------------------------------------------

    incremental_net = recoverai_net - baseline_net

    improvement = (
        incremental_net / abs(baseline_net) * 100
        if baseline_net != 0
        else 0
    )

    automation_rate = (
        automated_actions / len(df) * 100
    )

    human_review_rate = (
        human_reviews / len(df) * 100
    )

    recovery_rate_baseline = (
        baseline_recoveries / len(df) * 100
    )

    recovery_rate_recoverai = (
        recoverai_recoveries / len(df) * 100
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    print("\n" + "=" * 72)
    print("RECOVERAI PRODUCTION DECISION ENGINE EXPERIMENT")
    print("=" * 72)

    print(f"Transactions evaluated: {len(df):,}")

    print("\nBASELINE — ALWAYS RETRY")

    print(
        f"Recovered revenue: "
        f"₹{baseline_revenue:,.2f}"
    )

    print(
        f"Intervention cost: "
        f"₹{baseline_cost:,.2f}"
    )

    print(
        f"Net recovery: "
        f"₹{baseline_net:,.2f}"
    )

    print(
        f"Successful recoveries: "
        f"{baseline_recoveries:,}"
    )

    print(
        f"Recovery rate: "
        f"{recovery_rate_baseline:.2f}%"
    )

    print("\nRECOVERAI")

    print(
        f"Recovered revenue: "
        f"₹{recoverai_revenue:,.2f}"
    )

    print(
        f"Intervention cost: "
        f"₹{recoverai_cost:,.2f}"
    )

    print(
        f"Net recovery: "
        f"₹{recoverai_net:,.2f}"
    )

    print(
        f"Successful recoveries: "
        f"{recoverai_recoveries:,}"
    )

    print(
        f"Recovery rate: "
        f"{recovery_rate_recoverai:.2f}%"
    )

    print("\nBUSINESS IMPACT")

    print(
        f"Incremental net recovery: "
        f"₹{incremental_net:,.2f}"
    )

    print(
        f"Improvement over baseline: "
        f"{improvement:.2f}%"
    )

    print("\nOPERATIONAL SAFETY")

    print(
        f"Automated actions: "
        f"{automated_actions:,} "
        f"({automation_rate:.2f}%)"
    )

    print(
        f"Human reviews: "
        f"{human_reviews:,} "
        f"({human_review_rate:.2f}%)"
    )

    print("\nACTION DISTRIBUTION")

    for action, count in action_counts.items():

        percentage = count / len(df) * 100

        print(
            f"{action}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    print("=" * 72)


if __name__ == "__main__":
    main()