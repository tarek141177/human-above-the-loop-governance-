"""
Human-Above-The-Loop: A Minimal Runtime Governance Engine for Autonomous AI Agents.
Authored by Tarek Mostafa (Principal Systems Architect)
Formalized in "The Unshakeable Series"

Humans define immutable policy. Deterministic software enforces it at runtime:
  1. PolicyEngine      -> Hard limits + rate limits + human escalation triggers
  2. Validator         -> Schema and state pre-condition checks
  3. CircuitBreaker    -> Statistical anomaly brake (Z-score & rejection rates)
  4. GovernedExecutor  -> Isolates agent intent from state mutation
"""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


# --------------------------------------------------------------------------
# 1. Data Models
# --------------------------------------------------------------------------

class Decision(Enum):
    ALLOW = "allow"
    REJECT = "reject"
    ESCALATE = "escalate"   # Requires human judgment
    HALT = "halt"           # Circuit breaker tripped


@dataclass(frozen=True)
class Action:
    """An action proposed by the autonomous AI agent."""
    type: str
    account_id: str
    amount: float


@dataclass(frozen=True)
class Policy:
    """Defined and owned by human leadership. Immutable at runtime."""
    allowed_actions: frozenset = frozenset({"transfer", "refund"})
    max_amount: float = 10_000.0          # Hard limit: Always rejected above this
    escalation_amount: float = 2_000.0    # Above this: Human judgment required
    max_actions_per_minute: int = 30      # Rate limit


@dataclass
class Result:
    decision: Decision
    reason: str


# --------------------------------------------------------------------------
# 2. Hard Limits & Policy Engine
# --------------------------------------------------------------------------

class PolicyEngine:
    def __init__(self, policy: Policy):
        self.policy = policy
        self._timestamps: deque[float] = deque()

    def evaluate(self, action: Action) -> Result:
        p = self.policy

        if action.type not in p.allowed_actions:
            return Result(Decision.REJECT, f"Action '{action.type}' is forbidden by policy")

        if action.amount > p.max_amount:
            return Result(Decision.REJECT, f"Amount {action.amount:,.2f} exceeds hard cap of {p.max_amount:,.2f}")

        if not self._within_rate_limit():
            return Result(Decision.REJECT, "Rate limit exceeded (too many actions per minute)")

        if action.amount > p.escalation_amount:
            return Result(Decision.ESCALATE, f"Amount {action.amount:,.2f} requires human sign-off")

        return Result(Decision.ALLOW, "Action complies with policy")

    def _within_rate_limit(self) -> bool:
        now = time.monotonic()
        while self._timestamps and now - self._timestamps[0] > 60:
            self._timestamps.popleft()
        if len(self._timestamps) >= self.policy.max_actions_per_minute:
            return False
        self._timestamps.append(now)
        return True


# --------------------------------------------------------------------------
# 3. Pre-execution State Validation
# --------------------------------------------------------------------------

class Validator:
    """Validates schema integrity and system state invariants BEFORE mutation."""

    def __init__(self, balances: dict[str, float]):
        self.balances = balances

    def validate(self, action: Action) -> Result:
        # Schema constraints
        if not isinstance(action.amount, (int, float)) or action.amount <= 0:
            return Result(Decision.REJECT, "Schema error: Amount must be a positive number")
        if not action.account_id:
            return Result(Decision.REJECT, "Schema error: Missing account_id")

        # State pre-conditions
        if action.account_id not in self.balances:
            return Result(Decision.REJECT, f"Target account '{action.account_id}' does not exist")
        if action.type == "transfer" and self.balances[action.account_id] < action.amount:
            return Result(Decision.REJECT, "Insufficient funds for transfer")

        return Result(Decision.ALLOW, "System state invariants satisfied")


# --------------------------------------------------------------------------
# 4. Statistical Circuit Breaker
# --------------------------------------------------------------------------

