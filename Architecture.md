                         ┌──────────────────────────────┐
                         │        RECOVERAI UI          │
                         │      React + Vite            │
                         │                              │
                         │  • Overview                  │
                         │  • Payments                  │
                         │  • AI Decisions              │
                         │  • Audit Trail               │
                         └──────────────┬───────────────┘
                                        │
                              HTTP / REST API
                                        │
                                        ▼
                    ┌───────────────────────────────────┐
                    │          FASTAPI BACKEND          │
                    │                                   │
                    │  /api/v1/payments                 │
                    │  /api/v1/recover                  │
                    │  /api/v1/audit                    │
                    │  /health                           │
                    └───────────────┬───────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────┐
                    │       RECOVERY SERVICE             │
                    │                                   │
                    │  Coordinates the decision pipeline│
                    └───────────────┬───────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────────┐
              │          XGBOOST ML MODEL                   │
              │                                             │
              │  Transaction Features                       │
              │        ↓                                    │
              │  Recovery Probability                       │
              └────────────────────┬────────────────────────┘
                                   │
                                   ▼
              ┌─────────────────────────────────────────────┐
              │       INTERVENTION OPTIMIZATION             │
              │                                             │
              │   ┌────────┐  ┌──────────┐  ┌───────────┐  │
              │   │ RETRY  │  │ REMINDER │  │ ESCALATE  │  │
              │   └────────┘  └──────────┘  └───────────┘  │
              │                                             │
              │   Expected Recovery - Intervention Cost    │
              └────────────────────┬────────────────────────┘
                                   │
                                   ▼
              ┌─────────────────────────────────────────────┐
              │       DETERMINISTIC POLICY ENGINE          │
              │                                             │
              │  • Confidence threshold                     │
              │  • Transaction amount limit                 │
              │  • Retry attempt limit                      │
              │  • Retryable failure validation             │
              │  • Human-review protection                  │
              └────────────────────┬────────────────────────┘
                                   │
                       ┌───────────┴───────────┐
                       ▼                       ▼
              ┌────────────────┐      ┌────────────────────┐
              │    APPROVED    │      │    HUMAN REVIEW    │
              │                │      │                    │
              │ Automated      │      │ Escalation         │
              │ recovery       │      │ required           │
              └───────┬────────┘      └─────────┬──────────┘
                      │                         │
                      └────────────┬────────────┘
                                   ▼
                    ┌───────────────────────────────────┐
                    │          AUDIT DATABASE            │
                    │              SQLite                │
                    │                                   │
                    │  • Payment ID                     │
                    │  • Action                          │
                    │  • Decision                        │
                    │  • Recovery probability            │
                    │  • Expected recovery               │
                    │  • Policy reason                   │
                    │  • Timestamp                       │
                    └───────────────────────────────────┘


       ┌─────────────────────────────┐
       │       DATA / ML LAYER       │
       │                             │
       │  transactions.csv           │
       │        ↓                    │
       │  Data generation            │
       │        ↓                    │
       │  Model training             │
       │        ↓                    │
       │  recovery_model.joblib     │
       └─────────────────────────────┘
