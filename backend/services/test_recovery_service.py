from backend.policies.recovery_policy import PolicyDecision
from backend.services.recovery_service import RecoveryService


def create_transaction(
    amount=8999.0,
    failure_reason="bank_timeout",
    attempt_number=1,
):
    return {
        "payment_id": "pay_test_001",
        "amount": amount,
        "payment_method": "upi",
        "failure_reason": failure_reason,
        "attempt_number": attempt_number,
        "previous_successes": 7,
        "previous_failures": 1,
        "customer_avg_amount": 7200.0,
        "hour": 14,
        "day_of_week": 2,
    }


def test_normal_transaction_can_be_approved():
    service = RecoveryService()

    transaction = create_transaction()

    result = service.recommend_action(transaction)

    assert result["policy_decision"] == PolicyDecision.APPROVED.value


def test_high_value_transaction_requires_human_review():
    service = RecoveryService()

    transaction = create_transaction(
        amount=25000.0,
    )

    result = service.recommend_action(transaction)

    assert result["policy_decision"] == PolicyDecision.HUMAN_REVIEW.value
    assert result["approved_action"] == "escalate"


def test_non_retryable_failure_requires_review():
    service = RecoveryService()

    transaction = create_transaction(
        failure_reason="card_declined",
    )

    result = service.recommend_action(transaction)

    assert result["policy_decision"] == PolicyDecision.HUMAN_REVIEW.value
    assert result["approved_action"] == "escalate"


def test_max_retry_attempts_are_stopped():
    service = RecoveryService()

    transaction = create_transaction(
        attempt_number=2,
    )

    result = service.recommend_action(transaction)

    assert result["policy_decision"] == PolicyDecision.STOPPED.value
    assert result["approved_action"] == "escalate"