"""
Alternative Credit Scoring Multi-Agent Crew
=============================================
Agents:
  1. Income Verifier   – validates income consistency and reliability
  2. Credit Analyst    – computes an alternative credit score (0–850)
  3. Loan Advisor      – determines micro-loan eligibility and terms

This replaces traditional CIBIL-only scoring with gig-economy-aware metrics.
Falls back to formula-based scoring when no LLM is configured.
"""

import io
import json
import sys

from com.gxs.bank.agents.llm_config import CREWAI_AVAILABLE, get_llm


# ---------------------------------------------------------------------------
# CrewAI live implementation
# ---------------------------------------------------------------------------

def _run_crew(profile: dict, llm) -> dict:
    from crewai import Agent, Crew, Process, Task

    ctx = f"""
=== ALTERNATIVE CREDIT SCORING CONTEXT ===
Account balance        : S${profile['total_balance']:,.2f}
Income (30d)           : S${profile['income_30d']:,.2f}
Income (90d)           : S${profile['income_90d']:,.2f}
Expense (30d)          : S${profile['expense_30d']:,.2f}
Savings (30d)          : S${profile['savings_30d']:,.2f}
Savings rate           : {profile['savings_rate_pct']}%
Active loans           : {profile['active_loans_count']}
Monthly EMI burden     : S${profile['total_monthly_emi']:,.2f}
EMI-to-income ratio    : {profile['emi_to_income_pct']}%
Outstanding debt       : S${profile['total_outstanding_debt']:,.2f}

Loan details:
{json.dumps(profile['loans'], indent=2)}

Daily income trend:
{json.dumps(dict(list(profile['daily_income'].items())[-21:]), indent=2)}
"""

    income_verifier = Agent(
        role="Gig Income Verifier",
        goal=(
            "Assess the reliability, consistency, and growth trajectory of "
            "the Grab driver's income as a creditworthiness signal."
        ),
        backstory=(
            "You are a credit specialist who pioneered alternative data scoring "
            "for gig workers. You know that a steady S$800/day driver with no CIBIL "
            "history deserves credit just as much as a salaried employee."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    credit_analyst = Agent(
        role="Alternative Credit Score Analyst",
        goal=(
            "Compute a composite credit score (0–850) using gig income data, "
            "savings behaviour, debt-to-income ratio, and account activity."
        ),
        backstory=(
            "You designed GXS Bank's proprietary GigScore system. "
            "Unlike CIBIL, GigScore rewards consistent income, healthy savings "
            "rates, and responsible EMI management — even without formal credit history."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    loan_advisor = Agent(
        role="Micro-Loan Eligibility Advisor",
        goal=(
            "Determine the maximum loan amount, interest rate, and tenure "
            "the driver qualifies for based on their GigScore."
        ),
        backstory=(
            "You are a lending officer who specialises in micro-loans for "
            "gig economy workers. You balance risk with financial inclusion, "
            "offering fair terms that help drivers grow without over-leveraging."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    t_verify = Task(
        description=(
            f"{ctx}\n"
            "Assess income reliability. Output JSON: "
            "income_consistency_score (0–100), income_trend (rising/stable/falling), "
            "monthly_income_estimate, income_reliability_grade (A/B/C/D/F), "
            "verification_notes."
        ),
        expected_output="JSON with income verification",
        agent=income_verifier,
    )

    t_score = Task(
        description=(
            f"{ctx}\n"
            "Calculate the GigScore. Components:\n"
            "  - Income consistency (30%)\n"
            "  - Savings behaviour (25%)\n"
            "  - Debt-to-income ratio (20%)\n"
            "  - Account balance stability (15%)\n"
            "  - Transaction volume (10%)\n"
            "Output JSON: gig_score (0–850), score_grade (Excellent/Good/Fair/Poor), "
            "component_scores (dict), score_explanation."
        ),
        expected_output="JSON with credit score",
        agent=credit_analyst,
        context=[t_verify],
    )

    t_loan = Task(
        description=(
            f"{ctx}\n"
            "Based on the GigScore, determine loan eligibility. Output JSON: "
            "is_eligible (bool), max_loan_amount_inr, recommended_loan_inr, "
            "interest_rate_pct, tenure_months, monthly_emi_inr, "
            "eligibility_reason, improvement_tips (list of 3 actionable tips)."
        ),
        expected_output="JSON with loan eligibility",
        agent=loan_advisor,
        context=[t_verify, t_score],
    )

    crew = Crew(
        agents=[income_verifier, credit_analyst, loan_advisor],
        tasks=[t_verify, t_score, t_loan],
        process=Process.sequential,
        verbose=True,
    )

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        crew.kickoff()
    finally:
        sys.stdout = old_stdout
    reasoning_log = buffer.getvalue()

    def _safe_json(text):
        try:
            if hasattr(text, "raw"):
                text = text.raw
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except Exception:
            return {"raw": str(text)}

    tasks = crew.tasks
    verify_out = _safe_json(str(tasks[0].output) if tasks[0].output else "{}")
    score_out = _safe_json(str(tasks[1].output) if tasks[1].output else "{}")
    loan_out = _safe_json(str(tasks[2].output) if tasks[2].output else "{}")

    return {
        "mode": "live_crew",
        "income_verification": verify_out,
        "credit_score": score_out,
        "loan_eligibility": loan_out,
        "reasoning_log": reasoning_log[:4000],
    }


# ---------------------------------------------------------------------------
# Formula-based fallback
# ---------------------------------------------------------------------------

def _run_fallback(profile: dict) -> dict:
    income = profile["income_30d"]
    income_90d = profile["income_90d"]
    savings = profile["savings_30d"]
    savings_rate = profile["savings_rate_pct"]
    balance = profile["total_balance"]
    emi = profile["total_monthly_emi"]
    outstanding = profile["total_outstanding_debt"]
    emi_ratio = profile["emi_to_income_pct"]

    # ── Income consistency score (30 pts) ───────────────────────────────────
    monthly_avg_90d = income_90d / 3 if income_90d > 0 else 0
    consistency = 0.0
    if monthly_avg_90d > 0:
        deviation = abs(income - monthly_avg_90d) / monthly_avg_90d
        consistency = max(0, 1 - deviation)  # 0–1
    income_consistency_pts = round(consistency * 30)

    # ── Savings behaviour (25 pts) ──────────────────────────────────────────
    if savings_rate >= 25:
        savings_pts = 25
    elif savings_rate >= 15:
        savings_pts = 18
    elif savings_rate >= 5:
        savings_pts = 10
    elif savings_rate >= 0:
        savings_pts = 5
    else:
        savings_pts = 0

    # ── Debt-to-income ratio (20 pts) ───────────────────────────────────────
    if emi_ratio <= 10:
        debt_pts = 20
    elif emi_ratio <= 20:
        debt_pts = 15
    elif emi_ratio <= 35:
        debt_pts = 8
    elif emi_ratio <= 50:
        debt_pts = 3
    else:
        debt_pts = 0

    # ── Balance stability (15 pts) ──────────────────────────────────────────
    months_runway = balance / max(profile["expense_30d"], 1)
    if months_runway >= 3:
        balance_pts = 15
    elif months_runway >= 1:
        balance_pts = 10
    elif months_runway >= 0.5:
        balance_pts = 5
    else:
        balance_pts = 0

    # ── Transaction volume (10 pts) ─────────────────────────────────────────
    txn_count = len(profile["recent_transactions"])
    txn_pts = min(txn_count // 3, 10)

    # ── Composite GigScore ──────────────────────────────────────────────────
    raw_score = income_consistency_pts + savings_pts + debt_pts + balance_pts + txn_pts
    gig_score = int(300 + (raw_score / 100) * 550)  # map 0–100 → 300–850
    gig_score = max(300, min(850, gig_score))

    if gig_score >= 750:
        grade = "Excellent"
    elif gig_score >= 650:
        grade = "Good"
    elif gig_score >= 550:
        grade = "Fair"
    else:
        grade = "Poor"

    # ── Loan eligibility ────────────────────────────────────────────────────
    eligible = gig_score >= 500 and income > 5000
    monthly_income = income

    if gig_score >= 750:
        max_loan = monthly_income * 6
        rate = 10.5
        tenure = 12
    elif gig_score >= 650:
        max_loan = monthly_income * 4
        rate = 12.5
        tenure = 9
    elif gig_score >= 550:
        max_loan = monthly_income * 2
        rate = 15.0
        tenure = 6
    elif gig_score >= 500:
        # Starter tier: score 500-549 qualifies for a modest micro-loan
        max_loan = monthly_income * 1.5
        rate = 16.5
        tenure = 6
    else:
        max_loan = 0
        rate = 0
        tenure = 0

    recommended_loan = round(max_loan * 0.7, -2)  # 70% of max, rounded
    monthly_emi = 0.0
    if eligible and tenure > 0:
        r = rate / 100 / 12
        monthly_emi = round(recommended_loan * r * (1 + r) ** tenure / ((1 + r) ** tenure - 1), 2)

    tips = [
        f"Increase savings rate from {savings_rate:.0f}% to 20% to boost score by ~30 pts",
        "Reduce EMI-to-income ratio below 30% for better credit terms",
        "Maintain account balance above 1 month of expenses for 3 consecutive months",
    ]

    income_reliability_grade = "A" if consistency >= 0.8 else "B" if consistency >= 0.6 else "C" if consistency >= 0.4 else "D"

    # ── Build eligibility reason with correct conditions ────────────────────
    if eligible:
        eligibility_reason = f"GigScore {gig_score} qualifies you for up to S${max_loan:,.0f}"
    elif gig_score < 500 and income <= 5000:
        eligibility_reason = (
            f"GigScore {gig_score} is below 500 and monthly income S${income:,.0f} "
            f"is below the S$5,000 minimum. Improve both to unlock loan eligibility."
        )
    elif gig_score < 500:
        eligibility_reason = (
            f"GigScore {gig_score} is below the minimum threshold of 500. "
            f"Improve your savings rate and income consistency to boost your score."
        )
    else:
        eligibility_reason = (
            f"Monthly income S${income:,.0f} is below the S$5,000 minimum for loan eligibility. "
            f"Your GigScore {gig_score} is strong — increase income to qualify."
        )

    return {
        "mode": "deterministic_fallback",
        "income_verification": {
            "income_consistency_score": round(consistency * 100),
            "income_trend": "rising" if income > monthly_avg_90d else "stable",
            "monthly_income_estimate": round(income, 2),
            "income_reliability_grade": income_reliability_grade,
            "verification_notes": f"30-day income S${income:,.0f} vs 90-day avg S${monthly_avg_90d:,.0f}/mo",
        },
        "credit_score": {
            "gig_score": gig_score,
            "score_grade": grade,
            "component_scores": {
                "income_consistency_30pct": income_consistency_pts,
                "savings_behaviour_25pct": savings_pts,
                "debt_to_income_20pct": debt_pts,
                "balance_stability_15pct": balance_pts,
                "transaction_volume_10pct": txn_pts,
                "raw_total": raw_score,
            },
            "score_explanation": (
                f"GigScore {gig_score} ({grade}): income consistency={income_consistency_pts}/30, "
                f"savings={savings_pts}/25, debt={debt_pts}/20, balance={balance_pts}/15, txn={txn_pts}/10"
            ),
        },
        "loan_eligibility": {
            "is_eligible": eligible,
            "max_loan_amount_inr": round(max_loan, 2),
            "recommended_loan_inr": recommended_loan,
            "interest_rate_pct": rate,
            "tenure_months": tenure,
            "monthly_emi_inr": monthly_emi,
            "eligibility_reason": eligibility_reason,
            "improvement_tips": tips,
        },
        "reasoning_log": (
            f"Step 1: Fetched 90-day income data; monthly avg = S${monthly_avg_90d:,.0f}\n"
            f"Step 2: Income consistency score = {income_consistency_pts}/30 "
            f"(deviation = {abs(income - monthly_avg_90d) / max(monthly_avg_90d, 1):.1%})\n"
            f"Step 3: Savings score = {savings_pts}/25 (rate = {savings_rate:.1f}%)\n"
            f"Step 4: Debt score = {debt_pts}/20 (EMI ratio = {emi_ratio:.1f}%)\n"
            f"Step 5: Balance score = {balance_pts}/15 ({months_runway:.1f} months runway)\n"
            f"Step 6: Transaction volume score = {txn_pts}/10\n"
            f"Step 7: GigScore = {gig_score} ({grade})\n"
            f"Step 8: Loan eligibility = {eligible}, max = S${max_loan:,.0f}"
        ),
    }


# ---------------------------------------------------------------------------
# Public entry point — credit scoring
# ---------------------------------------------------------------------------

def run_credit_scoring(profile: dict) -> dict:
    """Run the Credit Scoring crew (live or fallback)."""
    llm = get_llm()
    if llm and CREWAI_AVAILABLE:
        try:
            return _run_crew(profile, llm)
        except Exception as e:
            return {**_run_fallback(profile), "crew_error": str(e)}
    return _run_fallback(profile)


# ---------------------------------------------------------------------------
# Asset-backed Gig Loan — crew implementation
# ---------------------------------------------------------------------------

_ASSET_CONFIG = {
    "bike":      {"ltv": 0.80, "rate_discount": 2.0, "tenure": 36, "income_boost_pct": 0.25},
    "phone":     {"ltv": 0.70, "rate_discount": 1.0, "tenure": 18, "income_boost_pct": 0.05},
    "laptop":    {"ltv": 0.70, "rate_discount": 1.0, "tenure": 18, "income_boost_pct": 0.08},
    "equipment": {"ltv": 0.75, "rate_discount": 1.5, "tenure": 24, "income_boost_pct": 0.15},
}


def _run_asset_crew(profile: dict, asset_type: str, asset_price: float, llm) -> dict:
    from crewai import Agent, Crew, Process, Task

    base = run_credit_scoring(profile)
    gig_score = base.get("credit_score", {}).get("gig_score", 500)
    cfg = _ASSET_CONFIG.get(asset_type, _ASSET_CONFIG["equipment"])

    ctx = f"""
=== ASSET-BACKED GIG LOAN CONTEXT ===
GigScore               : {gig_score}
Income (30d)           : S${profile['income_30d']:,.2f}
Income (90d)           : S${profile['income_90d']:,.2f}
Savings rate           : {profile['savings_rate_pct']}%
EMI-to-income ratio    : {profile['emi_to_income_pct']}%
Outstanding debt       : S${profile['total_outstanding_debt']:,.2f}

Asset being financed   : {asset_type}
Asset price            : S${asset_price:,.2f}
Max LTV allowed        : {cfg['ltv'] * 100:.0f}%
Rate discount vs personal loan : {cfg['rate_discount']:.1f}%
Expected tenure        : {cfg['tenure']} months
Estimated income boost : {cfg['income_boost_pct'] * 100:.0f}% of current 30d income
"""

    asset_specialist = Asset = Agent(
        role="Asset-Backed Gig Loan Specialist",
        goal=(
            "Determine eligibility and optimal loan terms for a vehicle or equipment loan "
            "for a gig worker. The asset is collateral and an income-generating tool — "
            "factor in the earning capacity uplift it provides."
        ),
        backstory=(
            "You are a specialist lender at GXS Bank who pioneered gig-asset financing. "
            "You know that a Grab driver's bike is not just a purchase — it is infrastructure. "
            "A working bike means more rides, more income, and faster loan repayment. "
            "You price asset loans with this income-boost multiplier in mind."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    t_asset = Task(
        description=(
            f"{ctx}\n"
            "Assess eligibility for this asset-backed loan. Output JSON:\n"
            "asset_type, asset_price_inr, down_payment_inr, loan_amount_inr, "
            "interest_rate_pct, tenure_months, monthly_emi_inr, ltv_ratio_pct, "
            "is_eligible (bool), eligibility_reason, "
            "income_capacity_uplift_pct (how much this asset boosts earning capacity), "
            "monthly_income_boost_inr (estimated extra monthly income from asset), "
            "payback_months (months for asset to pay for itself via extra income), "
            "collateral_value_inr (resale/repossession value), "
            "improvement_tips (list of 2 tips to improve eligibility if not eligible)."
        ),
        expected_output="JSON with asset loan eligibility",
        agent=asset_specialist,
    )

    crew = Crew(
        agents=[asset_specialist],
        tasks=[t_asset],
        process=Process.sequential,
        verbose=True,
    )

    import io, sys, json
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        crew.kickoff()
    finally:
        sys.stdout = old_stdout
    reasoning_log = buffer.getvalue()

    def _safe_json(text):
        try:
            if hasattr(text, "raw"):
                text = text.raw
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except Exception:
            return {"raw": str(text)}

    asset_out = _safe_json(str(t_asset.output) if t_asset.output else "{}")
    return {
        "mode": "live_crew",
        "gig_score_used": gig_score,
        "asset_loan": asset_out,
        "base_credit": base.get("credit_score", {}),
        "reasoning_log": reasoning_log[:4000],
    }


def _run_asset_fallback(profile: dict, asset_type: str, asset_price: float) -> dict:
    """Formula-based asset loan eligibility — no LLM required."""
    import math

    base = run_credit_scoring(profile)
    gig_score = base.get("credit_score", {}).get("gig_score", 500)
    cfg = _ASSET_CONFIG.get(asset_type, _ASSET_CONFIG["equipment"])

    income = profile["income_30d"]
    emi_ratio = profile["emi_to_income_pct"]

    # ── Eligibility gate ────────────────────────────────────────────────────────
    eligible = gig_score >= 450 and income >= 8000 and emi_ratio < 55

    # ── Loan amount (LTV of asset price, capped by income multiple) ─────────────
    ltv_amount = asset_price * cfg["ltv"]
    income_cap = income * 5          # max 5× monthly income
    loan_amount = min(ltv_amount, income_cap)
    down_payment = asset_price - loan_amount

    # ── Interest rate (personal loan base - asset discount) ─────────────────────
    if gig_score >= 750:
        base_rate = 10.5
    elif gig_score >= 650:
        base_rate = 12.5
    elif gig_score >= 550:
        base_rate = 15.0
    else:
        base_rate = 18.0
    rate = max(base_rate - cfg["rate_discount"], 8.0)

    # ── EMI calculation ──────────────────────────────────────────────────────────
    tenure = cfg["tenure"]
    r = rate / 100 / 12
    monthly_emi = 0.0
    if eligible and loan_amount > 0 and r > 0:
        monthly_emi = round(loan_amount * r * (1 + r) ** tenure / ((1 + r) ** tenure - 1), 2)

    # ── Income capacity uplift ───────────────────────────────────────────────────
    monthly_income_boost = round(income * cfg["income_boost_pct"], 2)
    payback_months = math.ceil(loan_amount / monthly_income_boost) if monthly_income_boost > 0 else 999
    collateral_value = round(asset_price * 0.60, 2)   # 60% resale assumption

    tips = []
    if not eligible:
        if gig_score < 450:
            tips.append(f"Raise your GigScore above 500 (currently {gig_score}) by improving savings rate")
        if income < 8000:
            tips.append(f"Maintain monthly income above S$8,000 for 3 consecutive months")
        if emi_ratio >= 55:
            tips.append(f"Reduce EMI-to-income ratio below 50% (currently {emi_ratio:.1f}%)")
    else:
        tips = [
            f"Making a larger down payment (>25%) reduces EMI to S${monthly_emi * 0.85:,.0f}/month",
            "On-time payments for 6 months unlocks a rate reduction of 0.5%",
        ]

    reasoning = (
        f"Step 1: GigScore = {gig_score}, income = S${income:,.0f}, EMI ratio = {emi_ratio:.1f}%\n"
        f"Step 2: Eligible = {eligible}\n"
        f"Step 3: LTV {cfg['ltv']*100:.0f}% of S${asset_price:,.0f} = S${ltv_amount:,.0f}, capped at S${loan_amount:,.0f}\n"
        f"Step 4: Rate = {base_rate:.1f}% base - {cfg['rate_discount']:.1f}% asset discount = {rate:.1f}%\n"
        f"Step 5: Monthly EMI = S${monthly_emi:,.0f} over {tenure} months\n"
        f"Step 6: Income boost {cfg['income_boost_pct']*100:.0f}% = S${monthly_income_boost:,.0f}/month\n"
        f"Step 7: Asset pays for itself in {payback_months} months"
    )

    return {
        "mode": "deterministic_fallback",
        "gig_score_used": gig_score,
        "base_credit": base.get("credit_score", {}),
        "asset_loan": {
            "asset_type": asset_type,
            "asset_price_inr": round(asset_price, 2),
            "down_payment_inr": round(down_payment, 2),
            "loan_amount_inr": round(loan_amount, 2),
            "interest_rate_pct": rate,
            "tenure_months": tenure,
            "monthly_emi_inr": monthly_emi,
            "ltv_ratio_pct": round(cfg["ltv"] * 100, 1),
            "is_eligible": eligible,
            "eligibility_reason": (
                f"GigScore {gig_score} qualifies for asset-backed financing at {rate:.1f}% p.a."
                if eligible else
                f"Not eligible — {'score below threshold' if gig_score < 450 else 'income or EMI ratio outside limits'}"
            ),
            "income_capacity_uplift_pct": round(cfg["income_boost_pct"] * 100, 1),
            "monthly_income_boost_inr": monthly_income_boost,
            "payback_months": payback_months,
            "collateral_value_inr": collateral_value,
            "improvement_tips": tips,
        },
        "reasoning_log": reasoning,
    }


# ---------------------------------------------------------------------------
# Public entry point — asset loan
# ---------------------------------------------------------------------------

def run_asset_loan_eligibility(profile: dict, asset_type: str, asset_price: float) -> dict:
    """
    Assess eligibility for a vehicle / equipment loan.
    asset_type: one of 'bike', 'phone', 'laptop', 'equipment'
    asset_price: purchase price in SGD
    """
    asset_type = asset_type.lower().strip()
    if asset_type not in _ASSET_CONFIG:
        asset_type = "equipment"

    llm = get_llm()
    if llm and CREWAI_AVAILABLE:
        try:
            return _run_asset_crew(profile, asset_type, asset_price, llm)
        except Exception as e:
            return {**_run_asset_fallback(profile, asset_type, asset_price), "crew_error": str(e)}
    return _run_asset_fallback(profile, asset_type, asset_price)


# ---------------------------------------------------------------------------
# Dynamic Loan Rate Review — behaviour scoring engine
# ---------------------------------------------------------------------------
#
# Five behaviour dimensions (each 0–20 pts → total 0–100):
#   1. Income performance  – this week vs 30-day weekly average
#   2. Savings discipline  – current savings rate vs 20% target
#   3. Spending control    – this week's spend vs weekly baseline
#   4. Balance buffer      – months of expenses covered by balance
#   5. EMI-to-income ratio – debt burden health
#
# Score → rate adjustment:
#   85–100 → −1.50%  (Excellent — reward with rate cut)
#   70–84  → −0.75%  (Good — smaller rate cut)
#   55–69  →  0.00%  (Neutral — rate holds)
#   40–54  → +0.50%  (Caution — warning nudge upward)
#    0–39  → +1.50%  (At-risk — clear warning signal)
#
# Hard caps:
#   • Effective rate never below 7.0% (floor)
#   • Effective rate never above (base_rate + 3.0%) (ceiling)
#   • Cumulative adjustment never exceeds ±2.0% from original approved rate
# ---------------------------------------------------------------------------

_RATE_FLOOR = 7.0
_MAX_POSITIVE_DRIFT = 3.0   # max above original approved rate
_MAX_NEGATIVE_DRIFT = 2.0   # max below original approved rate

# Score bands → (label, rate_delta_pct, colour)
_SCORE_BANDS = [
    (85, 100, "Excellent",  -1.50, "green"),
    (70,  84, "Good",       -0.75, "teal"),
    (55,  69, "Neutral",     0.00, "grey"),
    (40,  54, "Caution",    +0.50, "amber"),
    ( 0,  39, "At-Risk",    +1.50, "red"),
]


def _score_behaviour(profile: dict) -> dict:
    """
    Compute a 0–100 behaviour score from 5 dimensions.
    Returns full breakdown for transparency.
    """
    income_30d   = profile["income_30d"]
    income_7d    = profile["income_7d"]
    expense_30d  = profile["expense_30d"]
    savings_rate = profile["savings_rate_pct"]
    balance      = profile["total_balance"]
    emi_ratio    = profile["emi_to_income_pct"]

    weekly_avg_income  = income_30d / 4.3
    weekly_avg_expense = expense_30d / 4.3

    # ── Dimension 1: Income performance (0–20) ─────────────────────────────
    if weekly_avg_income > 0:
        income_ratio = income_7d / weekly_avg_income
    else:
        income_ratio = 0.0

    if income_ratio >= 1.20:
        d1 = 20
        d1_label = f"S${income_7d:,.0f} this week (+{(income_ratio-1)*100:.0f}% above avg)"
    elif income_ratio >= 1.00:
        d1 = 16
        d1_label = f"S${income_7d:,.0f} this week (on target)"
    elif income_ratio >= 0.80:
        d1 = 10
        d1_label = f"S${income_7d:,.0f} this week (-{(1-income_ratio)*100:.0f}% below avg)"
    elif income_ratio >= 0.60:
        d1 = 5
        d1_label = f"S${income_7d:,.0f} this week (significantly below avg)"
    else:
        d1 = 0
        d1_label = f"S${income_7d:,.0f} this week (critical shortfall)"

    # ── Dimension 2: Savings discipline (0–20) ────────────────────────────
    if savings_rate >= 25:
        d2, d2_label = 20, f"{savings_rate:.1f}% savings rate (excellent)"
    elif savings_rate >= 20:
        d2, d2_label = 16, f"{savings_rate:.1f}% savings rate (on target)"
    elif savings_rate >= 15:
        d2, d2_label = 10, f"{savings_rate:.1f}% savings rate (slightly below 20% target)"
    elif savings_rate >= 5:
        d2, d2_label = 5, f"{savings_rate:.1f}% savings rate (low)"
    else:
        d2, d2_label = 0, f"{savings_rate:.1f}% savings rate (critical)"

    # ── Dimension 3: Spending control (0–20) ─────────────────────────────
    # We use expense_7d proxy: expense_30d * (income_7d / income_30d) as estimate
    # since we don't have direct expense_7d in profile
    # Use savings-derived estimate: spending_7d ≈ income_7d - (savings_30d/4.3)
    weekly_savings = profile["savings_30d"] / 4.3
    spend_7d_est = max(income_7d - weekly_savings, 0)
    if weekly_avg_expense > 0:
        spend_ratio = spend_7d_est / weekly_avg_expense
    else:
        spend_ratio = 1.0

    if spend_ratio <= 0.80:
        d3, d3_label = 20, f"Spending S${spend_7d_est:,.0f}/wk — well below baseline (disciplined)"
    elif spend_ratio <= 1.00:
        d3, d3_label = 15, f"Spending S${spend_7d_est:,.0f}/wk — within budget"
    elif spend_ratio <= 1.20:
        d3, d3_label = 7, f"Spending S${spend_7d_est:,.0f}/wk — slightly over budget"
    else:
        d3, d3_label = 0, f"Spending S${spend_7d_est:,.0f}/wk — overspending ({spend_ratio:.0%} of baseline)"

    # ── Dimension 4: Balance buffer (0–20) ───────────────────────────────
    monthly_expense = expense_30d or 1
    months_buffer = balance / monthly_expense

    if months_buffer >= 3.0:
        d4, d4_label = 20, f"S${balance:,.0f} balance covers {months_buffer:.1f}x monthly expenses"
    elif months_buffer >= 2.0:
        d4, d4_label = 15, f"S${balance:,.0f} balance covers {months_buffer:.1f}x monthly expenses"
    elif months_buffer >= 1.0:
        d4, d4_label = 8, f"S${balance:,.0f} balance covers {months_buffer:.1f}x monthly expenses"
    elif months_buffer >= 0.5:
        d4, d4_label = 3, f"S${balance:,.0f} balance — less than 1 month of expenses"
    else:
        d4, d4_label = 0, f"S${balance:,.0f} balance — dangerously thin buffer"

    # ── Dimension 5: EMI-to-income ratio (0–20) ──────────────────────────
    if emi_ratio <= 15:
        d5, d5_label = 20, f"EMI burden {emi_ratio:.1f}% of income (healthy)"
    elif emi_ratio <= 25:
        d5, d5_label = 15, f"EMI burden {emi_ratio:.1f}% of income (manageable)"
    elif emi_ratio <= 35:
        d5, d5_label = 8, f"EMI burden {emi_ratio:.1f}% of income (elevated)"
    elif emi_ratio <= 50:
        d5, d5_label = 3, f"EMI burden {emi_ratio:.1f}% of income (high risk)"
    else:
        d5, d5_label = 0, f"EMI burden {emi_ratio:.1f}% — exceeds safe threshold"

    total = d1 + d2 + d3 + d4 + d5

    # Determine band
    band_label, rate_delta, colour = "Neutral", 0.0, "grey"
    for lo, hi, label, delta, col in _SCORE_BANDS:
        if lo <= total <= hi:
            band_label, rate_delta, colour = label, delta, col
            break

    return {
        "behaviour_score":  total,
        "band":             band_label,
        "colour":           colour,
        "rate_delta_pct":   rate_delta,
        "breakdown": {
            "income_performance_20":  {"score": d1, "detail": d1_label},
            "savings_discipline_20":  {"score": d2, "detail": d2_label},
            "spending_control_20":    {"score": d3, "detail": d3_label},
            "balance_buffer_20":      {"score": d4, "detail": d4_label},
            "emi_burden_20":          {"score": d5, "detail": d5_label},
        },
    }


def _compute_new_rate(base_rate: float, current_rate: float, delta: float) -> dict:
    """
    Apply delta to current_rate with floor, ceiling and drift caps.
    Returns new_rate and the clamping reason if applicable.
    """
    proposed = current_rate + delta

    clamp_reason = None
    # Floor: never below 7%
    if proposed < _RATE_FLOOR:
        proposed = _RATE_FLOOR
        clamp_reason = f"Floor applied — rate cannot go below {_RATE_FLOOR:.1f}%"

    # Ceiling: never above base + 3%
    ceiling = base_rate + _MAX_POSITIVE_DRIFT
    if proposed > ceiling:
        proposed = ceiling
        clamp_reason = f"Ceiling applied — rate capped at base_rate + {_MAX_POSITIVE_DRIFT:.1f}%"

    # Drift: cumulative shift from original base cannot exceed ±2%
    total_drift = proposed - base_rate
    if total_drift > _MAX_NEGATIVE_DRIFT * -1 and total_drift < 0:
        pass   # within negative drift cap
    elif total_drift < -_MAX_NEGATIVE_DRIFT:
        proposed = base_rate - _MAX_NEGATIVE_DRIFT
        clamp_reason = f"Max benefit applied — rate floored at base - {_MAX_NEGATIVE_DRIFT:.1f}%"

    return {
        "new_rate":      round(proposed, 2),
        "clamp_reason":  clamp_reason,
        "total_drift":   round(proposed - base_rate, 2),
    }


def _run_dynamic_rate_crew(
    profile: dict, base_rate: float, current_rate: float,
    asset_type: str, behaviour: dict, llm,
) -> dict:
    from crewai import Agent, Crew, Process, Task
    import io, sys, json

    ctx = f"""
=== DYNAMIC LOAN RATE REVIEW ===
Asset type             : {asset_type}
Original approved rate : {base_rate:.2f}%
Current effective rate : {current_rate:.2f}%

Behaviour Score this week: {behaviour['behaviour_score']}/100 ({behaviour['band']})

Dimension scores:
  Income performance    : {behaviour['breakdown']['income_performance_20']['score']}/20 — {behaviour['breakdown']['income_performance_20']['detail']}
  Savings discipline    : {behaviour['breakdown']['savings_discipline_20']['score']}/20 — {behaviour['breakdown']['savings_discipline_20']['detail']}
  Spending control      : {behaviour['breakdown']['spending_control_20']['score']}/20 — {behaviour['breakdown']['spending_control_20']['detail']}
  Balance buffer        : {behaviour['breakdown']['balance_buffer_20']['score']}/20 — {behaviour['breakdown']['balance_buffer_20']['detail']}
  EMI burden            : {behaviour['breakdown']['emi_burden_20']['score']}/20 — {behaviour['breakdown']['emi_burden_20']['detail']}

Proposed rate delta     : {behaviour['rate_delta_pct']:+.2f}%
"""

    rate_advisor = Agent(
        role="Dynamic Loan Rate Advisor",
        goal=(
            "Review the borrower's weekly financial behaviour score and determine "
            "whether to adjust their loan interest rate. Explain the adjustment clearly "
            "so the borrower understands exactly what they did well or need to improve."
        ),
        backstory=(
            "You are GXS Bank's dynamic pricing specialist. You believe interest rates "
            "should reward good financial behaviour, not just credit history. "
            "Your rate adjustments are transparent, fair, and always explained in plain language "
            "that a gig worker can act on next week."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    t_review = Task(
        description=(
            f"{ctx}\n"
            "Review the behaviour score and produce the weekly rate decision. Output JSON:\n"
            "behaviour_score, band, rate_delta_pct, current_rate_pct, new_rate_pct,\n"
            "adjustment_narrative (2-3 sentences explaining the change in plain language),\n"
            "top_win (the one behaviour dimension that helped most this week),\n"
            "top_gap (the one dimension with most room for improvement),\n"
            "next_week_tip (single actionable instruction to improve score next week),\n"
            "projected_savings_inr (how much interest saved over remaining tenure if rate stays at new level)."
        ),
        expected_output="JSON with rate review decision",
        agent=rate_advisor,
    )

    crew = Crew(agents=[rate_advisor], tasks=[t_review], process=Process.sequential, verbose=True)
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        crew.kickoff()
    finally:
        sys.stdout = old_stdout

    def _safe_json(text):
        try:
            if hasattr(text, "raw"):
                text = text.raw
            start = text.find("{"); end = text.rfind("}") + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except Exception:
            return {}

    out = _safe_json(str(t_review.output) if t_review.output else "{}")
    return {"mode": "live_crew", "review": out, "reasoning_log": buffer.getvalue()[:3000]}


def _run_dynamic_rate_fallback(
    profile: dict, base_rate: float, current_rate: float,
    asset_type: str, outstanding: float, remaining_months: int,
) -> dict:
    """Full deterministic dynamic rate review — no LLM required."""
    behaviour = _score_behaviour(profile)
    rate_result = _compute_new_rate(base_rate, current_rate, behaviour["rate_delta_pct"])
    new_rate = rate_result["new_rate"]
    delta = behaviour["rate_delta_pct"]

    # ── Projected interest saving / cost over remaining tenure ───────────────
    old_monthly_interest = outstanding * (current_rate / 100 / 12)
    new_monthly_interest = outstanding * (new_rate / 100 / 12)
    diff_per_month = old_monthly_interest - new_monthly_interest
    projected_savings = round(diff_per_month * remaining_months, 2)

    # ── Human-readable narrative ─────────────────────────────────────────────
    score = behaviour["behaviour_score"]
    band  = behaviour["band"]
    breakdown = behaviour["breakdown"]

    if delta < 0:
        narrative = (
            f"Great week! Your behaviour score of {score}/100 ({band}) earned you a "
            f"{abs(delta):.2f}% rate cut. Your rate drops from {current_rate:.2f}% to {new_rate:.2f}%. "
            f"If you maintain this level, you'll save S${abs(projected_savings):,.0f} in interest over the remaining tenure."
        )
    elif delta == 0:
        narrative = (
            f"Steady week. Your behaviour score of {score}/100 ({band}) holds your rate at {current_rate:.2f}%. "
            f"Push savings above 20% or income above your weekly average to unlock a rate cut next week."
        )
    else:
        narrative = (
            f"Your behaviour score of {score}/100 ({band}) triggered a {delta:.2f}% rate warning increase. "
            f"Rate moves from {current_rate:.2f}% to {new_rate:.2f}%. "
            f"This adds S${abs(projected_savings):,.0f} in interest — improve performance next week to reverse this."
        )

    # ── Top win and gap ──────────────────────────────────────────────────────
    dims = breakdown
    sorted_dims = sorted(dims.items(), key=lambda x: x[1]["score"], reverse=True)
    top_win = sorted_dims[0][1]["detail"]
    top_gap = sorted_dims[-1][1]["detail"]

    # ── Next week tip based on worst dimension ───────────────────────────────
    worst_key = sorted_dims[-1][0]
    tips_map = {
        "income_performance_20": f"Work peak slots (Evening Rush on Fri/Sat) to push weekly income above S${profile['income_30d']/4.3*1.1:,.0f}",
        "savings_discipline_20": f"Auto-transfer S${round(profile['income_7d']*0.05):,.0f} to savings right after next income credit",
        "spending_control_20":   "Pause non-essential purchases this week — one less food delivery order per day saves ~S$500",
        "balance_buffer_20":     f"Keep your balance above S${round(profile['expense_30d'] * 2):,.0f} (2x monthly expenses) for the full week",
        "emi_burden_20":         "Avoid taking on any new credit this week — let the EMI ratio recover naturally",
    }
    next_week_tip = tips_map.get(worst_key, "Focus on saving more than you spend this week")

    reasoning = (
        f"Step 1: Computed 5-dimension behaviour score = {score}/100 (band: {band})\n"
        f"Step 2: Rate delta = {delta:+.2f}% based on score band\n"
        f"Step 3: Applied floor/ceiling/drift caps → new rate = {new_rate:.2f}%\n"
        f"Step 4: Outstanding = S${outstanding:,.0f}, {remaining_months} months remaining\n"
        f"Step 5: Interest diff = S${diff_per_month:,.2f}/month → projected impact = S${abs(projected_savings):,.0f}\n"
        f"Step 6: Worst dimension = {worst_key} → personalised tip generated"
    )
    if rate_result["clamp_reason"]:
        reasoning += f"\nStep 7: Rate clamped — {rate_result['clamp_reason']}"

    return {
        "mode": "deterministic_fallback",
        "review": {
            "behaviour_score":       score,
            "band":                  band,
            "colour":                behaviour["colour"],
            "rate_delta_pct":        delta,
            "current_rate_pct":      current_rate,
            "new_rate_pct":          new_rate,
            "base_rate_pct":         base_rate,
            "total_drift_from_base": rate_result["total_drift"],
            "clamp_reason":          rate_result["clamp_reason"],
            "outstanding_inr":       outstanding,
            "remaining_months":      remaining_months,
            "projected_savings_inr": projected_savings,
            "adjustment_narrative":  narrative,
            "top_win":               top_win,
            "top_gap":               top_gap,
            "next_week_tip":         next_week_tip,
            "dimension_breakdown":   breakdown,
        },
        "reasoning_log": reasoning,
    }


# ---------------------------------------------------------------------------
# Public entry point — dynamic rate review
# ---------------------------------------------------------------------------

def run_dynamic_rate_review(
    profile: dict,
    base_rate: float,
    current_rate: float,
    asset_type: str = "bike",
    outstanding: float = 0.0,
    remaining_months: int = 12,
) -> dict:
    """
    Weekly dynamic rate review for an asset-backed gig loan.

    base_rate        : original approved interest rate (%)
    current_rate     : this week's effective rate (%)
    asset_type       : 'bike' | 'phone' | 'laptop' | 'equipment'
    outstanding      : remaining loan principal (INR)
    remaining_months : months left on the loan
    """
    asset_type = asset_type.lower().strip()
    if asset_type not in _ASSET_CONFIG:
        asset_type = "equipment"

    llm = get_llm()
    if llm and CREWAI_AVAILABLE:
        try:
            behaviour = _score_behaviour(profile)
            rate_result = _compute_new_rate(base_rate, current_rate, behaviour["rate_delta_pct"])
            crew_result = _run_dynamic_rate_crew(
                profile, base_rate, current_rate, asset_type, behaviour, llm
            )
            # Merge formula-computed rate result into crew output (rate numbers are always formula-driven)
            crew_result["review"].update({
                "new_rate_pct":          rate_result["new_rate"],
                "rate_delta_pct":        behaviour["rate_delta_pct"],
                "behaviour_score":       behaviour["behaviour_score"],
                "band":                  behaviour["band"],
                "colour":                behaviour["colour"],
                "total_drift_from_base": rate_result["total_drift"],
                "clamp_reason":          rate_result["clamp_reason"],
                "dimension_breakdown":   behaviour["breakdown"],
            })
            return crew_result
        except Exception as e:
            return {
                **_run_dynamic_rate_fallback(profile, base_rate, current_rate, asset_type, outstanding, remaining_months),
                "crew_error": str(e),
            }

    return _run_dynamic_rate_fallback(
        profile, base_rate, current_rate, asset_type, outstanding, remaining_months
    )
