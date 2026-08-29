import numpy as np


ACTIONS = ["retry", "reminder", "escalate"]


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(value, maximum))


def action_recovery_probability(
    amount: float,
    failure_reason: str,
    previous_successes: int,
    previous_failures: int,
    attempt_number: int,
    action: str,
) -> float:
    """
    Generate an independent synthetic probability for an intervention.

    This function represents our evaluation environment, not the
    production model.

    IMPORTANT:
    The model being evaluated does not receive these probabilities.
    They are used only to simulate possible outcomes.
    """

    # General customer recovery tendency.
    customer_signal = 0.50

    customer_signal += min(previous_successes * 0.012, 0.18)
    customer_signal -= min(previous_failures * 0.035, 0.20)

    # Repeated attempts reduce recovery probability.
    customer_signal -= min((attempt_number - 1) * 0.10, 0.20)

    # Transaction size has a small effect.
    if amount < 5000:
        customer_signal += 0.04
    elif amount > 30000:
        customer_signal -= 0.06

    # ---------------------------------------------------------
    # Action-specific behavior
    # ---------------------------------------------------------

    action_signal = 0.0

    if action == "retry":

        if failure_reason == "bank_timeout":
            action_signal += 0.20
        elif failure_reason == "network_error":
            action_signal += 0.17
        elif failure_reason == "upi_failure":
            action_signal += 0.12
        elif failure_reason == "insufficient_funds":
            action_signal -= 0.12
        elif failure_reason == "card_declined":
            action_signal -= 0.18
        elif failure_reason == "authentication_failed":
            action_signal -= 0.14

    elif action == "reminder":

        if failure_reason == "insufficient_funds":
            action_signal += 0.18
        elif failure_reason == "authentication_failed":
            action_signal += 0.07
        elif failure_reason == "card_declined":
            action_signal += 0.04
        elif failure_reason in {
            "bank_timeout",
            "network_error",
        }:
            action_signal -= 0.04

    elif action == "escalate":

        # Human review is useful for difficult cases, but it is
        # deliberately expensive and not automatically superior.
        if failure_reason in {
            "card_declined",
            "authentication_failed",
        }:
            action_signal += 0.08

        if amount > 20000:
            action_signal += 0.06

    probability = customer_signal + action_signal

    return clamp(probability)


def simulate_outcome(
    amount: float,
    failure_reason: str,
    previous_successes: int,
    previous_failures: int,
    attempt_number: int,
    action: str,
    rng: np.random.Generator,
) -> dict:
    """
    Simulate one independent outcome for a selected action.

    The random generator is supplied by the evaluation experiment
    so the entire experiment remains reproducible.
    """

    probability = action_recovery_probability(
        amount=amount,
        failure_reason=failure_reason,
        previous_successes=previous_successes,
        previous_failures=previous_failures,
        attempt_number=attempt_number,
        action=action,
    )

    recovered = int(rng.random() < probability)

    if recovered:
        recovery_amount = amount * rng.uniform(0.85, 1.0)
    else:
        recovery_amount = 0.0

    intervention_costs = {
        "retry": 20.0,
        "reminder": 10.0,
        "escalate": 100.0,
    }

    cost = intervention_costs[action]

    return {
        "action": action,
        "probability": probability,
        "recovered": recovered,
        "recovery_amount": recovery_amount,
        "intervention_cost": cost,
        "net_recovery": recovery_amount - cost,
    }