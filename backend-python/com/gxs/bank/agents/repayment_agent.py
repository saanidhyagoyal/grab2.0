"""
Repayment Intelligence Agent
==============================
Calculates a dynamic micro-repayment deduction percentage for every
Grab delivery payout based on three layers:

  1. Base Rate (3–5%)   — determined by GigScore (creditworthiness)
  2. Risk Modifier (8–12%) — triggered by Fraud Agent risk level
  3. Subsistence Floor (0%) — pauses deduction if daily earnings < threshold

The agent only activates when the user has at least one active loan.
If there are no outstanding loans, the full payout goes to the wallet.
"""
from __future__ import annotations

from datetime import datetime, timedelta

# ── Constants ─────────────────────────────────────────────────────────────────
FLOOR_THRESHOLD_SGD = 50.0       # Daily minimum before deductions kick in
MAX_DEDUCTION_PCT   = 15.0       # Hard cap — never deduct more than 15%


def calculate_deduction(
    profile: dict,
    payout_amount: float,
    fraud_result: dict | None = None,
) -> dict:
    """
    Calculate the dynamic micro-repayment deduction for a single payout.

    Args:
        profile:        Full financial profile from data_fetcher
        payout_amount:  The incoming Grab delivery payout (S$)
        fraud_result:   Optional fraud analysis result (risk_score, risk_level)

    Returns:
        {
            "should_deduct":    bool,
            "deduction_pct":    float,  # 0–15
            "deduction_amount": float,  # actual S$ to deduct
            "net_deposit":      float,  # amount credited to wallet
            "band":             str,    # BASE | RISK_PREMIUM | FLOOR_PAUSED | NO_LOAN
            "reason":           str,    # human-readable explanation
            "gig_score":        int,
            "risk_level":       str,
            "risk_score":       int,
            "today_earnings":   float,
            "floor_threshold":  float,
            "loan_id":          str | None,
            "loan_outstanding": float,
            "routing_chain":    list[str],
        }
    """
    routing_chain = []

    # ── Step 1: Check for active loans ────────────────────────────────────────
    loans = profile.get("loans", [])
    active_loans = [l for l in loans if l.get("outstanding", 0) > 0]
    routing_chain.append("Step 1: Checked active loans")

    if not active_loans:
        routing_chain.append("→ No active loans found — full payout to wallet")
        return _result(
            payout_amount, 0.0, 0.0, "NO_LOAN",
            "No active loans — full payout credited to your wallet.",
            0, "N/A", 0, 0.0, None, 0.0, routing_chain,
        )

    # Pick the loan with the highest outstanding (primary loan for repayment)
    primary_loan = max(active_loans, key=lambda l: l.get("outstanding", 0))
    loan_outstanding = primary_loan.get("outstanding", 0)
    routing_chain.append(f"→ Primary loan: {primary_loan.get('type', 'PERSONAL')} — outstanding S${loan_outstanding:,.2f}")

    # ── Step 2: Get GigScore ──────────────────────────────────────────────────
    gig_score = profile.get("gig_score", 0)
    if gig_score == 0:
        # Compute on-the-fly if not pre-injected
        from com.gxs.bank.agents.credit_agent import run_credit_scoring
        credit_res = run_credit_scoring(profile)
        gig_score = credit_res.get("credit_score", {}).get("gig_score", 500)
    routing_chain.append(f"Step 2: GigScore = {gig_score}")

    # ── Step 3: Get Fraud Risk ────────────────────────────────────────────────
    risk_level = "LOW"
    risk_score = 0
    if fraud_result:
        risk_level = fraud_result.get("risk_assessment", {}).get("risk_level", "LOW")
        risk_score = fraud_result.get("risk_assessment", {}).get("risk_score", 0)
    routing_chain.append(f"Step 3: Fraud Risk = {risk_level} ({risk_score}/100)")

    # ── Step 4: Calculate today's total earnings ──────────────────────────────
    today_key = datetime.utcnow().strftime("%Y-%m-%d")
    daily_income = profile.get("daily_income", {})
    today_earnings = daily_income.get(today_key, 0.0)
    routing_chain.append(f"Step 4: Today's earnings so far = S${today_earnings:,.2f}")

    # ── Step 5: Subsistence Floor Check ───────────────────────────────────────
    if (today_earnings + payout_amount) < FLOOR_THRESHOLD_SGD:
        routing_chain.append(
            f"Step 5: ⛔ FLOOR — S${today_earnings + payout_amount:,.2f} < "
            f"S${FLOOR_THRESHOLD_SGD:,.2f} threshold → Deduction PAUSED"
        )
        return _result(
            payout_amount, 0.0, 0.0, "FLOOR_PAUSED",
            f"Daily earnings S${today_earnings + payout_amount:,.2f} below "
            f"S${FLOOR_THRESHOLD_SGD:,.2f} subsistence floor — deduction paused to protect your cash flow.",
            gig_score, risk_level, risk_score, today_earnings, None, loan_outstanding, routing_chain,
        )
    routing_chain.append(f"Step 5: Floor check passed — S${today_earnings + payout_amount:,.2f} ≥ S${FLOOR_THRESHOLD_SGD:,.2f}")

    # ── Step 6: Calculate Dynamic Rate ────────────────────────────────────────
    deduction_pct = 5.0  # default
    band = "BASE"
    reason = ""

    # Risk Modifier (overrides base rate)
    if risk_level in ("HIGH", "CRITICAL") or risk_score > 60:
        deduction_pct = 8.0 + (risk_score / 100.0 * 4.0)  # 8–12%
        band = "RISK_PREMIUM"
        reason = f"Risk modifier active — fraud level {risk_level} (score {risk_score}/100) → {deduction_pct:.1f}%"
        routing_chain.append(f"Step 6: 🔴 RISK_PREMIUM — {deduction_pct:.1f}% (fraud: {risk_level})")

    elif gig_score < 500:
        deduction_pct = 8.0
        band = "RISK_PREMIUM"
        reason = f"GigScore {gig_score} below 500 — elevated rate {deduction_pct:.1f}%"
        routing_chain.append(f"Step 6: 🔴 RISK_PREMIUM — {deduction_pct:.1f}% (GigScore {gig_score} < 500)")

    else:
        # Base Rate (good standing)
        if gig_score >= 750:
            deduction_pct = 3.0
            reason = f"Excellent GigScore {gig_score} — lowest base rate 3%"
        elif gig_score >= 650:
            deduction_pct = 4.0
            reason = f"Good GigScore {gig_score} — base rate 4%"
        else:
            deduction_pct = 5.0
            reason = f"Fair GigScore {gig_score} — standard base rate 5%"
        band = "BASE"
        routing_chain.append(f"Step 6: 🟢 BASE — {deduction_pct:.1f}% (GigScore {gig_score})")

    # ── Step 7: Hard cap ──────────────────────────────────────────────────────
    deduction_pct = min(deduction_pct, MAX_DEDUCTION_PCT)

    # ── Step 8: Compute actual deduction ──────────────────────────────────────
    deduction_amount = round(payout_amount * deduction_pct / 100.0, 2)

    # Never deduct more than the loan outstanding
    if deduction_amount > loan_outstanding:
        deduction_amount = round(loan_outstanding, 2)
        deduction_pct = round(deduction_amount / payout_amount * 100, 2) if payout_amount > 0 else 0
        routing_chain.append(f"Step 7: Capped to remaining outstanding S${loan_outstanding:,.2f}")

    net_deposit = round(payout_amount - deduction_amount, 2)
    routing_chain.append(
        f"Step 8: Deduction S${deduction_amount:,.2f} ({deduction_pct:.1f}% of S${payout_amount:,.2f}) → "
        f"Net deposit S${net_deposit:,.2f}"
    )

    return _result(
        payout_amount, deduction_pct, deduction_amount, band, reason,
        gig_score, risk_level, risk_score, today_earnings,
        None, loan_outstanding, routing_chain,
    )


