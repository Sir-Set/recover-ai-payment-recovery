import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker


fake = Faker()
random.seed(42)
np.random.seed(42)


NUM_TRANSACTIONS = 5000


FAILURE_REASONS = [
    "bank_timeout",
    "insufficient_funds",
    "upi_failure",
    "card_declined",
    "network_error",
    "authentication_failed",
]

PAYMENT_METHODS = [
    "upi",
    "credit_card",
    "debit_card",
    "netbanking",
]


def generate_transaction(transaction_number: int) -> dict:
    """Generate one synthetic failed payment transaction."""

    customer_id = f"cust_{random.randint(1, 1000):04d}"
    payment_id = f"pay_demo_{transaction_number:06d}"

    amount = round(random.uniform(200, 50000), 2)

    payment_method = random.choice(PAYMENT_METHODS)
    failure_reason = random.choice(FAILURE_REASONS)

    attempt_number = random.choices(
        [1, 2, 3],
        weights=[70, 25, 5],
        k=1,
    )[0]

    previous_successes = random.randint(0, 20)
    previous_failures = random.randint(0, 5)

    customer_avg_amount = round(
        random.uniform(500, 30000),
        2,
    )

    transaction_time = datetime.now() - timedelta(
        days=random.randint(0, 180),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )

    hour = transaction_time.hour
    day_of_week = transaction_time.weekday()

    # ---------------------------------------------------------
    # Synthetic recovery behavior
    # ---------------------------------------------------------
    #
    # We intentionally create relationships between the
    # transaction features and recovery probability.
    #
    # This gives our future ML model a meaningful signal to learn
    # instead of completely random outcomes.
    # ---------------------------------------------------------

    recovery_score = 0.50

    # Failure-specific behavior
    if failure_reason == "bank_timeout":
        recovery_score += 0.20
    elif failure_reason == "network_error":
        recovery_score += 0.15
    elif failure_reason == "upi_failure":
        recovery_score += 0.08
    elif failure_reason == "insufficient_funds":
        recovery_score -= 0.05
    elif failure_reason == "card_declined":
        recovery_score -= 0.15
    elif failure_reason == "authentication_failed":
        recovery_score -= 0.10

    # Strong customer history increases recovery likelihood
    recovery_score += min(previous_successes * 0.015, 0.20)

    # Repeated failures reduce recovery likelihood
    recovery_score -= previous_failures * 0.04

    # Multiple attempts reduce the chance of another recovery
    recovery_score -= (attempt_number - 1) * 0.12

    # Extremely large transactions are slightly harder to recover
    if amount > 30000:
        recovery_score -= 0.10
    elif amount < 5000:
        recovery_score += 0.05

    # Transactions during normal business hours get a small boost
    if 9 <= hour <= 20:
        recovery_score += 0.05

    # Add a small amount of randomness so the problem isn't perfect
    recovery_score += np.random.normal(0, 0.08)

    recovery_probability = 1 / (1 + np.exp(-5 * (recovery_score - 0.5)))

    recovered = int(np.random.random() < recovery_probability)

    if recovered:
        recovery_amount = round(
            amount * random.uniform(0.85, 1.0),
            2,
        )
    else:
        recovery_amount = 0.0

    return {
        "payment_id": payment_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": "INR",
        "payment_method": payment_method,
        "failure_reason": failure_reason,
        "attempt_number": attempt_number,
        "previous_successes": previous_successes,
        "previous_failures": previous_failures,
        "customer_avg_amount": customer_avg_amount,
        "transaction_time": transaction_time.isoformat(),
        "hour": hour,
        "day_of_week": day_of_week,
        "recovered": recovered,
        "recovery_amount": recovery_amount,
    }


def main():
    print("Generating synthetic payment data...")

    transactions = [
        generate_transaction(i)
        for i in range(1, NUM_TRANSACTIONS + 1)
    ]

    df = pd.DataFrame(transactions)

    output_path = "ml/data/transactions.csv"
    df.to_csv(output_path, index=False)

    total_failed_revenue = df["amount"].sum()
    recovered_revenue = df["recovery_amount"].sum()
    recovery_rate = df["recovered"].mean() * 100

    print("\nDataset generated successfully.")
    print(f"Transactions: {len(df):,}")
    print(f"Total failed revenue: ₹{total_failed_revenue:,.2f}")
    print(f"Recovered revenue: ₹{recovered_revenue:,.2f}")
    print(f"Recovery rate: {recovery_rate:.2f}%")

    print("\nFailure distribution:")
    print(df["failure_reason"].value_counts())

    print("\nFirst 5 transactions:")
    print(df.head())


if __name__ == "__main__":
    main()