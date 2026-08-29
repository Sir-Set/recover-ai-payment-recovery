from backend.policies.recovery_policy import (
    Action,
    PolicyDecision,
    RecoveryContext,
    evaluate_policy,
)


def test_high_confidence_retry_is_approved():
    context = RecoveryContext(
        amount=5000,
        confidence=0.90,
        attempt_number=1,
        failure_reason="bank_timeout",
        recommended_action=Action.RETRY,
    )

    result = evaluate_policy(context)

    assert result.decision == PolicyDecision.APPROVED
    assert result.action == Action.RETRY


def test_high_value_transaction_requires_review():
    context = RecoveryContext(
        amount=25000,
        confidence=0.95,
        attempt_number=1,
        failure_reason="bank_timeout",
        recommended_action=Action.RETRY,
    )

    result = evaluate_policy(context)

    assert result.decision == PolicyDecision.HUMAN_REVIEW
    assert result.action == Action.ESCALATE


def test_low_confidence_requires_review():
    context = RecoveryContext(
        amount=5000,
        confidence=0.50,
        attempt_number=1,
        failure_reason="bank_timeout",
        recommended_action=Action.RETRY,
    )

    result = evaluate_policy(context)

    assert result.decision == PolicyDecision.HUMAN_REVIEW


def test_non_retryable_failure_cannot_be_retried():
    context = RecoveryContext(
        amount=5000,
        confidence=0.95,
        attempt_number=1,
        failure_reason="card_declined",
        recommended_action=Action.RETRY,
    )

    result = evaluate_policy(context)

    assert result.decision == PolicyDecision.HUMAN_REVIEW
    assert result.action == Action.ESCALATE


def test_max_retry_attempts_stops_retry():
    context = RecoveryContext(
        amount=5000,
        confidence=0.95,
        attempt_number=2,
        failure_reason="bank_timeout",
        recommended_action=Action.RETRY,
    )

    result = evaluate_policy(context)

    assert result.decision == PolicyDecision.STOPPED
    assert result.action == Action.ESCALATE