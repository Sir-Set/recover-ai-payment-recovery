import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const defaultPayment = {
  payment_id: "pay_demo_live",
  amount: 8999,
  payment_method: "upi",
  failure_reason: "bank_timeout",
  attempt_number: 1,
  previous_successes: 7,
  previous_failures: 1,
  customer_avg_amount: 7200,
  hour: 14,
  day_of_week: 2,
};

const demoTransactions = [
  {
    id: "pay_demo_001",
    amount: "₹8,999",
    reason: "Bank timeout",
    probability: "87.4%",
    action: "Retry",
    status: "Approved",
  },
  {
    id: "pay_demo_002",
    amount: "₹32,500",
    reason: "Card declined",
    probability: "71.2%",
    action: "Escalate",
    status: "Human review",
  },
  {
    id: "pay_demo_003",
    amount: "₹4,200",
    reason: "UPI failure",
    probability: "82.1%",
    action: "Retry",
    status: "Approved",
  },
  {
    id: "pay_demo_004",
    amount: "₹12,800",
    reason: "Network error",
    probability: "79.6%",
    action: "Escalate",
    status: "Human review",
  },
  {
    id: "pay_demo_005",
    amount: "₹3,750",
    reason: "Insufficient funds",
    probability: "64.8%",
    action: "Reminder",
    status: "Approved",
  },
];