def get_repayment_config(profile: dict) -> dict:
    """
    Returns the current micro-repayment configuration for display on the
    AI Insights dashboard — without actually processing a payout.
    """
    loans = profile.get("loans", [])
    active_loans = [l for l in loans if l.get("outstanding", 0) > 0]

    if not active_loans:
        return {
            "enabled": False,
            "reason": "No active loans — micro-repayment is inactive.",
            "current_rate_pct": 0,
            "band": "NO_LOAN",
        }

    primary_loan = max(active_loans, key=lambda l: l.get("outstanding", 0))

    gig_score = profile.get("gig_score", 0)
    if gig_score == 0:
        from com.gxs.bank.agents.credit_agent import run_credit_scoring
        credit_res = run_credit_scoring(profile)
        gig_score = credit_res.get("credit_score", {}).get("gig_score", 500)

    # Determine base rate
    if gig_score >= 750:
        rate, band = 3.0, "BASE"
    elif gig_score >= 650:
        rate, band = 4.0, "BASE"
    elif gig_score >= 500:
        rate, band = 5.0, "BASE"
    else:
        rate, band = 8.0, "RISK_PREMIUM"

    today_key = datetime.utcnow().strftime("%Y-%m-%d")
    daily_income = profile.get("daily_income", {})
    today_earnings = daily_income.get(today_key, 0.0)

    # Calculate last 7 days deduction summary from daily_income
    last_7d_total = 0.0
    for i in range(7):
        day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        last_7d_total += daily_income.get(day, 0.0)
    estimated_7d_deduction = round(last_7d_total * rate / 100, 2)

    return {
        "enabled": True,
        "current_rate_pct": rate,
        "band": band,
        "gig_score": gig_score,
        "floor_threshold_sgd": FLOOR_THRESHOLD_SGD,
        "active_loan": {
            "type": primary_loan.get("type", "PERSONAL"),
            "outstanding": primary_loan.get("outstanding", 0),
            "monthly_emi": primary_loan.get("monthly_emi", 0),
            "interest_rate": primary_loan.get("interest_rate", 0),
        },
        "today_summary": {
            "total_earnings": today_earnings,
            "floor_triggered": today_earnings < FLOOR_THRESHOLD_SGD,
        },
        "last_7_days": {
            "total_payouts": round(last_7d_total, 2),
            "estimated_deductions": estimated_7d_deduction,
            "effective_rate_pct": rate,
        },
    }


# ── Helper ────────────────────────────────────────────────────────────────────

def _result(
    payout, pct, amt, band, reason,
    gig_score, risk_level, risk_score, today_earnings,
    loan_id, loan_outstanding, routing_chain,
) -> dict:
    return {
        "should_deduct":    amt > 0,
        "deduction_pct":    round(pct, 2),
        "deduction_amount": round(amt, 2),
        "net_deposit":      round(payout - amt, 2),
        "band":             band,
        "reason":           reason,
        "gig_score":        gig_score,
        "risk_level":       risk_level,
        "risk_score":       risk_score,
        "today_earnings":   round(today_earnings, 2),
        "floor_threshold":  FLOOR_THRESHOLD_SGD,
        "loan_id":          loan_id,
        "loan_outstanding": round(loan_outstanding, 2),
        "routing_chain":    routing_chain,
    }
