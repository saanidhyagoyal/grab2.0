"""
Autonomous Financial Action Agent
====================================
Monitors the user's financial profile and autonomously executes or schedules
financial actions without manual intervention.

Actions triggered:
  • Low savings rate    → schedule weekly auto-savings transfer
  • Excess idle balance → recommend / schedule FD transfer
  • High EMI ratio      → raise debt alert + suggest pre-payment
  • Income below floor  → apply spending-limit guardrails
  • Savings milestone   → acknowledge + compute cashback bonus
  • Healthy balance     → schedule EMI pre-payment to reduce interest

This agent operates in rule-based mode (no LLM required).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

# ── Action status constants ─────────────────────────────────────────────────

EXECUTED     = "executed"
SCHEDULED    = "scheduled"
RECOMMENDED  = "recommended"
ALERT        = "alert_raised"


def run_auto_executor(profile: dict, db: Session = None) -> dict:
    """
    Analyse financial profile and produce a list of autonomous actions.
    Each action has: id, title, description, amount, status, priority, icon.
    """
    actions: list[dict] = []

    income      = profile["income_30d"]
    expense     = profile["expense_30d"]
    savings_30d = profile["savings_30d"]
    savings_pct = profile["savings_rate_pct"]
    balance     = profile["total_balance"]
    emi         = profile["total_monthly_emi"]
    emi_ratio   = profile["emi_to_income_pct"]
    outstanding = profile.get("total_outstanding_debt", 0)

    # ── Rule 1: Low savings rate → auto-savings ──────────────────────────────
    if income > 0 and savings_pct < 15:
        weekly_save = round(income * 0.05)
        actions.append({
            "id": "AUTO_SAVINGS",
            "action": "auto_savings_transfer_scheduled",
            "title": "Auto-Savings Transfer Scheduled",
            "description": (
                f"Savings rate {savings_pct:.1f}% is below 15% target. "
                f"Scheduling weekly auto-transfer of S${weekly_save:,} to savings wallet."
            ),
            "amount": weekly_save,
            "status": SCHEDULED,
            "priority": "HIGH",
            "icon": "💰",
        })

    # ── Rule 2: Idle balance → FD recommendation ─────────────────────────────
    buffer_target = expense * 3
    if balance > buffer_target * 1.5:
        move_amt = round((balance - buffer_target) * 0.6)
        if move_amt > 500:
            actions.append({
                "id": "AUTO_FD",
                "action": "idle_funds_to_fd",
                "title": "Idle Funds → Fixed Deposit",
                "description": (
                    f"Balance S${balance:,.0f} exceeds 3-month emergency buffer. "
                    f"Moving S${move_amt:,} to Fixed Deposit (6.5% p.a.) for better returns."
                ),
                "amount": move_amt,
                "status": RECOMMENDED,
                "priority": "MEDIUM",
                "icon": "🏦",
            })

    # ── Rule 3: High EMI ratio → debt alert ──────────────────────────────────
    if emi_ratio > 40:
        prepay_suggest = round(income * 0.05)
        actions.append({
            "id": "DEBT_ALERT",
            "action": "high_emi_ratio_alert",
            "title": "High Debt-to-Income Alert",
            "description": (
                f"EMI/income ratio {emi_ratio:.1f}% exceeds safe 40% threshold. "
                f"Current monthly EMI: S${emi:,.0f}. "
                f"Suggested micro pre-payment: S${prepay_suggest:,}/month."
            ),
            "amount": prepay_suggest,
            "status": ALERT,
            "priority": "HIGH",
            "icon": "⚠️",
        })

    # ── Rule 4: Income below floor → spending limits ──────────────────────────
    INCOME_FLOOR = 20_000  # expected monthly baseline for gig workers
    if 0 < income < INCOME_FLOOR * 0.7:
        ent_limit  = round(income * 0.04)
        shop_limit = round(income * 0.05)
        actions.append({
            "id": "SPENDING_LIMIT",
            "action": "spending_limits_adjusted",
            "title": "Spending Limits Auto-Adjusted",
            "description": (
                f"Income S${income:,.0f} is 30% below baseline. "
                f"Entertainment cap → S${ent_limit:,}, Shopping cap → S${shop_limit:,}."
            ),
            "amount": ent_limit + shop_limit,
            "status": EXECUTED,
            "priority": "MEDIUM",
            "icon": "🎯",
        })

    # ── Rule 5: Savings milestone reward ────────────────────────────────────
    if savings_pct >= 25:
        bonus = round(savings_30d * 0.01)
        actions.append({
            "id": "SAVINGS_REWARD",
            "action": "savings_milestone_reward",
            "title": "Savings Milestone — Reward Unlocked!",
            "description": (
                f"Excellent! {savings_pct:.1f}% savings rate (S${savings_30d:,.0f} saved). "
                f"GXS Cashback Bonus of S${bonus:,} will be credited to your account."
            ),
            "amount": bonus,
            "status": EXECUTED,
            "priority": "LOW",
            "icon": "🏆",
        })

    # ── Rule 6: Healthy balance → EMI pre-payment ────────────────────────────
    if outstanding > 0 and savings_pct > 20 and balance > expense * 2:
        prepay = round(min(balance * 0.08, outstanding * 0.05))
        if prepay > 500:
            actions.append({
                "id": "EMI_PREPAY",
                "action": "emi_prepayment_scheduled",
                "title": "Smart EMI Pre-payment Scheduled",
                "description": (
                    f"Healthy cash position detected. Scheduling S${prepay:,} principal pre-payment "
                    f"to reduce outstanding debt (saves interest over loan tenure)."
                ),
                "amount": prepay,
                "status": SCHEDULED,
                "priority": "LOW",
                "icon": "📉",
            })

    # ── Summary ──────────────────────────────────────────────────────────────
    counts = {
        "executed":    sum(1 for a in actions if a["status"] == EXECUTED),
        "scheduled":   sum(1 for a in actions if a["status"] == SCHEDULED),
        "recommended": sum(1 for a in actions if a["status"] == RECOMMENDED),
        "alerts":      sum(1 for a in actions if a["status"] == ALERT),
    }

    return {
        "actions": actions,
        "summary": {"total_actions": len(actions), **counts},
        "financial_snapshot": {
            "income_30d":      income,
            "expense_30d":     expense,
            "savings_rate_pct": savings_pct,
            "balance":         balance,
            "emi_ratio_pct":   emi_ratio,
        },
        "agent_mode": "autonomous_rule_engine",
    }
