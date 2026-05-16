"""
Agent Orchestrator
==================
Unified interface for all CrewAI multi-agent features.
Handles data fetching, crew routing, and response assembly.
"""

from __future__ import annotations

import time
import json
import re
import logging

from sqlalchemy.orm import Session

from com.gxs.bank.agents.credit_agent import run_asset_loan_eligibility, run_credit_scoring, run_dynamic_rate_review
from com.gxs.bank.agents.data_fetcher import get_user_financial_profile
from com.gxs.bank.agents.fraud_agent import run_fraud_check
from com.gxs.bank.agents.llm_config import direct_llm_call, is_crewai_mode, is_live_mode
from com.gxs.bank.agents.nudge_agent import run_nudges
from com.gxs.bank.agents.prediction_agent import run_income_prediction, run_peak_hours_optimiser
from com.gxs.bank.agents.wellness_agent import run_financial_wellness


log = logging.getLogger("orchestrator")


def _extract_json_payload(raw: str) -> dict | None:
    """Best-effort extraction of a JSON object from model output."""
    if not raw:
        return None

    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\s*```$", "", text, flags=re.DOTALL)

    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    return None


def _profile(user_id: str, db: Session) -> dict:
    return get_user_financial_profile(user_id, db)


def _audit(user_id: str, agent_name: str, intent: str, result: dict, duration_ms: float, db):
    """Write one entry to the agent reasoning audit log."""
    try:
        from com.gxs.bank.agents.audit_logger import log_agent_call
        log_agent_call(
            user_id=str(user_id),
            agent_name=agent_name,
            intent=intent,
            input_message=intent,
            output=result,
            duration_ms=duration_ms,
            routing_chain=[f"direct call -> {agent_name}"],
            agents_called=[agent_name],
            graph_mode="direct",
            db=db,
        )
    except Exception as _audit_exc:
        import traceback
        print(f"[AUDIT ERROR] {agent_name}: {_audit_exc}", flush=True)
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Public orchestration methods
# ---------------------------------------------------------------------------

def get_financial_wellness(user_id: str, db: Session) -> dict:
    """
    Runs the full Financial Wellness crew:
    income analysis + savings plan + budget + nudges.
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_financial_wellness(profile)
    result["profile_snapshot"] = {
        "income_30d": profile["income_30d"],
        "expense_30d": profile["expense_30d"],
        "savings_rate_pct": profile["savings_rate_pct"],
        "total_balance": profile["total_balance"],
    }
    result["agent_mode"] = "live" if is_live_mode() else "deterministic"
    _audit(user_id, "wellness", "wellness", result, (time.time() - t0) * 1000, db)
    return result


def get_fraud_analysis(user_id: str, db: Session, suspect_amount: float = 0.0) -> dict:
    """
    Runs the Fraud Detection crew:
    anomaly detection + risk scoring + mitigation advice.
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_fraud_check(profile, suspect_amount)
    result["agent_mode"] = "live" if is_live_mode() else "deterministic"
    _audit(user_id, "fraud", "fraud", result, (time.time() - t0) * 1000, db)
    return result


def get_credit_score(user_id: str, db: Session) -> dict:
    """
    Runs the Alternative Credit Scoring crew:
    income verification + GigScore + loan eligibility.
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_credit_scoring(profile)
    result["agent_mode"] = "live" if is_live_mode() else "deterministic"
    _audit(user_id, "credit", "credit", result, (time.time() - t0) * 1000, db)
    return result


def get_income_prediction(user_id: str, db: Session) -> dict:
    """
    Runs the Income Prediction crew:
    trend analysis + 4-week forecast + debt management plan.
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_income_prediction(profile)
    result["agent_mode"] = "live" if is_live_mode() else "deterministic"
    _audit(user_id, "income", "income", result, (time.time() - t0) * 1000, db)
    return result


def get_nudges(user_id: str, db: Session) -> dict:
    """
    Returns personalised financial nudges via the dedicated nudge_agent.
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_nudges(profile)
    out = {
        "nudges": result.get("nudges", []),
        "income_30d": profile["income_30d"],
        "savings_rate_pct": profile["savings_rate_pct"],
        "expense_by_category": profile.get("expense_by_category", {}),
        "embedding_mode": profile.get("embedding_mode", "keyword_rules"),
        "agent_mode": "live" if is_live_mode() else "deterministic",
    }
    _audit(user_id, "nudges", "nudges", out, (time.time() - t0) * 1000, db)
    return out


def get_financial_health_score(user_id: str, db: Session) -> dict:
    """
    Computes a composite Financial Health Score (0–100) across 5 dimensions.
    Uses both credit and wellness data.
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    credit = run_credit_scoring(profile)

    income = profile["income_30d"]
    expense = profile["expense_30d"]
    savings_rate = profile["savings_rate_pct"]
    emi_ratio = profile["emi_to_income_pct"]
    balance = profile["total_balance"]

    # Component scores (0–20 each = 100 total)
    savings_score = min(savings_rate / 25 * 20, 20)
    debt_score = max(20 - emi_ratio / 2, 0)
    buffer_score = min(balance / max(expense, 1) / 3 * 20, 20)

    gig_score = credit.get("credit_score", {}).get("gig_score", 500)
    credit_score_norm = (gig_score - 300) / 550 * 20

    activity_score = min(len(profile["recent_transactions"]) / 30 * 20, 20)

    total = round(savings_score + debt_score + buffer_score + credit_score_norm + activity_score)
    total = max(0, min(100, total))

    if total >= 80:
        grade, verdict = "A", "Excellent financial health!"
    elif total >= 65:
        grade, verdict = "B", "Good — a few areas to improve"
    elif total >= 50:
        grade, verdict = "C", "Fair — take action on savings and debt"
    else:
        grade, verdict = "D", "Needs attention — let's build a plan together"

    result = {
        "health_score": total,
        "grade": grade,
        "verdict": verdict,
        "components": {
            "savings_behaviour_20": round(savings_score, 1),
            "debt_management_20": round(debt_score, 1),
            "emergency_buffer_20": round(buffer_score, 1),
            "credit_profile_20": round(credit_score_norm, 1),
            "account_activity_20": round(activity_score, 1),
        },
        "agent_mode": "live" if is_live_mode() else "deterministic",
    }
    _audit(user_id, "health", "health", result, (time.time() - t0) * 1000, db)
    return result


def get_asset_loan_eligibility(user_id: str, db: Session, asset_type: str, asset_price: float) -> dict:
    """
    Runs the Asset-Backed Gig Loan eligibility check.
    asset_type: 'bike' | 'phone' | 'laptop' | 'equipment'
    asset_price: purchase price in SGD
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_asset_loan_eligibility(profile, asset_type, asset_price)
    result["agent_mode"] = "live" if is_live_mode() else "deterministic"
    _audit(user_id, "asset_loan", f"asset_loan:{asset_type}:S${asset_price:,.0f}", result, (time.time() - t0) * 1000, db)
    return result


def get_dynamic_loan_rate_review(
    user_id: str, db: Session,
    base_rate: float, current_rate: float,
    asset_type: str = "bike",
    outstanding: float = 0.0,
    remaining_months: int = 12,
) -> dict:
    """
    Run a weekly dynamic rate review for an active asset-backed loan.
    Scores the user's current financial behaviour across 5 dimensions
    and computes whether the rate should move up, down, or hold.
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_dynamic_rate_review(
        profile, base_rate, current_rate, asset_type, outstanding, remaining_months
    )
    result["agent_mode"] = "live" if is_live_mode() else "deterministic"
    _audit(user_id, "dynamic_rate_review", f"rate_review:{asset_type}:base={base_rate}%", result, (time.time() - t0) * 1000, db)
    return result


def get_peak_hours_schedule(user_id: str, db: Session, weekly_target: float) -> dict:
    """
    Runs the Peak Hours Earnings Optimiser.
    weekly_target: desired weekly income in SGD (0 = auto 20% above current avg)
    """
    t0 = time.time()
    profile = _profile(user_id, db)
    result = run_peak_hours_optimiser(profile, weekly_target)
    result["agent_mode"] = "live" if is_live_mode() else "deterministic"
    result["data_source"] = {
        "has_hourly_data": bool(profile.get("hourly_income")),
        "has_dow_data":    bool(profile.get("dow_avg_income")),
        "income_30d":      profile["income_30d"],
    }
    _audit(user_id, "peak_hours_optimiser", f"peak_hours:target=S${weekly_target:,.0f}", result, (time.time() - t0) * 1000, db)
    return result


def run_chat(user_id: str, message: str, db: Session) -> dict:
    """
    Conversational AI agent that answers natural-language financial questions
    using the user's real data as context.
    - CrewAI available: full agent-based chat
    - API key only (no crewai): direct SDK call
    - Neither: keyword-based deterministic response
    """
    profile = _profile(user_id, db)

    if is_crewai_mode():
        try:
            return _live_chat(profile, message)
        except Exception as e:
            log.exception("CrewAI chat failed; falling back")
            return {**_fallback_chat(profile, message), "chat_error": str(e)}

    if is_live_mode():
        try:
            return _direct_llm_chat(profile, message)
        except Exception as e:
            log.exception("Direct LLM chat failed; falling back")
            return {**_fallback_chat(profile, message), "chat_error": str(e)}

    return _fallback_chat(profile, message)


def _direct_llm_chat(profile: dict, message: str) -> dict:
    """Direct SDK call when crewai is unavailable (e.g. Python 3.14)."""
    categories = profile.get('expense_by_category', profile.get('expense_by_type', {}))
    ctx = (
        f"Balance: S${profile['total_balance']:,.2f}, "
        f"Income(30d): S${profile['income_30d']:,.2f}, "
        f"Expenses(30d): S${profile['expense_30d']:,.2f}, "
        f"Savings rate: {profile['savings_rate_pct']}%, "
        f"Active loans: {profile['active_loans_count']}, "
        f"Monthly EMI: S${profile['total_monthly_emi']:,.2f}, "
        f"Expense categories: {json.dumps(categories)}"
    )
    prompt = (
        f"User's financial data: {ctx}\n\n"
        f"User question: {message}\n\n"
        "Answer in 2-3 sentences using the real numbers. "
        'Reply as JSON: {"answer": "...", "action_tip": "one actionable step"}'
    )
    system = (
        "You are a friendly, concise financial advisor at GXS Bank for Grab drivers. "
        "Always personalise your answer using the user's real financial numbers."
    )
    raw = direct_llm_call(prompt, system)
    parsed = _extract_json_payload(raw)
    if parsed:
        return {
            "mode": "direct_llm",
            "answer": str(parsed.get("answer", raw)).strip(),
            "action_tip": str(parsed.get("action_tip", "")).strip(),
        }
    return {"mode": "direct_llm", "answer": raw or "I couldn't process that right now.", "action_tip": ""}


def _live_chat(profile: dict, message: str) -> dict:
    """CrewAI single-agent conversational response."""
    from crewai import Agent, Crew, Process, Task

    from com.gxs.bank.agents.llm_config import get_llm

    llm = get_llm()

    import json
    ctx = f"""
User's financial profile:
- Balance: S${profile['total_balance']:,.2f}
- Income (30d): S${profile['income_30d']:,.2f}
- Expenses (30d): S${profile['expense_30d']:,.2f}
- Savings (30d): S${profile['savings_30d']:,.2f}
- Savings rate: {profile['savings_rate_pct']}%
- Active loans: {profile['active_loans_count']}
- Monthly EMI: S${profile['total_monthly_emi']:,.2f}
- Expense breakdown: {json.dumps(profile['expense_by_type'])}
"""

    advisor = Agent(
        role="Personal Financial Advisor",
        goal="Answer the user's financial question clearly and helpfully using their real account data.",
        backstory=(
            "You are a friendly, concise financial advisor at GXS Bank. "
            "You always refer to the user's real numbers. "
            "You never give generic advice — every answer is personalised."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task = Task(
        description=(
            f"User question: '{message}'\n\n"
            f"Context:\n{ctx}\n\n"
            "Answer in 2-4 sentences. Be specific, use real numbers from the profile. "
            "Output JSON: {{\"answer\": \"...\", \"action_tip\": \"one actionable step\"}}"
        ),
        expected_output="JSON with answer and action_tip",
        agent=advisor,
    )

    crew = Crew(agents=[advisor], tasks=[task], process=Process.sequential, verbose=False)
    crew.kickoff()

    raw = str(task.output.raw if hasattr(task.output, "raw") else task.output)
    parsed = _extract_json_payload(raw)
    if parsed:
        answer = str(parsed.get("answer", raw)).strip()
        tip = str(parsed.get("action_tip", "")).strip()
    else:
        answer = raw
        tip = ""

    return {"mode": "live_crew", "answer": answer, "action_tip": tip}


def _fallback_chat(profile: dict, message: str) -> dict:
    """Keyword-based response when no LLM is available."""
    msg = message.lower()
    income = profile["income_30d"]
    expense = profile["expense_30d"]
    savings = profile["savings_30d"]
    balance = profile["total_balance"]
    rate = profile["savings_rate_pct"]
    emi = profile["total_monthly_emi"]
    categories = profile.get("expense_by_category", {})

    if any(w in msg for w in ["hi", "hello", "hey", "greetings"]):
        return {
            "mode": "deterministic_fallback",
            "answer": "Hello! I am your AI Financial Advisor. I can help you with your banking, savings, loans, and financial planning. How can I assist you today?",
            "action_tip": "Try asking 'Am I eligible for a loan?' or 'How much did I spend this month?'",
            "intent": "chat",
            "agents_called": ["fallback_router"],
            "routing_chain": [
                "1. Received user message and extracted financial profile.",
                "2. Matched harmless greeting intent.",
                "3. Routed to deterministic rules engine.",
                "4. Returned a friendly finance-focused response."
            ],
        }

    if any(phrase in msg for phrase in ["what can you do", "what do you do", "help me", "can you help", "who are you"]):
        return {
            "mode": "deterministic_fallback",
            "answer": "I’m your GXS financial advisor. I can help with balances, spending, savings, loans, fraud alerts, GigScore, and personalised money planning. Ask me a finance question and I’ll use your real numbers.",
            "action_tip": "Try asking about your spending, savings rate, or loan eligibility.",
            "intent": "chat",
            "agents_called": ["fallback_router"],
            "routing_chain": [
                "1. Received user message and extracted financial profile.",
                "2. Detected a harmless capability / help question.",
                "3. Routed to deterministic rules engine.",
                "4. Returned a brief finance-focused steering response."
            ],
        }

    if any(w in msg for w in ["food", "dining", "eat", "restaurant", "swiggy", "zomato"]):
        food_amt = categories.get("Food & Dining", 0)
        answer = f"You spent S${food_amt:,.2f} on Food & Dining this month."
        tip = "Cooking at home 3 days a week can cut food costs by 30%."

    elif any(w in msg for w in ["transport", "fuel", "grab", "ride", "petrol", "travel"]):
        transport_amt = categories.get("Transport & Fuel", 0)
        answer = f"You spent S${transport_amt:,.2f} on Transport & Fuel this month."
        tip = "Carpooling or off-peak rides can reduce transport costs significantly."

    elif any(w in msg for w in ["entertain", "netflix", "subscription", "movie", "streaming"]):
        ent_amt = categories.get("Entertainment", 0)
        answer = f"You spent S${ent_amt:,.2f} on Entertainment & subscriptions this month."
        tip = "Review recurring subscriptions — cancel ones you use less than twice a week."

    elif any(w in msg for w in ["shop", "amazon", "flipkart", "purchase", "bought"]):
        shop_amt = categories.get("Shopping", 0)
        answer = f"You spent S${shop_amt:,.2f} on Shopping this month."
        tip = "Use a 24-hour rule before non-essential purchases to reduce impulse buying."

    elif any(w in msg for w in ["bill", "utility", "electricity", "water", "internet"]):
        bills_amt = categories.get("Bills & Utilities", 0)
        answer = f"You spent S${bills_amt:,.2f} on Bills & Utilities this month."
        tip = "Set up autopay for bills to avoid late fees."

    elif any(w in msg for w in ["balance", "how much", "account"]):
        answer = f"Your current balance is S${balance:,.2f}."
        tip = "Consider moving idle funds to a Fixed Deposit for better interest."

    elif any(w in msg for w in ["income", "earn", "salary"]):
        answer = (
            f"You earned S${income:,.2f} in the last 30 days "
            f"(avg S${income/30:,.0f}/day)."
        )
        tip = "Weekend rides typically earn 30–40% more — optimise your schedule."

    elif any(w in msg for w in ["expense", "spend", "spending", "category", "breakdown"]):
        if categories:
            top = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join(f"{c}: S${a:,.0f}" for c, a in top)
            answer = f"You spent S${expense:,.2f} this month. Top categories: {top_str}."
        else:
            answer = f"You spent S${expense:,.2f} this month across all categories."
        tip = "Your top spending category has the most room for savings."

    elif any(w in msg for w in ["save", "saving", "savings"]):
        answer = (
            f"You saved S${savings:,.2f} this month — a {rate:.1f}% savings rate. "
            f"{'Great job!' if rate >= 20 else 'Try to increase this to 20%.'}"
        )
        tip = f"Set up an auto-transfer of S${round(income * 0.05):,.0f} every week to savings."

    elif any(w in msg for w in ["loan", "emi", "debt", "borrow"]):
        answer = (
            f"You have S${profile['total_outstanding_debt']:,.2f} outstanding "
            f"with S${emi:,.2f}/month in EMIs."
        )
        tip = "Pre-paying even 5% of principal reduces interest significantly."

    elif any(w in msg for w in ["low", "why", "negative", "less"]):
        answer = (
            f"Your income was S${income:,.2f} and expenses S${expense:,.2f}, "
            f"leaving S${savings:,.2f} as net savings this month."
        )
        tip = "Track daily spending to identify and reduce unnecessary costs."

    else:
        if categories:
            top = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:2]
            top_str = ", ".join(f"{c}: S${a:,.0f}" for c, a in top)
            answer = (
                f"This month: income S${income:,.2f}, expenses S${expense:,.2f}, "
                f"savings S${savings:,.2f} ({rate:.1f}% rate). "
                f"Top spending: {top_str}."
            )
        else:
            answer = (
                f"This month: income S${income:,.2f}, expenses S${expense:,.2f}, "
                f"savings S${savings:,.2f} ({rate:.1f}% rate). Balance: S${balance:,.2f}."
            )
        tip = "Ask me about food, transport, shopping, bills, savings, or loans."

    return {"mode": "deterministic_fallback", "answer": answer, "action_tip": tip}
