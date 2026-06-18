from __future__ import annotations

from dataclasses import dataclass

PROHIBITED_VERBS = {"transfer", "send", "withdraw", "trade", "buy", "sell", "approve", "execute", "wire", "pay"}
HIGH_RISK_VERBS = {"rebalance", "invest", "reallocate", "move"}


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    manual_approval_required: bool
    reason: str
    blocked_terms: list[str]


def _tokens(text: str) -> set[str]:
    normalized = text.lower().replace("-", " ").replace("_", " ")
    return {token.strip(".,:;!?()[]{}\"'`") for token in normalized.split() if token}


def is_prohibited_action(text: str) -> bool:
    tokens = _tokens(text)
    return any(verb in tokens for verb in PROHIBITED_VERBS)


def evaluate_action(text: str) -> PolicyDecision:
    tokens = _tokens(text)
    blocked = sorted(verb for verb in PROHIBITED_VERBS if verb in tokens)
    if blocked:
        return PolicyDecision(False, True, "Prohibited financial action detected", blocked)
    if any(verb in tokens for verb in HIGH_RISK_VERBS):
        return PolicyDecision(True, True, "High-risk advisory action; manual approval required", [])
    return PolicyDecision(True, False, "Read-only advisory request", [])
