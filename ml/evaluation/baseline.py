import pandas as pd


DATA_PATH = "ml/data/transactions.csv"


def main():
    df = pd.read_csv(DATA_PATH)

    # Baseline strategy:
    # blindly attempt one recovery action for every failed payment.
    #
    # For our simulation, the historical "recovered" outcome tells us
    # whether that retry would have succeeded.

    baseline_recovered = df["recovered"] == 1

    recovered_revenue = df.loc[baseline_recovered, "recovery_amount"].sum()
    total_failed_revenue = df["amount"].sum()

    recovery_rate = (
        recovered_revenue / total_failed_revenue * 100
    )

    successful_recoveries = baseline_recovered.sum()

    print("=" * 50)
    print("RECOVERAI BASELINE EVALUATION")
    print("=" * 50)

    print(f"Transactions evaluated: {len(df):,}")
    print(f"Failed revenue: ₹{total_failed_revenue:,.2f}")
    print(f"Successful recoveries: {successful_recoveries:,}")
    print(f"Recovered revenue: ₹{recovered_revenue:,.2f}")
    print(f"Revenue recovery rate: {recovery_rate:.2f}%")

    print("=" * 50)


if __name__ == "__main__":
    main()