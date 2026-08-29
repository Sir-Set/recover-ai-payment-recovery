import random
from dataclasses import dataclass


@dataclass
class InterventionOutcome:
    action: str
    recovery_probability: float
    expected_recovery: float
    intervention_cost: float
    net_expected_value: float


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Keep a probability between 0 and 1."""
    return max(minimum, min(value, maximum))


def calculate_intervention_outcomes(
    amount: float,
    failure_reason: str,
    previous_successes: int,
    previous_failures: int,
    attempt_number: int,
) -> list[InterventionOutcome]:
    """
    Simulate the expected economic outcome of each recovery intervention.

    This is a synthetic environment for experimentation.
    It does not represent real Razorpay production probabilities.
    """

    # Start with a neutral recovery probability.
    base_probability = 0.50

    # Customer history.
    base_probability += min(previous_successes * 0.015, 0.20)
    base_probability -= previous_failures * 0.04

    # Repeated attempts reduce the probability of successful recovery.
    base_probability -= (attempt_number - 1) * 0.10

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------

    retry_probability = base_probability

    if failure_reason == "bank_timeout":
        retry_probability += 0.20
    elif failure_reason == "network_error":
        retry_probability += 0.18
    elif failure_reason == "upi_failure":
        retry_probability += 0.12
    elif failure_reason == "insufficient_funds":
        retry_probability -= 0.10
    elif failure_reason == "card_declined":
        retry_probability -= 0.18
    elif failure_reason == "authentication_failed":
        retry_probability -= 0.12

    retry_probability = clamp(retry_probability)

    retry_cost = 20.0

    # ---------------------------------------------------------
    # REMINDER
    # ---------------------------------------------------------

    reminder_probability = base_probability

    if failure_reason == "insufficient_funds":
        reminder_probability += 0.20
    elif failure_reason == "authentication_failed":
        reminder_probability += 0.08
    elif failure_reason == "card_declined":
        reminder_probability += 0.05
    elif failure_reason in {"bank_timeout", "network_error"}:
        reminder_probability -= 0.05

    reminder_probability = clamp(reminder_probability)

    reminder_cost = 10.0

    # ---------------------------------------------------------
    # ESCALATION
    # ---------------------------------------------------------

    escalation_probability = base_probability + 0.05

    # Human intervention becomes more valuable for complex cases.
    if amount > 10000:
        escalation_probability += 0.10

    if failure_reason in {
        "card_declined",
        "authentication_failed",
    }:
        escalation_probability += 0.08

    escalation_probability = clamp(escalation_probability)

    escalation_cost = 100.0

    # ---------------------------------------------------------
    # Calculate expected recovery value.
    # ---------------------------------------------------------

    retry_expected_recovery = amount * retry_probability
    reminder_expected_recovery = amount * reminder_probability
    escalation_expected_recovery = amount * escalation_probability

    return [
        InterventionOutcome(
            action="retry",
            recovery_probability=retry_probability,
            expected_recovery=retry_expected_recovery,
            intervention_cost=retry_cost,
            net_expected_value=retry_expected_recovery - retry_cost,
        ),
        InterventionOutcome(
            action="reminder",
            recovery_probability=reminder_probability,
            expected_recovery=reminder_expected_recovery,
            intervention_cost=reminder_cost,
            net_expected_value=reminder_expected_recovery - reminder_cost,
        ),
        InterventionOutcome(
            action="escalate",
            recovery_probability=escalation_probability,
            expected_recovery=escalation_expected_recovery,
            intervention_cost=escalation_cost,
            net_expected_value=escalation_expected_recovery - escalation_cost,
        ),
    ]


def choose_best_intervention(
    outcomes: list[InterventionOutcome],
) -> InterventionOutcome:
    """Choose the intervention with the highest net expected value."""

    return max(
        outcomes,
        key=lambda outcome: outcome.net_expected_value,
    )


def main():
    random.seed(42)

    amount = 8999.0
    failure_reason = "bank_timeout"
    previous_successes = 7
    previous_failures = 1
    attempt_number = 1

    outcomes = calculate_intervention_outcomes(
        amount=amount,
        failure_reason=failure_reason,
        previous_successes=previous_successes,
        previous_failures=previous_failures,
        attempt_number=attempt_number,
    )

    best = choose_best_intervention(outcomes)

    print("=" * 60)
    print("RECOVERAI INTERVENTION SIMULATION")
    print("=" * 60)

    print(f"Payment amount: ₹{amount:,.2f}")
    print(f"Failure reason: {failure_reason}")

    print("\nIntervention comparison:")

    for outcome in outcomes:
        print(
            f"\n{outcome.action.upper()}"
            f"\n  Recovery probability: "
            f"{outcome.recovery_probability:.2%}"
            f"\n  Expected recovery: "
            f"₹{outcome.expected_recovery:,.2f}"
            f"\n  Intervention cost: "
            f"₹{outcome.intervention_cost:,.2f}"
            f"\n  Net expected value: "
            f"₹{outcome.net_expected_value:,.2f}"
        )

    print("\n" + "-" * 60)
    print(f"RECOMMENDED ACTION: {best.action.upper()}")
    print(f"Expected value: ₹{best.net_expected_value:,.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()