function App() {
  const [activeTab, setActiveTab] = useState("overview");

  const [payment, setPayment] = useState(defaultPayment);

  const [decision, setDecision] = useState(null);

  const [auditEvents, setAuditEvents] = useState([]);

  const [payments, setPayments] = useState([]);

  const [paymentsLoading, setPaymentsLoading] = useState(false);

  const [loading, setLoading] = useState(false);

  const [auditLoading, setAuditLoading] = useState(false);

  const [error, setError] = useState("");

  const [searchTerm, setSearchTerm] = useState("");

  const [failureFilter, setFailureFilter] = useState("all");

  const [selectedPayment, setSelectedPayment] = useState(null);

  const metrics = [
    {
      label: "Failed Revenue",
      value: "₹12.58 Cr",
      change: "5,000 transactions",
    },
    {
      label: "Recovery Rate",
      value: "54.50%",
      change: "+6.78 pp vs baseline",
    },
    {
      label: "Incremental Recovery",
      value: "₹64.45 L",
      change: "+11.96% vs baseline",
    },
    {
      label: "Automated Actions",
      value: "7.20%",
      change: "Policy controlled",
    },
  ];

  /*
   * ---------------------------------------------------------
   * LOAD REAL PAYMENTS
   * ---------------------------------------------------------
   */

  const loadPayments = async () => {
    setPaymentsLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/v1/payments`
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load payment transactions."
        );
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setPayments(data.payments || []);
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to the payment API."
      );
    } finally {
      setPaymentsLoading(false);
    }
  };

  /*
   * Load the real transaction dataset when the
   * Payments tab is opened.
   */

  useEffect(() => {
    if (activeTab === "payments" && payments.length === 0) {
      loadPayments();
    }
  }, [activeTab]);

  /*
   * ---------------------------------------------------------
   * UPDATE PAYMENT FORM
   * ---------------------------------------------------------
   */

  const updatePayment = (field, value) => {
    setPayment((current) => ({
      ...current,
      [field]: value,
    }));
  };

  /*
   * ---------------------------------------------------------
   * FORMATTERS
   * ---------------------------------------------------------
   */

  const formatCurrency = (value) => {
    if (value === undefined || value === null) {
      return "₹0";
    }

    return `₹${Number(value).toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    })}`;
  };

  const formatPercentage = (value) => {
    if (value === undefined || value === null) {
      return "0%";
    }

    return `${(Number(value) * 100).toFixed(1)}%`;
  };

  const formatAction = (value) => {
    if (!value) {
      return "UNKNOWN";
    }

    return String(value).toUpperCase();
  };

  const formatFailureReason = (value) => {
    if (!value) {
      return "Unknown";
    }

    return String(value)
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) =>
        char.toUpperCase()
      );
  };

  /*
   * ---------------------------------------------------------
   * ANALYZE PAYMENT
   * ---------------------------------------------------------
   */

  const analyzePayment = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/v1/recover`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...payment,

            amount: Number(payment.amount),

            attempt_number: Number(
              payment.attempt_number
            ),

            previous_successes: Number(
              payment.previous_successes
            ),

            previous_failures: Number(
              payment.previous_failures
            ),

            customer_avg_amount: Number(
              payment.customer_avg_amount
            ),

            hour: Number(payment.hour),

            day_of_week: Number(
              payment.day_of_week
            ),
          }),
        }
      );

      if (!response.ok) {
        let message =
          "Recovery API request failed.";

        try {
          const errorData = await response.json();

          if (errorData.detail) {
            message =
              typeof errorData.detail === "string"
                ? errorData.detail
                : JSON.stringify(
                    errorData.detail
                  );
          }
        } catch {
          // Keep default message.
        }

        throw new Error(message);
      }

      const data = await response.json();

      setDecision(data);

      await loadAuditEvents();
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to RecoverAI."
      );
    } finally {
      setLoading(false);
    }
  };

  /*
   * ---------------------------------------------------------
   * LOAD AUDIT EVENTS
   * ---------------------------------------------------------
   */

  const loadAuditEvents = async () => {
    setAuditLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/audit`
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load audit events."
        );
      }

      const data = await response.json();

      setAuditEvents(data.events || []);
    } catch (err) {
      setError(
        err.message ||
          "Unable to load the audit trail."
      );
    } finally {
      setAuditLoading(false);
    }
  };

  /*
   * ---------------------------------------------------------
   * SELECT A REAL PAYMENT
   * ---------------------------------------------------------
   */

  const selectPayment = (transaction) => {
    const mappedPayment = {
      payment_id: String(
        transaction.payment_id || ""
      ),

      amount: Number(transaction.amount || 0),

      payment_method: String(
        transaction.payment_method || "upi"
      ),

      failure_reason: String(
        transaction.failure_reason ||
          "bank_timeout"
      ),

      attempt_number: Number(
        transaction.attempt_number || 1
      ),

      previous_successes: Number(
        transaction.previous_successes || 0
      ),

      previous_failures: Number(
        transaction.previous_failures || 0
      ),

      customer_avg_amount: Number(
        transaction.customer_avg_amount || 0
      ),

      hour: Number(transaction.hour || 0),

      day_of_week: Number(
        transaction.day_of_week || 0
      ),
    };

    setPayment(mappedPayment);
    setSelectedPayment(transaction);
    setDecision(null);
    setError("");
  };

  /*
   * ---------------------------------------------------------
   * NAVIGATION
   * ---------------------------------------------------------
   */

  const openOverview = () => {
    setActiveTab("overview");
  };

  const openPayments = async () => {
    setActiveTab("payments");

    if (payments.length === 0) {
      await loadPayments();
    }
  };

  const openDecisions = () => {
    setActiveTab("decisions");
  };

  const openAudit = async () => {
    setActiveTab("audit");

    await loadAuditEvents();
  };

  /*
   * ---------------------------------------------------------
   * FILTER PAYMENTS
   * ---------------------------------------------------------
   */

  const filteredPayments = payments.filter(
    (transaction) => {
      const paymentId = String(
        transaction.payment_id || ""
      ).toLowerCase();

      const customerId = String(
        transaction.customer_id || ""
      ).toLowerCase();

      const failureReason = String(
        transaction.failure_reason || ""
      ).toLowerCase();

      const query =
        searchTerm.toLowerCase().trim();

      const matchesSearch =
        !query ||
        paymentId.includes(query) ||
        customerId.includes(query) ||
        failureReason.includes(query);

      const matchesFailure =
        failureFilter === "all" ||
        failureReason === failureFilter;

      return (
        matchesSearch &&
        matchesFailure
      );
    }
  );

  const failureReasons = [
    ...new Set(
      payments
        .map((payment) =>
          String(
            payment.failure_reason || ""
          )
        )
        .filter(Boolean)
    ),
  ];

  return (
    <div className="app">
      {/* =====================================================
          SIDEBAR
          ===================================================== */}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">R</div>

          <div>
            <h1>RecoverAI</h1>
            <span>
              Recovery Intelligence
            </span>
          </div>
        </div>

        <nav>
          <button
            className={
              activeTab === "overview"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={openOverview}
          >
            <span>▦</span>
            Overview
          </button>

          <button
            className={
              activeTab === "payments"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={openPayments}
          >
            <span>↗</span>
            Payments
          </button>

          <button
            className={
              activeTab === "decisions"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={openDecisions}
          >
            <span>✦</span>
            AI Decisions
          </button>

          <button
            className={
              activeTab === "audit"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={openAudit}
          >
            <span>◷</span>
            Audit Trail
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot"></span>

            <div>
              <strong>
                System operational
              </strong>

              <small>
                All services healthy
              </small>
            </div>
          </div>

          <div className="version">
            RecoverAI v0.1.0
          </div>
        </div>
      </aside>

      {/* =====================================================
          MAIN
          ===================================================== */}

      <main className="main">
        {/* ===================================================
            TOP BAR
            =================================================== */}

        <header className="topbar">
          <div>
            <p className="eyebrow">
              PAYMENT RECOVERY CONTROL CENTER
            </p>

            <h2>
              {activeTab === "overview" &&
                "Recovery Overview"}

              {activeTab === "payments" &&
                "Failed Payments"}

              {activeTab === "decisions" &&
                "AI Decisions"}

              {activeTab === "audit" &&
                "Decision Audit Trail"}
            </h2>
          </div>

          <div className="topbar-right">
            <div className="live-indicator">
              <span></span>
              LIVE
            </div>

            <div className="avatar">
              TS
            </div>
          </div>
        </header>

        {/* ===================================================
            OVERVIEW
            =================================================== */}

        {activeTab === "overview" && (
          <>
            <section className="hero">
              <div>
                <div className="hero-label">
                  <span className="spark">
                    ✦
                  </span>

                  RECOVERAI OPPORTUNITY
                </div>

                <h3>
                  Turn failed payments
                  <br />
                  into recovered revenue.
                </h3>

                <p>
                  AI predicts recovery probability,
                  evaluates intervention economics,
                  and applies deterministic safety
                  policies before any action is taken.
                </p>
              </div>

              <div className="hero-value">
                <span>
                  SIMULATED NET IMPACT
                </span>

                <strong>
                  ₹64.45 L
                </strong>

                <small>
                  Incremental recovery vs baseline
                </small>
              </div>
            </section>

            <section className="metrics">
              {metrics.map((metric) => (
                <div
                  className="metric-card"
                  key={metric.label}
                >
                  <span>
                    {metric.label}
                  </span>

                  <strong>
                    {metric.value}
                  </strong>

                  <small>
                    {metric.change}
                  </small>
                </div>
              ))}
            </section>

            <section className="content-grid">
              <div className="panel transactions-panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      RECOVERY QUEUE
                    </span>

                    <h3>
                      Recent failed payments
                    </h3>
                  </div>

                  <button
                    className="text-button"
                    onClick={openPayments}
                  >
                    View all →
                  </button>
                </div>

                <div className="table">
                  <div className="table-head">
                    <span>Payment</span>
                    <span>Amount</span>
                    <span>Failure</span>
                    <span>AI Score</span>
                    <span>Action</span>
                    <span>Status</span>
                  </div>

                  {demoTransactions.map(
                    (transaction) => (
                      <div
                        className="table-row"
                        key={transaction.id}
                      >
                        <span className="payment-id">
                          {transaction.id}
                        </span>

                        <span>
                          {transaction.amount}
                        </span>

                        <span>
                          {transaction.reason}
                        </span>

                        <span className="score">
                          {
                            transaction.probability
                          }
                        </span>

                        <span>
                          <span
                            className={`action ${transaction.action.toLowerCase()}`}
                          >
                            {
                              transaction.action
                            }
                          </span>
                        </span>

                        <span>
                          <span
                            className={
                              transaction.status ===
                              "Approved"
                                ? "status approved"
                                : "status review"
                            }
                          >
                            {
                              transaction.status
                            }
                          </span>
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>

              <div className="panel decision-panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      DECISION ENGINE
                    </span>

                    <h3>
                      How RecoverAI works
                    </h3>
                  </div>
                </div>

                <div className="decision-flow">
                  <div className="flow-step">
                    <div className="flow-number">
                      01
                    </div>

                    <div>
                      <strong>
                        Predict
                      </strong>

                      <p>
                        XGBoost estimates recovery
                        probability.
                      </p>
                    </div>
                  </div>

                  <div className="flow-line"></div>

                  <div className="flow-step">
                    <div className="flow-number">
                      02
                    </div>

                    <div>
                      <strong>
                        Optimize
                      </strong>

                      <p>
                        Compare expected value across
                        interventions.
                      </p>
                    </div>
                  </div>

                  <div className="flow-line"></div>

                  <div className="flow-step">
                    <div className="flow-number">
                      03
                    </div>

                    <div>
                      <strong>
                        Control
                      </strong>

                      <p>
                        Policy engine validates the
                        action.
                      </p>
                    </div>
                  </div>

                  <div className="flow-line"></div>

                  <div className="flow-step">
                    <div className="flow-number">
                      04
                    </div>

                    <div>
                      <strong>
                        Audit
                      </strong>

                      <p>
                        Every decision is recorded and
                        traceable.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* LIVE DECISION ENGINE */}

            <section className="panel analyze-panel">
              <div className="panel-header">
                <div>
                  <span className="panel-kicker">
                    LIVE DECISION ENGINE
                  </span>

                  <h3>
                    Analyze a failed payment
                  </h3>
                </div>

                <span className="api-badge">
                  API CONNECTED
                </span>
              </div>

              <div className="analyze-content">
                <div className="form-grid">
                  <label>
                    Payment ID

                    <input
                      value={
                        payment.payment_id
                      }
                      onChange={(e) =>
                        updatePayment(
                          "payment_id",
                          e.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Amount

                    <input
                      type="number"
                      min="1"
                      value={
                        payment.amount
                      }
                      onChange={(e) =>
                        updatePayment(
                          "amount",
                          e.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Payment method

                    <select
                      value={
                        payment.payment_method
                      }
                      onChange={(e) =>
                        updatePayment(
                          "payment_method",
                          e.target.value
                        )
                      }
                    >
                      <option value="upi">
                        UPI
                      </option>

                      <option value="card">
                        Card
                      </option>

                      <option value="netbanking">
                        Net Banking
                      </option>
                    </select>
                  </label>

                  <label>
                    Failure reason

                    <select
                      value={
                        payment.failure_reason
                      }
                      onChange={(e) =>
                        updatePayment(
                          "failure_reason",
                          e.target.value
                        )
                      }
                    >
                      <option value="bank_timeout">
                        Bank timeout
                      </option>

                      <option value="network_error">
                        Network error
                      </option>

                      <option value="upi_failure">
                        UPI failure
                      </option>

                      <option value="insufficient_funds">
                        Insufficient funds
                      </option>

                      <option value="card_declined">
                        Card declined
                      </option>

                      <option value="authentication_failed">
                        Authentication failed
                      </option>
                    </select>
                  </label>

                  <label>
                    Attempt number

                    <input
                      type="number"
                      min="1"
                      value={
                        payment.attempt_number
                      }
                      onChange={(e) =>
                        updatePayment(
                          "attempt_number",
                          e.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Previous successes

                    <input
                      type="number"
                      min="0"
                      value={
                        payment.previous_successes
                      }
                      onChange={(e) =>
                        updatePayment(
                          "previous_successes",
                          e.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Previous failures

                    <input
                      type="number"
                      min="0"
                      value={
                        payment.previous_failures
                      }
                      onChange={(e) =>
                        updatePayment(
                          "previous_failures",
                          e.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Customer avg. amount

                    <input
                      type="number"
                      min="0"
                      value={
                        payment.customer_avg_amount
                      }
                      onChange={(e) =>
                        updatePayment(
                          "customer_avg_amount",
                          e.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Transaction hour

                    <input
                      type="number"
                      min="0"
                      max="23"
                      value={
                        payment.hour
                      }
                      onChange={(e) =>
                        updatePayment(
                          "hour",
                          e.target.value
                        )
                      }
                    />
                  </label>

                  <label>
                    Day of week

                    <input
                      type="number"
                      min="0"
                      max="6"
                      value={
                        payment.day_of_week
                      }
                      onChange={(e) =>
                        updatePayment(
                          "day_of_week",
                          e.target.value
                        )
                      }
                    />
                  </label>
                </div>

                <button
                  className="analyze-button"
                  onClick={analyzePayment}
                  disabled={loading}
                >
                  {loading
                    ? "Analyzing..."
                    : "Analyze Payment →"}
                </button>
              </div>

              {error && (
                <div className="error-message">
                  <strong>
                    API Error
                  </strong>

                  <span>
                    {error}
                  </span>
                </div>
              )}

              {decision && (
                <div className="decision-result">
                  <div className="result-heading">
                    <div>
                      <span className="panel-kicker">
                        RECOVERAI DECISION
                      </span>

                      <h3>
                        {decision.payment_id}
                      </h3>
                    </div>

                    <span
                      className={
                        decision.policy_decision ===
                        "approved"
                          ? "result-status approved"
                          : "result-status review"
                      }
                    >
                      {decision.policy_decision ===
                      "approved"
                        ? "APPROVED"
                        : "HUMAN REVIEW"}
                    </span>
                  </div>

                  <div className="result-grid">
                    <div className="result-card">
                      <span>
                        RECOVERY PROBABILITY
                      </span>

                      <strong>
                        {formatPercentage(
                          decision.recovery_probability
                        )}
                      </strong>
                    </div>

                    <div className="result-card">
                      <span>
                        RECOMMENDED ACTION
                      </span>

                      <strong className="result-action">
                        {formatAction(
                          decision.recommended_action
                        )}
                      </strong>
                    </div>

                    <div className="result-card">
                      <span>
                        EXPECTED RECOVERY
                      </span>

                      <strong>
                        {formatCurrency(
                          decision.expected_recovery
                        )}
                      </strong>
                    </div>

                    <div className="result-card">
                      <span>
                        NET EXPECTED VALUE
                      </span>

                      <strong>
                        {formatCurrency(
                          decision.net_expected_value
                        )}
                      </strong>
                    </div>
                  </div>

                  <div className="policy-reason">
                    <span>
                      POLICY DECISION
                    </span>

                    <strong>
                      {decision.policy_reason}
                    </strong>
                  </div>

                  {decision.action_estimates &&
                    decision.action_estimates
                      .length > 0 && (
                      <div className="action-comparison">
                        <div className="comparison-title">
                          Intervention economics
                        </div>

                        <div className="comparison-grid">
                          {decision.action_estimates.map(
                            (estimate) => (
                              <div
                                className={
                                  estimate.action ===
                                  decision.recommended_action
                                    ? "comparison-card selected"
                                    : "comparison-card"
                                }
                                key={
                                  estimate.action
                                }
                              >
                                <strong>
                                  {formatAction(
                                    estimate.action
                                  )}
                                </strong>

                                <span>
                                  Recovery{" "}
                                  {formatPercentage(
                                    estimate.probability
                                  )}
                                </span>

                                <span>
                                  Expected{" "}
                                  {formatCurrency(
                                    estimate.expected_recovery
                                  )}
                                </span>

                                <span>
                                  Cost{" "}
                                  {formatCurrency(
                                    estimate.cost
                                  )}
                                </span>

                                <b>
                                  Net{" "}
                                  {formatCurrency(
                                    estimate.expected_net_value
                                  )}
                                </b>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                </div>
              )}
            </section>
          </>
        )}

        {/* ===================================================
            REAL PAYMENTS PAGE
            =================================================== */}

        {activeTab === "payments" && (
          <section className="panel payments-page">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  PAYMENT OPERATIONS
                </span>

                <h3>
                  Failed payment recovery queue
                </h3>
              </div>

              <div className="payments-header-right">
                <span className="dataset-count">
                  {payments.length > 0
                    ? `${payments.length.toLocaleString(
                        "en-IN"
                      )} TRANSACTIONS`
                    : "LOADING"}
                </span>

                <button
                  className="text-button"
                  onClick={loadPayments}
                  disabled={
                    paymentsLoading
                  }
                >
                  {paymentsLoading
                    ? "Loading..."
                    : "Refresh →"}
                </button>
              </div>
            </div>

            <div className="payment-page-content">
              <div className="payments-toolbar">
                <input
                  className="payment-search"
                  placeholder="Search payment ID, customer ID, or failure..."
                  value={searchTerm}
                  onChange={(e) =>
                    setSearchTerm(
                      e.target.value
                    )
                  }
                />

                <select
                  className="failure-filter"
                  value={failureFilter}
                  onChange={(e) =>
                    setFailureFilter(
                      e.target.value
                    )
                  }
                >
                  <option value="all">
                    All failure reasons
                  </option>

                  {failureReasons.map(
                    (reason) => (
                      <option
                        value={reason}
                        key={reason}
                      >
                        {formatFailureReason(
                          reason
                        )}
                      </option>
                    )
                  )}
                </select>
              </div>

              {paymentsLoading ? (
                <div className="payments-loading">
                  <div className="loading-spinner"></div>

                  <strong>
                    Loading transactions...
                  </strong>

                  <p>
                    RecoverAI is loading the
                    transaction dataset.
                  </p>
                </div>
              ) : (
                <>
                  <div className="payments-summary">
                    <span>
                      Showing{" "}
                      <strong>
                        {filteredPayments.length.toLocaleString(
                          "en-IN"
                        )}
                      </strong>{" "}
                      of{" "}
                      <strong>
                        {payments.length.toLocaleString(
                          "en-IN"
                        )}
                      </strong>{" "}
                      transactions
                    </span>

                    <span>
                      Select a payment to analyze
                    </span>
                  </div>

                  <div className="real-payment-table">
                    <div className="real-payment-head">
                      <span>PAYMENT</span>
                      <span>AMOUNT</span>
                      <span>METHOD</span>
                      <span>FAILURE</span>
                      <span>ATTEMPT</span>
                      <span>RECOVERY</span>
                      <span>ACTION</span>
                    </div>

                    {filteredPayments
                      .slice(0, 100)
                      .map(
                        (
                          transaction,
                          index
                        ) => (
                          <div
                            className={
                              selectedPayment?.payment_id ===
                              transaction.payment_id
                                ? "real-payment-row selected"
                                : "real-payment-row"
                            }
                            key={
                              transaction.payment_id ||
                              index
                            }
                          >
                            <div>
                              <span className="payment-id">
                                {
                                  transaction.payment_id
                                }
                              </span>

                              <small>
                                {
                                  transaction.customer_id
                                }
                              </small>
                            </div>

                            <span className="amount-cell">
                              {formatCurrency(
                                transaction.amount
                              )}
                            </span>

                            <span className="method-cell">
                              {String(
                                transaction.payment_method ||
                                  "—"
                              ).toUpperCase()}
                            </span>

                            <span className="failure-cell">
                              {formatFailureReason(
                                transaction.failure_reason
                              )}
                            </span>

                            <span>
                              {
                                transaction.attempt_number ??
                                "—"
                              }
                            </span>

                            <span>
                              {transaction.recovered
                                ? "Recovered"
                                : "Failed"}
                            </span>

                            <button
                              className="analyze-row-button"
                              onClick={() => {
                                selectPayment(
                                  transaction
                                );
                                setActiveTab(
                                  "overview"
                                );
                              }}
                            >
                              Analyze
                            </button>
                          </div>
                        )
                      )}
                  </div>

                  {filteredPayments.length >
                    100 && (
                    <div className="table-limit">
                      Showing the first 100 matching
                      transactions. Use search or filters
                      to narrow the queue.
                    </div>
                  )}

                  {filteredPayments.length ===
                    0 && (
                    <div className="empty-payments">
                      <div className="placeholder-icon">
                        ↗
                      </div>

                      <strong>
                        No matching payments
                      </strong>

                      <p>
                        Try a different search term or
                        failure reason.
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          </section>
        )}

        {/* ===================================================
            AI DECISIONS
            =================================================== */}

        {activeTab === "decisions" && (
          <section className="panel decisions-page">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  AI DECISION EXPLORER
                </span>

                <h3>
                  Explainable recovery decisions
                </h3>
              </div>
            </div>

            <div className="decision-explorer">
              <div className="explorer-card">
                <span className="explorer-number">
                  01
                </span>

                <div>
                  <strong>
                    Recovery probability
                  </strong>

                  <p>
                    XGBoost evaluates transaction
                    characteristics and estimates
                    the probability of successful
                    recovery.
                  </p>
                </div>
              </div>

              <div className="explorer-card">
                <span className="explorer-number">
                  02
                </span>

                <div>
                  <strong>
                    Intervention optimization
                  </strong>

                  <p>
                    RecoverAI compares retry,
                    reminder, and escalation using
                    expected economic value.
                  </p>
                </div>
              </div>

              <div className="explorer-card">
                <span className="explorer-number">
                  03
                </span>

                <div>
                  <strong>
                    Deterministic policy control
                  </strong>

                  <p>
                    The policy engine can override an
                    AI recommendation when confidence,
                    transaction value, failure type, or
                    retry limits make automation unsafe.
                  </p>
                </div>
              </div>

              <div className="explorer-card">
                <span className="explorer-number">
                  04
                </span>

                <div>
                  <strong>
                    Auditable decision
                  </strong>

                  <p>
                    Every decision is written to the
                    audit store with its action, policy
                    outcome, expected recovery, and
                    reason.
                  </p>
                </div>
              </div>
            </div>

            <div className="decision-cta">
              <strong>
                Ready to analyze a transaction?
              </strong>

              <button
                className="analyze-button"
                onClick={openOverview}
              >
                Open Decision Engine →
              </button>
            </div>
          </section>
        )}

        {/* ===================================================
            AUDIT TRAIL
            =================================================== */}

        {activeTab === "audit" && (
          <section className="panel audit-panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  AUDIT TRAIL
                </span>

                <h3>
                  Recovery decision history
                </h3>
              </div>

              <button
                className="text-button"
                onClick={loadAuditEvents}
                disabled={auditLoading}
              >
                {auditLoading
                  ? "Refreshing..."
                  : "Refresh →"}
              </button>
            </div>

            {auditEvents.length === 0 ? (
              <div className="empty-audit">
                <div className="placeholder-icon">
                  ◷
                </div>

                <strong>
                  No decisions recorded yet
                </strong>

                <p>
                  Analyze a payment to create an
                  auditable recovery decision.
                </p>

                <button
                  className="analyze-button"
                  onClick={openOverview}
                >
                  Analyze Payment →
                </button>
              </div>
            ) : (
              <div className="audit-list">
                {auditEvents.map(
                  (event, index) => (
                    <div
                      className="audit-row"
                      key={
                        event.id ||
                        `${event.payment_id}-${index}`
                      }
                    >
                      <div className="audit-main">
                        <span className="audit-payment">
                          {event.payment_id ||
                            "Unknown payment"}
                        </span>

                        <span className="audit-time">
                          {event.created_at ||
                            event.timestamp ||
                            "Recorded event"}
                        </span>
                      </div>

                      <div className="audit-action">
                        <span
                          className={`action ${
                            event.action
                              ? String(
                                  event.action
                                ).toLowerCase()
                              : "escalate"
                          }`}
                        >
                          {event.action ||
                            "unknown"}
                        </span>
                      </div>

                      <div>
                        <span
                          className={
                            event.decision ===
                            "approved"
                              ? "status approved"
                              : "status review"
                          }
                        >
                          {event.decision ||
                            "unknown"}
                        </span>
                      </div>

                      <div className="audit-probability">
                        {event.recovery_probability !==
                        undefined
                          ? formatPercentage(
                              event.recovery_probability
                            )
                          : "—"}
                      </div>

                      <div className="audit-reason">
                        {event.reason ||
                          "No reason recorded"}
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;