from dataclasses import dataclass


@dataclass
class ActionEstimate:
    action: str
    probability: float
    expected_recovery: float
    cost: float
    expected_net_value: float


ACTION_COSTS = {
    "retry": 20.0,
    "reminder": 10.0,
    "escalate": 100.0,
}


def clamp_probability(value: float) -> float:
    """Keep a probability between 0 and 1."""
    return max(0.0, min(value, 1.0))


def estimate_action_probability(
    model_probability: float,
    failure_reason: str,
    amount: float,
    action: str,
) -> float:
    """
    Estimate recovery probability for a specific intervention.

    The XGBoost prediction is the base signal. We then apply
    small, deterministic action-specific adjustments.
    """

    probability = model_probability

    if action == "retry":

        if failure_reason == "bank_timeout":
            probability += 0.12
        elif failure_reason == "network_error":
            probability += 0.10
        elif failure_reason == "upi_failure":
            probability += 0.07
        elif failure_reason == "card_declined":
            probability -= 0.10
        elif failure_reason == "insufficient_funds":
            probability -= 0.08
        elif failure_reason == "authentication_failed":
            probability -= 0.06

    elif action == "reminder":

        # A reminder is more useful when the customer needs
        # to take an action themselves.
        if failure_reason == "insufficient_funds":
            probability += 0.12
        elif failure_reason == "authentication_failed":
            probability += 0.05
        elif failure_reason == "card_declined":
            probability += 0.03

        if failure_reason in {
            "bank_timeout",
            "network_error",
        }:
            probability -= 0.04

    elif action == "escalate":

        # Human review gets a small advantage for complex cases,
        # but is intentionally expensive.
        if amount > 20000:
            probability += 0.06

        if failure_reason in {
            "card_declined",
            "authentication_failed",
        }:
            probability += 0.05

    return clamp_probability(probability)


def estimate_actions(
    amount: float,
    model_probability: float,
    failure_reason: str,
) -> list[ActionEstimate]:
    """
    Estimate the economic value of every available intervention.
    """

    estimates = []

    for action, cost in ACTION_COSTS.items():

        probability = estimate_action_probability(
            model_probability=model_probability,
            failure_reason=failure_reason,
            amount=amount,
            action=action,
        )

        expected_recovery = amount * probability

        expected_net_value = (
            expected_recovery - cost
        )

        estimates.append(
            ActionEstimate(
                action=action,
                probability=probability,
                expected_recovery=expected_recovery,
                cost=cost,
                expected_net_value=expected_net_value,
            )
        )

    return estimates


def choose_best_action(
    estimates: list[ActionEstimate],
) -> ActionEstimate:
    """Choose the action with the highest expected net value."""

    return max(
        estimates,
        key=lambda estimate: estimate.expected_net_value,
    )