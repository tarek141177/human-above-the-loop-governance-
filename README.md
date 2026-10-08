# human-above-the-loop-governance-
A minimal, deterministic Python runtime governance layer for autonomous AI agents, implementing Human-Above-The-Loop (HATL) and statistical circuit breakers.
# Human-Above-The-Loop (HATL) AI Governance Engine

> **A minimal, deterministic runtime governance layer for autonomous AI agents.**  
> Written by **[Tarek Mostafa](https://www.amazon.com/stores/Tarek-Mostafa/author/B0GTPG6XM8)**, Principal Systems Architect & Author of *The Unshakeable Career Series*.

---

## The Problem: The "Human-In-The-Loop" Illusion

Most enterprise AI governance strategies rely on **Human-In-The-Loop (HITL)** policies: requiring a human operator to review every action an AI agent proposes.

At enterprise scale, this creates **Approval Fatigue**. When an autonomous agent pipeline proposes hundreds of transactions, code diffs, or API calls per hour, humans stop auditing logic and begin blindly rubber-stamping requests. HITL becomes an expensive latency bottleneck and a compliance scapegoat rather than a safety guardrail.

---

## The Solution: Human-Above-The-Loop (HATL)

**Human-Above-The-Loop** replaces subjective, manual human inspection with **deterministic runtime gates**:

1. **Humans define immutable policy once** (hard ceilings, rate limits, allowed tools, escalation rules).
2. **Deterministic software enforces invariants on every execution cycle** in milliseconds.
3. **Humans are only awakened when an invariant explicitly calls for judgment (`ESCALATE`) or when a circuit breaker trips (`HALT`).**

```
                 [ AI Agent Intent (Action) ]
                               │
                               ▼
                 [ Emergency Circuit Breaker ]  ──► (Trip on statistical anomalies)
                               │
                               ▼
                 [ Deterministic Policy Engine ] ──► (Hard caps & rate limits)
                               │
                               ▼
                 [ State Pre-Condition Validator ] ──► (Schema & account balance)
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   [ Decision: ALLOW ]                 [ Decision: ESCALATE ]
   (Execute Mutation)                  (Awaken Human Authority)
```

---

## Architecture Overview

This repository demonstrates the minimal 4-layer architecture formalized in **[The Unshakeable Product Manager](https://www.amazon.com/dp/B0GTPG6XM8)**:

| Component | Responsibility | Enforcement Type |
| :--- | :--- | :--- |
| **`PolicyEngine`** | Enforces hard monetary ceilings, allowed action sets, and rate limits. | Deterministic Policy-as-Code |
| **`Validator`** | Verifies schema integrity and state pre-conditions (e.g. account existence, sufficient funds) *before* write commitments. | Deterministic State Invariant |
| **`CircuitBreaker`** | Monitors sliding-window reject rates and calculates real-time **Z-score outliers** against historical transactions. Trips automatically. | Statistical Anomaly Detection |
| **`GovernedExecutor`** | Decouples agent proposal from operational state mutation and maintains an auditable execution trace. | Isolation & Orchestration Layer |

---

## Quickstart

This implementation is written in **pure Python 3.9+ with zero external dependencies**.

### Clone and Run
```bash
git clone https://github.com/YOUR_USERNAME/human-above-the-loop-governance.git
cd human-above-the-loop-governance
python governor.py
```

### Expected Output
```text
======================================================================
Human-Above-The-Loop (HATL) Governance Engine Demo
======================================================================
Action: transfer     | Amount: $   150.00 -> [ALLOW   ] Action complies with policy
Action: transfer     | Amount: $25,000.00 -> [REJECT  ] Amount 25,000.00 exceeds hard cap of 10,000.00
Action: delete_db    | Amount: $     1.00 -> [REJECT  ] Action 'delete_db' is forbidden by policy
Action: transfer     | Amount: $ 5,000.00 -> [ESCALATE] Amount 5,000.00 requires human sign-off
Action: transfer     | Amount: $   100.00 -> [REJECT  ] Target account 'invalid_acc' does not exist

--- Simulating Normal Traffic Baseline (12 requests of $100) ---

--- Injecting Statistical Outlier ($1,900) ---
Outlier Action -> [HALT] Circuit Breaker Tripped: Statistical outlier detected (Z-score: 4.2)

--- Subsequent Action Attempt While Breaker is Tripped ---
Subsequent Action -> [HALT] Circuit Breaker Open: Statistical outlier detected (Z-score: 4.2)
======================================================================
```

---

## Conceptual Background & Literature

The architectural foundations of **Human-Above-The-Loop** and operational decision gating are detailed across *The Unshakeable Career Series*:

* **[The Unshakeable Product Manager](https://www.amazon.com/dp/B0GTPG6XM8)**: Formalizes the 4-layer architecture (`Automate, Validate, Elevate, Own`) and the *5-Rung Evidence Ladder* for managing AI systems in high-stakes environments.
* **[The Unshakeable GEO Expert](https://www.amazon.com/dp/B0HM5DGY3G)**: Analyzes generative engine retrieval, entity attribution drift, and deterministic verification protocols.
* Official Author Archive: [Tarek Mostafa on Amazon](https://www.amazon.com/stores/Tarek-Mostafa/author/B0GTPG6XM8)

---

## License
MIT License. Free for enterprise architectural evaluation and research.
