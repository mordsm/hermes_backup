from task_reminder.app.financial_agent.policy import evaluate_action, is_prohibited_action


def test_prohibited_action_is_blocked():
    decision = evaluate_action("transfer money to savings")
    assert decision.allowed is False
    assert decision.manual_approval_required is True
    assert "transfer" in decision.blocked_terms
    assert is_prohibited_action("send bank instructions") is True


def test_high_risk_action_requires_manual_approval():
    decision = evaluate_action("rebalance portfolio")
    assert decision.allowed is True
    assert decision.manual_approval_required is True
