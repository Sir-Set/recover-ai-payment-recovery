from backend.database.audit import (
    get_events,
    initialize_database,
    record_event,
)


def test_audit_event_can_be_recorded():
    initialize_database()

    payment_id = "pay_test_audit"

    record_event(
        payment_id=payment_id,
        event_type="TEST_EVENT",
        action="retry",
        decision="approved",
        recovery_probability=0.90,
        expected_recovery=5000.0,
        reason="Test audit event",
    )

    events = get_events(payment_id)

    assert len(events) >= 1
    assert events[-1]["payment_id"] == payment_id
    assert events[-1]["event_type"] == "TEST_EVENT"
    assert events[-1]["decision"] == "approved"