class CircuitBreaker:
    """
    Automated emergency brake.
    Trips instantly when agent runtime behavior deviates from normal distribution:
      - Statistical Z-score outlier on transaction amounts, or
      - High failure/rejection rate within a sliding window.
    Once tripped, all execution halts until human reset.
    """

    def __init__(self, window: int = 20, max_reject_rate: float = 0.5, z_threshold: float = 4.0):
        self.window = window
        self.max_reject_rate = max_reject_rate
        self.z_threshold = z_threshold
        self.recent_outcomes: deque[bool] = deque(maxlen=window)
        self.recent_amounts: deque[float] = deque(maxlen=window)
        self.is_open = False
        self.trip_reason = ""

    def check_anomaly(self, action: Action) -> bool:
        """Returns True and trips if the proposed action is a statistical outlier."""
        if len(self.recent_amounts) >= 10:
            mean = statistics.mean(self.recent_amounts)
            stdev = statistics.pstdev(self.recent_amounts) or 1.0
            z = abs(action.amount - mean) / stdev
            if z > self.z_threshold:
                self._trip(f"Statistical outlier detected (Z-score: {z:.1f})")
                return True
        return False

    def record(self, action: Action, decision: Decision) -> None:
        self.recent_outcomes.append(decision == Decision.REJECT)
        if decision == Decision.ALLOW:
            self.recent_amounts.append(action.amount)

        if len(self.recent_outcomes) == self.window:
            rate = sum(self.recent_outcomes) / self.window
            if rate > self.max_reject_rate:
                self._trip(f"High rejection rate ({rate:.0%}) detected over last {self.window} actions")

    def reset(self) -> None:
        """Explicit human reset required to resume operations."""
        self.is_open = False
        self.trip_reason = ""
        self.recent_outcomes.clear()

    def _trip(self, reason: str) -> None:
        self.is_open = True
        self.trip_reason = reason


# --------------------------------------------------------------------------
# 5. The Governed Executor
# --------------------------------------------------------------------------

@dataclass
class GovernedExecutor:
    policy: Policy
    balances: dict[str, float]
    audit_log: list = field(default_factory=list)

    def __post_init__(self):
        self.engine = PolicyEngine(self.policy)
        self.validator = Validator(self.balances)
        self.breaker = CircuitBreaker()

    def submit(self, action: Action) -> Result:
        # Step 1: Emergency Brake & Anomaly Check
        if self.breaker.is_open:
            return self._finish(action, Result(Decision.HALT, f"Circuit Breaker Open: {self.breaker.trip_reason}"))

        if self.breaker.check_anomaly(action):
            return self._finish(action, Result(Decision.HALT, f"Circuit Breaker Tripped: {self.breaker.trip_reason}"))

        # Step 2: Policy Evaluation (Hard limits, rate caps, escalation)
        result = self.engine.evaluate(action)
        
        # Step 3: State Validation (Pre-conditions)
        if result.decision == Decision.ALLOW:
            result = self.validator.validate(action)

        # Step 4: Atomic Execution (Only if all deterministic gates pass)
        if result.decision == Decision.ALLOW:
            self._execute(action)

        self.breaker.record(action, result.decision)
        return self._finish(action, result)

    def _execute(self, action: Action) -> None:
        if action.type == "transfer":
            self.balances[action.account_id] -= action.amount
        elif action.type == "refund":
            self.balances[action.account_id] += action.amount

    def _finish(self, action: Action, result: Result) -> Result:
        self.audit_log.append((action, result))
        return result


# --------------------------------------------------------------------------
# Execution Scenarios
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Human-Above-The-Loop (HATL) Governance Engine Demo")
    print("=" * 70)

    system = GovernedExecutor(Policy(), balances={"acc_enterprise": 50_000.0})

    test_actions = [
        Action("transfer", "acc_enterprise", 150),         # Routine -> ALLOW
        Action("transfer", "acc_enterprise", 25_000),      # Hard cap breach -> REJECT
        Action("delete_db", "acc_enterprise", 1),          # Forbidden action -> REJECT
        Action("transfer", "acc_enterprise", 5_000),       # High value -> ESCALATE (Human sign-off)
        Action("transfer", "invalid_acc", 100),            # Pre-condition fails -> REJECT
    ]

    for a in test_actions:
        res = system.submit(a)
        print(f"Action: {a.type:<12} | Amount: ${a.amount:>9,.2f} -> [{res.decision.value.upper():<8}] {res.reason}")

    print("\n--- Simulating Normal Traffic Baseline (12 requests of $100) ---")
    for _ in range(12):
        system.submit(Action("transfer", "acc_enterprise", 100))

    print("\n--- Injecting Statistical Outlier ($1,900) ---")
    outlier = system.submit(Action("transfer", "acc_enterprise", 1_900))
    print(f"Outlier Action -> [{outlier.decision.value.upper()}] {outlier.reason}")

    print("\n--- Subsequent Action Attempt While Breaker is Tripped ---")
    subsequent = system.submit(Action("transfer", "acc_enterprise", 100))
    print(f"Subsequent Action -> [{subsequent.decision.value.upper()}] {subsequent.reason}")
    print("=" * 70)
