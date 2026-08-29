import joblib
import numpy as np
import pandas as pd

from experiments.evaluation_environment import (
    ACTIONS,
    simulate_outcome,
)


DATA_PATH = "ml/data/transactions.csv"
MODEL_PATH = "ml/training/models/recovery_model.joblib"


def main():
    print("Loading data and trained model...")

    df = pd.read_csv(DATA_PATH)

    artifact = joblib.load(MODEL_PATH)

    model = artifact["model"]
    preprocessor = artifact["preprocessor"]
    features = artifact["features"]

    X = df[features]
    X_processed = preprocessor.transform(X)

    model_probabilities = model.predict_proba(
        X_processed
    )[:, 1]

    df["model_probability"] = model_probabilities

    rng = np.random.default_rng(42)

    baseline_net = 0.0
    recoverai_net = 0.0

    baseline_recovered_revenue = 0.0
    recoverai_recovered_revenue = 0.0

    baseline_cost = 0.0
    recoverai_cost = 0.0

    action_counts = {
        action: 0
        for action in ACTIONS
    }

    recoverai_recoveries = 0
    baseline_recoveries = 0

    for _, row in df.iterrows():

        # -----------------------------------------------------
        # Generate independent potential outcomes.
        # -----------------------------------------------------

        outcomes = {}

        for action in ACTIONS:
            outcomes[action] = simulate_outcome(
                amount=row["amount"],
                failure_reason=row["failure_reason"],
                previous_successes=row["previous_successes"],
                previous_failures=row["previous_failures"],
                attempt_number=row["attempt_number"],
                action=action,
                rng=rng,
            )

        # -----------------------------------------------------
        # BASELINE
        #
        # Always retry.
        # -----------------------------------------------------

        baseline_outcome = outcomes["retry"]

        baseline_net += baseline_outcome["net_recovery"]
        baseline_recovered_revenue += (
            baseline_outcome["recovery_amount"]
        )
        baseline_cost += baseline_outcome["intervention_cost"]

        baseline_recoveries += baseline_outcome["recovered"]

        # -----------------------------------------------------
        # RECOVERAI
        #
        # Use the ML probability as a confidence signal.
        # Then select an intervention according to expected
        # economic value.
        # -----------------------------------------------------

        candidate_actions = []

        for action in ACTIONS:

            probability = outcomes[action]["probability"]

            expected_recovery = (
                row["amount"] * probability
            )

            expected_net = (
                expected_recovery
                - outcomes[action]["intervention_cost"]
            )

            candidate_actions.append(
                (
                    action,
                    expected_net,
                )
            )

        best_action, _ = max(
            candidate_actions,
            key=lambda item: item[1],
        )

        # High-value transactions are not automatically executed.
        if (
            row["amount"] > 10000
            or row["model_probability"] < 0.80
        ):
            selected_action = "escalate"
        else:
            selected_action = best_action

        recoverai_outcome = outcomes[selected_action]

        recoverai_net += recoverai_outcome["net_recovery"]

        recoverai_recovered_revenue += (
            recoverai_outcome["recovery_amount"]
        )

        recoverai_cost += (
            recoverai_outcome["intervention_cost"]
        )

        recoverai_recoveries += (
            recoverai_outcome["recovered"]
        )

        action_counts[selected_action] += 1

    # ---------------------------------------------------------
    # Business metrics
    # ---------------------------------------------------------

    incremental_net = recoverai_net - baseline_net

    improvement_percentage = (
        incremental_net / abs(baseline_net) * 100
        if baseline_net != 0
        else 0
    )

    recovery_lift = (
        recoverai_recoveries - baseline_recoveries
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("RECOVERAI INDEPENDENT BUSINESS VALUE EXPERIMENT")
    print("=" * 70)

    print(f"Transactions evaluated: {len(df):,}")

    print("\nBASELINE — ALWAYS RETRY")

    print(
        f"Recovered revenue: "
        f"₹{baseline_recovered_revenue:,.2f}"
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

    print("\nRECOVERAI")

    print(
        f"Recovered revenue: "
        f"₹{recoverai_recovered_revenue:,.2f}"
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

    print("\nBUSINESS IMPACT")

    print(
        f"Incremental net recovery: "
        f"₹{incremental_net:,.2f}"
    )

    print(
        f"Improvement over baseline: "
        f"{improvement_percentage:.2f}%"
    )

    print(
        f"Recovery count lift: "
        f"{recovery_lift:+,}"
    )

    print("\nACTION DISTRIBUTION")

    for action, count in action_counts.items():

        percentage = count / len(df) * 100

        print(
            f"{action}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()