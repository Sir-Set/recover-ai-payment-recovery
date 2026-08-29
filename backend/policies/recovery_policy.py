from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    RETRY = "retry"
    REMINDER = "reminder"
    ESCALATE = "escalate"


class PolicyDecision(str, Enum):
    APPROVED = "approved"
    HUMAN_REVIEW = "human_review"
    STOPPED = "stopped"


@dataclass
class RecoveryContext:
    amount: float
    confidence: float
    attempt_number: int
    failure_reason: str
    recommended_action: Action


@dataclass
class PolicyResult:
    decision: PolicyDecision
    action: Action
    reason: str


# ---------------------------------------------------------
# Policy configuration
# ---------------------------------------------------------

MAX_AUTOMATION_AMOUNT = 10_000

MIN_AUTOMATION_CONFIDENCE = 0.55

MIN_HUMAN_REVIEW_CONFIDENCE = 0.40

MAX_RETRY_ATTEMPTS = 2


# Failure types where a retry may be automated.
RETRYABLE_FAILURES = {
    "bank_timeout",
    "network_error",
    "upi_failure",
}


# Failure types that require human review.
HUMAN_REVIEW_FAILURES = {
    "card_declined",
    "authentication_failed",
}


def evaluate_policy(context: RecoveryContext) -> PolicyResult:
    """
    Determine whether an AI-recommended recovery action
    is allowed by the deterministic policy engine.
    """

    # -----------------------------------------------------
    # Rule 1: Stop excessive retries.
    # -----------------------------------------------------

    if (
        context.recommended_action == Action.RETRY
        and context.attempt_number >= MAX_RETRY_ATTEMPTS
    ):
        return PolicyResult(
            decision=PolicyDecision.STOPPED,
            action=Action.ESCALATE,
            reason="Maximum retry attempts reached.",
        )

    # -----------------------------------------------------
    # Rule 2: Sensitive failure types require human review.
    # -----------------------------------------------------

    if context.failure_reason in HUMAN_REVIEW_FAILURES:
        return PolicyResult(
            decision=PolicyDecision.HUMAN_REVIEW,
            action=Action.ESCALATE,
            reason=(
                "Failure type requires human review "
                "before recovery action."
            ),
        )

    # -----------------------------------------------------
    # Rule 3: Only transient failures can be automatically retried.
    # -----------------------------------------------------

    if (
        context.recommended_action == Action.RETRY
        and context.failure_reason not in RETRYABLE_FAILURES
    ):
        return PolicyResult(
            decision=PolicyDecision.HUMAN_REVIEW,
            action=Action.ESCALATE,
            reason=(
                "Failure reason is not approved "
                "for automatic retry."
            ),
        )

    # -----------------------------------------------------
    # Rule 4: High-value transactions require human approval.
    # -----------------------------------------------------

    if context.amount > MAX_AUTOMATION_AMOUNT:
        return PolicyResult(
            decision=PolicyDecision.HUMAN_REVIEW,
            action=Action.ESCALATE,
            reason=(
                "Transaction exceeds the automatic "
                "recovery amount limit."
            ),
        )

    # -----------------------------------------------------
    # Rule 5: Very low-confidence recommendations require review.
    # -----------------------------------------------------

    if context.confidence < MIN_HUMAN_REVIEW_CONFIDENCE:
        return PolicyResult(
            decision=PolicyDecision.HUMAN_REVIEW,
            action=Action.ESCALATE,
            reason=(
                "AI confidence is too low "
                "for automated recovery."
            ),
        )

    # -----------------------------------------------------
    # Rule 6: Below automation threshold requires review.
    # -----------------------------------------------------

    if context.confidence < MIN_AUTOMATION_CONFIDENCE:
        return PolicyResult(
            decision=PolicyDecision.HUMAN_REVIEW,
            action=Action.ESCALATE,
            reason=(
                "AI confidence is below "
                "the automation threshold."
            ),
        )

    # -----------------------------------------------------
    # Rule 7: All safety checks passed.
    # -----------------------------------------------------

    return PolicyResult(
        decision=PolicyDecision.APPROVED,
        action=context.recommended_action,
        reason="Recovery action satisfies all automation policies.",
    )